# Monitoring using NETCONF

The goal is to get telemetry data with NETCONF whether its a series of get RPCs or streaming.
![Cellular Modem Statistics on Grafana](screenshots/dashboard_cellular-modem-statistics.png)
## Components:
- NETCONF-capable Device - Used a Cisco IOS-XE device in this instance
- Telegraf - Data Collection
- Prometheus - Time-Series Database
- Grafana - Visualization

Forked from https://github.com/anirudhkamath/monitoring-practice-with-netconf

## Requirements

Have [docker-compose](https://docs.docker.com/compose/install/) installed, alongside Docker.

## Running this tool

1. Clone the repository with `git clone https://github.com/qmph22/MDT-with-NETCONF-on-IOS-XE.git`
2. Move into the telegraf directory with `cd MDT-with-NETCONF-on-IOS-XE/telegraf`
3. Clone the Python ncclient library from Cisco DevNet with `clone https://github.com/CiscoDevNet/ncclient.git` since `ncclient` from pip does not contain the `establish-subscription` functionality at this time.
4. Go to the top level directory of the project with `cd ..`
6. Create an environmental variable in the `.env` file. Place your passwords in there noting the name of the environmental variable per password. Create multiple environmental variables if you intend on using multiple passwords.
   - You can clone the `.env.example` file with `cp .env.example .env` to get started.
7. Specify your devices in `telegraf/networkdevices.yml`. For the password, specify the environmental variable name you created in the `.env` file.
   - You can copy `networkdevices.example.yml` to `networkdevices.yml` with `cp telegraf/networkdevices.example.yml telegraf/networkdevices.yml` to help you get started.
8. Run the following:
```bash
docker-compose build
docker-compose up
```
9. View metrics collected by Telegraf at http://localhost:9273/metrics
10. View metrics being stored by Prometheus at http://localhost:9090/
11. View the dashboards in Grafana at http://localhost:3000/

## PromQL queries supported

- intf_stats_in_octets
- intf_stats_in_errors
- intf_stats_out_octets
- intf_stats_out_errors
- intf_stats_admin_status
- intf_stats_operational_status
- cpu_process_consumed_bytes
- cpu_utilization_percentage
- memory_pool_percent_used
- cellular_modem_radio_rsrp
- cellular_modem_radio_rsrq
- cellular_modem_radio_rssi
- cellular_modem_radio_snr

# Development
1. Clone the repository with `git clone https://github.com/qmph22/MDT-with-NETCONF-on-IOS-XE.git`
2. Move into the directory with `cd MDT-with-NETCONF-on-IOS-XE`
3. Clone the ncclient from the DevNet repository with `git clone https://github.com/CiscoDevNet/ncclient`
3. Create a Python virtual environment with `python -m venv` (ensure you are using Python 3.10 or higher)
4. Enter the Python virtual environment (if on Linux) with `source venv/bin/activate`
5. Install the required packages with `pip3 install xmltodict dotenv pyyaml typing six python-dateutil lxml paramiko`
6. Create an environmental variable in the `.env` file. Place your passwords in there noting the name of the environmental variable per password. Create multiple environmental variables if you intend on using multiple passwords.
   - You can clone the `.env.example` file with `cp .env.example .env` to get started.
7. Specify your devices in `telegraf/networkdevices.yml`. For the password, specify the environmental variable name you created in the `.env` file.
   - You can copy `networkdevices.example.yml` to `networkdevices.yml` with `cp telegraf/networkdevices.example.yml telegraf/networkdevices.yml` to help you get started. 
8. When ready to test the Docker stack, run the following:
```bash
docker-compose build
docker-compose up
```
or 
```bash
docker compose up --build
```

## Tips
- Streaming telemetry is preferred but if you want to use a series of NETCONF get RPCs, the Python files are in the `telegraf/rpc_get` directory. Then, modify the `telegraf/telegraf.conf` file to use the `inputs.exec` plugin.
- Always be in the `telegraf` directory if executing the Python scripts from CLI. For example, first `cd telegraf` then `python3 netconf-cellular.py`.
- Always be in the top-level directory of `MDT-with-NETCONF-on-IOS-XE` before running any `docker compose` commands.
- If making changes other than just the readme, do them in a different branch of this project.

# To Do
1. Update the dashboard to show the relationship between an interface's operational state and administrative state
2. Handle session disconnects by cleaning up the `subscriptions` dictionary then restarting the sections.
