import json, urllib.request, sys
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r), dict(r.headers)
out = []
page = 1
while True:
    data, h = get(f"https://www.tcf.org.pk/wp-json/wp/v2/schools?per_page=100&page={page}&_fields=id,slug,link,title,province,featured_media,date,modified")
    out += data
    tp = int(h.get("X-WP-TotalPages") or h.get("x-wp-totalpages"))
    print(page, tp, len(out), file=sys.stderr)
    if page >= tp: break
    page += 1
prov, _ = get("https://www.tcf.org.pk/wp-json/wp/v2/province?per_page=100&_fields=id,name,slug,count")
json.dump({"schools": out, "provinces": prov}, open(sys.argv[1], "w"), indent=1)
print(len(out), prov)
