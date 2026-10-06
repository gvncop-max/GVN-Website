"""
Every form on the site, in one place.

`label` is the exact question wording from the old Wix form. It is what gets
sent to the CRM as the field name, so do not tidy it: the CRM recognises
answers by matching phrases ("Right now", "month or two", "Busy professional",
condition words and so on). `show` is only the text the visitor reads, used
where the Wix wording had odd capitals. Answer options are sent exactly as
written here.

build.py renders these into the pages ({{FORM:key}}) and writes forms.md.
"""

import html

ENDPOINT_NOTE = 'https://bkgjoztepcdranhbaurx.supabase.co/functions/v1/site-form (constant FORM_ENDPOINT in assets/js/site.js)'

CONSENT = "By clicking you consent to being contacted via Email & SMS"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday (by appointment)"]
TIMES = ["Morning (9 AM – 12 PM)", "Afternoon (12 PM – 3 PM)", "Late afternoon (3 PM – 6 PM)", "Any time"]

AVAILABILITY = {
    "legend": "When are You Available to Discuss",
    "note": "A free 30-minute strategy call by phone. Our call hours are Monday–Friday, 9 AM – 6 PM, and Saturday by appointment. Tell us what suits you and we will confirm a time.",
    "fields": [
        {"label": "Preferred days", "type": "checkboxes", "options": DAYS, "required": False, "new": True},
        {"label": "Preferred time of day", "type": "select", "options": TIMES, "required": True, "placeholder": "Choose a time of day", "new": True},
        {"label": "Preferred date", "type": "date", "required": False, "new": True,
         "hint": "Optional. Leave blank if any day that week works."},
    ],
}

