"""
Build the GVN Estate Invest website.

    python build.py      writes public/   (the only folder that gets served)
    python check.py      checks every page, link, image, id and meta tag

Where to edit:
    src/pages/*.html     one file per page. The JSON block at the top of each
                         file is the page's address, title and description.
    src/posts/*.html     one file per Provenance Pulse article, same idea.
    forms.py             every form: questions, answer options, messages.
    assets/              stylesheet, script, fonts, images, the investor guide.

Never edit anything in public/ - it is deleted and rebuilt on every run.

Preview on your own computer:
    python build.py
    python -m http.server 8000 --directory public
    then open http://localhost:8000
"""

import datetime
import html
import json
import pathlib
import re
import shutil
import sys

from forms import FORMS, render_form, write_forms_md

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
PUBLIC = ROOT / "public"
SITE = "https://www.gvnestateinvest.com"

# ---------------------------------------------------------------- business facts
# Every fact here is from the old Wix site or KNOWLEDGE BASE 001. Do not add
# figures, client counts or results here that are not true and checkable.
BIZ = {
    "name": "GVN Estate Invest",
    "legal": "GVN Reality Trading Ltd",
    "company_no": "16127907",
    "ico": "ZB923509",
    "ico_url": "https://ico.org.uk/ESDWebPages/Entry/ZB923509",
    "email": "info@gvnestateinvest.com",          # general enquiries
    "email_invest": "invest@gvnestateinvest.com",  # investor leads (Valentine, 6 Oct 2026)
    "email_sales": "propertysales@gvnestateinvest.com",  # vendor leads
    "phone_display": "01782 938 111",
    "phone_intl": "+44 1782 938 111",
    "phone_href": "tel:+441782938111",
    "whatsapp": "https://wa.me/447304082886",
    "street": "203 West Street",
    "town": "Fareham",
    "postcode": "PO16 0EN",
    "hours": "Monday–Friday: 9 AM – 6 PM | Saturday: By Appointment",
    "slogan": "We Spot. You Earn. Effortlessly.",
    "motto": "Built on dedication, driven by passion, upheld by integrity.",
    "console": "https://console.gvnestateinvest.com/",
    "founder_site": "https://www.valentinegrey.me",
}
# The credibility ribbon. Each badge states something true and checkable, and
# links to the proof. TRUST_SWITCHES turns one on only when it is true:
# showing a scheme you have not joined is a false claim of membership (a
# banned practice under UK consumer law, and against the scheme's own logo
# rules), so the Ombudsman badge is built but OFF until Valentine registers.
TRUST_SWITCHES = {
    "ombudsman": False,          # set True once registered with The Property Ombudsman
    "ombudsman_no": "",          # and put the TPO membership number here
}
TRUSTPILOT_URL = "https://uk.trustpilot.com/review/gvnestateinvest.com"
# Valentine's Google Calendar appointment schedule "Free 30-minute strategy call"
# (8 Oct 2026). A booking lands straight in his Google Calendar. BOOKING_EMBED is
# the same page in Google's embeddable form (?gv=true), used in an iframe.
BOOKING_URL = "https://calendar.app.google/pUW1sVTso3YxPrqR7"
BOOKING_EMBED = ("https://calendar.google.com/calendar/appointments/schedules/"
                 "AcZssZ2uLd6wrPzjgRlbLRMmuPL1M_W7_BtcZCK1cjyiJn0xONS2a0OSe5s-KtROvTZDF3m_Nr-1mUIM?gv=true")


def trust_ribbon():
    items = [
        ("shield-check", "ICO registered", "Data protection, ref. %s" % BIZ["ico"], BIZ["ico_url"]),
        ("buildings", "Registered company", "England &amp; Wales, no. %s" % BIZ["company_no"],
         "https://find-and-update.company-information.service.gov.uk/company/%s" % BIZ["company_no"]),
    ]
    if TRUST_SWITCHES["ombudsman"]:
        items.append(("scales", "The Property Ombudsman",
                      "Member" + (", no. " + esc(TRUST_SWITCHES["ombudsman_no"]) if TRUST_SWITCHES["ombudsman_no"] else ""),
                      "https://www.tpos.co.uk/"))
    items.append(("star", "Trustpilot", "Read or leave a review", TRUSTPILOT_URL))
    cells = "".join(
        '<li><a href="%s" rel="noopener" target="_blank">%s<span><b>%s</b><small>%s</small></span>'
        '<span class="sr-only"> (opens in a new tab)</span></a></li>' % (url, icon(ic), title, sub)
        for ic, title, sub, url in items)
    return ('<section class="trust" aria-labelledby="trust-h"><div class="wrap">'
            '<h2 id="trust-h" class="trust-h">Credibility</h2><ul class="trust-list">%s</ul></div></section>' % cells)


