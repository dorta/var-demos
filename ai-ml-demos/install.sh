#!/bin/sh

# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

set -eu

ASSET_BASE_URL=${ASSET_BASE_URL:-}
BIN_DIR=${BIN_DIR:-/usr/bin}
INSTALL_ROOT=${INSTALL_ROOT:-/opt/var-demos/ai-ml}
VAR_DEMOS_REF=${VAR_DEMOS_REF:-demos}
VAR_DEMOS_REPOSITORY=${VAR_DEMOS_REPOSITORY:-varigit/var-demos}

BOARD=
DRY_RUN=0
LIST_ONLY=0
REQUESTED_DEMOS=
SOURCE_ROOT=
WORK_DIR=

usage() {
    cat <<'EOF'
Usage: install.sh [options] [demo ...]

Install every compatible demo, or only the demos named on the command line.

Options:
  --board BOARD       Override automatic board detection
  --bin-dir DIRECTORY Install the var-ai command in this directory
  --dry-run           Show what would be installed
  --list              List demos compatible with the detected board
  --prefix DIRECTORY  Installation directory
  --source DIRECTORY  Use a local ai-ml-demos source tree
  -h, --help          Show this help

Known board ids are defined in catalog.toml.
EOF
}

fail() {
    echo "Error: $*" >&2
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || \
        fail "required command not found: $1"
}

cleanup() {
    if [ -n "${WORK_DIR}" ] && [ -d "${WORK_DIR}" ]; then
        rm -rf "${WORK_DIR}"
    fi
}

detect_board() {
    [ -r /proc/device-tree/compatible ] || \
        fail "Device Tree compatible string is not available"
    BOARD=$(catalog detect) || \
        fail "unsupported board; use --board only for development"
}

download() {
    url=$1
    destination=$2

    curl \
        --fail \
        --location \
        --retry 5 \
        --retry-all-errors \
        --connect-timeout 15 \
        --output "${destination}" \
        "${url}"
}

fetch_source() {
    if [ -n "${SOURCE_ROOT}" ]; then
        [ -d "${SOURCE_ROOT}" ] || fail "source directory does not exist"
        return
    fi

    script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd || true)
    if [ -n "${script_dir}" ] && \
       [ -f "${script_dir}/catalog.toml" ]; then
        SOURCE_ROOT=${script_dir}
        return
    fi

    require_command curl
    require_command tar
    archive="${WORK_DIR}/source.tar.gz"
    source_dir="${WORK_DIR}/source"
    install -d "${source_dir}"
    url="https://github.com/${VAR_DEMOS_REPOSITORY}/archive/refs/heads/${VAR_DEMOS_REF}.tar.gz"
    echo "Downloading source from ${VAR_DEMOS_REPOSITORY}@${VAR_DEMOS_REF}"
    download "${url}" "${archive}"
    tar -xzf "${archive}" -C "${source_dir}"
    SOURCE_ROOT=$(find "${source_dir}" -type d \
        -path '*/ai-ml-demos' -print | head -n 1)
    [ -n "${SOURCE_ROOT}" ] || fail "ai-ml-demos not found"
}

catalog() {
    python3 "${SOURCE_ROOT}/catalog.py" \
        --catalog "${SOURCE_ROOT}/catalog.toml" "$@"
}

check_platform() {
    status=$(catalog platform-field "${BOARD}" status) || \
        fail "unknown board: ${BOARD}"
    [ "${status}" = "validated" ] || \
        fail "${BOARD} support is ${status}; hardware validation is required"

    if [ -z "${ASSET_BASE_URL}" ]; then
        ASSET_BASE_URL=$(catalog \
            platform-field "${BOARD}" asset_base_url)
    fi
}

load_demo() {
    demo=$1
    DEMO_TITLE=$(catalog demo-field "${demo}" title)
    DEMO_PATH=$(catalog demo-field "${demo}" path)
    DEMO_ENTRYPOINT=$(catalog demo-field "${demo}" entrypoint)
    DEMO_MANIFEST=$(catalog demo-field "${demo}" manifest)
}

demo_is_compatible() {
    catalog supports "$1" "${BOARD}" >/dev/null
}

selected_demos() {
    if [ -n "${REQUESTED_DEMOS}" ]; then
        printf '%s\n' ${REQUESTED_DEMOS}
    else
        catalog demos --platform "${BOARD}"
    fi
}

list_demos() {
    echo "Compatible demos for ${BOARD}:"
    catalog demos --platform "${BOARD}" --titles | \
        while IFS="$(printf '\t')" read -r demo title; do
            printf '  %-32s %s\n' "${demo}" "${title}"
        done
}

