"""Find, fetch and track blog photos so no image is ever used twice.

  python tools/blog-images/images.py search commons "Burton upon Trent terraced"
  python tools/blog-images/images.py search pixabay "rental keys"      (needs PIXABAY_API_KEY)
  python tools/blog-images/images.py add commons "File:Some photo.jpg" <post-slug> <name>
  python tools/blog-images/images.py add pixabay 123456 <post-slug> <name>
  python tools/blog-images/images.py graphic assets/img/blog/<file>.webp <post-slug>
  python tools/blog-images/images.py check
  python tools/blog-images/images.py seed          (one-off: record every image already on the site)

ledger.json is the record of every image on the site. `add` refuses a photo
that is already in it (same source id, or a near-identical picture by
perceptual hash, even if it came from somewhere else). `check` fails if any
post repeats an image, or a new post breaks the picture rules.

Security: downloads only over https from the hosts below, never SVG, opened
with Pillow and re-encoded (which drops EXIF/GPS and anything hidden in the
file). API keys are read from the environment and never printed or saved.
"""
import hashlib, html, io, json, os, pathlib, re, sys, tempfile, urllib.parse, urllib.request
from datetime import date
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
LEDGER = pathlib.Path(__file__).with_name("ledger.json")
BLOG_IMG = ROOT / "assets" / "img" / "blog"
POSTS = ROOT / "src" / "posts"
UA = "GVNEstateInvestBlog/1.0 (https://www.gvnestateinvest.com; blog image sourcing)"
HOSTS = {"commons.wikimedia.org", "upload.wikimedia.org", "thumb.wikimedia.org", "pixabay.com", "cdn.pixabay.com"}
OPEN_LICENCES = re.compile(r"^(CC BY(-SA)? [0-9.]+|CC0|Public domain|PD)", re.I)
MAX_BYTES = 30 * 1024 * 1024
NEAR = 6                      # dHash Hamming distance that counts as the same picture
RULES_FROM = "2026-11-01"     # posts dated from here must have >=2 photos and <=1 graphic in the body
Image.MAX_IMAGE_PIXELS = 80_000_000


def die(msg):
    print("ERROR:", msg)
    sys.exit(1)


def get(url, binary=False):
    u = urllib.parse.urlparse(url)
    if u.scheme != "https" or u.hostname not in HOSTS:
        die("refusing to fetch from %s" % u.hostname)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            data = r.read(MAX_BYTES + 1)
    except Exception as e:  # never echo the URL: it may hold an API key
        die("download failed from %s (%s)" % (u.hostname, type(e).__name__))
    if len(data) > MAX_BYTES:
        die("file too large")
    return data if binary else json.loads(data.decode("utf-8"))


def load():
    return json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {"images": []}


def save(led):
    LEDGER.write_text(json.dumps(led, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def dhash(im):
    g = im.convert("L").resize((9, 8), Image.LANCZOS)
    px = list(g.tobytes())
    bits = "".join("1" if px[r * 9 + c] > px[r * 9 + c + 1] else "0" for r in range(8) for c in range(8))
    return "%016x" % int(bits, 2)


def dist(a, b):
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def clash(led, source, sid, h):
    for e in led["images"]:
        if source and e.get("source") == source and str(e.get("source_id")) == str(sid):
            return "already used: %s (%s)" % (e["file"], e.get("post") or "site")
        if e.get("dhash") and dist(e["dhash"], h) <= NEAR:
            return "near-identical to %s (%s)" % (e["file"], e.get("post") or "site")
    return None


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


# ---------- search ----------
def search_commons(q):
    api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": q + " filetype:bitmap", "gsrlimit": 30, "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1800})
    pages = (get(api).get("query") or {}).get("pages") or {}
    out = []
    for p in sorted(pages.values(), key=lambda p: p.get("index", 0)):
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata") or {}
        lic = strip_tags((md.get("LicenseShortName") or {}).get("value"))
        if ii.get("mime") not in ("image/jpeg", "image/png", "image/webp") or not OPEN_LICENCES.match(lic):
            continue
        if ii.get("width", 0) < 1200 or ii.get("height", 0) < 800:
            continue
        out.append({"id": p["title"], "licence": lic,
                    "author": strip_tags((md.get("Artist") or {}).get("value"))[:80],
                    "size": "%dx%d" % (ii["width"], ii["height"]),
                    "date": strip_tags((md.get("DateTimeOriginal") or {}).get("value"))[:10],
                    "about": " ".join(strip_tags((md.get("ImageDescription") or {}).get("value")).split())[:160]})
    return out


def pixabay_key():
    k = os.environ.get("PIXABAY_API_KEY", "").strip()
    if not re.fullmatch(r"[0-9]+-[0-9a-f]+", k):
        die("PIXABAY_API_KEY is not set (or not in Pixabay's format)")
    return k