SOCIAL = [
    ("Instagram", "https://www.instagram.com/gvn_estate_invest"),
    ("Facebook", "https://www.facebook.com/profile.php?id=61567800793761"),
    ("LinkedIn", "https://www.linkedin.com/company/gvn-estate-invest"),
    ("X", "https://x.com/GVNESTATEINVEST"),
    ("Threads", "https://www.threads.com/@gvn_estate_invest"),
    ("WhatsApp", "https://wa.me/447304082886"),
]
AREAS = [
    ("Stoke-on-Trent", "ST"), ("Crewe", "CW"), ("Newcastle-under-Lyme", "ST"),
    ("Stafford", "ST"), ("Burton upon Trent", "DE"), ("Rugeley", "WS"),
    ("Cannock", "WS"), ("Wolverhampton", "WV"), ("Walsall", "WS"),
    ("Lichfield", "WS"), ("Sutton Coldfield", "B"), ("Tamworth", "B"),
    ("Uttoxeter", "ST"),
]

NAV = [
    ("services", "/services", "Services"),
    ("about", "/about-us", "About"),
    ("sell", "/sellmyhome", "Sell"),
    ("pulse", "/provenance-pulse", "P-Pulse"),
    ("faq", "/#faq", "FAQ"),
    ("contact", "/contact", "Contact"),
]

# Old addresses that no longer have their own page. Each becomes a tiny page
# that forwards the visitor (and tells Google where the page went).
REDIRECTS = {
    "/home": "/",
    "/properties/semi-detached-house-fenton-": "/sellmyhome",  # excluded by Valentine
    "/properties-list": "/sellmyhome",
    "/offmarketdeals": "/sellmyhome",  # page removed by Valentine, 5 Oct 2026
    "/start": "/investnow",
    "/popup-suauy": "/book-a-strategy-call",
    "/popup-cf17t": "/sellmyhome",
    "/popup-d1pyg": "/provenance-pulse",
    "/popup-syzwe": "/",
    "/book-online": "/book-a-strategy-call",
    "/booking-calendar": "/book-a-strategy-call",
    "/booking-form": "/book-a-strategy-call",
    "/service-page": "/book-a-strategy-call",
    "/search": "/provenance-pulse",
    "/cart-page": "/",
    "/checkout": "/",
    "/fullscreen-page": "/",
    "/blank-ncx68": "/",
    "/error404": "/",
    "/post": "/provenance-pulse",
}

DOC_HEAD = """<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0a111d">
"""


def esc(s):
    return html.escape(str(s), quote=True)


SOCIAL_ICONS = {"Instagram": "instagram-logo", "Facebook": "facebook-logo", "LinkedIn": "linkedin-logo",
                "X": "x-logo", "Threads": "threads-logo", "WhatsApp": "whatsapp-logo"}


def icon(name, cls="ic"):
    """An icon from the Phosphor sprite (assets/img/icons.svg). Always
    decorative: the text beside it carries the meaning."""
    return ('<svg class="%s" aria-hidden="true" focusable="false"><use href="/assets/img/icons.svg#i-%s"></use></svg>'
            % (cls, name))


def social_list(cls="social"):
    items = "".join('<li><a href="%s" rel="noopener" target="_blank">%s%s<span class="sr-only"> (opens in a new tab)</span></a></li>'
                    % (esc(u), icon(SOCIAL_ICONS[n]), esc(n)) for n, u in SOCIAL)
    return '<ul class="%s">%s</ul>' % (cls, items)


