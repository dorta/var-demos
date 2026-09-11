#!/usr/bin/env bash
# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

set -euo pipefail

readonly DEFAULT_REF="imx8mp-ml-demo-suite"
readonly REPOSITORY="dorta/var-demos"

install_dir="${VAR_DEMOS_INSTALL_DIR:-${HOME}/var-demos}"
archive_ref="${VAR_DEMOS_REF:-$DEFAULT_REF}"
force=false

usage() {
    cat <<EOF
Install the Variscite demo suite from github.com/$REPOSITORY.

Usage: install.sh [options]

Options:
  --dir PATH   Installation directory (default: $install_dir)
  --ref REF    Branch, tag, or commit to install (default: $archive_ref)
  --force      Back up and replace an existing installation
  -h, --help   Show this help

Environment equivalents:
  VAR_DEMOS_INSTALL_DIR, VAR_DEMOS_REF, VAR_DEMOS_ARCHIVE_URL
EOF
}

die() {
    echo "[ERROR] $*" >&2
    exit 1
}

while (($#)); do
    case "$1" in
        --dir)
            (($# >= 2)) || die "--dir requires a path"
            install_dir="$2"
            shift 2
            ;;
        --ref)
            (($# >= 2)) || die "--ref requires a value"
            archive_ref="$2"
            shift 2
            ;;
        --force)
            force=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "Unknown option: $1"
            ;;
    esac
done

command -v curl >/dev/null 2>&1 || die "curl is required"
command -v tar >/dev/null 2>&1 || die "tar is required"

[[ -n "$install_dir" ]] || die "Installation directory cannot be empty"
[[ "$install_dir" != "/" ]] || die "Refusing to install over /"

install_parent="$(dirname -- "$install_dir")"
install_name="$(basename -- "$install_dir")"
mkdir -p "$install_parent"

if [[ -e "$install_dir" && "$force" != true ]]; then
    die "$install_dir already exists; use --force to back it up and replace it"
fi

work_dir="$(mktemp -d "$install_parent/.${install_name}.install.XXXXXX")"
archive="$work_dir/archive.tar.gz"
stage="$work_dir/stage"
backup=""

cleanup() {
    rm -rf -- "$work_dir"
}
trap cleanup EXIT

archive_url="${VAR_DEMOS_ARCHIVE_URL:-https://github.com/$REPOSITORY/archive/$archive_ref.tar.gz}"
echo "[INFO] Downloading $REPOSITORY at $archive_ref"
curl --fail --location --silent --show-error --retry 3 \
    --proto '=https' --tlsv1.2 "$archive_url" --output "$archive"

mkdir -p "$stage"
tar -xzf "$archive" --strip-components=1 -C "$stage"

[[ -x "$stage/ml-demo" ]] || die "Archive validation failed: ml-demo is missing"
[[ -s "$stage/machine-learning-demos/tflite/python/imx8mplus/assets/models/ssd-mobilenet-v1/ssd_mobilenet_v1_1_default_1.tflite" ]] || \
    die "Archive validation failed: SSD MobileNet model is missing"

if broken_link="$(find "$stage" -type l ! -exec test -e {} \; -print -quit)" && \
        [[ -n "$broken_link" ]]; then
    die "Archive validation failed: broken symlink $broken_link"
fi

if [[ -e "$install_dir" ]]; then
    backup="${install_dir}.backup.$(date -u +%Y%m%dT%H%M%SZ)"
    echo "[INFO] Moving existing installation to $backup"
    mv -- "$install_dir" "$backup"
fi

mv -- "$stage" "$install_dir"
trap - EXIT
rm -rf -- "$work_dir"

echo "[OK] Installed to $install_dir"
[[ -z "$backup" ]] || echo "[INFO] Previous installation: $backup"
echo "[INFO] Run: cd '$install_dir' && ./ml-demo --help"