def search_pixabay(q):
    api = "https://pixabay.com/api/?" + urllib.parse.urlencode({
        "key": pixabay_key(), "q": q[:100], "image_type": "photo", "orientation": "horizontal",
        "safesearch": "true", "min_width": 1200, "per_page": 40})
    return [{"id": h["id"], "licence": "Pixabay Content License", "author": h.get("user", ""),
             "size": "%dx%d" % (h["imageWidth"], h["imageHeight"]), "date": "",
             "about": h.get("tags", "")} for h in get(api).get("hits", [])]


def cmd_search(source, q):
    led = load()
    used = {(e.get("source"), str(e.get("source_id"))) for e in led["images"]}
    hits = search_commons(q) if source == "commons" else search_pixabay(q) if source == "pixabay" else die("source must be commons or pixabay")
    for h in hits:
        if (source, str(h["id"])) in used:
            continue  # used before: not even offered
        print("- %s\n    %s | %s | %s %s\n    %s" % (h["id"], h["licence"], h["author"], h["size"], h["date"], h["about"]))
    if not hits:
        print("no results")


# ---------- add ----------
def fetch_commons(title):
    if not title.startswith("File:"):
        title = "File:" + title
    api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "titles": title, "prop": "imageinfo",
        "iiprop": "url|mime|extmetadata", "iiurlwidth": 1800})
    page = next(iter(get(api)["query"]["pages"].values()))
    ii = (page.get("imageinfo") or [None])[0] or die("not found on Commons: " + title)
    md = ii.get("extmetadata") or {}
    lic = strip_tags((md.get("LicenseShortName") or {}).get("value"))
    if not OPEN_LICENCES.match(lic):
        die("licence not allowed: " + lic)
    return get(ii.get("thumburl") or ii["url"], binary=True), {
        "source": "commons", "source_id": page["title"], "page": ii["descriptionurl"],
        "author": strip_tags((md.get("Artist") or {}).get("value"))[:120], "licence": lic,
        "licence_url": strip_tags((md.get("LicenseUrl") or {}).get("value")),
        "about": strip_tags((md.get("ImageDescription") or {}).get("value"))[:300]}


def fetch_pixabay(pid):
    api = "https://pixabay.com/api/?" + urllib.parse.urlencode({"key": pixabay_key(), "id": str(int(pid))})
    hits = get(api).get("hits") or die("not found on Pixabay: %s" % pid)
    h = hits[0]
    return get(h["largeImageURL"], binary=True), {
        "source": "pixabay", "source_id": str(h["id"]), "page": h["pageURL"], "author": h.get("user", ""),
        "licence": "Pixabay Content License", "licence_url": "https://pixabay.com/service/license-summary/",
        "about": h.get("tags", "")}


