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

```bash
docker-compose build
docker-compose up
```

> Set the username, password, and port for NETCONF related files (`netconf-*.py`) in the `telegraf/` folder.

Once the apps are up and running, you can view the Prometheus console at `localhost:9090` on your browser.

## PromQL queries supported (need to update this list)

- intf_stats_in_octets
- intf_stats_in_errors
- intf_stats_out_octets
- intf_stats_out_errors
- cpu_process_consumed_bytes
- memory_pool_percent_used
