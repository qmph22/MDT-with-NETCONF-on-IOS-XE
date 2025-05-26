from typing import Dict
from ncclient import manager
import xmltodict
import json
from dotenv import load_dotenv
import os
import yaml
import sys

def dict_to_telegraf_json(rpc_reply_dict: Dict) -> str:
    """
    """

    cpu_process_stats_array = []

    for process_entry in rpc_reply_dict["rpc-reply"]["data"]["memory-usage-processes"]["memory-usage-process"]:
        if int(process_entry["allocated-memory"]) > 0:
            process_dict = {
                "name": process_entry["name"].replace(" ", "_"),
                "process_id": int(process_entry["pid"]),
                "consumed_bytes": int(process_entry["holding-memory"]),
                "field": "cpu_process"
            }  # trying to get rate of consumption of processes
            cpu_process_stats_array.append(process_dict)

    return json.dumps(cpu_process_stats_array)  # return JSON formatted data


def main():

    load_dotenv()

    with open('networkdevices.yml', 'r') as file:
        config = yaml.safe_load(file)
    
    # https://github.com/YangModels/yang/blob/master/vendor/cisco/xe/16111/Cisco-IOS-XE-process-memory-oper.yang
    netconf_filter = """
    <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <memory-usage-processes xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-process-memory-oper">
            <memory-usage-process>
                <name/>
                <pid/>
                <allocated-memory/>
                <freed-memory/>
                <holding-memory/>
            </memory-usage-process>
        </memory-usage-processes>
    </filter>
    """
    
    routers = list(config['devices'].keys())
    for deviceIndex in range(0, len(config['devices'])):
        for router in routers:
            try:
                credentials = list(config['devices'][router]['credentials'].keys())
                for credential in credentials:
                    with manager.connect(
                        host = config['devices'][router]['host'],  # Locally connected device. Will eventually make this a configurable item
                        port = config['devices'][router]['port'],
                        username = config['devices'][router]['credentials'][credential]['username'],
                        password = os.environ[config['devices'][router]['credentials'][credential]['password_env']],  # <--------- enter device password
                        hostkey_verify = bool(config['devices'][router]['hostkey_verify']),
                        device_params = config['devices'][router]['device_params']
                    ) as m:
                        netconf_rpc_reply = m.get(
                            filter = netconf_filter
                        ).xml
                    break
                
            except Exception as e:
                print(e)
                if deviceIndex == len(config['devices']):
                    print(e, file=sys.stderr)
                else:
                    continue

        netconf_reply_dict = xmltodict.parse(netconf_rpc_reply)
        
        telegraf_json_input = dict_to_telegraf_json(netconf_reply_dict)

        # telegraf needs data in a certain data format.
        # I have chosen JSON data that will be picked up by the exec plugin
        print(telegraf_json_input)


if __name__ == "__main__":
    main()
