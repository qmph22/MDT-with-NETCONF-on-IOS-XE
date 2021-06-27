# Monitoring using NETCONF

I started this on a Saturday, just because I wanted to better understand:

- NETCONF
- Telegraf
- Working with time series data on Prometheus

All just for fun!

## Requirements

Have [docker-compose](https://docs.docker.com/compose/install/) installed, alongside Docker.

## Running this tool

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