check_runtime() {
    require_command cp
    require_command curl
    require_command install
    require_command ln
    require_command python3
    require_command sha256sum

    [ -r /usr/lib/libvx_delegate.so ] || \
        fail "missing NPU delegate: /usr/lib/libvx_delegate.so"

    python3 - <<'PY' || fail "required Python modules are missing"
import cv2
import numpy
import tflite_runtime.interpreter
PY

    require_command gst-inspect-1.0
    for plugin in appsink decodebin imxvideoconvert_g2d; do
        gst-inspect-1.0 "${plugin}" >/dev/null 2>&1 || \
            fail "missing GStreamer plugin: ${plugin}"
    done
}

install_asset() {
    demo=$1
    expected=$2
    remote_path=$3
    relative_path=$4

    case "${remote_path}:${relative_path}" in
        /*:*|*:/|*..*) fail "unsafe asset path in ${demo}" ;;
    esac

    cache_file="${WORK_DIR}/assets/${expected}"
    if [ ! -f "${cache_file}" ]; then
        echo "Downloading ${remote_path}"
        download "${ASSET_BASE_URL}/${remote_path}" "${cache_file}.part"
        printf '%s  %s\n' "${expected}" "${cache_file}.part" | \
            sha256sum -c - >/dev/null
        mv -f "${cache_file}.part" "${cache_file}"
    fi

    destination="${INSTALL_ROOT}/${demo}/${relative_path}"
    install -d "$(dirname -- "${destination}")"
    install -m 0644 "${cache_file}" "${destination}"
}

install_demo() {
    demo=$1
    load_demo "${demo}"
    demo_is_compatible "${demo}" || \
        fail "${demo} is not compatible with ${BOARD}"

    echo "Installing ${DEMO_TITLE}"
    install -d "${INSTALL_ROOT}/${DEMO_PATH}"
    cp -R "${SOURCE_ROOT}/${DEMO_PATH}/." \
        "${INSTALL_ROOT}/${DEMO_PATH}/"

    manifest="${SOURCE_ROOT}/${DEMO_PATH}/${DEMO_MANIFEST}"
    while read -r expected remote_path relative_path; do
        case "${expected}" in
            ''|'#'*) continue ;;
        esac
        install_asset "${DEMO_PATH}" "${expected}" \
            "${remote_path}" "${relative_path}"
    done < "${manifest}"

    echo "  Run: cd ${INSTALL_ROOT}/${DEMO_PATH} && ${DEMO_ENTRYPOINT}"
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --board)
            [ "$#" -ge 2 ] || fail "--board requires a value"
            BOARD=$2
            shift 2
            ;;
        --bin-dir)
            [ "$#" -ge 2 ] || fail "--bin-dir requires a value"
            BIN_DIR=$2
            shift 2
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --list)
            LIST_ONLY=1
            shift
            ;;
        --prefix)
            [ "$#" -ge 2 ] || fail "--prefix requires a value"
            INSTALL_ROOT=$2
            shift 2
            ;;
        --source)
            [ "$#" -ge 2 ] || fail "--source requires a value"
            SOURCE_ROOT=$2
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --*) fail "unknown option: $1" ;;
        *)
            REQUESTED_DEMOS="${REQUESTED_DEMOS} $1"
            shift
            ;;
    esac
done

require_command install
require_command python3
WORK_DIR=$(mktemp -d)
trap cleanup EXIT HUP INT TERM
install -d "${WORK_DIR}/assets"
fetch_source
catalog validate --root "${SOURCE_ROOT}"

if [ -z "${BOARD}" ]; then
    detect_board
fi
check_platform

if [ "${LIST_ONLY}" -eq 1 ]; then
    list_demos
    exit 0
fi

if [ "${DRY_RUN}" -eq 1 ]; then
    echo "Board: ${BOARD}"
    echo "Install root: ${INSTALL_ROOT}"
    echo "Command: ${BIN_DIR}/var-ai"
    echo "Demos:"
    selected_demos | while read -r demo; do
        load_demo "${demo}"
        demo_is_compatible "${demo}" || \
            fail "${demo} is not compatible with ${BOARD}"
        echo "  ${demo}"
    done
    exit 0
fi

check_runtime
install -d "${INSTALL_ROOT}"
install -m 0755 "${SOURCE_ROOT}/install.sh" "${INSTALL_ROOT}/install.sh"
install -m 0644 "${SOURCE_ROOT}/catalog.toml" \
    "${INSTALL_ROOT}/catalog.toml"
install -m 0755 "${SOURCE_ROOT}/catalog.py" \
    "${INSTALL_ROOT}/catalog.py"
install -m 0755 "${SOURCE_ROOT}/manager.py" \
    "${INSTALL_ROOT}/manager.py"
selected_demos | while read -r demo; do
    install_demo "${demo}"
done

install -d "${BIN_DIR}"
if [ -e "${BIN_DIR}/var-ai" ] && [ ! -L "${BIN_DIR}/var-ai" ]; then
    fail "refusing to replace non-symlink: ${BIN_DIR}/var-ai"
fi
ln -sfn "${INSTALL_ROOT}/manager.py" "${BIN_DIR}/var-ai"

echo
echo "Installation complete: ${INSTALL_ROOT}"
echo "Run the demo manager: var-ai"