def header(active):
    links = []
    for key, href, label in NAV:
        cur = ' aria-current="page"' if key == active else ""
        links.append('<a href="%s"%s>%s</a>' % (href, cur, label))
    return """<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/" aria-label="GVN Estate Invest home"><img src="/assets/img/logo-gold.webp" alt="GVN Estate Invest" width="560" height="119"></a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">%s%s<span>Menu</span></button>
    <nav id="site-nav" class="nav" aria-label="Main">
      %s
      <a class="btn btn--gold" href="/book-a-strategy-call">Book a strategy call</a>
    </nav>
  </div>
</header>""" % (icon("list", "ic i-open"), icon("x", "ic i-close"), "\n      ".join(links))


def footer():
    b = BIZ
    year = datetime.date.today().year
    return """<footer class="site-footer">
  <div class="wrap">
    <div class="footer-cta">
      <p>We Spot. You Earn. <span>Effortlessly.</span></p>
      <a class="btn btn--gold" href="/book-a-strategy-call">Book a strategy call%(arrow)s</a>
    </div>
    <div class="footer-grid">
      <div class="footer-brand">
        <img src="/assets/img/logo-gold.webp" alt="GVN Estate Invest" width="560" height="119" loading="lazy">
        <p class="footer-motto">%(motto)s</p>
      </div>
      <div>
        <h2>Contact</h2>
        <ul class="footer-contact">
          <li>%(i_pin)s<address>Postal address:<br>%(street)s, %(town)s,<br>%(postcode)s</address></li>
          <li>%(i_mail)s<a href="mailto:%(email)s?subject=PROPERTY%%20INVESTMENT%%20Query">%(email)s</a></li>
          <li>%(i_phone)s<a href="%(phone_href)s">Tel: %(phone_display)s</a></li>
          <li>%(i_wa)s<a href="%(whatsapp)s" rel="noopener" target="_blank">WhatsApp<span class="sr-only"> (opens in a new tab)</span></a></li>
          <li>%(i_chat)s<a href="/askaquestion">Ask a question</a></li>
        </ul>
      </div>
      <div>
        <h2>Menu</h2>
        <ul>
          <li><a href="/">Home</a></li>
          <li><a href="/services">Services</a></li>
          <li><a href="/about-us">About</a></li>
          <li><a href="/investnow">Investor guide</a></li>
          <li><a href="/sellmyhome">Sell my home</a></li>
          <li><a href="/provenance-pulse">P-Pulse</a></li>
          <li><a href="/#faq">FAQ</a></li>
          <li><a href="/contact">Contact</a></li>
        </ul>
      </div>
      <div>
        <h2>Security</h2>
        <ul>
          <li><a href="/privacyandcookiepolicy">Privacy and Cookie Policy</a></li>
          <li><a href="/mediadisclaimerandattributions">Media Attribution</a></li>
          <li><a href="%(ico_url)s" rel="noopener" target="_blank">ICO &ndash; Data Protection Reg.<span class="sr-only"> (opens in a new tab)</span></a></li>
          <li>Anti-Money Laundering</li>
          <li><a href="%(console)s" rel="noopener" target="_blank">C.P.V.C<span class="sr-only"> investor console (opens in a new tab)</span></a></li>
        </ul>
        <h2 style="margin-top:28px">Follow us on</h2>
        %(social)s
      </div>
    </div>
    <div class="footer-legal">
      <div class="trading">
        <img src="/assets/img/gvn-reality-trading-logo.webp" alt="GVN Reality Trading" width="300" height="194" loading="lazy">
        <p style="margin:0">All trades are carried out by<br><strong>%(legal_upper)s</strong></p>
      </div>
      <p style="margin:0">&copy; %(year)s %(legal)s &middot; Company No. %(company_no)s &middot; ICO registration %(ico)s</p>
    </div>
  </div>
</footer>
<script src="/assets/js/site.js" defer></script>""" % dict(b, social=social_list(), year=year, legal_upper=b["legal"].upper(),
                                                          arrow=icon("arrow-right"), i_pin=icon("map-pin"),
                                                          i_mail=icon("envelope-simple"), i_phone=icon("phone"),
                                                          i_wa=icon("whatsapp-logo"), i_chat=icon("chat-circle-text"))


