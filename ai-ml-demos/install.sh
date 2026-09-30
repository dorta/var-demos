#!/bin/sh

# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

set -eu

ALL_DEMOS="classification detection high-resolution-video-detection"
ASSET_BASE_URL=${ASSET_BASE_URL:-"https://nyc3.digitaloceanspaces.com/variscite-marketing/demos/machine-learning/imx8mplus/v1"}
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
  --dry-run           Show what would be installed
  --list              List demos compatible with the detected board
  --prefix DIRECTORY  Installation directory
  --source DIRECTORY  Use a local ai-ml-demos source tree
  -h, --help          Show this help

Supported board names: imx8mplus
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
    compatible=
    if [ -r /proc/device-tree/compatible ]; then
        compatible=$(tr '\0' '\n' </proc/device-tree/compatible)
    fi

    case "${compatible}" in
        *fsl,imx8mp*) BOARD=imx8mplus ;;
        *fsl,imx93*) fail "i.MX 93 demos are not validated yet" ;;
        *fsl,imx95*) fail "i.MX 95 demos are not validated yet" ;;
        *) fail "unsupported board; use --board only for development" ;;
    esac
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
       [ -f "${script_dir}/classification/demo.conf" ]; then
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

load_demo() {
    demo=$1
    config="${SOURCE_ROOT}/${demo}/demo.conf"
    [ -f "${config}" ] || fail "unknown demo: ${demo}"
    DEMO_TITLE=
    DEMO_BOARDS=
    DEMO_ENTRYPOINT=
    # shellcheck disable=SC1090
    . "${config}"
}

demo_is_compatible() {
    case " ${DEMO_BOARDS} " in
        *" ${BOARD} "*) return 0 ;;
        *) return 1 ;;
    esac
}

selected_demos() {
    if [ -n "${REQUESTED_DEMOS}" ]; then
        printf '%s\n' ${REQUESTED_DEMOS}
    else
        printf '%s\n' ${ALL_DEMOS}
    fi
}

list_demos() {
    echo "Compatible demos for ${BOARD}:"
    for demo in ${ALL_DEMOS}; do
        load_demo "${demo}"
        if demo_is_compatible; then
            printf '  %-32s %s\n' "${demo}" "${DEMO_TITLE}"
        fi
    done
}

check_runtime() {
    require_command cp
    require_command curl
    require_command install
    require_command python3
    require_command sha256sum

    [ -r /usr/lib/libvx_delegate.so ] || \
        fail "missing NPU delegate: /usr/lib/libvx_delegate.so"

    python3 - <<'PY' || fail "required Python modules are missing"
import cv2
import gi
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
    demo_is_compatible || \
        fail "${demo} is not compatible with ${BOARD}"

    echo "Installing ${DEMO_TITLE}"
    install -d "${INSTALL_ROOT}/${demo}"
    cp -R "${SOURCE_ROOT}/${demo}/." "${INSTALL_ROOT}/${demo}/"

    manifest="${SOURCE_ROOT}/${demo}/assets.manifest"
    while read -r expected remote_path relative_path; do
        case "${expected}" in
            ''|'#'*) continue ;;
        esac
        install_asset "${demo}" "${expected}" \
            "${remote_path}" "${relative_path}"
    done < "${manifest}"

    echo "  Run: cd ${INSTALL_ROOT}/${demo} && ${DEMO_ENTRYPOINT}"
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --board)
            [ "$#" -ge 2 ] || fail "--board requires a value"
            BOARD=$2
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

case "${BOARD}" in
    '') detect_board ;;
    imx8mplus) ;;
    *) fail "unsupported board override: ${BOARD}" ;;
esac

require_command install
WORK_DIR=$(mktemp -d)
trap cleanup EXIT HUP INT TERM
install -d "${WORK_DIR}/assets"
fetch_source

if [ "${LIST_ONLY}" -eq 1 ]; then
    list_demos
    exit 0
fi

if [ "${DRY_RUN}" -eq 1 ]; then
    echo "Board: ${BOARD}"
    echo "Install root: ${INSTALL_ROOT}"
    echo "Demos:"
    selected_demos | while read -r demo; do
        load_demo "${demo}"
        demo_is_compatible || \
            fail "${demo} is not compatible with ${BOARD}"
        echo "  ${demo}"
    done
    exit 0
fi

check_runtime
install -d "${INSTALL_ROOT}"
install -m 0755 "${SOURCE_ROOT}/install.sh" "${INSTALL_ROOT}/install.sh"
selected_demos | while read -r demo; do
    install_demo "${demo}"
done

echo
echo "Installation complete: ${INSTALL_ROOT}"
