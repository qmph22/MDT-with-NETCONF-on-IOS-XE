# Monitoring using NETCONF

The goal here is to get telemetry data with NETCONF.
Components:
- NETCONF-capable Device - Used a Cisco IOS-XE device in this instance
- Telegraf - Data Collection
- Prometheus - Time-Series Database
- Grafana - Visualization

Forked from https://github.com/anirudhkamath/monitoring-practice-with-netconf

## Requirements

Have [docker-compose](https://docs.docker.com/compose/install/) installed, alongside Docker.

## Running this tool

1.Set the username, password, IP address/hostname, and port for NETCONF related files
> Create an environmental variable in the `.env` file. Place your password in there.
> Create specify your devices in `telegraf/networkdevices.yml`. For the password, specify the environmental variable name you created in the `.env` file.
> You can copy `networkdevices.example.yml` to `networkdevices.yml` to help you get started.


```bash
docker-compose build
docker-compose up
```


Once the apps are up and running, you can view the Prometheus console at `localhost:9090` on your browser.

## PromQL queries supported

- intf_stats_in_octets
- intf_stats_in_errors
- intf_stats_out_octets
- intf_stats_out_errors
- cpu_process_consumed_bytes
- memory_pool_percent_used
- cellular_modem_radio_rsrp
- cellular_modem_radio_rsrq
- cellular_modem_radio_rssi
- cellular_modem_radio_snr