def org_jsonld():
    b = BIZ
    data = {
        "@context": "https://schema.org",
        "@type": ["Organization", "LocalBusiness"],
        "@id": SITE + "/#organization",
        "name": b["name"],
        "legalName": b["legal"],
        "url": SITE + "/",
        "logo": SITE + "/assets/img/logo-golden.png",
        "image": SITE + "/assets/img/og-card.jpg",
        "email": b["email"],
        "telephone": b["phone_intl"],
        "slogan": b["slogan"],
        "address": {"@type": "PostalAddress", "streetAddress": b["street"], "addressLocality": b["town"],
                    "postalCode": b["postcode"], "addressCountry": "GB"},
        "areaServed": [a for a, _ in AREAS],
        "founder": {"@type": "Person", "name": "Valentine Grey", "url": b["founder_site"]},
        "identifier": {"@type": "PropertyValue", "propertyID": "Companies House company number", "value": b["company_no"]},
        "sameAs": [u for n, u in SOCIAL if n != "WhatsApp"] + [TRUSTPILOT_URL],
        "contactPoint": [
            {"@type": "ContactPoint", "contactType": "customer service", "email": b["email"], "telephone": b["phone_intl"], "areaServed": "GB", "availableLanguage": "en-GB"},
            {"@type": "ContactPoint", "contactType": "investor enquiries", "email": b["email_invest"], "areaServed": "GB", "availableLanguage": "en-GB"},
            {"@type": "ContactPoint", "contactType": "property sales", "email": b["email_sales"], "areaServed": "GB", "availableLanguage": "en-GB"},
        ],
        # Call hours as on the contact page; Saturday is by appointment only.
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "opens": "09:00", "closes": "18:00"}],
    }
    return '<script type="application/ld+json">%s</script>' % json.dumps(data, ensure_ascii=False)


# The services, in schema.org terms, for /services. Wording from the site's own
# package descriptions. Only the Achiever price is published (home FAQ, his
# words 8 Oct 2026: GBP 7,500 per investment property); Elite and Bold have none.
SERVICE_PRICES = {"Achiever Investor Package": "7500"}
SERVICES_LD = [
    ("Elite Investor Package", "/elite-investor-blueprint-handsfree-service",
     "Hands-free property investment for first-time investors: company (SPV) set-up, banking, HMRC and compliance, then sourcing, refurbishment, lettings, income and optional refinance."),
    ("Achiever Investor Package", "/achiever-investor-blueprint-handsfree-service",
     "Hands-free property investment: sourcing, refurbishment to legal standards, vetted lettings, income and optional refinance."),
    ("Bold Investor Package", "/bold-investor-blueprint-handsfree-service",
     "Property sourcing and vetted lettings management."),
    ("Sell your house fast", "/sellmyhome",
     "A cash offer for your Staffordshire house, or a matched buyer, completing on your timeline."),
]


def faq_ld(body):
    """FAQPage built from the page's own <details class="faq"> items, so the
    schema can never say something the visible FAQ does not."""
    items = []
    for q, a in re.findall(r'<details class="faq"><summary>(.*?)</summary><div class="answer">(.*?)</div></details>', body, re.S):
        text = lambda h: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()
        items.append({"@type": "Question", "name": text(q),
                      "acceptedAnswer": {"@type": "Answer", "text": text(a)}})
    if not items:
        return ""
    return '<script type="application/ld+json">%s</script>' % json.dumps(
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": items}, ensure_ascii=False)


def page_ld(meta):
    """Structured data that depends on the page: the WebSite on the home page
    (so Google can show the site's name), breadcrumbs elsewhere, and the
    services on /services."""
    path = meta["path"]
    org = {"@id": SITE + "/#organization"}
    out = []
    if path == "/":
        out.append({"@context": "https://schema.org", "@type": "WebSite", "@id": SITE + "/#website",
                    "name": BIZ["name"], "alternateName": "GVN", "url": SITE + "/", "publisher": org,
                    "inLanguage": "en-GB"})
    elif not meta.get("noindex"):
        crumbs = [("Home", SITE + "/")]
        if path.startswith("/post/") or path.startswith("/provenance-pulse/"):
            crumbs.append(("The Provenance Pulse", SITE + "/provenance-pulse"))
        name = meta.get("crumb") or meta["title"].split(" | ")[0]
        if path != "/provenance-pulse":
            crumbs.append((name, SITE + path))
        out.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(crumbs)]})
    if path == "/services":
        out.append({"@context": "https://schema.org", "@type": "OfferCatalog", "name": "GVN Estate Invest services",
                    "itemListElement": [dict({"@type": "Offer", "itemOffered": {
                        "@type": "Service", "name": n, "description": d, "url": SITE + u,
                        "provider": org, "areaServed": "Staffordshire, England"}},
                        **({"priceSpecification": {"@type": "UnitPriceSpecification",
                            "price": SERVICE_PRICES[n], "priceCurrency": "GBP",
                            "unitText": "per investment property"}} if n in SERVICE_PRICES else {}))
                        for n, u, d in SERVICES_LD]})
    return "".join('<script type="application/ld+json">%s</script>' % json.dumps(o, ensure_ascii=False) for o in out)