FORMS = {
    "booking": {
        "email": "invest@gvnestateinvest.com",
        "title": "Book a strategy call",
        "page": "/book-a-strategy-call",
        "origin": "Wix 'Strategy Call Form' (id b579bd21…), shown in the STRATEGY CALL REQUEST pop-up (popup-suauy) behind the "
                  "'Let's Discuss How This Works', 'Request Your Free Strategy Call' and 'Book Your Free Consultation' buttons; "
                  "also the booking form of the Wix Bookings service 'Strategy Session' (/book-online, /booking-calendar, /booking-form, /service-page).",
        "submit": "Request Strategy Session",
        "success": "Thank you. Your strategy call request has been received. We will contact you to confirm a time.",
        "redirect": "/optinform/gv2mkhfkhkkhdkhjcd10ku",
        # Valentine, 5 Oct 2026: long forms put people off, so the strategy
        # call forms go one short step at a time. Same questions, same labels.
        "steps": [("Your details", [0]), ("About you", [1]), ("When suits you", [2, 3])],
        "fieldsets": [
            {"legend": "Strategy Session: Please Provide The Following Details.", "fields": [
                {"label": "First name", "type": "text", "required": True, "auto": "given-name", "placeholder": "First name"},
                {"label": "Last name", "type": "text", "required": True, "auto": "family-name", "placeholder": "Last name"},
                {"label": "Phone", "type": "tel", "required": True, "auto": "tel", "placeholder": "Enter your phone number"},
                {"label": "Email", "type": "email", "required": True, "auto": "email", "placeholder": "Enter your email"},
            ]},
            {"legend": "Let's Get To Know You", "fields": [
                {"label": "what best describes you", "show": "What best describes you?", "type": "select", "required": True,
                 "placeholder": "What best describes you ?",
                 "options": ["Busy Professional", "First-Time Investor", "Retiree", "Seasoned Investor", "I Have Capital To Deploy Now"]},
                {"label": "What Type of Property investment Interest You ?", "show": "What type of property investment interests you?",
                 "type": "text", "required": False, "full": True, "placeholder": "What Type of Property investment Interest You ?"},
                {"label": "How Do You Plan To Finance Your Investment", "show": "How do you plan to finance your investment?",
                 "type": "text", "required": False, "full": True, "placeholder": "How Do You Plan To Finance Your Investment"},
                {"label": "How Soon Are You Looking To Buy", "show": "How soon are you looking to buy / invest?", "type": "select",
                 "required": True, "full": True, "placeholder": "How Soon Are You Looking To Buy / Invest",
                 "options": ["Right Now - Ready to Go!", "Soon, Within the next Month or Two", "In The Next Few Months", "Just Enquiring"]},
            ]},
            AVAILABILITY,
            {"legend": None, "fields": [
                {"label": CONSENT, "type": "checkbox", "required": False},
            ]},
        ],
    },

    "strategy_call_2": {
        "email": "invest@gvnestateinvest.com",
        "title": "Request a strategy call",
        "page": "/optinform",
        "origin": "Wix 'Strategy Call Form 2' (id c533cefe…) on /optinform; also the booking form of the Wix Bookings service 'STRATEGY CALL'.",
        "submit": "Request Strategy Session",
        "success": "Thank you. Your request has been received. We will contact you to confirm a time.",
        "redirect": "/optinform/gv2mkhfkhkkhdkhjcd10ku",
        "steps": [("Your details", [0]), ("About you", [1]), ("When suits you", [2, 3])],
        "fieldsets": [
            {"legend": "Please Provide The Following Details", "fields": [
                {"label": "First name", "type": "text", "required": True, "auto": "given-name", "placeholder": "First name"},
                {"label": "Last name", "type": "text", "required": True, "auto": "family-name", "placeholder": "Last name"},
                {"label": "Phone", "type": "tel", "required": True, "auto": "tel", "placeholder": "Enter your phone number"},
                {"label": "Email", "type": "email", "required": True, "auto": "email", "placeholder": "Enter your email"},
            ]},
            {"legend": "Let's Get To Know You", "note": "(Recommended but optional)", "fields": [
                {"label": "which best describes you ?", "show": "Which best describes you?", "type": "select", "required": False,
                 "placeholder": "Which Best Describes You ?",
                 "options": ["Busy Professional", "First-Time Investor", "Retiree", "Seasoned Investor", "I Have Capital To Deploy Now", "Other"]},
                {"label": "How soon are you looking to buy / invest", "show": "How soon are you looking to buy / invest?", "type": "select",
                 "required": False, "placeholder": "How Soon Are You Looking To Buy / Invest",
                 "options": ["Right Now - Ready to Go!", "Soon Within the next Month or Two", "In the next few Months", "Just Enquiring"]},
                {"label": "What Type Of Property Investment Interest You ?", "show": "What type of property investment interests you?",
                 "type": "text", "required": False, "full": True, "placeholder": "What Type Of Property Investment Interest You ?"},
                {"label": "How Do You Plan To Finance Your Investment", "show": "How do you plan to finance your investment?",
                 "type": "text", "required": False, "full": True, "placeholder": "How Do You Plan To Finance Your Investment"},
            ]},
            AVAILABILITY,
            {"legend": None, "fields": [
                {"label": CONSENT, "type": "checkbox", "required": True},
            ]},
        ],
    },

    "investor_guide": {
        "email": "invest@gvnestateinvest.com",
        "title": "Where should we send your FREE guide?",
        "page": "/investnow",
        "origin": "Wix 'INVESTOR GUIDE DOWNLOAD REQUEST' (id f744f57f…) on /investnow.",
        "submit": "Download Now",
        "success": "Thank you. Taking you to your guide now…",
        "redirect": "/investnow/gv1mkhfkhkkhdkhjcd10ku",
        "note": "\U0001F512 Your privacy matters. We never spam.",
        "fieldsets": [
            {"legend": None, "fields": [
                {"label": "First name", "type": "text", "required": True, "auto": "given-name", "placeholder": "First name"},
                {"label": "Last name", "type": "text", "required": False, "auto": "family-name", "placeholder": "Last name"},
                {"label": "Email", "type": "email", "required": True, "auto": "email", "placeholder": "Enter your email"},
                {"label": "Phone", "type": "tel", "required": True, "auto": "tel", "placeholder": "Enter your phone number"},
            ]},
        ],
    },

    "vendor_lead": {
        "email": "propertysales@gvnestateinvest.com",
        "title": "Your Property's Free Appraisal and Cash Offer",
        "intro": "Fill out this quick form. All information is confidential.",
        "page": "/sellmyhome",
        "origin": "Wix 'Sell my Home Form' (id fcd3d024…) on /sellmyhome. Success text from the Wix pop-up 'property sale thanks' (popup-cf17t).",
        "submit": "Submit",
        "success": "Thanks! We'll get in touch soon.",
        "redirect": None,
        "note": "\U0001F512 We never share your details. Privacy Guaranteed.",
        "fieldsets": [
            {"legend": None, "fields": [
                {"label": "Full name", "type": "text", "required": True, "auto": "name", "placeholder": "Enter your full name", "full": True},
                {"label": "Email", "type": "email", "required": True, "auto": "email", "placeholder": "Enter your Email"},
                {"label": "Phone", "type": "tel", "required": True, "auto": "tel", "placeholder": "Enter your phone number"},
                {"label": "Property Type", "type": "select", "required": True, "placeholder": "Choose one Property Type",
                 "options": ["Flat", "Mid Terraced", "End Terraced", "Semi Terraced", "Maisonette", "Detached"]},
                {"label": "No. of Bedrooms", "type": "select", "required": True, "placeholder": "No. of Bedrooms",
                 "options": ["1", "2", "3", "4", "5+"]},
                {"label": "Current Condition", "type": "select", "required": True, "placeholder": "Current Condition",
                 "options": ["Excellent (no work needed)", "Good (minor repairs)", "Needs Major Renovation"]},
                {"label": "Reason for Selling", "type": "select", "required": True, "placeholder": "Reason for Selling",
                 "options": ["Divorce", "Debt", "Scaling Back", "Relocation", "Up Size", "Probate", "Tenant Issues", "Other"],
                 "changed": "Wix option 'Depth' corrected to 'Debt' (obvious typo; the CRM does not classify this field)."},
            ]},
            {"legend": "Property address", "wix": "Multi-line address", "fields": [
                {"label": "Country/Region", "type": "text", "required": True, "auto": "country-name", "value": "United Kingdom"},
                {"label": "Address", "type": "text", "required": True, "auto": "street-address", "full": True},
                {"label": "City", "type": "text", "required": True, "auto": "address-level2"},
                {"label": "Zip / Postal code", "show": "Postcode", "type": "text", "required": True, "auto": "postal-code"},
            ]},
            {"legend": None, "fields": [
                {"label": "File upload", "show": "Upload Photos of Property", "type": "file", "required": False, "full": True,
                 "accept": "image/*", "max": 10, "hint": "Optional. Up to 10 photos."},
            ]},
        ],
    },

    "question": {
        "title": "Let’s Know What You Need Help With",
        "intro": "Get in touch so we can start working together.",
        "page": "/askaquestion",
        "origin": "Wix 'Complaint and Question' (id e211efab…) on /askaquestion.",
        "submit": "Submit",
        "success": "Thank you. Your message has been received and we will reply by email.",
        "redirect": None,
        "fieldsets": [
            {"legend": None, "fields": [
                {"label": "Full name", "type": "text", "required": False, "auto": "name", "placeholder": "Enter your full name"},
                {"label": "Email", "type": "email", "required": True, "auto": "email", "placeholder": "Enter your email"},
                {"label": "Question or Complaint", "type": "textarea", "required": True, "full": True, "placeholder": "Type Your Question or Complaint"},
            ]},
        ],
    },

    "contact": {
        "title": "Send us a message",
        "page": "/contact",
        "origin": "NEW. The old /contact page had no form (only phone, email and social links). Added because the CRM already has a "
                  "'site:contact' source. Labels chosen to match what the CRM's intake already looks for (name, email, phone, message).",
        "submit": "Send message",
        "success": "Thank you. Your message has been received and we will be in touch soon.",
        "redirect": None,
        "fieldsets": [
            {"legend": None, "fields": [
                {"label": "Full name", "type": "text", "required": True, "auto": "name", "placeholder": "Enter your full name"},
                {"label": "Email", "type": "email", "required": True, "auto": "email", "placeholder": "Enter your email"},
                {"label": "Phone", "type": "tel", "required": False, "auto": "tel", "placeholder": "Enter your phone number", "full": True},
                {"label": "Message", "type": "textarea", "required": True, "full": True, "placeholder": "How can we help?"},
            ]},
        ],
    },
}


