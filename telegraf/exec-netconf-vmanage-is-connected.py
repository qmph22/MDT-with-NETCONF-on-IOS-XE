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
            <system xmlns="http://viptela.com/system">
                <vmanage-is-connected/>
            </system>
        </filter>
        """
    # Attempt to connect to every router. Upon a successful connection, subscribe to the telemetry data
    for router in routers:
        if connectRouter(router=router, config=config):
            for manager in routerManagers:
                netconf_rpc_reply = routerManagers[manager].get(
                            filter = netconf_filter
                        ).xml
                netconf_reply_dict = xmltodict.parse(netconf_rpc_reply)
                telegraf_json_input = dict_to_telegraf_json(netconf_reply_dict, router)
                # telegraf needs data in a certain data format.
                # I have chosen JSON data that will be picked up by the exec plugin
                print(telegraf_json_input)
        else:
            logging.warning(f"Unable to connect to {router}")


if __name__ == "__main__":
    main()