def page_html(meta, body):
    """Wrap a body fragment in the full document."""
    path = meta["path"]
    canonical = SITE + ("" if path == "/" else path)
    if path == "/":
        canonical = SITE + "/"
    title = meta["title"]
    desc = meta["description"]
    og_image = SITE + meta.get("og_image", "/assets/img/og-card.jpg")
    robots = '<meta name="robots" content="noindex, follow">\n' if meta.get("noindex") else ""
    extra_ld = meta.get("jsonld_extra", "") + page_ld(meta) + faq_ld(body)
    head = """<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<link rel="canonical" href="%(canonical)s">
%(robots)s<meta property="og:type" content="%(ogtype)s">
<meta property="og:site_name" content="GVN Estate Invest">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(canonical)s">
<meta property="og:image" content="%(og_image)s">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.json">
<link rel="preload" href="/assets/fonts/bodoni-moda.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/hanken-grotesk.woff2" as="font" type="font/woff2" crossorigin>
%(preload_img)s
<link rel="stylesheet" href="/assets/css/site.css">
%(orgld)s
%(extra_ld)s""" % dict(title=esc(title), desc=esc(desc), canonical=canonical, robots=robots,
                       ogtype=meta.get("og_type", "website"), og_image=og_image, orgld=org_jsonld(),
                       extra_ld=extra_ld, preload_img=meta.get("preload_img", ""))
    return "%s%s\n</head>\n<body>\n%s\n<main id=\"main\">\n%s\n</main>\n%s\n</body>\n</html>\n" % (
        DOC_HEAD, head, header(meta.get("nav", "")), body.strip(), footer())


# ---------------------------------------------------------------- tokens
def expand_tokens(body, meta):
    def form_token(m):
        key = m.group(1)
        if key not in FORMS:
            sys.exit("unknown form %s in %s" % (key, meta["path"]))
        return render_form(key)
    body = re.sub(r"\{\{FORM:([a-z0-9_]+)\}\}", form_token, body)
    body = re.sub(r"\{\{I:([a-z-]+)\}\}", lambda m: icon(m.group(1)), body)
    reps = {
        "{{SOCIAL}}": social_list("social social--light"),
        "{{EMAIL}}": BIZ["email"],
        "{{EMAIL_INVEST}}": BIZ["email_invest"],
        "{{EMAIL_SALES}}": BIZ["email_sales"],
        "{{PHONE}}": BIZ["phone_display"],
        "{{PHONE_INTL}}": BIZ["phone_intl"],
        "{{PHONE_HREF}}": BIZ["phone_href"],
        "{{WHATSAPP}}": BIZ["whatsapp"],
        "{{HOURS}}": BIZ["hours"],
        "{{MOTTO}}": BIZ["motto"],
        "{{SLOGAN}}": BIZ["slogan"],
        "{{ADDRESS}}": "%s, %s, %s" % (BIZ["street"], BIZ["town"], BIZ["postcode"]),
        "{{COMPANY_NO}}": BIZ["company_no"],
        "{{GUIDE_PDF}}": "/assets/files/staffordshire-investor-guide.pdf",
        "{{BOOKING_URL}}": BOOKING_URL,
        "{{BOOKING_EMBED}}": BOOKING_EMBED,
        "{{AREAS}}": '<ul class="chips">%s</ul>' % "".join(
            "<li>%s<span>%s</span></li>" % (esc(a), esc(c)) for a, c in AREAS),
        "{{LATEST_POSTS}}": latest_posts_html(3),
        "{{TRUST}}": trust_ribbon(),
    }
    for k, v in reps.items():
        body = body.replace(k, v)
    left = re.findall(r"\{\{[A-Z_:a-z0-9]+\}\}", body)
    if left:
        sys.exit("unknown tokens in %s: %s" % (meta["path"], left))
    return body


