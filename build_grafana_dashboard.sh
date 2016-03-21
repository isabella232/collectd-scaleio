#!/bin/bash

# print all commands
set -x

VERSION='1.0'
ITERATION=${1:-1}
TARGET_DIR=${2:-/usr/share/grafana/public/dashboards/}

fpm \
-t rpm \
-s dir \
-n grafana-dashboard-scaleio \
-v $VERSION \
--iteration $ITERATION \
--url "https://github.com/swisscom/collectd-scaleio" \
--rpm-user root \
--rpm-group root \
./grafana/=$TARGET_DIR \
|| exit 1

