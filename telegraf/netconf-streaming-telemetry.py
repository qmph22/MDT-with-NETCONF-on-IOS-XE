from typing import Dict
from ncclient import manager
import xmltodict
import json
from dotenv import load_dotenv
import os
import yaml
import sys
#from lxml import etree 
import time
import logging

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.DEBUG)

subscriptions = {}

def notificationCallback(notif) -> str:
    """Callback to process telemetry notifications."""
    try:
        rpc_reply_dict = xmltodict.parse(notif.xml)
    except:
        print(f"Issue with {notif}")
    subscriptionID = notif.subscription_id
    hostname = ''
    try:
        hostname = subscriptions[subscriptionID]
    except:
        hostname = ''
        print('not ready')

    if rpc_reply_dict['notification']['push-update']:
        for content in rpc_reply_dict['notification']['push-update']['datastore-contents-xml']:
            match content:
                case "cpu-usage":
                        stats_array = []
                        for item, value in rpc_reply_dict['notification']['push-update']['datastore-contents-xml']['cpu-usage']["cpu-utilization"].items():
                            dict = {
                                "time_period": item,
                                "percentage": float(value),
                                "field": "cpu_utilization"
                            }
                            if hostname:
                                dict.update({"hostname": hostname})
                            stats_array.append(dict)
                        print(json.dumps(stats_array))  # return JSON formatted data
                        
                case "cellwan-oper-data":
                    stats_array = []
                    for cellularModem in rpc_reply_dict['notification']['push-update']['datastore-contents-xml']["cellwan-oper-data"]["cellwan-radio"]:
                        if "online" in str(cellularModem["radio-power-mode"]):
                            dict = {
                                "name": cellularModem["cellular-interface"],
                                "radio_rssi": float(cellularModem["radio-rssi"]),
                                "radio_rsrp": float(cellularModem["radio-rsrp"]),
                                "radio_rsrq": float(cellularModem["radio-rsrq"]),
                                "radio_snr": float(cellularModem["radio-snr"]),
                                "field": "cellular_modem"
                            }
                            if hostname:
                                dict.update({"hostname": hostname})
                            stats_array.append(dict)
                    print(json.dumps(stats_array))

                case "interfaces":
                    stats_array = []
                    for intf_entry in rpc_reply_dict['notification']['push-update']['datastore-contents-xml']["interfaces"]["interface"]:
                        intf_name = intf_entry["name"].replace(" ", "_")
                        dict = {
                            "admin_status": 1 if intf_entry["admin-status"]=="if-state-up" else 0,
                            "operational_status": 1 if intf_entry["oper-status"]=="if-oper-state-ready" else 0,
                            "in_octets": int(intf_entry["statistics"]["in-octets"]),
                            "in_errors": int(intf_entry["statistics"]["in-errors"]),
                            "out_octets": int(intf_entry["statistics"]["out-octets"]),
                            "out_errors": int(intf_entry["statistics"]["out-errors"]),
                            "name": intf_name,
                            "field": "intf_stats"
                        }
                        if hostname:
                            dict.update({"hostname": hostname})
                        stats_array.append(dict)
                    print(json.dumps(stats_array))

                case "memory-statistics":
                    stats_array = []
                    for memory_entry in rpc_reply_dict['notification']['push-update']['datastore-contents-xml']["memory-statistics"]["memory-statistic"]:
                        dict = {
                            "name": memory_entry["name"],
                            "percent_used": ( int(memory_entry["used-memory"])/int(memory_entry["total-memory"]) ) * 100,
                            "field": "memory_pool"
                        } 
                        if hostname:
                            dict.update({"hostname": hostname})
                        stats_array.append(dict)
                    print(json.dumps(stats_array))

                case "memory-usage-processes":
                    stats_array = []
                    for process_entry in rpc_reply_dict['notification']['push-update']['datastore-contents-xml']["memory-usage-processes"]["memory-usage-process"]:
                        if int(process_entry["allocated-memory"]) > 0:
                            dict = {
                                "name": process_entry["name"].replace(" ", "_"),
                                "process_id": int(process_entry["pid"]),
                                "consumed_bytes": int(process_entry["holding-memory"]),
                                "field": "cpu_process"
                            }  # trying to get rate of consumption of processes
                            if hostname:
                                dict.update({"hostname": hostname})
                            stats_array.append(dict)
                    print(json.dumps(stats_array))

                case _:
                    print(f"No matching case for {content}",file=sys.stderr)
                    logger.error(f"No matching case for {content}")

def subscriptionCallback(notif):
    print('-->>')
    print('(Not Default Callback)')
    print('Event time      : %s' % notif.event_time)
    print('Subscription Id : %d' % notif.subscription_id)
    print('Type            : %d' % notif.type)
    print('Data            :')
    print(notif)
    #print(etree.tostring(notif, pretty_print=True).decode('utf-8'))
    print('<<--')

def subscriptionErrorCallback(notif):
    logging.error(notif)
    pass

def main():
    load_dotenv()

    with open('networkdevices.yml', 'r') as file:
        config = yaml.safe_load(file)

    routers = list(config['devices'].keys())

    for router in routers:
            credentials = config['devices'][router]['credentials']
            for credential in credentials.keys():
                m = manager.connect(
                    host=config['devices'][router]['host'],
                    port=config['devices'][router]['port'],
                    username=config['devices'][router]['credentials'][credential]['username'],
                    password=os.environ[config['devices'][router]['credentials'][credential]['password_env']],
                    hostkey_verify=bool(config['devices'][router]['hostkey_verify']),
                    device_params=config['devices'][router]['device_params'],
                    allow_agent=False,
                    look_for_keys=False,
                    timeout=300,
                    keepalive=True
                )
                subs = []
                xpaths = [
                    "/process-cpu-ios-xe-oper:cpu-usage/cpu-utilization/five-seconds", 
                    "/cellwan-ios-xe-oper:cellwan-oper-data/cellwan-radio",
                    "/interfaces-ios-xe-oper:interfaces/interface",
                    "/memory-ios-xe-oper:memory-statistics/memory-statistic",
                    "/process-memory-ios-xe-oper:memory-usage-processes/memory-usage-process"
                    ]
                period = 1000 #centiseconds
                #dampening_period = 100 #centiseconds, pick one or the other
                for xpath in xpaths:
                    s = m.establish_subscription(
                        notificationCallback,
                        subscriptionErrorCallback,
                        xpath=xpath,
                        period=period
                        )
                    logger.info('Subscription Result : %s' % s.subscription_result)
                    if s.subscription_result.endswith('ok'):
                        logger.info('Subscription Id     : %d' % s.subscription_id)
                        subs.append(s.subscription_id)
                        subscriptions.update({s.subscription_id: router})
                if not len(subs):
                    logger.info('No active subscriptions')
                logger.info(f"Subscription(s) to {router} established.")
    while True:
        # print("Checking notifications")
        # notification = m.t ake_notification(block=False)
        # if notification:
        #     print(etree.tostring(notification.notification_ele, pretty_print=True).decode('utf-8'))
        # else:
        #     print("None")
        #print(f"Is connected: {m.connected}")
        time.sleep(5)


if __name__ == "__main__":
    main()
