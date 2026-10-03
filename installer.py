#!/usr/bin/env python3
# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib

SAMPLE_URL = ('https://nyc3.digitaloceanspaces.com/variscite-marketing/demos/'
              'machine-learning/imx8mplus/v2/media/chicago_1280x720.mp4')
SAMPLE_HASH = 'bb0a4ababcf63f98548ac2e7106ef1774e3d96fc756ef4d9c45c48c2315689ff'
OWNED = '.var-demos-owned'


def active_processes(root):
    for process in Path('/proc').glob('[0-9]*'):
        try:
            if process.name == str(os.getpid()):
                continue
            arguments = (process / 'cmdline').read_bytes().split(b'\0')
            if not Path(os.fsdecode(arguments[0])).name.startswith('python'):
                continue
            paths = [(process / 'cwd').resolve()]
            if len(arguments) > 1 and arguments[1].startswith(b'/'):
                paths.append(Path(os.fsdecode(arguments[1])).resolve())
            if any(path == root or root in path.parents for path in paths):
                raise RuntimeError(f'Installation in use by PID {process.name}; '
                                   'close var-demos and running demos first')
        except (OSError, ValueError):
            continue


def valid_root(value):
    path = Path(value)
    if (not path.is_absolute() or '..' in path.parts or path.is_symlink()
            or str(path) in ('/', '/opt', '/usr', '/usr/bin', '/home', '/root')
            or path == Path.home()):
        raise RuntimeError(f'Unsafe installation prefix: {value}')
    return path.resolve()


def verified(path):
    if not path.is_file():
        return False
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest() == SAMPLE_HASH


