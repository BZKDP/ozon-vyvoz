# -*- coding: utf-8 -*-
import json, os, collections, io
OUTDIR = r"."
import openpyxl
def num(x):
    try: return int(round(float(x)))
    except: return 0
wb = openpyxl.load_workbook(r"Забрать.xlsx", data_only=True)
ws = wb["Лист1"]
boss = set()
for r in list(ws.iter_rows(values_only=True))[1:]:
    if not r[1] or (isinstance(r[1], str) and ("ИТОГО" in r[1] or "ещё" in r[1])): continue
    boss.add(str(r[1]).strip().upper())
rows = json.load(open(os.path.join(OUTDIR,"stock2_raw.json"), encoding="utf-8"))
wh = collections.Counter()
for r in rows:
    if str(r.get("item_code")).strip().upper() in boss:
        wh[r.get("warehouse_name")] += int(r.get("free_to_sell_amount") or 0)
out = io.StringIO()
for w in sorted(wh, key=lambda x:-wh[x]):
    out.write("%-32s %5d\n" % (w, wh[w]))
out.write("ВСЕГО складов: %d, единиц: %d\n" % (len(wh), sum(wh.values())))
open(os.path.join(OUTDIR,"wh_list.txt"),"w",encoding="utf-8").write(out.getvalue())
print("OK wh=%d units=%d" % (len(wh), sum(wh.values())))
