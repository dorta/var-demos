#!/usr/bin/env python3
# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path
import os
import sys
import tomllib

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'lib'))
sys.path.insert(0, str(ROOT / 'ai-ml'))
sys.path.insert(0, str(ROOT / 'ai-ml-demos'))
import manager


def add_external_demos(catalog):
    """Expose curated BSP executables without installing or owning them."""
    available = []
    for entry in catalog.get('external_demos', []):
        executable = Path(entry['executable'])
        if (not executable.is_absolute()
                or '..' in executable.parts
                or not executable.is_relative_to('/opt/imx-gpu-sdk')
                or not executable.is_file()
                or not os.access(executable, os.X_OK)):
            continue
        demo_id = 'bsp/' + entry['id']
        catalog['demos'].append({
            'id': demo_id, 'path': str(executable.parent),
            'platforms': entry['platforms'],
        })
        available.append({
            'id': demo_id, 'demo': demo_id, 'group': 'bsp',
            'title': entry['title'], 'description': entry['description'],
            'command': [str(executable)], 'native_wayland': True,
        })
    if available:
        catalog['groups'].append({
            'id': 'bsp', 'title': 'Installed BSP demos /opt',
            'description': 'Existing GPU examples supplied with the image',
            'platforms': sorted({platform
                                 for entry in catalog['external_demos']
                                 for platform in entry['platforms']}),
        })
        catalog['launchers'].extend(available)


def load_suite():
    with (ROOT / 'catalog.toml').open('rb') as source:
        catalog = tomllib.load(source)
    catalog['demos'] = []
    catalog['groups'] = [group for group in catalog['groups']
                         if (ROOT / group['id']).is_dir()]
    for group in catalog['groups']:
        catalog['demos'].append({
            'id': group['id'], 'path': group['id'],
            'platforms': group['platforms'],
        })
        if group['id'] != 'ai-ml':
            continue
        with (ROOT / 'ai-ml/catalog.toml').open('rb') as source:
            ai = tomllib.load(source)
        for demo in ai['demos']:
            demo['id'] = 'ai-ml/' + demo['id']
            demo['path'] = 'ai-ml/' + demo['path']
            catalog['demos'].append(demo)
        for launcher in ai['launchers']:
            launcher['demo'] = 'ai-ml/' + launcher['demo']
            launcher['group'] = 'ai-ml'
            catalog['launchers'].append(launcher)
        for video in ai.get('videos', []):
            video['demo'] = 'ai-ml/' + video['demo']
        catalog['videos'] = ai.get('videos', [])
    add_external_demos(catalog)
    return catalog


if __name__ == '__main__':
    manager.ROOT = ROOT
    manager.load_catalog = load_suite
    raise SystemExit(manager.main())