def link_command(bin_dir, name, target):
    link = bin_dir / name
    if link.exists() or link.is_symlink():
        if not link.is_symlink() or link.readlink() != target:
            raise RuntimeError(f'Refusing to overwrite unrelated {link}')
        return
    link.symlink_to(target)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path,
                        default=Path(__file__).resolve().parent)
    parser.add_argument('--prefix', default='/opt/var-demos')
    parser.add_argument('--bin-dir', type=Path, default=Path('/usr/bin'))
    parser.add_argument('--only', action='append', choices=['ai-ml',
                         'multimedia', 'opencl'])
    parser.add_argument('--board')
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--uninstall', action='store_true')
    args = parser.parse_args()
    source = args.source.resolve()
    root = valid_root(args.prefix)
    if args.uninstall:
        source = root
    with (source / 'catalog.toml').open('rb') as file:
        catalog = tomllib.load(file)
    compatible = Path('/proc/device-tree/compatible')
    values = compatible.read_bytes().split(b'\0') if compatible.exists() else []
    board = args.board or next((key for key, entry in catalog['platforms'].items()
        if any(value.encode() in values for value in entry['compatible'])), None)
    if not args.uninstall and (board not in catalog['platforms'] or
            catalog['platforms'][board]['status'] != 'validated'):
        raise RuntimeError('This board has not been validated yet')
    groups = [group for group in catalog['groups']
              if (args.uninstall or board in group['platforms'])
              and (not args.only or group['id'] in args.only)]
    if args.list or args.dry_run:
        for group in groups:
            action = 'Remove' if args.uninstall else 'Install'
            print(f"{action}: {group['title']} -> {root / group['id']}")
        return
    active_processes(root)
    args.bin_dir = args.bin_dir.resolve()
    if args.uninstall:
        if not (root / '.var-demos-installed').is_file():
            raise RuntimeError('Unrecognized suite installation')
        for group in groups:
            target = root / group['id']
            if target.is_symlink():
                raise RuntimeError(f'Refusing symlink installation: {target}')
            if group['id'] == 'ai-ml' and target.exists():
                subprocess.run(['sh', str(target / 'install.sh'), '--uninstall',
                    '--prefix', str(target), '--bin-dir', str(args.bin_dir)],
                    check=True)
            elif target.exists():
                if not (target / OWNED).is_file():
                    raise RuntimeError(f'Unrecognized installation: {target}')
                shutil.rmtree(target)
                print(f'Removed {target}')
        for name, relative in [('var-demos', 'suite.py'),
                               ('var-media', 'multimedia/video-player/player.py')]:
            link = args.bin_dir / name
            if link.is_symlink() and link.readlink() == root / relative:
                if not args.only or (name == 'var-media' and
                                    'multimedia' in args.only):
                    link.unlink()
        if not args.only:
            if not (root / '.var-demos-installed').is_file():
                raise RuntimeError('Unrecognized suite installation')
            shutil.rmtree(root / 'lib')
            for name in ('suite.py', 'catalog.toml', 'installer.py', 'install.sh',
                         '.var-demos-installed'):
                (root / name).unlink(missing_ok=True)
        print('Uninstall complete; unrelated files were preserved')
        return
    # Validate before downloading or changing any installation.
    if (root / 'lib').is_symlink():
        raise RuntimeError('Refusing symlink support directory')
    if not (root / '.var-demos-installed').is_file():
        for name in ('suite.py', 'catalog.toml', 'installer.py', 'install.sh'):
            if (root / name).exists() or (root / name).is_symlink():
                raise RuntimeError(f'Refusing unrelated {root / name}')
    for group in groups:
        target = root / group['id']
        if target.is_symlink():
            raise RuntimeError(f'Refusing symlink installation: {target}')
        if (target.exists() and group['id'] != 'ai-ml'
                and not (target / OWNED).is_file()):
            raise RuntimeError(f'Refusing unrelated directory: {target}')
        if group['id'] == 'multimedia':
            subprocess.run([sys.executable,
                str(source / group['source'] / 'video-player/player.py'),
                '--check'], check=True)
        if group['id'] == 'opencl':
            subprocess.run([sys.executable,
                str(source / group['source'] / 'vector_add.py'),
                '--check'], check=True)
    for name, relative in [('var-demos', 'suite.py'),
                           ('var-media', 'multimedia/video-player/player.py')]:
        link = args.bin_dir / name
        if (link.exists() or link.is_symlink()) and (
                not link.is_symlink() or link.readlink() != root / relative):
            raise RuntimeError(f'Refusing to overwrite unrelated {link}')
    with tempfile.TemporaryDirectory(prefix='var-demos-') as temporary:
        cache = Path(temporary) / 'chicago.mp4'
        if any(group['id'] == 'multimedia' for group in groups):
            previous = [root / 'multimedia/video-player/media/chicago.mp4',
                root / 'ai-ml/high-resolution-video-detection/assets/videos/'
                       'chicago_1280x720.mp4']
            reusable = next((path for path in previous if verified(path)), None)
            if reusable:
                shutil.copy2(reusable, cache)
            else:
                subprocess.run(['curl', '-fSL', '--retry', '2', SAMPLE_URL,
                                '-o', str(cache)], check=True)
            if not verified(cache):
                raise RuntimeError('Sample video SHA-256 mismatch')
        root.mkdir(parents=True, exist_ok=True)
        for group in groups:
            target = root / group['id']
            if group['id'] == 'ai-ml':
                subprocess.run(['sh', str(source / 'ai-ml-demos/install.sh'),
                    '--source', str(source / 'ai-ml-demos'), '--prefix',
                    str(target), '--bin-dir', str(args.bin_dir), '--board',
                    board], check=True)
            else:
                shutil.copytree(source / group['source'], target,
                    dirs_exist_ok=True, ignore=shutil.ignore_patterns(
                        '__pycache__', '*.pyc', 'tests'))
                (target / OWNED).touch()
            if group['id'] == 'multimedia':
                media = target / 'video-player/media'
                media.mkdir(exist_ok=True)
                shutil.copy2(cache, media / 'chicago.mp4')
                (target / 'video-player/player.py').chmod(0o755)
        lib = root / 'lib'
        lib.mkdir(exist_ok=True)
        for name in ('manager.py', 'terminal_ui.py', 'runtime.py', 'telemetry.py'):
            shutil.copy2(source / 'ai-ml-demos' / name, lib / name)
        for name in ('suite.py', 'catalog.toml', 'installer.py', 'install.sh'):
            shutil.copy2(source / name, root / name)
        (root / 'suite.py').chmod(0o755)
        (root / 'install.sh').chmod(0o755)
        (root / '.var-demos-installed').touch()
        args.bin_dir.mkdir(parents=True, exist_ok=True)
        link_command(args.bin_dir, 'var-demos', root / 'suite.py')
        if (root / 'multimedia/video-player/player.py').is_file():
            link_command(args.bin_dir, 'var-media',
                         root / 'multimedia/video-player/player.py')
    print('Installation complete. Run: var-demos')


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        raise SystemExit(f'Error: {error}')