def read_source(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"\s*<!--\s*(\{.*?\})\s*-->\s*", text, re.S)
    if not m:
        sys.exit("%s: missing JSON header" % path.name)
    return json.loads(m.group(1)), text[m.end():]


def out_file(path):
    if path == "/":
        return PUBLIC / "index.html"
    return PUBLIC / path.strip("/") / "index.html"


def write(path, text):
    f = out_file(path)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------- blog
POSTS = []
CATEGORIES = [
    ("property-news", "Property News"),
    ("hands-free-property-investment", "Hands-Free Property Investment"),
    ("hmrc", "HMRC"),
    ("accounts", "Accounts"),
    ("companies-house", "Companies House"),
    ("renters-rights-bill", "Renters’ Rights Bill"),
]
CAT_NAMES = dict(CATEGORIES)


def load_posts():
    for f in sorted((SRC / "posts").glob("*.html")):
        meta, body = read_source(f)
        meta["body"] = body
        meta["dt"] = datetime.datetime.fromisoformat(meta["date"].replace("Z", "+00:00"))
        POSTS.append(meta)
    POSTS.sort(key=lambda p: p["dt"], reverse=True)


def nice_date(dt):
    return "%d %s %d" % (dt.day, dt.strftime("%B"), dt.year)


def post_card(p, heading="h2"):
    cats = ", ".join(CAT_NAMES.get(c, n) for c, n in p["categories"])
    return """<article class="post-card">
  <a href="/post/%(slug)s" tabindex="-1" aria-hidden="true"><img src="%(cover)s" alt="" width="%(w)s" height="%(h)s" loading="lazy" decoding="async"></a>
  <div class="body">
    <p class="meta"><time datetime="%(iso)s">%(date)s</time><span>%(rt)s</span></p>
    <%(hx)s><a href="/post/%(slug)s">%(title)s</a></%(hx)s>
    <p>%(desc)s</p>
    %(cats)s
  </div>
</article>""" % dict(slug=p["slug"], cover=p["cover"], w=p["cover_w"], h=p["cover_h"], iso=p["dt"].date().isoformat(),
                     date=nice_date(p["dt"]), rt=esc(p["readtime"]), title=esc(p["title"]), hx=heading,
                     desc=esc(short(p["description"], 190)),
                     cats=('<p class="meta" style="margin-top:auto">%s</p>' % esc(cats)) if cats else "")


def short(s, n):
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= n:
        return s
    return s[:n].rsplit(" ", 1)[0].rstrip(",;:—-") + "…"


def latest_posts_html(n):
    if not POSTS:
        return ""
    return '<div class="post-grid">%s</div>' % "".join(post_card(p, "h3") for p in POSTS[:n])


def cat_nav(active):
    items = ['<li><a href="/provenance-pulse"%s>All articles</a></li>' % (' aria-current="page"' if active is None else "")]
    for slug, name in CATEGORIES:
        cur = ' aria-current="page"' if slug == active else ""
        items.append('<li><a href="/provenance-pulse/categories/%s"%s>%s</a></li>' % (slug, cur, esc(name)))
    return '<nav aria-label="Article categories"><ul class="cat-nav">%s</ul></nav>' % "".join(items)


