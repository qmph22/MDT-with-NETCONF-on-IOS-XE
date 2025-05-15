from typing import Dict
from ncclient import manager
import xmltodict
import json

def dict_to_telegraf_json(rpc_reply_dict: Dict) -> str:
    """
    """

    stats_array = []

    for cellularModem in rpc_reply_dict["rpc-reply"]["data"]["cellwan-oper-data"]["cellwan-radio"]:
        if "online" in str(cellularModem["radio-power-mode"]):
            cellularModemDict = {
                "name": cellularModem["cellular-interface"],
                "radio_rssi": float(cellularModem["radio-rssi"]),
                "radio_rsrp": float(cellularModem["radio-rsrp"]),
                "radio_rsrq": float(cellularModem["radio-rsrq"]),
                "radio_snr": float(cellularModem["radio-snr"]),
                "field": "cellular_modem"
            }  # trying to get rate of consumption of processes
            stats_array.append(cellularModemDict)

    return json.dumps(stats_array)  # return JSON formatted data


def main():
    with manager.connect(
        #host = "ios-xe-mgmt.cisco.com",  # sandbox ios-xe always on
        host = "10.0.0.1",  # Locally connected device. Will eventually make this a configurable item
        port = 830,
        username = "admin",
        password = "admin",  # enter device password
        hostkey_verify=False,
        device_params = {'name': 'iosxe'}
    ) as m:
        # https://github.com/YangModels/yang/blob/master/vendor/cisco/xe/16111/Cisco-IOS-XE-process-memory-oper.yang
        netconf_filter = """
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <cellwan-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-cellwan-oper">
            <cellwan-radio/>
        </cellwan-oper-data>
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
