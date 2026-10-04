"""
Checks the built site. Run after build.py.

    python check.py

For every HTML file in public/:
  - <title>, meta description and canonical are present (canonical on the
    www.gvnestateinvest.com host)
  - no duplicate ids; every #anchor and aria-controls / aria-labelledby /
    aria-describedby / label[for] target exists
  - tags balance
  - every internal link, image, script, stylesheet and download resolves to a
    file in public/
  - every <img> has alt text and width/height
  - every form posts through data-form and has the honeypot
Plus: every old Wix URL still answers, and sitemap.xml only lists real pages.
"""

import pathlib
import re
import sys
from urllib.parse import urlparse, unquote

ROOT = pathlib.Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
HOST = "https://www.gvnestateinvest.com"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

# Every URL the old Wix site served (from its sitemaps and its page table).
OLD_URLS = """/ /about-us /services /investnow /offmarketdeals /sellmyhome /askaquestion /contact /provenance-pulse
/provenance-pulse/categories/property-news /provenance-pulse/categories/companies-house /provenance-pulse/categories/hmrc
/provenance-pulse/categories/hands-free-property-investment /provenance-pulse/categories/renters-rights-bill
/provenance-pulse/categories/accounts /properties/semi-detached-house-fenton- /privacyandcookiepolicy
/mediadisclaimerandattributions /elite-investor-blueprint-handsfree-service /achiever-investor-blueprint-handsfree-service
/bold-investor-blueprint-handsfree-service /start /optinform /optinform/gv2mkhfkhkkhdkhjcd10ku
/investnow/gv1mkhfkhkkhdkhjcd10ku /thank-you-page /home /popup-d1pyg /popup-suauy /popup-syzwe /popup-cf17t
/book-online /booking-calendar /booking-form /service-page /search /cart-page /checkout /fullscreen-page /blank-ncx68
/error404 /post /properties-list
/post/the-60-day-capital-gains-tax-clock-what-landlords-must-do-the-moment-a-sale-completes
/post/three-rental-indices-three-different-numbers-reading-the-uk-rental-market-in-summer-2026
/post/section-21-is-gone-mtd-is-live-what-august-2026-s-rule-changes-mean-for-uk-landlords
/post/selling-a-rental-property-in-2026-the-60-day-capital-gains-tax-clock-most-landlords-miss
/post/epc-c-by-2030-what-the-warm-homes-plan-means-for-your-rental-portfolio
/post/buy-refurbish-refinance-repeat-how-hands-free-investors-recycle-their-capital-in-2026
/post/own-it-personally-or-through-a-company-what-uk-property-investors-need-to-know-about-structure-and
/post/renters-rights-bill-2025
/post/making-tax-digital-why-landlords-below-the-threshold-should-still-get-ready-now
/post/companies-house-2027-revolution-as-paper-filings-become-illegal
/post/hands-free-property-investment-in-2026-why-more-uk-investors-are-choosing-managed-over-diy
/post/approvals-are-rising-purchase-lending-isn-t-what-the-uk-s-latest-mortgage-data-means-for-investors""".split()

problems = []


def fail(page, msg):
    problems.append("%s: %s" % (page, msg))


def resolve(path):
    """Map a site path to a file in public/ the way a static host would."""
    path = unquote(path.split("#")[0].split("?")[0])
    if path in ("", "/"):
        return PUBLIC / "index.html"
    p = PUBLIC / path.lstrip("/")
    if p.is_file():
        return p
    if (p / "index.html").is_file():
        return p / "index.html"
    return None


def strip_non_markup(h):
    h = re.sub(r"<!--.*?-->", "", h, flags=re.S)
    h = re.sub(r"(<(style|script)\b[^>]*>).*?(</\2>)", r"\1\3", h, flags=re.S | re.I)
    return h


def check_balance(page, h):
    stack = []
    for m in re.finditer(r"<(/?)([a-zA-Z][\w-]*)([^>]*?)(/?)>", h):
        closing, name = m.group(1), m.group(2).lower()
        if name in VOID or m.group(4):
            continue
        if closing:
            if stack and stack[-1] == name:
                stack.pop()
            else:
                fail(page, "mismatched </%s> (open: %s)" % (name, stack[-1] if stack else "nothing"))
                if name in stack:
                    while stack and stack.pop() != name:
                        pass
        else:
            stack.append(name)
    if stack:
        fail(page, "unclosed tags: %s" % ", ".join(stack))


