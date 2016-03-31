#!/bin/bash

# print all commands
set -x

VERSION='1.0'
ITERATION=${1:-1}
PKG_TYPE=${2:-rpm}
TARGET_DIR=${3:-/usr/share/collectd/python}

fpm \
-t $PKG_TYPE \
-s dir \
-n collectd-plugin-scaleio \
-v $VERSION \
--iteration $ITERATION \
--url "https://github.com/swisscom/collectd-scaleio" \
--rpm-user root \
--rpm-group root \
--after-install after_plugin_install.sh \
../plugin/=$TARGET_DIR \
|| exit 1

