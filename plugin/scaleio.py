# Collectd plugin for ScaleIO

# Sample configuration
#    <LoadPlugin "python">
#        Globals true
#    </LoadPlugin>
#    <Plugin "python">
#        ModulePath "/usr/share/collectd/"
#        Import scaleio
#        <Module scaleio>
#            debug false
#            cluster myClusterNameToDisplay
#            verbose false
#            scli_wrap "/usr/bin/si"
#        </Module>
#    </Plugin>


import collectd
import subprocess
import traceback
import types
import re
import json

CONF = {
    'debug':     False,
    'verbose':   False,
    'scli_user': 'admin',
    'scli_password': 'password',
    'cluster':   'myCluster',
    'pools':     [],  #TODO: only report pools that are specified
    'scli_wrap': '/usr/bin/si',
}

class AutoVivification(dict):
    """Implementation of perl's autovivification feature."""
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value

def config_callback(conf):
    collectd.debug('config callback')
    for node in conf.children:
        key = node.key.lower()
        values = node.values
        collectd.debug('Reading config %s: %s' % (key, " ".join(str(v) for v in values)))

        if key == 'debug':
            CONF['debug'] = str2bool(values[0])
        elif key == 'verbose':
            CONF['verbose'] = str2bool(values[0])
        elif key == 'cluster':
            CONF['cluster'] = values[0]
        elif key == 'pools':
            CONF['pools'] = values
        elif key == 'scli_wrap':
            CONF['scli_wrap'] = values[0]
        elif key == 'user':
            CONF['scli_user'] = values[0]
        elif key == 'password':
            CONF['scli_password'] = values[0]
        else:
            collectd.warning('ScaleIO: unknown config key: %s' % (key))

def init_callback():
    my_debug('init callback')

def read_callback(input_data=None):
    dispatch_pools()


def dispatch_value(plugin, value, plugin_instance=None, type_instance=None):
    val = collectd.Values(type = 'gauge')

    val.host = CONF['cluster']
    val.plugin = 'scaleio_' + plugin
    val.plugin_instance = plugin_instance
    val.type_instance = type_instance
    val.values = [value]
    val.dispatch()


def dispatch_pools():


    pools = read_properties('--query_properties', '--object_type', 'STORAGE_POOL', '--all_objects',
        '--properties', 'NAME,MAX_CAPACITY_IN_KB,SPARE_CAPACITY_IN_KB,THIN_CAPACITY_ALLOCATED_IN_KB,'
                        'THICK_CAPACITY_IN_USE_IN_KB,UNUSED_CAPACITY_IN_KB,SNAP_CAPACITY_IN_USE_OCCUPIED_IN_KB,'
                        'CAPACITY_IN_USE_IN_KB,UNREACHABLE_UNUSED_CAPACITY_IN_KB,DEGRADED_HEALTHY_CAPACITY_IN_KB,'
                        'FAILED_CAPACITY_IN_KB,SPARE_CAPACITY_IN_KB,'
                        'USER_DATA_READ_BWC,USER_DATA_WRITE_BWC,REBALANCE_READ_BWC,'
                        'FWD_REBUILD_READ_BWC,BCK_REBUILD_READ_BWC'
            )

    for pool_id, pool in pools.iteritems():
        # raw capacity
        dispatch_value('pool', long(pool['MAX_CAPACITY_IN_KB']) / 2, pool['NAME'], 'raw_bytes')

        # useable capacity
        dispatch_value('pool',
            (long(pool['UNUSED_CAPACITY_IN_KB']) + long(pool['CAPACITY_IN_USE_IN_KB']) -
                long(pool['UNREACHABLE_UNUSED_CAPACITY_IN_KB'])) / 2 - long(pool['FAILED_CAPACITY_IN_KB'])-
                long(pool['DEGRADED_HEALTHY_CAPACITY_IN_KB']),
            pool['NAME'], 'useable_bytes')

        # used capacity
        dispatch_value('pool', (long(pool['CAPACITY_IN_USE_IN_KB'])) / 2, pool['NAME'], 'used_bytes')

        # allocated capacity
        dispatch_value('pool',
            (long(pool['THIN_CAPACITY_ALLOCATED_IN_KB']) +
                long(pool['THICK_CAPACITY_IN_USE_IN_KB']) + long(pool['SNAP_CAPACITY_IN_USE_OCCUPIED_IN_KB'])) / 2,
            pool['NAME'], 'allocated_bytes')

        # unreachable unused capacity
        dispatch_value('pool', long(pool['UNREACHABLE_UNUSED_CAPACITY_IN_KB']) / 2, pool['NAME'], 'unreachable_unused_bytes')

        # degraded capacity
        dispatch_value('pool', long(pool['DEGRADED_HEALTHY_CAPACITY_IN_KB']), pool['NAME'], 'degraded_bytes')

        # failed capacity
        dispatch_value('pool', long(pool['FAILED_CAPACITY_IN_KB']), pool['NAME'], 'failed_bytes')

        # failed capacity
        dispatch_value('pool', long(pool['SPARE_CAPACITY_IN_KB']), pool['NAME'], 'spare_bytes')



        # user data read IOPS
        dispatch_value('pool', long(pool['USER_DATA_READ_BWC']['IOPS']), pool['NAME'], 'read_iops')

        # user data read throughput
        dispatch_value('pool', long(pool['USER_DATA_READ_BWC']['BPS']), pool['NAME'], 'read_bps')

        # user data write IOPS
        dispatch_value('pool', long(pool['USER_DATA_WRITE_BWC']['IOPS']), pool['NAME'], 'write_iops')

        # user data write throughput
        dispatch_value('pool', long(pool['USER_DATA_WRITE_BWC']['BPS']), pool['NAME'], 'write_bps')

        # rebalance IOPS
        dispatch_value('pool', long(pool['REBALANCE_READ_BWC']['IOPS']), pool['NAME'], 'rebalance_iops')

        # rebalance throughput
        dispatch_value('pool', long(pool['REBALANCE_READ_BWC']['BPS']), pool['NAME'], 'rebalance_bps')

        # rebuild IOPS
        dispatch_value('pool',
            long(pool['FWD_REBUILD_READ_BWC']['IOPS'])  +
                long(pool['BCK_REBUILD_READ_BWC']['IOPS']),
            pool['NAME'], 'rebuild_iops')

        # rebuild throughput
        dispatch_value('pool',
            long(pool['FWD_REBUILD_READ_BWC']['BPS']) +
                long(pool['BCK_REBUILD_READ_BWC']['BPS']),
            pool['NAME'], 'rebuild_bps')

