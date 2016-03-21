# Collectd plugin for ScaleIO
This is a collectd plugin to collect metrics of a ScaleIO cluster. It queries the ScaleIO cluster on the primary MDM by using the 'scli --query_properties' command.  
A grafana dashboard that visualizes the metrics is available as well.

## Installation
General requirements:

* The collectd plugin has to be installed on all MDM nodes, so that in case of a MDM switch, the data will be collectd from the new primary MDM.
* scli_wrap.sh is a required bash script that wraps the scli login/logout with a locking mechanism.
* This collectd plugin is written in Python and thus requires the collectd-python plugin.

### Option 1
Build a package (ie: RPM) for your distribution using the build_plugin.sh script.

### Option 2
Copy the files manually from the plugin folder to the module path, ie:
```bash
cp plugin/* /usr/share/collectd/python
```

### Collectd plugin configuration
The plugin needs to be configured in collectd as follows.
```
<LoadPlugin "python">
    Globals true
</LoadPlugin>
<Plugin "python">
    ModulePath "/usr/share/collectd/python"
    Import scaleio
    <Module scaleio>
        Debug true                      # default: false
        Verbose true                    # default: false
        Cluster myClusterNameToDisplay  # Cluster name will be reported as the collectd hostname, default: myCluster
        Scli_wrap "/usr/bin/scli_wrap"  # Location of wrapping script used for login/logout, default: /usr/share/collectd/python/scli_wrap.sh
        User admin                      # ScaleIO user for getting metrics (creating a read-only user makes sense), default: admin
        Password admin                  # Password of the ScaleIO user, default: admin
        Pools poolA poolB               # list of pools to be reported or ignored (see: IgnoreSelected), default: empty
        IgnoreSelected false            # ignore pools given in the pools list, default: false
    </Module>
</Plugin>
```

## Grafana dashboard
A grafana dashboard that visualizes the pool data can be found in the grafana directory.
The dashboard is ready to be installed, which can done by either packaging it (build_grafana_dashboard.sh) or by importing the dashboard manually.  
Make sure to replace MY_DATASOURCE_NAME with the name of your grafana datasource that contains the collectd data, before imporing/installing it.
```bash
sed -i 's/__dsname__/MY_DATASOURCE_NAME/g' grafana/dashboard.json
```

### Screenshots

![Sample ScaleIO dashboard (on remove of SDS)](public/force_remove_sds.png "Sample ScaleIO dashboard (on remove of SDS)")
![Sample ScaleIO dashboard (data growth)](public/pool_growth.png "Sample ScaleIO dashboard (data growth)")

## Data collected
The plugin collects the following data

- Per storage pool (capacity is divided by 2, to have the 'real' values a user understands)
  - raw bytes
  - useable bytes
  - available bytes
  - allocated bytes
  - unreachable unused bytes
  - degraded bytes
  - failed bytes
  - spare bytes
  - user read iops
  - user read throughput
  - user write iops
  - user write throughput
  - rebalance iops
  - rebalance throughput
  - rebuild iops
  - rebuild throughput
