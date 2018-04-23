#!/usr/bin/env python3

import collections
import datetime
import math
import requests
import sys
import tabulate


DEFAULT_HEADERS = {
    'Accept': 'application/json, application/hal+json',
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
}


def get_publisher_metrics(snap_name, metric_name, authorization):
    headers = DEFAULT_HEADERS.copy()
    headers['Authorization'] = authorization

    url = 'https://dashboard.snapcraft.io/dev/api/snaps/info/{}'.format(snap_name)
    r = requests.get(url=url, headers=headers)
    r.raise_for_status()
    snap_id = r.json()['snap_id']

    yesterday = datetime.datetime.utcnow().date() - datetime.timedelta(1)

    start = end = yesterday.isoformat()
    filters = [
        {"metric_name": metric_name, "snap_id": snap_id, "start": start, "end": end},
    ]

    url = 'https://dashboard.snapcraft.io/dev/api/snaps/metrics'
    payload = {"filters": filters}
    r = requests.post(url=url, json=payload, headers=headers)
    r.raise_for_status()
    return {m['name']: m['values'][0] for m in r.json()['metrics'][0]['series']}


def get_public_metrics(snap_name, metric_name):
    headers = DEFAULT_HEADERS.copy()
    headers['X-Ubuntu-Series'] = '16'

    url = 'https://api.snapcraft.io/api/v1/snaps/details/{}'.format(snap_name)
    r = requests.get(url=url, headers=headers)
    r.raise_for_status()
    snap_id = r.json()['snap_id']

    yesterday = datetime.datetime.utcnow().date() - datetime.timedelta(1)
    start = end = yesterday.isoformat()
    filters = [
        {"metric_name": metric_name, "snap_id": snap_id, "start": start, "end": end},
    ]

    url = 'https://api.snapcraft.io/api/v1/snaps/metrics'
    payload = filters
    r = requests.post(url=url, json=payload, headers=headers)
    r.raise_for_status()
    return {m['name']: m['values'][0] for m in r.json()[0]['series']}


def transform_to_ratio(samples):
    total = sum(v for v in samples.values() if v is not None)
    sorted_samples = sorted(samples.items(), key=lambda t: t[1] or -1, reverse=True)
    ratios = [
        (k, round((v / total) * 200) / 200 if v is not None else None)
        for k, v in sorted_samples]
    return collections.OrderedDict(ratios)


def transform_to_log_ratio(samples):
    total = sum(v for v in samples.values() if v is not None)
    sorted_samples = sorted(samples.items(), key=lambda t: t[1] or -1, reverse=True)
    ratios = [
        (k, (round((math.log10(v) / math.log10(total)) * 200) / 200
             if v is not None and v > 1 else None))
        for k, v in sorted_samples]
    return collections.OrderedDict(ratios)


def transform_to_normalized(samples):
    total = sum(v for v in samples.values() if v is not None)
    sorted_samples = sorted(samples.items(), key=lambda t: t[1] or -1, reverse=True)

    # Drop any sample smaller than 5.
    ratios = [
        (k, v if v is not None and v >= 5 else None)
        for k, v in sorted_samples]

    # Normalize as Log10 ratio of the total.
    ratios = [
        (k, math.log10(v) / math.log10(total) if v is not None else None)
        for k, v in ratios]

    # Shift with the top sample complement to 1.
    _, top_sample = ratios[0]
    ratios = [
        (k, v + (1 - top_sample) if v is not None else None)
        for k, v in ratios]

    # Round up with 2.5 % precision.
    ratios = [
        (k, math.ceil(v  * 40) / 40 if v is not None else None)
        for k, v in ratios]

    return collections.OrderedDict(ratios)


def main():

    if len(sys.argv) > 1:
        snap_name = sys.argv[1]
    else:
        snap_name = 'lxd'

    try:
        with open('store.auth') as fd:
            authorization = fd.read().strip().replace('\n', '')
        print('Using authorization from `store.auth` file ...')
    except FileNotFoundError:
        print('Missing authorization! Please run the following command:')
        print()
        print('\t$ snap install surl')
        print('\t$ surl -v -e <email> -s production '
              '-p package_access -p package_metrics '
              'https://dashboard.snapcraft.io/dev/api/account')
        print('\t...')
        print()
        print('fill in your credentials and copy the `Authorization` header '
              'to the `store.auth` file')
        return

    print('Collecting publisher metrics for {} ...'.format(snap_name))
    raw_absolute = get_publisher_metrics(
        snap_name, 'weekly_installed_base_by_operating_system', authorization)
    absolute = collections.OrderedDict(
        sorted(raw_absolute.items(), key=lambda t: t[1] or -1, reverse=True))

    print('Collecting public metrics for {} ...'.format(snap_name))
    raw_normalized = get_public_metrics(
        snap_name, 'weekly_installed_base_by_operating_system_normalized')
    normalized = collections.OrderedDict(
        sorted(raw_normalized.items(), key=lambda t: t[1] or -1, reverse=True))

    table = collections.OrderedDict([
        ('Distro', absolute.keys()),
        ('Absolute', absolute.values()),
        ('Normalized', normalized.values()),
        #('Log10', [v or '-' for v in  transform_to_log_ratio(absolute).values()]),
        #('Normalized (local)', [v or '-' for v in transform_to_normalized(absolute).values()]),
    ])
    print(tabulate.tabulate(table, headers='keys'))


if __name__ == '__main__':
    main()
