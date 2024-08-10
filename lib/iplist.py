#!/usr/bin/env python3

# Source: https://github.com/O-X-L/nftables_addon_iplist
# Copyright (C) 2024 Rath Pascal
# License: MIT

from urllib import request
from urllib.error import URLError, HTTPError
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address, AddressValueError, NetmaskValueError

from util import validate_and_write, load_config, format_var

PROCESS_IPv6 = True

# paths are set in util (shared between addons)
CONFIG_FILE = 'iplist.json'
CONFIG_FILE_KEY = 'iplist'
OUT_FILE = 'iplist.nft'


def _filter_result_protocol(protocol: int, results: list) -> list:
    filtered = []
    protocols = {
        4: {'network': IPv4Network, 'address': IPv4Address},
        6: {'network': IPv6Network, 'address': IPv6Address},
    }

    if protocol not in protocols:
        protocol = 4

    for result in results:
        result = result.strip()

        try:
            protocols[protocol]['address'](result)
            filtered.append(result)

        except AddressValueError:
            try:
                protocols[protocol]['network'](result)
                filtered.append(result)

            except (AddressValueError, NetmaskValueError):
                pass

    filtered.sort()
    return filtered


def _download_list(url: str, sep: str, cmt: str) -> list:
    cleaned = []

    try:
        with request.urlopen(url, timeout=10) as u:
            for r in u.read().decode('utf-8').split(sep):
                cleaned.append(r.split(cmt, 1)[0].strip())

    except (URLError, HTTPError) as exc:
        raise SystemExit(f"Failed to download IPList: '{url}'!") from exc

    return cleaned


CONFIG = load_config(file=CONFIG_FILE, key=CONFIG_FILE_KEY)

if CONFIG is None or len(CONFIG) == 0:
    raise SystemExit(f"Config file could not be loaded: '{CONFIG_FILE}'!")

lines = []
for var, iplist_config in CONFIG.items():
    if 'urls' not in iplist_config:
        print(
            "You need to provide the 'urls' parameter! "
            f"Ignoring variable: '{var}'"
        )
        continue

    urls = iplist_config['urls']
    separator = iplist_config['separator'] if 'separator' in iplist_config else '\n'
    comment = iplist_config['comment'] if 'comment' in iplist_config else '#'

    if not isinstance(urls, list):
        urls = [urls]

    values_v4 = []
    values_v6 = []

    for entry in urls:
        data = _download_list(url=entry, sep=separator, cmt=comment)

        lines.append(
            format_var(
                name=var,
                data=_filter_result_protocol(
                    protocol=4,
                    results=data,
                ),
                version=4,
            )
        )

        if PROCESS_IPv6:
            lines.append(
                format_var(
                    name=var,
                    data=_filter_result_protocol(
                        protocol=6,
                        results=data,
                    ),
                    version=6,
                )
            )

validate_and_write(lines=lines, file=OUT_FILE, key=CONFIG_FILE_KEY)
