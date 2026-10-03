#!/usr/bin/env python3
# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path
import sys
import tomllib

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'lib'))
sys.path.insert(0, str(ROOT / 'ai-ml'))
sys.path.insert(0, str(ROOT / 'ai-ml-demos'))
import manager


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
    return catalog


if __name__ == '__main__':
    manager.ROOT = ROOT
    manager.load_catalog = load_suite
    raise SystemExit(manager.main())