def build_blog():
    intro = "Stay Up to Date with Market intelligence, Property News, Tax Strategies and Hands-Free wealth building"
    hero = """<section class="hero hero--page"><div class="wrap">
  <p class="eyebrow">The Provenance Pulse (P-Pulse)</p>
  <h1>%s</h1>
  <p class="lede">%s</p>
</div></section>"""
    body = hero % ("The Provenance Pulse", intro) + """
<section class="section"><div class="wrap">%s<div class="post-grid">%s</div></div></section>""" % (
        cat_nav(None), "".join(post_card(p) for p in POSTS))
    write("/provenance-pulse", page_html({
        "path": "/provenance-pulse", "nav": "pulse",
        "title": "The Provenance Pulse | Property News & Insight | GVN Estate Invest",
        "description": intro + "."}, body))

    for slug, name in CATEGORIES:
        posts = [p for p in POSTS if slug in [c for c, _ in p["categories"]]]
        body = hero % (esc(name), "Articles from The Provenance Pulse filed under %s." % esc(name)) + """
<section class="section"><div class="wrap">%s<div class="post-grid">%s</div></div></section>""" % (
            cat_nav(slug), "".join(post_card(p) for p in posts))
        path = "/provenance-pulse/categories/" + slug
        write(path, page_html({"path": path, "nav": "pulse",
                               "title": "%s | The Provenance Pulse | GVN Estate Invest" % name,
                               "description": short("%s articles from The Provenance Pulse, the GVN Estate Invest blog: %s." % (name, intro.lower()), 158)}, body))

    for i, p in enumerate(POSTS):
        cats = " &middot; ".join('<a href="/provenance-pulse/categories/%s">%s</a>' % (c, esc(CAT_NAMES.get(c, n)))
                                 for c, n in p["categories"])
        tags = ('<p class="meta" style="margin-top:28px">Tags</p><ul class="tags">%s</ul>' %
                "".join("<li>%s</li>" % esc(t) for t in p["tags"])) if p["tags"] else ""
        others = [q for q in POSTS if q is not p][:3]
        ld = {
            "@context": "https://schema.org", "@type": "BlogPosting",
            "headline": p["title"], "description": p["description"],
            "datePublished": p["date"], "dateModified": p.get("modified") or p["date"],
            "image": SITE + p["cover"], "mainEntityOfPage": SITE + "/post/" + p["slug"],
            "author": {"@type": "Organization" if p["author"] == "GVN Estate Invest" else "Person", "name": p["author"]},
            "publisher": {"@id": SITE + "/#organization"},
        }
        body = """<article>
<header class="hero hero--page"><div class="wrap post-head">
  <p class="eyebrow post-cats">%(cats)s</p>
  <h1>%(title)s</h1>
  <p class="meta"><span>By %(author)s</span><time datetime="%(iso)s">%(date)s</time><span>%(rt)s</span></p>
</div></header>
<div class="section section--ivory"><div class="wrap"><div class="prose" style="margin:0 auto">
%(body)s
%(tags)s
</div></div></div>
</article>
<section class="section section--tight"><div class="wrap">
  <div class="cta-band cta-band--photo" style="--cta-img:url('/assets/img/street-chimneys.webp')">
    <div><h2>Want this <em>handled</em> for you?</h2><p>Hands-free property investment in Staffordshire, from sourcing to lettings.</p></div>
    <div class="btn-row"><a class="btn btn--gold" href="/book-a-strategy-call">Book a strategy call%(arrow)s</a><a class="btn btn--ghost" href="/askaquestion">Ask a question</a></div>
  </div>
</div></section>
<section class="section section--deep"><div class="wrap">
  <div class="head-row"><h2>Recent posts</h2><a class="text-link" href="/provenance-pulse">See all articles%(arrow)s</a></div>
  <div class="post-grid">%(others)s</div>
</div></section>""" % dict(arrow=icon("arrow-right"),cats=cats or "The Provenance Pulse", title=esc(p["title"]), author=esc(p["author"]),
                           iso=p["dt"].date().isoformat(), date=nice_date(p["dt"]), rt=esc(p["readtime"]),
                           cover=p["cover"], w=p["cover_w"], h=p["cover_h"], body=tidy_post(p["body"]),
                           tags=tags, others="".join(post_card(q, "h3") for q in others))
        path = "/post/" + p["slug"]
        write(path, page_html({
            "path": path, "nav": "pulse", "og_type": "article", "og_image": p["cover"].replace(".webp", ".webp"),
            # Google shows about 60 characters; a long headline keeps its words, not the suffix.
            "title": p["title"] if len(p["title"]) > 42 else "%s | GVN Estate Invest" % p["title"],
            "description": short(p["description"], 158),
            "jsonld_extra": '<script type="application/ld+json">%s</script>' % json.dumps(ld, ensure_ascii=False),
        }, body))


