FROM grafana/grafana:12.0.1-ubuntu

LABEL author="Alexis Le Provost <alexis.leprovost@outlook.com>, qmph22"
LABEL version="1.3.0"
LABEL description="Grafana docker image"

USER root

RUN apt-get -q update &&\
    DEBIAN_FRONTEND="noninteractive" apt-get -q upgrade -y -o Dpkg::Options::="--force-confnew" --no-install-recommends &&\
    DEBIAN_FRONTEND="noninteractive" apt-get -q install -y -o Dpkg::Options::="--force-confnew" --no-install-recommends curl gosu &&\
    apt-get -q autoremove &&\
    apt-get -q clean -y && rm -rf /var/lib/apt/lists/* && rm -f /var/cache/apt/*.bin

RUN mkdir -p /opt/grafana/dashboards
ADD *.json /opt/grafana/dashboards/
ADD default-dashboard.yaml /etc/grafana/provisioning/dashboards/

ADD provisioning/datasources/*.yaml /etc/grafana/provisioning/datasources/

ADD run.sh /run.sh
ENTRYPOINT ["bash", "/run.sh"]
