import json, re, sys, gzip, time, html, urllib.request, os
from concurrent.futures import ThreadPoolExecutor
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
src, dst = sys.argv[1], sys.argv[2]
schools = json.load(open(src))["schools"]
done = set()
if os.path.exists(dst):
    for l in open(dst):
        try: done.add(json.loads(l)["id"])
        except Exception: pass
todo = [s for s in schools if s["id"] not in done]
print("todo", len(todo), file=sys.stderr)

def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()

def parse(h):
    i = h.find('class="school-inner"')
    j = h.find('class="col-md-3 pullleft"', i)
    seg = h[i:j] if i >= 0 else ""
    d = {}
    m = re.search(r'maps\.google\.com/maps\?q=\s*([-0-9.]+)\s*,\s*([-0-9.]+)', seg)
    if m: d["lat"], d["lng"] = float(m.group(1)), float(m.group(2))
    else:
        m = re.search(r'maps\?q=([^&"]+)', seg)
        if m: d["map_q"] = html.unescape(m.group(1))
    m = re.search(r'<div class="pic">\s*<img[^>]*?\ssrc="([^"]+)"', seg)
    if m: d["img"] = m.group(1)
    m = re.search(r'<span class="post-cat">(.*?)</span>', seg, re.S)
    if m: d["subtitle"] = clean(m.group(1))
    rows = {}
    for r in re.finditer(r"<tr>(.*?)</tr>", seg, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", r.group(1), re.S)
        if len(tds) >= 2:
            k = clean(tds[0])
            lis = re.findall(r"<li[^>]*>(.*?)</li>", tds[1], re.S)
            rows[k] = [clean(x) for x in lis if clean(x)] if lis else clean(tds[1])
    d["rows"] = rows
    # any other detail section headings
    d["sections"] = [clean(x) for x in re.findall(r'<div class="detail">\s*<h2>(.*?)</h2>', seg, re.S)]
    # any free text paragraphs inside detail
    ps = [clean(x) for x in re.findall(r"<p[^>]*>(.*?)</p>", seg, re.S)]
    d["paras"] = [p for p in ps if p]
    return d

def fetch(s):
    for attempt in range(5):
        try:
            req = urllib.request.Request(s["link"], headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=60) as r:
                b = r.read()
                if r.headers.get("Content-Encoding") == "gzip": b = gzip.decompress(b)
            d = parse(b.decode("utf-8", "replace"))
            d["id"] = s["id"]
            return d
        except Exception as e:
            err = str(e); time.sleep(2 * (attempt + 1))
    return {"id": s["id"], "error": err}

with open(dst, "a") as f, ThreadPoolExecutor(6) as ex:
    for n, d in enumerate(ex.map(fetch, todo), 1):
        f.write(json.dumps(d) + "\n"); f.flush()
        if n % 50 == 0: print(n, file=sys.stderr)
print("done", file=sys.stderr)