def _e(s):
    return html.escape(str(s), quote=True)


def _field(key, n, f):
    fid = "%s-%d" % (key.replace("_", "-"), n)
    label = f["label"]
    show = f.get("show", label)
    req = f.get("required", False)
    mark = '<span class="req" aria-hidden="true">*</span>' if req else '<span class="opt">(optional)</span>'
    cls = "field full" if f.get("full") or f["type"] in ("checkbox", "checkboxes", "textarea", "file") else "field"
    common = 'id="%s" name="%s" data-label="%s"%s' % (fid, fid, _e(label), " required" if req else "")
    hint = ""
    if f.get("hint"):
        hint = '<p class="hint" id="%s-hint">%s</p>' % (fid, _e(f["hint"]))
        common += ' aria-describedby="%s-hint"' % fid
    t = f["type"]
    if t == "checkbox":
        return '<div class="%s"><label class="check"><input type="checkbox" %s value="Yes"> <span>%s%s</span></label></div>' % (
            cls, common, _e(show), ' <span class="req" aria-hidden="true">*</span>' if req else "")
    if t == "checkboxes":
        boxes = "".join('<label class="check"><input type="checkbox" id="%s-%d" name="%s" data-label="%s" data-group value="%s"> <span>%s</span></label>'
                        % (fid, i, fid, _e(label), _e(o), _e(o)) for i, o in enumerate(f["options"]))
        return '<fieldset class="%s" style="margin:0"><legend class="label" style="font-family:inherit;font-size:.97rem;font-weight:600">%s %s</legend><div class="check-grid">%s</div></fieldset>' % (
            cls, _e(show), mark, boxes)
    lab = '<label for="%s">%s %s</label>' % (fid, _e(show), mark)
    ph = ' placeholder="%s"' % _e(f["placeholder"]) if f.get("placeholder") and t not in ("select",) else ""
    auto = ' autocomplete="%s"' % f["auto"] if f.get("auto") else ""
    if t == "select":
        opts = '<option value="">%s</option>' % _e(f.get("placeholder") or "Please choose")
        opts += "".join('<option value="%s">%s</option>' % (_e(o), _e(o)) for o in f["options"])
        ctl = '<select %s>%s</select>' % (common, opts)
    elif t == "textarea":
        ctl = '<textarea %s%s rows="6"></textarea>' % (common, ph)
    elif t == "file":
        ctl = '<input type="file" class="file-input" %s accept="%s" multiple data-max="%d">' % (common, _e(f.get("accept", "")), f.get("max", 10))
    else:
        value = ' value="%s"' % _e(f["value"]) if f.get("value") else ""
        ctl = '<input type="%s" %s%s%s%s>' % (t, common, ph, auto, value)
    return '<div class="%s">%s%s%s</div>' % (cls, lab, ctl, hint)