def tidy_post(body):
    """Wrap tables so they scroll sideways on a phone instead of the page.
    Wix wrote post subheadings as h3 (and h4) under the page h1; with no h2
    in the body they move up one level so the outline has no gap."""
    if "<h2" not in body:
        shift = {"3": "2", "4": "3", "5": "4", "6": "5"}
        body = re.sub(r"<(/?)h([3-6])(?=[ >])", lambda m: "<" + m.group(1) + "h" + shift[m.group(2)], body)
    return re.sub(r"(<table>.*?</table>)", lambda m: '<div class="table-wrap">' + m.group(1) + "</div>", body, flags=re.S)


# ---------------------------------------------------------------- misc output
def redirect_page(src, dst):
    url = SITE + ("/" if dst == "/" else dst)
    return """<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>This page has moved | GVN Estate Invest</title>
<meta name="description" content="This page has moved to %(url)s">
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="%(url)s">
<meta http-equiv="refresh" content="0; url=%(dst)s">
<style>body{font-family:system-ui,sans-serif;background:#f8f5ef;color:#23262b;margin:0;padding:48px 20px;text-align:center}a{color:#7a5620}</style>
</head>
<body>
<p>This page has moved. <a href="%(dst)s">Continue to the new page</a>.</p>
</body>
</html>
""" % dict(url=url, dst=dst)


def build_sitemap(entries):
    today = datetime.date.today().isoformat()
    rows = []
    for path, lastmod in entries:
        loc = SITE + ("/" if path == "/" else path)
        rows.append("  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n  </url>" % (loc, lastmod or today))
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % "\n".join(rows)


MANIFEST = {
    "name": "GVN Estate Invest", "short_name": "GVN", "start_url": "/", "display": "standalone",
    "background_color": "#0a111d", "theme_color": "#0a111d",
    "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
              {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}],
}


def main():
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir()
    shutil.copytree(ROOT / "assets", PUBLIC / "assets", ignore=shutil.ignore_patterns("icons"))
    for icon in (ROOT / "assets" / "icons").iterdir():
        shutil.copy2(icon, PUBLIC / icon.name)

    load_posts()
    sitemap = []
    for f in sorted((SRC / "pages").glob("*.html")):
        meta, body = read_source(f)
        body = expand_tokens(body, meta)
        text = page_html(meta, body)
        if meta["path"] == "/404.html":
            (PUBLIC / "404.html").write_text(text, encoding="utf-8")
            continue
        write(meta["path"], text)
        if not meta.get("noindex") and meta.get("sitemap", True):
            sitemap.append((meta["path"], None))

    build_blog()
    sitemap.append(("/provenance-pulse", POSTS[0]["dt"].date().isoformat()))
    for slug, _ in CATEGORIES:
        sitemap.append(("/provenance-pulse/categories/" + slug, None))
    for p in POSTS:
        sitemap.append(("/post/" + p["slug"], (p.get("modified") or p["date"])[:10]))

    # Old tag pages: forward to the blog. Generated from the tags on the posts.
    tag_redirects = {}
    for p in POSTS:
        for t in p["tags"]:
            slug = re.sub(r"[^a-z0-9]+", "-", t.lower().replace("'", "")).strip("-")
            tag_redirects["/provenance-pulse/tags/" + slug] = "/provenance-pulse"
    for src, dst in list(REDIRECTS.items()) + list(tag_redirects.items()):
        if out_file(src).exists():
            sys.exit("redirect %s would overwrite a real page" % src)
        out_file(src).parent.mkdir(parents=True, exist_ok=True)
        out_file(src).write_text(redirect_page(src, dst), encoding="utf-8")

    (PUBLIC / "sitemap.xml").write_text(build_sitemap(sitemap), encoding="utf-8")
    (PUBLIC / "robots.txt").write_text("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE, encoding="utf-8")
    (PUBLIC / "manifest.json").write_text(json.dumps(MANIFEST, indent=2), encoding="utf-8")
    write_forms_md(ROOT / "forms.md")

    pages = list(PUBLIC.rglob("*.html"))
    total = sum(f.stat().st_size for f in PUBLIC.rglob("*") if f.is_file())
    print("built %d html files (%d posts, %d redirects, %d tag redirects), %d sitemap urls, public/ = %.1f MB"
          % (len(pages), len(POSTS), len(REDIRECTS), len(tag_redirects), len(sitemap), total / 1048576))


if __name__ == "__main__":
    main()
