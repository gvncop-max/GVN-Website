"""Email Valentine that a draft post is waiting on the preview site.

  python tools/blog-agent/notify.py "<post title>" <slug> "<one-paragraph summary>"

Sends through Resend from task.gvnestateinvest.com (GVN's sending domain) to
NOTIFY_EMAIL. The Resend key (send-only) is best stored as a cloud "network
secret" for api.resend.com, so the proxy adds it and the agent never sees it;
RESEND_API_KEY in the environment works too. No NOTIFY_EMAIL, or Resend says
no key: it prints that no email was sent and exits 0, and the run summary on
claude.ai is the notification. A key is never printed.
"""
import html, json, os, re, sys, urllib.error, urllib.request

PREVIEW = "https://gvn-website-preview.onrender.com/post/"


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    title, slug, summary = sys.argv[1][:200], sys.argv[2], sys.argv[3][:2000]
    if not re.fullmatch(r"[a-z0-9-]{3,120}", slug):
        sys.exit("bad slug")
    key, to = os.environ.get("RESEND_API_KEY", "").strip(), os.environ.get("NOTIFY_EMAIL", "").strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", to, re.I):
        print("notify: NOTIFY_EMAIL not set, no email sent")
        return
    link = PREVIEW + slug
    text = ("A new Provenance Pulse post is ready for you to read on the preview site. "
            "It is NOT live.\n\n%s\n%s\n\n%s\n\nTo publish it, tell Claude \"push it live\". "
            "To change it, say what to change.\n" % (title, link, summary))
    body = ('<p>A new Provenance Pulse post is ready for you to read on the preview site. '
            '<strong>It is not live.</strong></p><p><a href="%s">%s</a></p><p>%s</p>'
            '<p>To publish it, tell Claude &ldquo;push it live&rdquo;. To change it, say what to change.</p>'
            % (html.escape(link), html.escape(title), html.escape(summary)))
    req = urllib.request.Request("https://api.resend.com/emails", method="POST", data=json.dumps({
        "from": "GVN Blog Agent <blog@task.gvnestateinvest.com>", "to": [to],
        "reply_to": "support@gvnestateinvest.com",
        "subject": "Draft ready to review: " + title, "text": text, "html": body}).encode(),
        headers=dict({"Content-Type": "application/json", "User-Agent": "GVNEstateInvestBlog/1.0"},
                     **({"Authorization": "Bearer " + key} if key else {})))  # else the network secret adds it
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("notify: email sent (HTTP %d)" % r.status)
    except urllib.error.HTTPError as e:
        if e.code in (401, 403) and not key:
            print("notify: no Resend key configured, no email sent")
            return
        print("notify: Resend refused the email (HTTP %d)" % e.code)  # never echo the key
        sys.exit(1)
    except Exception as e:
        print("notify: could not reach Resend (%s)" % type(e).__name__)
        sys.exit(1)


if __name__ == "__main__":
    main()