def render_form(key):
    spec = FORMS[key]
    parts = []
    n = 0
    for fs in spec["fieldsets"]:
        inner = []
        for f in fs["fields"]:
            n += 1
            inner.append(_field(key, n, f))
        grid = '<div class="form-grid">%s</div>' % "".join(inner)
        if fs.get("legend"):
            note = '<p class="legend-note">%s</p>' % _e(fs["note"]) if fs.get("note") else ""
            parts.append('<fieldset><legend>%s</legend>%s%s</fieldset>' % (_e(fs["legend"]), note, grid))
        else:
            parts.append('<div style="margin-bottom:22px">%s</div>' % grid)
    # A stepped form wraps its fieldsets in steps. Without JavaScript every
    # step shows and the form works as one page; site.js shows one at a time.
    if spec.get("steps"):
        total = len(spec["steps"])
        parts = ['<div class="form-step" data-step="%d" data-step-title="%s">%s</div>' % (
                     i + 1, _e(title), "".join(parts[j] for j in idx))
                 for i, (title, idx) in enumerate(spec["steps"])]
        parts.insert(0, '<div class="form-progress" hidden><p class="form-progress-text" aria-live="polite">Step 1 of %d</p>'
                        '<div class="form-progress-bar"><span style="transform:scaleX(%.4f)"></span></div></div>' % (total, 1 / total))
    intro = '<p>%s</p>' % _e(spec["intro"]) if spec.get("intro") else ""
    note = '<p class="form-note">%s</p>' % _e(spec["note"]) if spec.get("note") else ""
    redirect = ' data-redirect="%s"' % spec["redirect"] if spec.get("redirect") else ""
    # The inbox this form belongs to: named under the form, and in the error
    # message if sending fails (investors: invest@, sellers: propertysales@).
    inbox = spec.get("email", "info@gvnestateinvest.com")
    error = ' data-error="Sorry, that didn&#39;t go through. Please try again, or email %s or call 01782 938 111."' % inbox
    return """<form class="form-card" data-form="%(key)s" data-success="%(success)s"%(redirect)s%(error)s action="#" method="post" aria-labelledby="%(hid)s">
  <h2 id="%(hid)s">%(title)s</h2>
  %(intro)s
  <p class="form-note" style="margin:0 0 20px">Fields marked <span class="req">*</span> are required.</p>
  %(parts)s
  <div class="hp" aria-hidden="true"><label for="%(hpid)s">Leave this field empty</label><input type="text" id="%(hpid)s" name="website" tabindex="-1" autocomplete="off"></div>
  <div class="form-actions"><button class="btn btn--ghost form-back" type="button" hidden>Back</button><button class="btn btn--dark form-next" type="button" hidden>Next</button><button class="btn btn--dark" type="submit">%(submit)s</button></div>
  %(note)s
  <div class="form-status" role="status" aria-live="polite"></div>
  <p class="form-note form-inbox">Prefer email? Write to <a href="mailto:%(inbox)s">%(inbox)s</a></p>
</form>""" % dict(key=key, success=_e(spec["success"]), redirect=redirect, hid="%s-title" % key.replace("_", "-"),
                  title=_e(spec["title"]), intro=intro, parts="\n  ".join(parts), hpid="%s-website" % key.replace("_", "-"), error=error, inbox=inbox,
                  submit=_e(spec["submit"]), note=note)


