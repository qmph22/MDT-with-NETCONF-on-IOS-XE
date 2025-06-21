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

routerManagers = {}

def dict_to_telegraf_json(rpc_reply_dict: Dict, hostname: str) -> str:
    """
    """

    stats_array = []
    dict = {
        "vmanage-is-connected": 1 if rpc_reply_dict["rpc-reply"]["data"]["system"]["vmanage-is-connected"]=="true" else 0,
        "field": "system"
    }  # trying to get rate of consumption of processes
    if hostname:
        dict.update({"hostname": hostname})
    stats_array.append(dict)

    return json.dumps(stats_array)  # return JSON formatted data

def parseRPC(rpc_reply_dict: Dict, hostname: str) -> list:
    """
    """
    sessionArray = []
    for session in rpc_reply_dict['rpc-reply']['data']['bfd']['sessions-list']:
        dict = {
            "protocol": session['proto'],
            "remote-system-ip": session['system-ip'],
            "remote-site-id": session['site-id'],
            "local-color": session['local-color'],
            "remote-color": session['color'],
            "state": 1 if session['state']=="up" else 0,
            "field": "bfd_sessions"
        }
        
        if hostname:
            dict.update({"hostname": hostname})
        sessionArray.append(dict) 

    return sessionArray  # return array of data

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
                    except:
                        logger.warning(f"Credential {[config['devices'][router]['credentials'][credential]['password_env']]} for {router} failed on attempt {i + 1}")
                        routerManagers.update({router: None})
            if success:
                return True
            else:
                return False


def main():
    load_dotenv()

    with open('networkdevices.yml', 'r') as file:
        config = yaml.safe_load(file)

    routers = list(config['devices'].keys())

    netconf_filter = """
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
            <bfd xmlns="http://viptela.com/bfd">
                <sessions-list/>
            </bfd>
        </filter>
        """
    # Attempt to connect to every router. Upon a successful connection, subscribe to the telemetry data
    collectedJson = []
    parsedJSON = []
    for router in routers:
        if connectRouter(router=router, config=config):
            netconf_rpc_reply = routerManagers[router].get(
                        filter = netconf_filter
                    ).xml
            netconf_reply_dict = xmltodict.parse(netconf_rpc_reply)
            telegraf_json_input = parseRPC(netconf_reply_dict, router)
            collectedJson.append(telegraf_json_input)
            parsedJSON.append(parseRPC(netconf_reply_dict, router))
        else:
            logging.warning(f"Unable to connect to {router}")
    if len(collectedJson) != 0:
        jsonArray = []
        # Arrange the data in a way that the exec plugin of Telegraf requires
        for router in parsedJSON:
            jsonArray.extend(router)
        print(json.dumps(jsonArray))

if __name__ == "__main__":
    main()
