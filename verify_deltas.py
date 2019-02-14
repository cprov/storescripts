#!/usr/bin/env python3
import argparse
import logging
import os
import sys

import humanize
import requests


RELEASED_REVISIONS = {
    # The core snap is seeded in Ubuntu Desktop 18.04 (4486), 18.04.1 (4917),
    # 18.10 (5662). It is also present in Ubuntu Server "live" images from
    # 18.04 and possibly some cloud images, accounting for the large number of
    # "baked" revisions we have identified.
    ('core', 'amd64'): [
        4830,
        4917,
        4571,
        4486,
        4650,
        5742,
        5897,
        6034,
        6130,
    ],
    # The Gnome snaps are only seeded in Ubuntu Desktop images, and some have
    # the same revision, accounting for some having only 2 baked revisions over
    # 3 images.
    ('gnome-3-26-1604', 'amd64'): [
        49,
        70,
    ],
    ('gnome-calculator', 'amd64'): [
        154,
        180,
        238,
    ],
    ('gnome-characters', 'amd64'): [
        69,
        103,
        124,
    ],
    ('gnome-logs', 'amd64'): [
        25,
        37,
        45,
    ],
    ('gnome-system-monitor', 'amd64'): [
        36,
        51,
        57,
    ],
    # This is only seeded on 18.04.1 and 18.10
    ('gtk-common-themes', 'amd64'): [
        319,
        701,
    ],
}


def get_info(name):
    headers = {
        'Snap-Device-Series': '16',
    }
    url = 'https://api.snapcraft.io/v2/snaps/info/{}'.format(name)
    r = requests.get(url, headers=headers)
    return r.json()


def get_deltas(snap_id, architecture, source_revisions, candidate):
    headers = {
        'Content-Type': 'application/json',
        'Snap-Device-Series': '16',
        'Snap-Device-Architecture': architecture,
        'Snap-Accept-Delta-Format': 'xdelta',
    }
    url = 'https://api.snapcraft.io/v2/snaps/refresh'

    # Build a context with all source_revisions
    context = [{
        'snap-id': snap_id,
        'revision': src,
        'tracking-channel': candidate,
        # Use the instance-key to carry src_revision information, so
        # results can be identified and sorted later even if no deltas
        # are available.
        'instance-key': str(src),
    } for src in source_revisions]

    # Request a refresh for the entire context.
    actions = [{
        'action': 'refresh',
        'snap-id': snap_id,
        'instance-key': c['instance-key']
    } for c in context]

    payload = {'context': context, 'actions': actions}
    r = requests.post(url, json=payload, headers=headers)
    return r.json()['results']


def main():
    parser = argparse.ArgumentParser(
        description='check snap delta availability'
    )
    parser.add_argument(
        '--version', action='version',
        version=' "{}"'.format(
            os.environ.get('SNAP_VERSION', 'devel')))
    parser.add_argument('-v', '--debug', action='store_true',
                        help='Prints request and response headers')
    parser.add_argument(
        '-a', '--architecture', default='amd64',
        choices=['amd64', 'arm64', 'armhf', 'i386', 'ppc64el', 's390x'])
    parser.add_argument(
        '-c', '--candidate', default='candidate', metavar='CHANNEL',
        help=('Promoted channel, defaults to "candidate", but can be any '
              'branch or track.'))
    parser.add_argument('name', metavar='SNAP_NAME')

    args = parser.parse_args()

    if args.debug:
        handler = requests.packages.urllib3.add_stderr_logger()
        handler.setFormatter(logging.Formatter('\033[1m%(message)s\033[0m'))

    # Figure out the `snap-id` and `stable_revision` for the context architecture.
    info = get_info(args.name)
    snap_id = info['snap-id']
    stable_revision = [
        c['revision'] for c in info['channel-map']
        if (c['channel']['name'] == 'stable' and
            c['channel']['architecture'] == args.architecture)][0]

    # Consider RELEASED revisions for the context (snap, arch).
    sources = RELEASED_REVISIONS.get(
        (args.name, args.architecture), []) + [stable_revision]

    results = get_deltas(snap_id, args.architecture, sources, args.candidate)
    candidate_revision = results[0]['snap']['revision']
    candidate_size = results[0]['snap']['download']['size']
    print('Snap:      {} ({})'.format(args.name, snap_id))
    print('Promoting: {}'.format(args.candidate))
    print('Candidate: {} ({})'.format(
        candidate_revision, humanize.naturalsize(candidate_size, gnu=True)))

    # Walk throught results in revision ASC (numeric) order.
    print('Deltas:')
    for r in sorted(results, key=lambda r: int(r['instance-key'])):
        src = r['instance-key']
        if r['snap']['download']['deltas']:
            delta_size = r['snap']['download']['deltas'][0]['size']
            note = '{} / saves {:.0f} %'.format(
                humanize.naturalsize(delta_size, gnu=True),
                (candidate_size - delta_size) / float(candidate_size) * 100,
            )
        else:
            note = 'not available'
        print('  {}: {}'.format(src, note))


if __name__ == '__main__':
    sys.exit(main())