def write_forms_md(path):
    out = ["# Website forms",
           "",
           "Generated by `build.py` from `forms.py` - edit `forms.py`, not this file.",
           "",
           "Every form posts JSON with `fetch` to " + ENDPOINT_NOTE + ":",
           "",
           "```json",
           '{ "form": "<form key>", "fields": { "<exact label>": "<value>", ... }, "page": "/path/the/form/was/on" }',
           "```",
           "",
           "- The field names in `fields` are the exact question wording from the old Wix forms (column **Sent as**). "
           "Where the visitor sees tidier wording, that is in **Shown as**.",
           "- Every form also has a hidden honeypot input named `website`. A person never sees it; if it has a value the "
           "browser shows the success message and sends nothing. The endpoint should also reject any body whose fields contain `website`.",
           "- Single checkboxes are sent as `\"Yes\"` / `\"No\"`. Checkbox groups are sent as one comma-separated string. "
           "Empty optional fields are sent as `\"\"`.",
           "- On a 2xx response the form shows its success message (and, where listed, moves to the thank-you page after "
           "1.2 seconds). Any other response, or no response, shows an error message that gives the email address and phone number. "
           "No alert/confirm/prompt is used.",
           "- **Until the endpoint exists every form will show the error message.**",
           "",
           "## Notes for whoever builds the endpoint",
           "",
           "- The old intake normalises a key by lower-casing and removing spaces, `_` and `-`. Under that rule "
           "`what best describes you` becomes `whatbestdescribesyou` (matches the existing SEGMENTS lookup), but "
           "`which best describes you ?` becomes `whichbestdescribesyou?`, `How Soon Are You Looking To Buy` becomes "
           "`howsoonareyoulookingtobuy` and `How soon are you looking to buy / invest` becomes `howsoonareyoulookingtobuy/invest`. "
           "The new endpoint should map these explicitly rather than rely on the old `pick()` list.",
           "- The Wix appointment picker (\"When are You Available to Discuss\", a 30-minute phone call) cannot be rebuilt on a "
           "static site. It is replaced by three new fields: `Preferred days`, `Preferred time of day`, `Preferred date`. "
           "A real calendar is a later decision.",
           "- File upload (`vendor_lead`): the browser only sends the **file names** in `File upload`, because the body is JSON. "
           "Uploading the photos themselves needs the endpoint to support it (for example a signed Supabase Storage upload URL, "
           "or switching this one form to multipart/form-data). The input allows images only, up to 10.",
           "- The two strategy-call forms and the booking form redirect to `/optinform/gv2mkhfkhkkhdkhjcd10ku`, which (copied "
           "from the old site) says the investor guide has been emailed. That is only true if the endpoint emails it. "
           "The vendor form's success message also says \"check your email for confirmation\". Either send those emails "
           "or change the wording.",
           ""]
    for key, spec in FORMS.items():
        out += ["## `%s` - %s" % (key, spec["title"]), "",
                "- **Page:** `%s`" % spec["page"],
                "- **Came from:** %s" % spec["origin"],
                "- **Submit button:** %s" % spec["submit"],
                "- **Success message:** %s" % spec["success"],
                "- **After success:** %s" % ("goes to `%s`" % spec["redirect"] if spec.get("redirect") else "stays on the page"),
                ""]
        out += ["| Sent as (exact label) | Shown as | Input | Required | Options |", "|---|---|---|---|---|"]
        for fs in spec["fieldsets"]:
            for f in fs["fields"]:
                opts = "; ".join("`%s`" % o for o in f.get("options", [])) or "-"
                extra = []
                if f.get("new"):
                    extra.append("new field (replaces the Wix appointment picker)")
                if f.get("changed"):
                    extra.append(f["changed"])
                if fs.get("wix"):
                    extra.append("part of the Wix '%s' field" % fs["wix"])
                if f.get("value"):
                    extra.append("pre-filled with '%s'" % f["value"])
                if f["type"] == "file":
                    extra.append("images only, max %d; only file names are sent" % f.get("max", 10))
                if extra:
                    opts += " - " + "; ".join(extra)
                out.append("| `%s` | %s | %s | %s | %s |" % (f["label"], f.get("show", f["label"]), f["type"],
                                                             "yes" if f.get("required") else "no", opts))
        out.append("")
        if key == "vendor_lead":
            out += ["The Wix form also had a hidden field `Quick Description` (textarea, \"Give a Detailed Description e.g., "
                    "outstanding mortgage, legal issues\"). It was switched off on Wix, so it is not on the new form.", ""]
    out += ["## Old forms not rebuilt", "",
            "- Wix Bookings services \"Personal Solution Planning\", \"Expert Guidance Package\" (GBP 500), \"Custom Project\" (GBP 1,000) "
            "and \"30 min meeting\" were all set to hidden on Wix and look like Wix template defaults. They are not on the new site.",
            ""]
    path.write_text("\n".join(out), encoding="utf-8")
