from typing import Dict
import xmltodict
import json
from dotenv import load_dotenv
import os
import yaml
import sys
sys.path.append('ncclient')
from ncclient import manager # type: ignore
import time
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.WARNING)

# This should be a dictionary of lists. The key is always a router and the value is always a list representing the router's current active subscriptions.
# defaultdict(list) allows us to call the update method on a key in the dictionary without having to first check whether the value exists. We can simply call the update method without checking if the router exists first.
activeSubscriptions = defaultdict(list)
# This should be a dictionary. The key is always a router and the value is always the router's Manager instance from ncclient. If the value is None, an attempt has been made but there is a problem with connecting to the router.
routerManagers = {}

def notificationCallback(notif):
    """Callback to process telemetry notifications."""
    try:
        logger.debug('Trying notificationCallback')
        rpc_reply_dict = xmltodict.parse(notif.xml)
        logger.debug('Sucessfully parsed notification in notificationCallback')
    except:
        logger.error(f"Issue with {notif} from callback")
        return
    subscriptionID = notif.subscription_id
    hostname = ''
    try:
        logger.debug('Trying to get the router associated with the subscription ID {subscriptionID}')
        #hostname = subscriptions[subscriptionID]['hostname']
        for router in activeSubscriptions:
                for subscription in activeSubscriptions[router]:
                    if subscription['subscription_id'] == subscriptionID:
                        hostname = router
                        logger.debug('Sucessfully found the router associated with the subscription ID {subscriptionID}')
        if hostname == '':
            logger.debug('Unable to find hostname associated with subscription ID {subscriptionID}')
    except:
        hostname = ''
        logger.debug('Unable to find hostname associated with subscription ID {subscriptionID}. It could be due to subscription ID could not be read from the callback or the hostname and subscription IDs not being stored in the activeSubscriptions variable yet')

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
                    # Radio Access Technology mappings according to typedef rat-technology of https://github.com/YangModels/yang/blob/main/vendor/cisco/xe/17121/Cisco-IOS-XE-cellwan-oper.yang
                    rat_technology_mapping = {
                        "system-mode-none": {
                            "value": 0,
                            "description": "Radio technology selected is none"
                        },
                        "system-mode-gprs": {
                            "value": 1,
                            "description": "Radio technology selected is GPRS (General Packet Radio Service)"
                        },
                        "system-mode-edge": {
                            "value": 2,
                            "description": "Radio technology selected is EDGE (Enhanced Data rates for GSM Evolution)"
                        },
                        "system-mode-umts": {
                            "value": 3,
                            "description": "Radio technology selected is UMTS (Universal Mobile Telecommunications System)"
                        },
                        "system-mode-hsdpa": {
                            "value": 4,
                            "description": "Radio technology selected is HSDPA (High Speed Downlink Packet Access)"
                        },
                        "system-mode-hsupa": {
                            "value": 5,
                            "description": "Radio technology selected is HSUPA (High Speed Uplink Packet Access)"
                        },
                        "system-mode-hspa": {
                            "value": 6,
                            "description": "Radio technology selected is HSPA (High Speed Packet Access)"
                        },
                        "system-mode-hspa-plus": {
                            "value": 7,
                            "description": "Radio technology selected is HSPA+ (Evolved High Speed Packet Access)"
                        },
                        "system-mode-lte-fdd": {
                            "value": 8,
                            "description": "Radio technology selected is LTE-FDD (Long Term Evolution-Frequency Division Duplex)"
                        },
                        "system-mode-lte-tdd": {
                            "value": 9,
                            "description": "Radio technology selected is LTE-TDD (Long Term Evolution-Time Division Duplex)"
                        },
                        "system-mode-lte-e-hrpd-1x-rtt": {
                            "value": 10,
                            "description": "Radio technology selected is LTE / eHRPD / 1xRTT"
                        },
                        "system-mode-lte-e-hrpd-evdo": {
                            "value": 11,
                            "description": "Radio technology selected is LTE / eHRPD / EVDO"
                        },
                        "system-mode-evdo": {
                            "value": 12,
                            "description": "Radio technology selected is EVDO (Evolution-Data Optimized)"
                        },
                        "system-mode-evdo-reva": {
                            "value": 13,
                            "description": "Radio technology selected is EVDO / REVA"
                        },
                        "system-mode-hsdpa-n-wcdma": {
                            "value": 14,
                            "description": "Radio technology selected is HSDPA & WCDMA"
                        },
                        "system-mode-wcdma-n-hsupa": {
                            "value": 15,
                            "description": "Radio technology selected is WCDMA & HSUPA"
                        },
                        "system-mode-hsdpa-n-hsupa": {
                            "value": 16,
                            "description": "Radio technology selected is HSDPA & HSUPA"
                        },
                        "system-mode-hsdpa-plus-n-wcdma": {
                            "value": 17,
                            "description": "Radio technology selected is HSDPA+ & WCDMA"
                        },
                        "system-mode-hsdpa-plus-n-hsupa": {
                            "value": 18,
                            "description": "Radio technology selected is HSDPA+ & HSUPA"
                        },
                        "system-mode-dc-hsdpa-plus-n-wcdma": {
                            "value": 19,
                            "description": "Radio technology selected is DC HSDPA+ & WCDMA"
                        },
                        "system-mode-dc-hsdpa-plus-n-hsupa": {
                            "value": 20,
                            "description": "Radio technology selected is DC HSDPA+ & HSUPA"
                        },
                        "system-mode-null-bearer": {
                            "value": 21,
                            "description": "Radio technology selected is null bearer"
                        },
                        "system-mode-unknown": {
                            "value": 22,
                            "description": "Radio technology selected is unknown"
                        }
                    }
                    for cellularModem in rpc_reply_dict['notification']['push-update']['datastore-contents-xml']["cellwan-oper-data"]["cellwan-radio"]:
                        if "online" in str(cellularModem["radio-power-mode"]):
                            dict = {
                                "name": cellularModem["cellular-interface"],
                                "radio_rssi": float(cellularModem["radio-rssi"]),
                                "radio_rsrp": float(cellularModem["radio-rsrp"]),
                                "radio_rsrq": float(cellularModem["radio-rsrq"]),
                                "radio_snr": float(cellularModem["radio-snr"]),
                                "radio-rat-selected": rat_technology_mapping[str(cellularModem["radio-rat-selected"])]['value'],
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

                # case "bfd": # For some reason, some routers are replying with nothing in 'datastore-contents-xml'
                #     array = []
                #     # Can be pulled via netconf get but not via yang-push
                #     # for session in rpc_reply_dict['notification']['push-update']['datastore-contents-xml']["bfd"]["sessions-list"]:
                #     #     dict = {
                #     #         "protocol": session['proto'],
                #     #         "system-ip": session['system-ip'],
                #     #         "site-id": session['site-id'],
                #     #         "local-color": session['local-color'],
                #     #         "remote-color": session['color'],
                #     #         "state": session['state'],                                                                                     
                #     #         "field": "bfd_sessions"
                #     #     }  
                #     for tloc in rpc_reply_dict['notification']['push-update']['datastore-contents-xml']["bfd"]["tloc-summary-list"]:
                #         dict = {
                #             "name": tloc['if-name'],
                #             "sessions-up": tloc['sessions-up'],
                #             "sessions-total": tloc['sessions-total'],                                                                                     
                #             "field": "bfd_sessions"
                #         }  
                #         if hostname:
                #             dict.update({"hostname": hostname})
                #         array.append(dict)
                #     print(json.dumps(array))

                # case _:
                #     print(f"No matching case for {content}",file=sys.stderr)
                #     logger.error(f"No matching case for {content}")

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

def connectRouter(router: str, config, reattempts=3):
        assert reattempts > 0
        credentials = config['devices'][router]['credentials']
        success = False
        for i in range(0, reattempts):
            if success is not True:
                for credential in credentials.keys():
                    try:
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
                        routerManagers.update({router: m})
                        success = True
                        break
                    except Exception as e:
                        logger.warning(f"Credential {[config['devices'][router]['credentials'][credential]['password_env']]} for {router} failed on attempt {i + 1}. Exception: {e}")
                        routerManagers.update({router: None})
            if success:
                return True
            else:
                return False

def subscribe(router: str, config):
        manager = routerManagers[router]
        subs = []
        period = 100 #centiseconds
        #dampening_period = 100 #centiseconds, pick one or the other

        # Get xpaths from provided config
        xpaths = list(config['devices'][router]['xpaths'])
        for xpath in xpaths:
            s = manager.establish_subscription(
                notificationCallback,
                subscriptionErrorCallback,
                xpath=xpath,
                period=period
                )
            logger.info('Subscription Result : %s' % s.subscription_result)
            if s.subscription_result.endswith('ok'):
                logger.info('Subscription Id     : %d' % s.subscription_id)
                subs.append(s.subscription_id)
                activeSubscriptions[router].insert(0, {'subscription_id': s.subscription_id, 'xpath': xpath})            
                # Remove old subscriptions that have the same xpath
                subscriptionToDelete = []

                for subscription in activeSubscriptions[router]:
                    if subscription['subscription_id'] != s.subscription_id and subscription['xpath'] == xpath:
                        logger.debug(f"Marking subscription {subscription} for removal.")
                        subscriptionToDelete.append(subscription)
                        logger.debug(f"subscriptionToDelete is now {subscriptionToDelete}")
                for oldSubscription in subscriptionToDelete:
                    activeSubscriptions[router].remove(oldSubscription)
                
        if not len(subs):
            logger.info('No active subscriptions')
            return False
        logger.info(f"Subscription(s) to {router} established.")
        return True

def main():
    # Load environment variables from a .env file. Will need to handle this at some point since the Telegraf container also has the environmental variables
    load_dotenv()

    # Open the config file
    with open('networkdevices.yml', 'r') as file:
        config = yaml.safe_load(file)

    # Read the names of the routers from the config file
    routers = list(config['devices'].keys())

    # Attempt to connect to every router. Upon a successful connection, subscribe to the telemetry data
    for router in routers:
        if connectRouter(router=router, config=config):
            if subscribe(router=router, config=config):
                logging.info(f"Subscribed to telemetry from router {router}")
            else:
                logging.warning(f"Unable to subscribe to telemetry from router {router} on the first attempt")
        else:
            logging.error(f"Unable to connect to {router} on the first attempt")

    # A loop to keep the program running. The listeners from the ncclient will use the callback notificationCallback whenever there are notifications from the routers.
    # While we're using cycles, attempt to reconnect and resubscribe for any routers that have lost their connection. Will need to see if I can do this in an async manner.
    while True:
        managers = routerManagers
        if len(managers) > 0: # Without this, the script may fail on startup.
            for router in managers:
                if managers.get(router) is None:
                    if connectRouter(router=router, config=config, reattempts=1):
                        logging.info(f"Reconnected to router {router}")
                        if subscribe(router=router, config=config):
                            logging.info(f"Re-subscribed to telemetry from router {router}")
                    else:
                        logger.warning(f"Failed to reconnect to router {router}")     
                else:
                    if not routerManagers[router].connected:
                        logger.warning(f"Router {router} has lost connection while streaming. Reconnecting.")
                        if connectRouter(router=router, config=config, reattempts=1):
                            logging.info(f"Reconnected to router {router}")
                            if subscribe(router=router, config=config):
                                logging.info(f"Re-subscribed to telemetry from router {router}")
        time.sleep(.25) # If this is not present, the CPU utilization can go to 100%

if __name__ == "__main__":
    main()