# Execute a scli --query_properties command and convert the CLI output to a dict/JSON
def read_properties(*cmd):
    properties = AutoVivification()
    out = None
    real_cmd = (CONF['scli_wrap'],CONF['scli_user'],CONF['scli_password']) + cmd
    my_debug('Executing command: %s' % (" ".join(str(v) for v in real_cmd)))

    try:
        out = subprocess.check_output(real_cmd)
    except Exception as e:
        collectd.error('ScaleIO: error on executing scli command %s --- %s' %
            (e, traceback.format_exc()))
        return

    group_name = None
    group_regex = re.compile("^([^\s]+)\s([^:]+)")
    kv_regex = re.compile("^\s+([^\s]+)\s+(.*)$")
    for line in out.split('\n'):
        new_group_match = group_regex.match(line)
        if new_group_match:
            group_name = new_group_match.group(2)
        else:
            kv_match = kv_regex.match(line)
            if kv_match:
                properties[group_name][kv_match.group(1)] = kv_match.group(2)

    my_debug('Read properties: %s' % (json.dumps(properties)))
    rectify_dict(properties)
    my_debug('Properties after rectify: %s' % (json.dumps(properties)))
    return properties

# Recitify the properties read from the command line:
#  - convert units such as KB,MB,GB to bytes
#  - interpret the BWC values and extract IOPS, Throughput
def rectify_dict(var):
    for key, val in var.iteritems():
        if type(val) is dict or type(val) is AutoVivification:
            rectify_dict(val)
        elif type(val) is str:
            if key.endswith('BWC'):
                var[key] = convert_bwc_to_dict(val)
            else:
                var[key] = convert_units_to_bytes(val)

def convert_bwc_to_dict(val):
    m = re.search('([0-9]+) IOPS (.*) per-second', val, re.I)
    return {'IOPS': m.group(1), 'BPS': convert_units_to_bytes(m.group(2))}

def convert_units_to_bytes(val):
    val = convert_unit_to_bytes(val, "Bytes", 0)
    val = convert_unit_to_bytes(val, "KB", 1)
    val = convert_unit_to_bytes(val, "MB", 2)
    val = convert_unit_to_bytes(val, "GB", 3)
    val = convert_unit_to_bytes(val, "TB", 4)
    val = convert_unit_to_bytes(val, "PB", 5)
    return val

def convert_unit_to_bytes(val, unit, power):
    m = re.search('([0-9\.]+) ' + unit, val, re.I)
    if m:
        return str(long(m.group(1)) * (1024 ** power))
    return val

def str2bool(v):
    if type(v) == types.BooleanType:
        return v
    return v.lower() in ("yes", "true", "t", "1")

def my_debug(msg):
    if CONF['debug']:
        collectd.info('ScaleIO: %s' % (msg))

def my_verbose(msg):
    if CONF['verbose']:
        collectd.info('ScaleIO: %s' % (msg))

# register callback functions
collectd.register_config(config_callback)
collectd.register_init(init_callback)
collectd.register_read(read_callback)
