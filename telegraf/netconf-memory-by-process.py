from typing import Dict
from ncclient import manager
import xmltodict
import json

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
    with manager.connect(
        host = "10.0.0.1",  # Locally connected device. Will eventually make this a configurable item
        port = 830,
        username = "admin",
        password = "admin",  # <------- enter device password
        hostkey_verify=False,
        device_params = {'name': 'iosxe'}
    ) as m:
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

        netconf_rpc_reply = m.get(
            filter = netconf_filter
        ).xml

        netconf_reply_dict = xmltodict.parse(netconf_rpc_reply)
        
        telegraf_json_input = dict_to_telegraf_json(netconf_reply_dict)

        # telegraf needs data in a certain data format.
        # I have chosen JSON data that will be picked up by the exec plugin
        print(telegraf_json_input)


if __name__ == "__main__":
    main()
