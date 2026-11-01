"""Render a graphic HTML file to WebP with headless Chrome: render.py in.html out.webp WIDTH HEIGHT"""
import sys, subprocess, pathlib, tempfile
from PIL import Image
src, out, w, h = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
k = float(sys.argv[5]) if len(sys.argv) > 5 else 1
png = pathlib.Path(tempfile.mkdtemp()) / "shot.png"
chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                "--window-size=%d,%d" % (w, h), "--virtual-time-budget=3000", "--allow-file-access-from-files",
                "--screenshot=" + str(png), src.as_uri()], check=True, capture_output=True)
im = Image.open(png).convert("RGB").crop((0, 0, w * 2, h * 2)).resize((int(w * k), int(h * k)), Image.LANCZOS)
im.save(out, "WEBP", quality=88, method=6)
print(out, im.size, out.stat().st_size // 1024, "KB")
