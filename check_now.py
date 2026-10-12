import os
# -*- coding: utf-8 -*-
"""Свежий срез остатков по 19 боссовским артикулам: сколько ещё лежит на FBO."""
import json, urllib.request, urllib.error, time, collections
import openpyxl

CID = "2843272"; KEY = os.environ.get("OZON_API_KEY", "")

def api(path, body, tries=6):
    data = json.dumps(body).encode()
    for a in range(tries):
        req = urllib.request.Request("https://api-seller.ozon.ru"+path, data=data,
            headers={"Client-Id": CID, "Api-Key": KEY, "Content-Type": "application/json"}, method="POST")
        try:
            return json.loads(urllib.request.urlopen(req).read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(6*(a+1)); continue
            print("HTTP", e.code, e.read().decode()[:300]); raise
    raise SystemExit("rate limited "+path)

wb = openpyxl.load_workbook(r"Забрать.xlsx", data_only=True)
ws = wb["Лист1"]
boss = {}
for r in list(ws.iter_rows(values_only=True))[1:]:
    if not r[1] or (isinstance(r[1], str) and ("ИТОГО" in r[1] or "ещё" in r[1])): continue
    art = str(r[1]).strip().upper()
    try: qty = int(round(float(r[2])))
    except: qty = 0
    boss[art] = qty
print("Босс-лист: %d SKU, %d шт (срез 18.08)" % (len(boss), sum(boss.values())))

rows = []
offset = 0
while True:
    j = api("/v2/analytics/stock_on_warehouses", {"limit": 1000, "offset": offset, "warehouse_type": "ALL"})
    part = (j.get("result") or {}).get("rows") or []
    rows += part
    if len(part) < 1000: break
    offset += 1000
print("API строк:", len(rows))

cur = collections.Counter()
by_wh = collections.defaultdict(int)
for r in rows:
    art = (r.get("item_code") or "").strip().upper()
    if art in boss:
        q = int(r.get("free_to_sell_amount") or 0) + int(r.get("reserved_amount") or 0)
        cur[art] += q
        if q: by_wh[r.get("warehouse_name")] += q

tot_now = sum(cur.values())
print("СЕЙЧАС по боссовским артикулам: %d шт  (было 5638)" % tot_now)
print("Дельта: %+d" % (tot_now - sum(boss.values())))
print()
print("%-12s %6s %6s %6s" % ("Артикул", "было", "сейчас", "дельта"))
for art in sorted(boss, key=lambda a: -boss[a]):
    print("%-12s %6d %6d %+6d" % (art, boss[art], cur.get(art, 0), cur.get(art, 0)-boss[art]))
print()
print("Топ складов сейчас:")
for wh, q in sorted(by_wh.items(), key=lambda x: -x[1])[:20]:
    print("  %-30s %5d" % (wh, q))
