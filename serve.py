#!/usr/bin/env python3
"""Usage: python3 serve.py [/path/to/scan.json]
No arg: serve this dir, open viewer with its default fetch fallback chain.
With arg: copy the scan.json into scans/ and open the viewer pointed at it.
Cross-platform (macOS/Linux/Windows), stdlib only.
"""
import subprocess
import sys
import shutil
import socket
import time
import urllib.request
import webbrowser
from pathlib import Path

DIR = Path(__file__).resolve().parent
STATE = DIR / ".serve.port"
SCAN_ARG = sys.argv[1] if len(sys.argv) > 1 else None


def port_alive(port):
    try:
        urllib.request.urlopen(f"http://localhost:{port}/viewer.html", timeout=0.5)
        return True
    except Exception:
        return False


# ponytail: only checks *a* server answers on the stored port, not that it's
# ours — good enough for a local dev helper.
port = None
if STATE.exists() and port_alive(STATE.read_text().strip()):
    port = STATE.read_text().strip()

if port is None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        port = str(s.getsockname()[1])

    kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if sys.platform == "win32":
        kwargs["creationflags"] = 0x00000208  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(
        [sys.executable, "-m", "http.server", port, "--directory", str(DIR)], **kwargs
    )
    STATE.write_text(port)
    for _ in range(50):
        if port_alive(port):
            break
        time.sleep(0.1)

url = f"http://localhost:{port}/viewer.html"
if SCAN_ARG:
    scans_dir = DIR / "scans"
    scans_dir.mkdir(exist_ok=True)
    name = f"{Path(SCAN_ARG).stem}-{int(time.time())}.json"
    shutil.copy(SCAN_ARG, scans_dir / name)
    url = f"{url}?src=scans/{name}"

print(url)
try:
    webbrowser.open(url)
except Exception:
    pass
