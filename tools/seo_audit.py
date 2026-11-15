"""Schema / SEO / GEO audit of every P-Pulse post (Valentine's rule, 15 Nov 2026).

Run after `python build.py`:  python tools/seo_audit.py [slug ...]
Reads the source in src/posts/ and the built page in public/post/<slug>/.
Prints one block per post: FAIL lines must be fixed, WARN lines are for a
person to judge (GEO wording can't be fully checked by a script).
"""
import html
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "posts"
PUB = ROOT / "public"
GVN_PAGES = ("/services", "/investnow", "/sellmyhome", "/askaquestion", "/book-a-strategy-call",
             "/achiever-", "/elite-", "/bold-", "/contact")


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def words(s):
    return len(text(s).split())


def audit(slug):
    out = []
    fail = lambda m: out.append("  FAIL " + m)
    warn = lambda m: out.append("  WARN " + m)
    src = (SRC / f"{slug}.html").read_text(encoding="utf-8")
    meta = json.loads(re.search(r"<!--\s*(\{.*?\})\s*-->", src, re.S).group(1))
    body = src.split("-->", 1)[1]
    built_p = PUB / "post" / slug / "index.html"
    if not built_p.exists():
        return [f"{slug}: NOT BUILT (draft?)"]
    built = built_p.read_text(encoding="utf-8")

    t, d = meta.get("title", ""), meta.get("description", "")
    if not 50 <= len(t) <= 65: fail(f"title {len(t)} chars (50-65): {t}")
    if not 140 <= len(d) <= 158: fail(f"description {len(d)} chars (140-158)")
    if built.count("<h1") != 1: fail(f"{built.count('<h1')} H1s")
    if "noindex" in built: fail("noindex on built page")
    if meta.get("draft"): fail("still a draft")

    # schema
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', built, re.S)
    types, bp, faq = [], None, None
    for b in blocks:
        try:
            j = json.loads(b)
        except Exception as e:
            fail(f"JSON-LD does not parse: {e}"); continue
        ty = j.get("@type")
        types.append(ty if isinstance(ty, str) else "/".join(ty))
        if ty == "BlogPosting": bp = j
        if ty == "FAQPage": faq = j
    for need in ("BlogPosting", "FAQPage", "BreadcrumbList"):
        if need not in types: fail(f"no {need} schema")
    if bp:
        for k in ("headline", "description", "image", "author", "publisher", "datePublished", "dateModified",
                  "keywords", "wordCount", "mainEntityOfPage"):
            if not bp.get(k): fail(f"BlogPosting missing {k}")
        if bp.get("headline") != t: fail("headline != title")
        imgs = bp.get("image") or []
        if isinstance(imgs, (str, dict)): imgs = [imgs]
        if len(imgs) < 3: warn(f"BlogPosting has {len(imgs)} image(s)")
        cites = bp.get("citation") or []
        if not cites: fail("BlogPosting has no citation (primary sources)")
        if not (bp.get("contentLocation") or bp.get("spatialCoverage") or bp.get("about")):
            warn("no places in schema")
    # FAQ visible vs schema
    vis = re.findall(r'<details class="faq"><summary>(.*?)</summary><div class="answer">(.*?)</div></details>', body, re.S)
    if len(vis) < 3: fail(f"{len(vis)} FAQ items (want 3+)")
    if faq:
        sq = [(m["name"], m["acceptedAnswer"]["text"]) for m in faq.get("mainEntity", [])]
        if [text(q) for q, _ in vis] != [text(q) for q, _ in sq]: fail("FAQ schema questions != visible")
    for q, a in vis:
        n = words(a)
        if n < 25 or n > 90: warn(f"FAQ answer {n} words (40-80): {text(q)[:60]}")

    # structure
    h2s = [text(h) for h in re.findall(r"<h2[^>]*>(.*?)</h2>", body, re.S)]
    if not any(h.lower().startswith("key points") for h in h2s): fail("no Key points section")
    content_h2 = [h for h in h2s if not re.match(r"(key points|questions .* asking|sources)", h, re.I)]
    nq = sum(1 for h in content_h2 if h.endswith("?"))
    if content_h2 and nq < len(content_h2) * 0.6:
        warn(f"only {nq}/{len(content_h2)} H2s are questions: " + " | ".join(h for h in content_h2 if not h.endswith("?"))[:220])
    paras = re.findall(r"<p>(.*?)</p>", body, re.S)
    first2 = " ".join(text(p) for p in paras[:2])
    if not re.search(r"short answer|<strong>", " ".join(paras[:2])):
        warn("opening has no bolded direct answer")
    wc = words(body)
    if wc < 1000 or wc > 1700: warn(f"{wc} words in body source")

    # links
    links = re.findall(r'<a [^>]*href="([^"]+)"', body)
    internal_posts = {l for l in links if l.startswith("/post/")}
    gvn = [l for l in links if l.startswith(GVN_PAGES)]
    ext = [l for l in links if l.startswith("https://")]
    primary = [l for l in ext if re.search(r"gov\.uk|ons\.gov|nomisweb|bankofengland|legislation\.gov|parliament\.uk|"
                                           r"stoke\.gov|staffordshire\.gov|landregistry|ofgem|hmrc", l)]
    if len(internal_posts) < 2: fail(f"{len(internal_posts)} links to other posts (want 2-3)")
    if not gvn: fail("no link to a GVN page")
    if not primary: fail("no primary-source links")
    for l in internal_posts:
        if not (PUB / l.strip("/") / "index.html").exists(): fail(f"broken internal link {l}")
    for a in re.findall(r'<a [^>]*target="_blank"[^>]*>', body):
        if 'rel="noopener' not in a: fail("target=_blank without rel=noopener")

    # images
    for img in re.findall(r"<img [^>]*>", body):
        src_ = re.search(r'src="([^"]+)"', img).group(1)
        alt = re.search(r'alt="([^"]*)"', img)
        if not alt or len(alt.group(1)) < 15: fail(f"weak/no alt on {src_}")
        if "width=" not in img or "height=" not in img: fail(f"no width/height on {src_}")
        f = ROOT / src_.lstrip("/")
        if f.exists() and f.stat().st_size > 210_000: warn(f"{src_} is {f.stat().st_size // 1024} KB")
    if not re.search(r"not (legal|financial|tax)|general information", body, re.I): fail("no disclaimer")
    if len(meta.get("tags", [])) < 4: warn(f"{len(meta.get('tags', []))} tags")
    if not meta.get("places"): warn("no places in front matter")
    if "Updated" not in built and meta.get("modified"): warn("modified set but no visible Updated date")

    sitemap = (PUB / "sitemap.xml").read_text(encoding="utf-8")
    if f"/post/{slug}" not in sitemap: fail("not in sitemap")
    head = f"{slug}  [{wc} words, {len(vis)} FAQs, {len(internal_posts)} post links, {len(primary)} primary links, " \
           f"{len(cites) if bp else 0} citations, modified={meta.get('modified', '-')}]"
    return [head] + (out or ["  OK"])


if __name__ == "__main__":
    slugs = sys.argv[1:] or sorted(p.stem for p in SRC.glob("*.html"))
    nf = 0
    for s in slugs:
        lines = audit(s)
        nf += sum(1 for l in lines if "FAIL" in l)
        print("\n".join(lines))
    print(f"\n{len(slugs)} posts, {nf} FAIL lines")
    sys.exit(1 if nf else 0)
