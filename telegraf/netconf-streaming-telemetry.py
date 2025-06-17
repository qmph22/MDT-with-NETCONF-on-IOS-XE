from typing import Dict
import xmltodict
import json
from dotenv import load_dotenv
import os
import yaml
import sys
sys.path.append('ncclient')
from ncclient import manager
import time
import logging

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.WARNING)

subscriptions = {}
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
        hostname = subscriptions[subscriptionID]['hostname']
        logger.debug('Sucessfully found the router associated with the subscription ID {subscriptionID}')
    except:
        hostname = ''
        logger.debug('Subscription ID could not be read from the callback. It could be due to the hostname and subscription IDs not being stored in the subscriptions variable yet')

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

                case "sessions-list":
                    array = []
                    for session in rpc_reply_dict['notification']['push-update']['datastore-contents-xml']["bfd"]["sessions-list"]:
                        dict = {
                            "protocol": session['proto'],
                            "system-ip": session['system-ip'],
                            "site-id": session['site-id'],
                            "local-color": session['local-color'],
                            "remote-color": session['color'],
                            "state": session['state'],                                                                                     
                            "field": "bfd_sessions"
                        }  
                        if hostname:
                            dict.update({"hostname": hostname})
                        array.append(dict)
                    print(json.dumps(array))

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
                subscriptions.update({s.subscription_id: {"hostname": router, "xpath": xpath}})
                
                # Remove old subscriptions that have the same xpath
                subscriptionToDelete = []
                for subscription in subscriptions: 
                    if subscriptions[subscription]['xpath'] == xpath and subscription != s.subscription_id:
                        logger.debug(f"Marking subscription {subscription} for removal.")
                        subscriptionToDelete.append(subscription)
                        logger.debug(f"subscriptionToDelete is now {subscriptionToDelete}")
                for oldSubscription in subscriptionToDelete:
                    subscriptions.pop(oldSubscription)
                    logger.debug(f"subscriptions after pop of {oldSubscription} is now {subscriptions}")
                
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
