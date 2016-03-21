#!/bin/bash

# print all commands
set -x

VERSION='1.0'
ITERATION=${1:-1}
TARGET_DIR=${2:-/usr/share/collectd/python}

fpm \
-t rpm \
-s dir \
-n collectd-plugin-scaleio \
-v $VERSION \
--iteration $ITERATION \
--url "https://github.com/swisscom/collectd-scaleio" \
--rpm-user root \
--rpm-group root \
./plugin/=$TARGET_DIR \
|| exit 1

