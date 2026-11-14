import json, re, sys, html, statistics, math, collections, os, datetime
lst, det, gal, tpl, vendor, out = sys.argv[1:7]
L = json.load(open(lst))
provs = {p["id"]: html.unescape(p["name"]) for p in L["provinces"]}
D = {d["id"]: d for d in map(json.loads, open(det))}
G = json.load(open(gal)) if os.path.exists(gal) else {}
G = {int(k): v for k, v in G.items()}
PFIX = {"Khyber Paktoonkhwa": "Khyber Pakhtunkhwa", "Azad Jammu & Kashmir": "Azad Jammu & Kashmir", "#N/A": ""}
def inpk(la, lo): return 23.5 <= la <= 37.2 and 60.8 <= lo <= 77.9
def hav(a, b):
    r = math.pi / 180; dla = (b[0]-a[0])*r; dlo = (b[1]-a[1])*r
    x = math.sin(dla/2)**2 + math.cos(a[0]*r)*math.cos(b[0]*r)*math.sin(dlo/2)**2
    return 2*6371*math.asin(math.sqrt(x))
def tidy(s): return re.sub(r"\s+", " ", (s or "")).strip()

rows, issues = [], collections.Counter()
for s in L["schools"]:
    d = D.get(s["id"], {})
    if "error" in d or not d: issues["fetch_error"] += 1
    r = d.get("rows", {})
    prov = tidy(re.sub(r"^\(|\)$", "", d.get("subtitle", "") or "").strip())
    if not prov and s.get("province"): prov = provs.get(s["province"][0], "")
    prov = PFIX.get(prov, prov)
    cat = r.get("Category") or []
    cat = cat if isinstance(cat, list) else [cat]
    c = ("P" if any("primary" in x.lower() for x in cat) else "") + ("S" if any("secondary" in x.lower() for x in cat) else "")
    if not c: issues["no_category"] += 1
    sh = r.get("Shift") or []
    sh = sh if isinstance(sh, list) else [sh]
    sh = [tidy(x).title() for x in sh if tidy(x)]
    la, lo = d.get("lat"), d.get("lng")
    fixed = None
    if la is not None and not inpk(la, lo):
        if inpk(lo, la): la, lo = lo, la; issues["swapped_fixed"] += 1
        else: issues["out_of_pk"] += 1; fixed = (la, lo); la = lo = None
    if la is None: issues["no_coords"] += 1
    imgs = []
    if d.get("img") and "school-default" not in d["img"]: imgs.append(d["img"])
    for u in G.get(s["id"]) or []:
        if u not in imgs: imgs.append(u)
    link = s["link"].split("/schools/", 1)[1]
    rows.append(dict(i=s["id"], n=tidy(html.unescape(s["title"]["rendered"])), p=prov, d=tidy(r.get("District", "")),
                     r=tidy(r.get("Region", "")), y=tidy(r.get("Date of Start", "")), u=tidy(r.get("No. of Unit(s)", "")),
                     c=c, s=sh, la=la, lo=lo, im=imgs, l=link, _bad=fixed))

# normalise district spelling variants by case
dcase = collections.defaultdict(collections.Counter)
for x in rows: dcase[x["d"].lower()][x["d"]] += 1
for x in rows: x["d"] = dcase[x["d"].lower()].most_common(1)[0][0] if x["d"] else ""
# province from district when missing
dprov = collections.defaultdict(collections.Counter)
for x in rows:
    if x["p"] and x["d"]: dprov[x["d"]][x["p"]] += 1
for x in rows:
    if not x["p"] and x["d"] in dprov: x["p"] = dprov[x["d"]].most_common(1)[0][0]; issues["province_inferred"] += 1
# district centroids
dc = collections.defaultdict(list); pc = collections.defaultdict(list)
for x in rows:
    if x["la"] is not None: dc[x["d"]].append((x["la"], x["lo"])); pc[x["p"]].append((x["la"], x["lo"]))
med = lambda pts: (statistics.median(p[0] for p in pts), statistics.median(p[1] for p in pts))
dcen = {k: med(v) for k, v in dc.items() if k}
pcen = {k: med(v) for k, v in pc.items() if k}
outliers = []
for x in rows:
    if x["la"] is not None and x["d"] in dcen and len(dc[x["d"]]) >= 3:
        k = hav((x["la"], x["lo"]), dcen[x["d"]])
        if k > 150: outliers.append((round(k), x["n"], x["d"], x["la"], x["lo"]))
for x in rows:
    if x["la"] is None:
        c = dcen.get(x["d"]) or pcen.get(x["p"])
        if c: x["la"], x["lo"], x["a"] = c[0], c[1], 1
        else: issues["unplaceable"] += 1
placed = [x for x in rows if x["la"] is not None]
for x in placed:
    x["la"], x["lo"] = round(x["la"], 6), round(x["lo"], 6)
    x.pop("_bad", None)
    for k in ["r", "y", "u", "im", "p", "d"]:
        if not x.get(k): x.pop(k, None) if k in ("r", "y", "u", "im") else None
print("schools", len(rows), "placed", len(placed), dict(issues), file=sys.stderr)
print("outliers (>150km from district median):", len(outliers), file=sys.stderr)
for o in sorted(outliers, reverse=True)[:25]: print("  ", o, file=sys.stderr)
print("with images", sum(1 for x in placed if x.get("im")), file=sys.stderr)

order = ["Sindh", "Punjab", "Khyber Pakhtunkhwa", "Balochistan", "Azad Jammu & Kashmir"]
ps = sorted({x["p"] for x in placed if x["p"]}, key=lambda p: (order.index(p) if p in order else 99, p))
shifts = sorted({v for x in placed for v in x["s"]}, key=lambda v: ["Morning", "Afternoon", "Evening"].index(v) if v in ["Morning", "Afternoon", "Evening"] else 9)
meta = dict(provinces=ps, shifts=shifts, approx=sum(1 for x in placed if x.get("a")), date=datetime.date.today().strftime("%-d %b %Y"))
placed.sort(key=lambda x: x["n"].lower())
t = open(tpl).read()
V = lambda f: open(os.path.join(vendor, f)).read()
css = V("leaflet.css") + "\n" + V("MarkerCluster.css") + "\n" + V("MarkerCluster.Default.css")
js_safe = lambda s: s.replace("</script", "<\\/script")
t = t.replace("/*__LEAFLET_CSS__*/", css).replace("/*__LEAFLET_JS__*/", js_safe(V("leaflet.js"))).replace("/*__CLUSTER_JS__*/", js_safe(V("leaflet.markercluster.js")))
t = t.replace("/*__DATA__*/", js_safe(json.dumps(placed, ensure_ascii=False, separators=(",", ":")))).replace("/*__META__*/", json.dumps(meta, ensure_ascii=False))
open(out, "w").write(t)
# also export a CSV of the data
import csv
with open(re.sub(r"\.html$", ".csv", out), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["id", "name", "province", "district", "region", "level", "shift", "year_started", "units", "latitude", "longitude", "location_approximate", "tcf_url"])
    for x in placed:
        w.writerow([x["i"], x["n"], x.get("p", ""), x.get("d", ""), x.get("r", ""), {"P": "Primary", "S": "Secondary", "PS": "Primary + Secondary"}.get(x["c"], ""),
                    " + ".join(x["s"]), x.get("y", ""), x.get("u", ""), x["la"], x["lo"], "yes" if x.get("a") else "no", "https://www.tcf.org.pk/schools/" + x["l"]])
print("wrote", out, os.path.getsize(out), file=sys.stderr)
