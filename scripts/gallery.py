import json, re, sys, gzip, time, urllib.request, html
from concurrent.futures import ThreadPoolExecutor
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
lst, det, dst = sys.argv[1:4]
links = {s["id"]: s["link"] for s in json.load(open(lst))["schools"]}
ids = [d["id"] for d in map(json.loads, open(det)) if "School Gallery" in d.get("sections", [])]
print("gallery schools", len(ids), file=sys.stderr)
def fetch(i):
    for a in range(5):
        try:
            req = urllib.request.Request(links[i], headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=60) as r:
                b = r.read()
                if r.headers.get("Content-Encoding") == "gzip": b = gzip.decompress(b)
            h = b.decode("utf-8", "replace")
            k = h.find('class="gal-loop"'); e = h.find("</div>", k)
            return i, [html.unescape(u) for u in re.findall(r'data-fancybox="school-gallery" href="([^"]+)"', h[k:e])]
        except Exception as ex:
            time.sleep(2 * (a + 1))
    return i, None
with ThreadPoolExecutor(6) as ex:
    res = dict(ex.map(fetch, ids))
json.dump(res, open(dst, "w"))
print("done", sum(1 for v in res.values() if v), "with images; failed", sum(1 for v in res.values() if v is None), file=sys.stderr)
