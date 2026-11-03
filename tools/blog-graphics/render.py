"""Render a graphic HTML file to WebP with headless Chrome: render.py in.html out.webp WIDTH HEIGHT [scale]

Finds Chrome or Chromium on Windows, macOS or Linux (or the CHROME / CHROME_PATH variable).
No browser found: exits with a message, and the post uses a table instead.
"""
import os, sys, shutil, subprocess, pathlib, tempfile
from PIL import Image

CANDIDATES = [os.environ.get("CHROME", ""), os.environ.get("CHROME_PATH", ""),  # CHROME_PATH: set in Claude cloud sessions
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"]


def find_chrome():
    for c in CANDIDATES:
        if c and (os.path.isfile(c) or shutil.which(c)):
            return shutil.which(c) or c
    for p in sorted(pathlib.Path.home().glob(".cache/ms-playwright/chromium-*/chrome-linux*/chrome")):
        return str(p)  # Playwright's Chromium, if it was installed with `playwright install chromium`
    sys.exit("No Chrome/Chromium found: set CHROME, or skip the graphic and use a table.")


src, out, w, h = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
k = float(sys.argv[5]) if len(sys.argv) > 5 else 1
png = pathlib.Path(tempfile.mkdtemp()) / "shot.png"
args = [find_chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
        "--window-size=%d,%d" % (w, h), "--virtual-time-budget=3000", "--allow-file-access-from-files",
        "--screenshot=" + str(png), src.as_uri()]
if os.name != "nt" and hasattr(os, "geteuid") and os.geteuid() == 0:
    args.insert(1, "--no-sandbox")  # Chrome refuses to start as root (cloud containers) without it
subprocess.run(args, check=True, capture_output=True)
im = Image.open(png).convert("RGB").crop((0, 0, w * 2, h * 2)).resize((int(w * k), int(h * k)), Image.LANCZOS)
im.save(out, "WEBP", quality=88, method=6)
print(out, im.size, out.stat().st_size // 1024, "KB")
