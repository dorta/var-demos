import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


def run_cmd(cmd: List[str], check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=check)


def shutil_which(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def list_video_devices() -> List[Dict[str, str]]:
    devices = []
    by_path = {}
    paths = sorted(str(p) for p in Path("/dev").glob("video*"))

    for path in paths:
        drv = ""
        card = ""
        kind = "unknown"
        if shutil_which("v4l2-ctl"):
            out = run_cmd(["v4l2-ctl", "-d", path, "--all"]).stdout
            m_drv = re.search(r"^\s*Driver name\s*:\s*(.+)$", out, re.MULTILINE)
            m_card = re.search(r"^\s*Card type\s*:\s*(.+)$", out, re.MULTILINE)
            drv = m_drv.group(1).strip() if m_drv else ""
            card = m_card.group(1).strip() if m_card else ""
            if drv == "uvcvideo":
                kind = "USB"
            elif "mxc-isi" in card or "csi" in card.lower():
                kind = "MIPI/CSI"
        info = {"path": path, "driver": drv, "card": card, "kind": kind}
        devices.append(info)
        by_path[path] = info

    if shutil_which("v4l2-ctl"):
        out = run_cmd(["v4l2-ctl", "--list-devices"]).stdout
        current = ""
        for line in out.splitlines():
            if not line.strip():
                continue
            if not line.startswith("\t"):
                current = line.strip()
                continue
            dev = line.strip()
            if dev in by_path and not by_path[dev]["card"]:
                by_path[dev]["card"] = current

    return devices


def print_video_devices(devices: List[Dict[str, str]]) -> None:
    print("Available capture devices:")
    if not devices:
        print("  (none found)")
        return
    for idx, d in enumerate(devices):
        print(
            f"  [{idx}] {d['path']}  kind={d['kind']}  "
            f"driver={d['driver'] or '?'}  card={d['card'] or '?'}"
        )


def choose_default_camera(devices: List[Dict[str, str]]) -> str:
    for d in devices:
        if d["kind"] == "USB":
            return d["path"]
    for d in devices:
        if d["kind"] == "MIPI/CSI":
            return d["path"]
    if devices:
        return devices[0]["path"]
    return "/dev/video0"


def prompt_camera_selection(devices: List[Dict[str, str]], default_camera: str) -> str:
    if not devices:
        return default_camera

    default_idx = 0
    for idx, d in enumerate(devices):
        if d["path"] == default_camera:
            default_idx = idx
            break

    if not os.isatty(0):
        print(f"Non-interactive shell detected. Using default camera: {default_camera}")
        return default_camera

    print("")
    print("Select camera by index and press Enter.")
    print(f"Default [{default_idx}] = {default_camera}")
    while True:
        try:
            answer = input("Camera index: ").strip()
        except EOFError:
            print(f"Input closed. Using default camera: {default_camera}")
            return default_camera

        if answer == "":
            return default_camera
        if answer.isdigit():
            idx = int(answer)
            if 0 <= idx < len(devices):
                return devices[idx]["path"]
        print("Invalid index. Please try again.")


def resolve_media_device(preferred: str = "") -> Optional[str]:
    if preferred and Path(preferred).exists():
        return preferred
    for p in sorted(Path("/dev").glob("media*")):
        return str(p)
    return None


def infer_mipi_csi_index(camera: str, fallback: int = 0) -> int:
    match = re.search(r"/dev/video(\d+)$", camera)
    if not match:
        return fallback
    return int(match.group(1)) % 2


def setup_mipi_media_pipeline(csi_index: int, width: int, height: int, pixel_fmt: str, media_dev: str = "") -> None:
    if not shutil_which("media-ctl"):
        print("WARN: media-ctl not found, skipping MIPI setup.")
        return

    dev = resolve_media_device(media_dev)
    if not dev:
        print("WARN: no /dev/media* found, skipping MIPI setup.")
        return

    if csi_index == 1:
        sensor = "ov5640 7-003c"
        inactive_sensor = "ov5640 2-003c"
        csidev = "csidev-4ad40000.csi"
        inactive_csidev = "csidev-4ad30000.csi"
        formatter = "4ac10000.syscon:formatter@120"
        inactive_formatter = "4ac10000.syscon:formatter@20"
        crossbar_pad = 3
        active_routes = (
            "2/0->5/0[0],3/0->6/0[1],2/0->7/0[0],3/0->8/0[1],"
            "2/0->9/0[0],3/0->10/0[1],2/0->11/0[0],3/0->12/0[1]"
        )
    else:
        sensor = "ov5640 2-003c"
        inactive_sensor = "ov5640 7-003c"
        csidev = "csidev-4ad30000.csi"
        inactive_csidev = "csidev-4ad40000.csi"
        formatter = "4ac10000.syscon:formatter@20"
        inactive_formatter = "4ac10000.syscon:formatter@120"
        crossbar_pad = 2
        active_routes = (
            "2/0->5/0[1],3/0->6/0[0],2/0->7/0[1],3/0->8/0[0],"
            "2/0->9/0[1],3/0->10/0[0],2/0->11/0[1],3/0->12/0[0]"
        )

    topology = run_cmd(["media-ctl", "-d", dev, "-p"]).stdout
    if sensor not in topology and "mainline" in topology:
        sensor = sensor.replace("ov5640 ", "ov5640_mainline ")
        inactive_sensor = inactive_sensor.replace("ov5640 ", "ov5640_mainline ")

    print(f"Setting MIPI media pipeline: dev={dev} csi={csi_index} sensor='{sensor}' {width}x{height} fmt={pixel_fmt}")

    cmds = [
        ["media-ctl", "-d", dev, "-l", f"'{sensor}':0->'{csidev}':0 [1]"],
        ["media-ctl", "-d", dev, "-l", f"'{inactive_sensor}':0->'{inactive_csidev}':0 [0]"],
        ["media-ctl", "-d", dev, "-R", f"'{inactive_csidev}' [0/0->1/0[0]]"],
        ["media-ctl", "-d", dev, "-R", f"'{inactive_formatter}' [0/0->1/0[0]]"],
        ["media-ctl", "-d", dev, "-R", f"'{csidev}' [0/0->1/0[1]]"],
        ["media-ctl", "-d", dev, "-R", f"'{formatter}' [0/0->1/0[1]]"],
        ["media-ctl", "-d", dev, "-R", f"'crossbar' [{active_routes}]"],
        ["media-ctl", "-d", dev, "-V", f"'{sensor}':0 [fmt: {pixel_fmt}/{width}x{height} field:none]"],
        ["media-ctl", "-d", dev, "-V", f"'{csidev}':0 [fmt: {pixel_fmt}/{width}x{height} field:none]"],
        ["media-ctl", "-d", dev, "-V", f"'{formatter}':0 [fmt: {pixel_fmt}/{width}x{height} field:none]"],
        ["media-ctl", "-d", dev, "-V", f"'crossbar':{crossbar_pad} [fmt: {pixel_fmt}/{width}x{height} field:none]"],
    ]

    for i in range(8):
        cmds.append(["media-ctl", "-d", dev, "-V", f"'mxc_isi.{i}':0 [fmt: {pixel_fmt}/{width}x{height} field:none]"])

    for cmd in cmds:
        try:
            run_cmd(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            print(f"WARN: media-ctl command failed: {' '.join(cmd)}")
            print(exc.stdout)


def open_camera_capture(cv2_module, camera: str, kind: str, width: int, height: int, fps: int):
    if kind == "MIPI/CSI":
        pipeline = (
            f"v4l2src device={camera} io-mode=mmap ! "
            f"video/x-raw,width={width},height={height},format=YUY2 ! "
            "videoconvert ! video/x-raw,format=BGR ! "
            "appsink drop=1 max-buffers=1 sync=false"
        )
        cap = cv2_module.VideoCapture(pipeline, cv2_module.CAP_GSTREAMER)
        if cap.isOpened():
            return cap, pipeline

    if camera.startswith("/dev/video"):
        cap = cv2_module.VideoCapture(camera, cv2_module.CAP_V4L2)
        cap.set(cv2_module.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2_module.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2_module.CAP_PROP_FPS, fps)
        return cap, camera

    return cv2_module.VideoCapture(camera), camera
