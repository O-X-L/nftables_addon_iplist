# NFTables Addon - IPLists

NFTables lacks some functionality, that is commonly used in firewalling.

Having variables that hold the IPs of IPLists is one of those.

IPList examples:

* [Spamhaus DROP](https://www.spamhaus.org/drop/drop.txt)
* [Spamhaus EDROP](https://www.spamhaus.org/drop/edrop.txt)
* [Tor exit nodes](https://check.torproject.org/torbulkexitlist)


----

## Other Addons

* [DNS](https://github.com/superstes/nftables_addon_dns)
* [Failover](https://github.com/superstes/nftables_addon_failover)

NFTables documentation: [wiki.superstes.eu](https://wiki.superstes.eu/en/latest/1/network/firewall_nftables.html)


----

## Result

```text
cat /etc/nftables.d/addons/iplist.nft 
> # Auto-Generated config - DO NOT EDIT MANUALLY!
> 
> define tor_exit_nodes_v4 = { 102.130.113.9, 102.130.127.117, 102.130.127.238, ..., 95.216.107.148, 95.217.186.208 }
> define tor_exit_nodes_v6 = { :: }
> define spamhaus_edrop_v4 = { 109.206.243.0/24, 119.227.224.0/19, 120.128.128.0/17, ..., 95.161.128.0/24, 95.214.24.0/24 }
> define spamhaus_edrop_v6 = { :: }
```

----

## How does it work?

1. A configuration file needs to be created:

    `/etc/nftables.d/addons/iplist.json`

    ```json
    {
      "iplist": {
        "tor_exit_nodes": {
          "urls": ["https://check.torproject.org/torbulkexitlist"]
        },
        "spamhaus_edrop": {
          "urls": "https://www.spamhaus.org/drop/edrop.txt",
          "comment": ";"
        }
      }
    }
    ```

    **Config options**:

      * `separator`: default = `\n`

        What separates multiple IPs/Networks in the IPList

      * `comment`: default = `#`

        Comment-lines will be ignored when parsing the IPList content


2. The script is executed

    `python3 /usr/lib/nftables/iplist.py`

  * It will load the configuration
  * Pull the current IPLists for all configured variables
  * If it was unable to download an IPList - it will keep the existing values
  * If an empty IPList was found - a placeholder-value will be set:

    IPv4: `0.0.0.0`

    IPv6: `::`

  * The new addon-config is written to `/tmp/nftables_iplist.nft`
  * Its md5-hash is compared to the existing config to check if it changed

  * **If it has changed**:
    * **Config validation** is done:

      * An include-file is written to `/tmp/nftables_main.nft`:

        ```nft
        include /tmp/nftables_iplist.nft
        # including all other adoon configs
        include /etc/nftables.d/addons/other_addon1.nft
        include /etc/nftables.d/addons/other_addon2.nft
        # include other main configs
        include /etc/nftables.d/*.nft
        ```

      * This include-file is validated:

        `sudo nft -cf /tmp/nftables_main.nft`

    * The new config is written to `/etc/nftables.d/addons/iplist.nft`
    * The actual config is validated: `sudo nft -cf /etc/nftables.conf`
    * NFTables is reloaded: `sudo systemctl reload nftables.service`


3. You will have to include the addon-config in your main-config file `/etc/nftables.conf`:

    ```
    ...
    include /etc/nftables.d/addons/*.nft
    ...
    ```

----

## Privileges

If the script should be run as non-root user - you will need to add a sudoers.d file to add the needed privileges:

```text
Cmnd_Alias NFTABLES_ADDON = \
  /usr/bin/systemctl reload nftables.service,
  /usr/sbin/nft -cf *

service_user ALL=(ALL) NOPASSWD: NFTABLES_ADDON
```

You may not change the owner of the addon-files as the script will not be able to overwrite them.

----

## Safety

As explained above - there is a config-validation process to ensure the addon will not supply a bad config and lead to a failed nftables reload/restart.

If you want to be even safer - you can add a config-validation inside the `nftables.service`:

```text
# /etc/systemd/system/nftables.service.d/override.conf
[Service]
# catch errors at start
ExecStartPre=/usr/sbin/nft -cf /etc/nftables.conf

# catch errors at reload
ExecReload=
ExecReload=/usr/sbin/nft -cf /etc/nftables.conf
ExecReload=/usr/sbin/nft -f /etc/nftables.conf

# catch errors at restart
ExecStop=
ExecStop=/usr/sbin/nft -cf /etc/nftables.conf
ExecStop=/usr/sbin/nft flush ruleset

Restart=on-failure
RestartSec=5s
```

This will catch and log config-errors before doing a reload/restart.

----

## Scheduling

You can either:

* Add a Systemd Timer: [example](https://github.com/ansibleguy/addons_nftables/tree/latest/templates/etc/systemd/system)
* Add a cron job

----

## Ansible

Here you can find an Ansible Role to manage NFTables Addons:

* [ansibleguy.addons_nftables](https://github.com/ansibleguy/addons_nftables)
* [examples](https://github.com/ansibleguy/addons_nftables/blob/latest/Example.md)

----

## License

MIT
