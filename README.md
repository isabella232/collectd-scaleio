# Collectd plugin for ScaleIO
This is a collectd plugin to collect metrics of a ScaleIO cluster. It queries the ScaleIO cluster on the primary MDM by using the 'scli --query_properties' command.

## Installtion
General requirements:

* The collectd plugin has to be installed on all MDM nodes, so that in case of a MDM switch, the data will be collectd from the new primary MDM.
* scli_wrap.sh is a required bash script that wraps the scli login/logout with a locking mechanism.
* This collectd plugin is written in Python and thus requires the collectd-python plugin.

### Collectd plugin configuration
The plugin needs to be configured in collectd as follows.
```
<LoadPlugin "python">
    Globals true
</LoadPlugin>
<Plugin "python">
    ModulePath "/usr/share/collectd/"
    Import scaleio
    <Module scaleio>
        debug true                      # optional, default: false
        verbose true                    # optional, default: false
        cluster myClusterNameToDisplay  # optional, default: myCluster
        scli_wrap "/usr/bin/scli_wrap"  # optional, default: /usr/bin/si
    </Module>
</Plugin>
```

# Grafana dashboard
Replace MY_DATASOURCE_NAME with the name of your grafana datasource that contains the collectd data.
```bash
sed -i 's/__dsname__/MY_DATASOURCE_NAME/g' grafana/dashboard.json
```