def crop_3x2(im, w=1200, h=800):
    r = im.width / im.height
    if r > 1.5:
        nw = int(im.height * 1.5)
        im = im.crop(((im.width - nw) // 2, 0, (im.width - nw) // 2 + nw, im.height))
    else:
        nh = int(im.width / 1.5)
        top = max(0, int((im.height - nh) * 0.45))
        im = im.crop((0, top, im.width, top + nh))
    return im.resize((w, h), Image.LANCZOS)


def cmd_add(source, sid, slug, name):
    if not re.fullmatch(r"[a-z0-9-]+", slug) or not re.fullmatch(r"[a-z0-9-]+", name):
        die("slug and name must be lower-case letters, digits and hyphens")
    data, meta = fetch_commons(sid) if source == "commons" else fetch_pixabay(sid) if source == "pixabay" else die("source must be commons or pixabay")
    try:
        im = Image.open(io.BytesIO(data))
        if im.format not in ("JPEG", "PNG", "WEBP"):
            die("unexpected file type " + str(im.format))
        im.load()
    except Exception as e:
        die("not a valid image (%s)" % type(e).__name__)
    if im.width < 1200 or im.height < 800:
        die("too small (%dx%d); need at least 1200x800" % im.size)
    im = crop_3x2(im.convert("RGB"))
    h = dhash(im)
    led = load()
    why = clash(led, meta["source"], meta["source_id"], h)
    if why:
        die(why)
    out = BLOG_IMG / ("%s-%s.webp" % (slug, name))
    if out.exists():
        die("file exists: " + out.name)
    im.save(out, "WEBP", quality=82, method=6)  # fresh encode: no EXIF, no GPS
    rel = "/" + out.relative_to(ROOT).as_posix()
    led["images"].append(dict(file=rel, kind="photo", post=slug, added=date.today().isoformat(),
                              dhash=h, **meta))
    save(led)
    print("saved %s (%d KB)" % (rel, out.stat().st_size // 1024))
    print("credit: %s | %s | %s | %s" % (meta["author"], meta["licence"], meta["page"], meta["about"][:120]))


def cmd_graphic(path, slug):
    p = (ROOT / path).resolve()
    if not p.is_file() or BLOG_IMG not in p.parents:
        die("graphic must be a file in assets/img/blog")
    led = load()
    rel = "/" + p.relative_to(ROOT).as_posix()
    if any(e["file"] == rel for e in led["images"]):
        die("already recorded: " + rel)
    led["images"].append(dict(file=rel, kind="graphic", post=slug, added=date.today().isoformat(),
                              dhash=dhash(Image.open(p)), source="gvn", source_id=rel))
    save(led)
    print("recorded graphic", rel)


# ---------- check ----------
def post_images(text):
    body = text.split("-->", 1)[1] if "-->" in text else text
    return re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', body)


def cmd_check():
    led = load()
    by_file = {e["file"]: e for e in led["images"]}
    bad, old = [], []
    for e in led["images"]:
        if not (ROOT / e["file"].lstrip("/")).is_file():
            bad.append("ledger file missing on disk: " + e["file"])
    for i, a in enumerate(led["images"]):
        for b in led["images"][i + 1:]:
            # repeats between two images that were already on the site at seeding are
            # reported but don't fail; anything added since must be unique
            to = old if a["kind"] == "site" and b["kind"] == "site" else bad
            if a.get("source") == b.get("source") and a.get("source") != "site" and str(a.get("source_id")) == str(b.get("source_id")):
                to.append("same source used twice: %s and %s" % (a["file"], b["file"]))
            elif a.get("dhash") and b.get("dhash") and dist(a["dhash"], b["dhash"]) <= NEAR \
                    and not a["file"].replace("-m.webp", ".webp") == b["file"].replace("-m.webp", ".webp"):
                to.append("near-identical images: %s and %s" % (a["file"], b["file"]))
    seen = {}
    for f in sorted(POSTS.glob("*.html")):
        text = f.read_text(encoding="utf-8")
        head = json.loads(text.split("<!--", 1)[1].split("-->", 1)[0])
        imgs = post_images(text)
        cover = head.get("cover", "")
        for src in imgs + ([cover] if cover else []):
            if src.startswith("/assets/img/blog/") and src not in by_file:
                bad.append("%s: %s is not in the ledger" % (f.name, src))
            if src in seen and seen[src] != f.name:
                bad.append("%s reuses %s from %s" % (f.name, src, seen[src]))
            seen.setdefault(src, f.name)
        if len(imgs) != len(set(imgs)) or cover in imgs:
            bad.append("%s shows the same image twice" % f.name)
        mine = [by_file[s] for s in imgs + [cover] if s in by_file and by_file[s]["kind"] != "site"]
        for i, a in enumerate(mine):
            for b in mine[i + 1:]:
                if dist(a["dhash"], b["dhash"]) <= NEAR:
                    bad.append("%s: %s and %s look the same" % (f.name, a["file"], b["file"]))
        if head.get("date", "")[:10] >= RULES_FROM:
            kinds = [by_file.get(s, {}).get("kind") for s in imgs]
            if kinds.count("photo") < 2:
                bad.append("%s: needs at least 2 photos in the body (has %d)" % (f.name, kinds.count("photo")))
            if kinds.count("graphic") > 1:
                bad.append("%s: at most 1 graphic in the body (has %d)" % (f.name, kinds.count("graphic")))
            if cover and by_file.get(cover, {}).get("kind") != "photo":
                bad.append("%s: cover must be a recorded photo" % f.name)
    for b in bad:
        print("FAIL", b)
    print("images check: %s (%d images in ledger; %d repeats among older pre-ledger images, see `check --old`)"
          % ("FAIL" if bad else "PASS", len(led["images"]), len(old)))
    if "--old" in sys.argv:
        for o in old:
            print("OLD ", o)
    sys.exit(1 if bad else 0)


def cmd_seed():
    led = load()
    known = {e["file"] for e in led["images"]}
    for p in sorted((ROOT / "assets" / "img").rglob("*")):
        if p.suffix.lower() not in (".webp", ".jpg", ".jpeg", ".png"):
            continue
        rel = "/" + p.relative_to(ROOT).as_posix()
        if rel in known:
            continue
        led["images"].append({"file": rel, "kind": "site", "source": "site", "source_id": rel,
                              "dhash": dhash(Image.open(p)), "added": "seed"})
    save(led)
    print("ledger now holds", len(led["images"]))


if __name__ == "__main__":
    a = sys.argv[1:]
    try:
        if a[:1] == ["search"] and len(a) == 3:
            cmd_search(a[1], a[2])
        elif a[:1] == ["add"] and len(a) == 5:
            cmd_add(*a[1:])
        elif a[:1] == ["graphic"] and len(a) == 3:
            cmd_graphic(a[1], a[2])
        elif a[:1] == ["check"]:
            cmd_check()
        elif a == ["seed"]:
            cmd_seed()
        else:
            print(__doc__)
    except KeyboardInterrupt:
        sys.exit(1)