def check_page(f):
    page = "/" + str(f.relative_to(PUBLIC)).replace("\\", "/")
    h = f.read_text(encoding="utf-8")
    markup = strip_non_markup(h)
    is_redirect = 'http-equiv="refresh"' in h

    # head
    t = re.search(r"<title>([^<]+)</title>", h)
    if not t or not t.group(1).strip():
        fail(page, "missing <title>")
    d = re.search(r'<meta name="description" content="([^"]*)"', h)
    if not d or len(d.group(1).strip()) < 20:
        fail(page, "missing or too-short meta description")
    c = re.search(r'<link rel="canonical" href="([^"]+)"', h)
    if not c:
        fail(page, "missing canonical")
    elif not c.group(1).startswith(HOST):
        fail(page, "canonical not on %s: %s" % (HOST, c.group(1)))
    if "<!doctype html>" not in h.lower()[:30]:
        fail(page, "missing doctype")
    if 'name="viewport"' not in h:
        fail(page, "missing viewport")
    left = re.findall(r"\{\{[^}]+\}\}", h)
    if left:
        fail(page, "unsubstituted tokens %s" % left)

    check_balance(page, markup)

    ids = re.findall(r'\sid="([^"]+)"', markup)
    seen = set()
    for i in ids:
        if i in seen:
            fail(page, "duplicate id %s" % i)
        seen.add(i)
    for a in re.findall(r'href="#([^"]+)"', markup):
        if a not in seen:
            fail(page, "anchor #%s has no target" % a)
    for attr in ("aria-controls", "aria-labelledby", "for"):
        for v in re.findall(r'\s%s="([^"]+)"' % attr, markup):
            if v not in seen:
                fail(page, "%s=%s has no target" % (attr, v))
    for v in re.findall(r'aria-describedby="([^"]+)"', markup):
        for one in v.split():
            if one not in seen:
                fail(page, "aria-describedby=%s has no target" % one)

    # links and assets
    refs = re.findall(r'\s(?:href|src)="([^"]+)"', markup)
    refs += re.findall(r'content="0; url=([^"]+)"', h)
    for r in refs:
        if r.startswith(("mailto:", "tel:", "#", "data:")):
            continue
        u = urlparse(r)
        if u.scheme in ("http", "https"):
            if u.netloc.endswith("gvnestateinvest.com") and u.netloc != "console.gvnestateinvest.com":
                target = u.path or "/"
            else:
                continue
        else:
            target = r
            if not target.startswith("/"):
                fail(page, "relative link %s (use /root-relative)" % r)
                continue
        if resolve(target) is None:
            fail(page, "broken link %s" % r)

    for img in re.findall(r"<img\b[^>]*>", markup):
        if not re.search(r'\salt="', img):
            fail(page, "img without alt: %s" % img[:80])
        if not (re.search(r"\swidth=", img) and re.search(r"\sheight=", img)):
            fail(page, "img without width/height: %s" % img[:80])

    # forms
    for form in re.findall(r"<form\b[^>]*>.*?</form>", markup, flags=re.S):
        if "data-form=" not in form:
            fail(page, "form without data-form")
        if 'name="website"' not in form:
            fail(page, "form without honeypot")
        for ctl in re.findall(r"<(?:input|select|textarea)\b[^>]*>", form):
            if 'name="website"' in ctl:
                continue
            m = re.search(r'\sid="([^"]+)"', ctl)
            if not m:
                fail(page, "form control without id: %s" % ctl[:70])
                continue
            if 'data-group' in ctl:
                continue  # inside a fieldset whose legend labels it, and wrapped in its own label
            if ('for="%s"' % m.group(1)) not in form and not re.search(r'<label class="check"><input[^>]*id="%s"' % re.escape(m.group(1)), form):
                fail(page, "control %s has no label" % m.group(1))
            if "data-label=" not in ctl:
                fail(page, "control %s has no data-label" % m.group(1))
    if "<form" in markup and "/assets/js/site.js" not in h:
        fail(page, "form page without site.js")
    if re.search(r"\b(alert|confirm|prompt)\s*\(", h):
        fail(page, "uses alert/confirm/prompt")
    return is_redirect


def main():
    if not PUBLIC.exists():
        sys.exit("run build.py first")
    pages = sorted(PUBLIC.rglob("*.html"))
    redirects = sum(1 for f in pages if check_page(f))

    for u in OLD_URLS:
        if resolve(u) is None:
            fail("old URL", "%s no longer resolves" % u)
    sm = (PUBLIC / "sitemap.xml").read_text(encoding="utf-8")
    locs = re.findall(r"<loc>([^<]+)</loc>", sm)
    for loc in locs:
        f = resolve(urlparse(loc).path or "/")
        if f is None:
            fail("sitemap", "lists missing page %s" % loc)
        elif 'http-equiv="refresh"' in f.read_text(encoding="utf-8") or 'content="noindex' in f.read_text(encoding="utf-8"):
            fail("sitemap", "lists a redirect/noindex page %s" % loc)
    if "properties/" in sm:
        fail("sitemap", "lists /properties (excluded by Valentine)")
    for need in ("robots.txt", "sitemap.xml", "404.html", "favicon.ico", "apple-touch-icon.png", "manifest.json"):
        if not (PUBLIC / need).exists():
            fail("public", "missing %s" % need)
    js = (PUBLIC / "assets/js/site.js").read_text(encoding="utf-8")
    if js.count("FORM_ENDPOINT =") != 1:
        fail("site.js", "FORM_ENDPOINT must be defined exactly once")
    for f in PUBLIC.rglob("*"):
        if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp") and f.stat().st_size > 400 * 1024:
            fail("assets", "image over 400 KB: %s (%d KB)" % (f.relative_to(PUBLIC), f.stat().st_size // 1024))

    if problems:
        print("%d problem(s):" % len(problems))
        for p in problems:
            print("  FAIL " + p)
        sys.exit(1)
    print("CLEAN - %d html files (%d redirects), %d old URLs resolve, %d sitemap URLs" % (
        len(pages), redirects, len(OLD_URLS), len(locs)))


if __name__ == "__main__":
    main()
