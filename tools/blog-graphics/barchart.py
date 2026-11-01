"""Write a branded horizontal bar chart as HTML. Data in a JSON file:
{title, kicker, subtitle, unit, rows:[[label, value, kind]], ref:{value,label}, source, w, h}
kind: "nat" (UK / region, navy), "focus" (Stoke / county, gold), "" (district, light gold)."""
import json, sys, html, pathlib
FONTS = pathlib.Path(r"C:/Users/golde/IONOS HiDrive/MR.GREY/My Claude/GVN Website/assets/fonts")
d = json.load(open(sys.argv[1], encoding="utf-8"))
mx = max(max(r[1] for r in d["rows"]), d.get("ref", {}).get("value", 0)) * 1.12
e = html.escape
rows = "".join(
    '<div class="row %s"><span class="lab">%s</span><span class="track"><span class="bar" style="width:%.2f%%"></span>'
    '<span class="val" style="left:%.2f%%">%s%s</span></span></div>' % (k, e(l), v / mx * 100, v / mx * 100, ("%.1f" % v), d["unit"])
    for l, v, k in d["rows"])
ref = ""
if d.get("ref"):
    x = d["ref"]["value"] / mx * 100
    ref = '<div class="ref" style="left:calc(var(--lab) + (100%% - var(--lab)) * %.4f)"><span>%s</span></div>' % (x / 100, e(d["ref"]["label"]))
out = """<!doctype html><meta charset="utf-8"><style>
@font-face{font-family:Bodoni;src:url('%(f)s/bodoni-moda.woff2')}
@font-face{font-family:Hanken;src:url('%(f)s/hanken-grotesk.woff2')}
html,body{margin:0;width:100%%;height:100%%;background:#f3eee5;color:#121a28;font-family:Hanken,sans-serif}
.card{box-sizing:border-box;width:100%%;height:100%%;padding:46px 56px 40px;display:flex;flex-direction:column;border-top:6px solid #c6a15b}
.kick{font-size:15px;letter-spacing:.2em;text-transform:uppercase;color:#7a5719;font-weight:700;margin:0 0 10px}
h1{font-family:Bodoni,serif;font-weight:500;font-size:40px;line-height:1.1;margin:0 0 8px}
.sub{font-size:18px;color:#535b69;margin:0 0 26px}
.chart{position:relative;flex:1;display:flex;flex-direction:column;justify-content:space-between;--lab:270px}
.row{display:flex;align-items:center;height:%(rowh)dpx}
.lab{width:var(--lab);flex:none;font-size:19px;padding-right:16px;box-sizing:border-box;text-align:right}
.track{position:relative;flex:1;height:100%%;display:flex;align-items:center}
.bar{display:block;height:62%%;background:#e6cf98;border-radius:0 3px 3px 0}
.val{position:absolute;padding-left:10px;font-size:18px;font-weight:700;white-space:nowrap}
.nat .bar{background:#1a2a44}.nat .lab{font-weight:700}
.focus .bar{background:#c6a15b}.focus .lab{font-weight:700}
.ref{position:absolute;top:-6px;bottom:-6px;border-left:2px dashed #7a5719}
.ref span{position:absolute;bottom:100%%;left:-2px;transform:translateY(-4px);white-space:nowrap;font-size:15px;color:#7a5719;font-weight:700;background:#f3eee5;padding-right:6px}
.foot{display:flex;justify-content:space-between;align-items:flex-end;margin-top:22px;font-size:14px;color:#535b69;gap:24px}
.brand{font-family:Bodoni,serif;font-size:19px;color:#121a28;white-space:nowrap}
@media (max-width:700px){
html,body{width:100%%;height:100%%}
.card{padding:30px 26px 26px}
.kick{font-size:13px;letter-spacing:.14em}
h1{font-size:31px}
.sub{font-size:17px;margin-bottom:20px}
.foot{flex-direction:column;align-items:flex-start;gap:10px;font-size:13px;margin-top:18px}
.chart{--lab:178px}.lab{font-size:16px;padding-right:10px}.val{font-size:16px;padding-left:7px}.ref span{font-size:13px}
}
</style><div class="card"><p class="kick">%(kicker)s</p><h1>%(title)s</h1><p class="sub">%(sub)s</p>
<div class="chart">%(ref)s%(rows)s</div>
<div class="foot"><span>%(source)s</span><span class="brand">GVN Estate Invest</span></div></div>""" % dict(
    f=FONTS.as_uri(), w=d["w"], h=d["h"], rowh=d.get("rowh", 38), kicker=e(d["kicker"]), title=e(d["title"]),
    sub=e(d["subtitle"]), rows=rows, ref=ref, source=e(d["source"]))
pathlib.Path(sys.argv[2]).write_text(out, encoding="utf-8")
