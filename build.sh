#!/bin/bash

# print all commands
set -x

VERSION='1.0'
ITERATION=${1:-1}
TARGET_DIR=${2:-/usr/share/collectd/python}

# prepare directory
mkdir -p target

fpm \
-t rpm \
-s dir \
-n collectd-scaleio \
-v $VERSION \
--iteration $ITERATION \
--url "https://github.com/swisscom/collectd-scaleio" \
--rpm-user root \
--rpm-group root \
./plugin/=$TARGET_DIR \
|| exit 1

