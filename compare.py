# -*- coding: utf-8 -*-
import json, os, collections, io
import openpyxl

OUTDIR = r"."
REPORT = os.path.join(OUTDIR, "compare_report.txt")

def num(x):
    try: return int(round(float(x)))
    except: return 0

# boss Лист1
wb = openpyxl.load_workbook(r"Забрать.xlsx", data_only=True)
ws = wb["Лист1"]
boss_qty = {}; boss_sku = {}; boss_name = {}
for r in list(ws.iter_rows(values_only=True))[1:]:
    if not r[1] or (isinstance(r[1], str) and ("ИТОГО" in r[1] or "ещё" in r[1])): continue
    a = str(r[1]).strip().upper()
    boss_qty[a] = num(r[2]); boss_sku[a] = num(r[0]); boss_name[a] = str(r[9] or "")

# API acct 2843272
rows = json.load(open(os.path.join(OUTDIR, "stock2_raw.json"), encoding="utf-8"))
api_by_art = collections.Counter()
api_by_sku = collections.Counter()
for r in rows:
    a = str(r.get("item_code")).strip().upper()
    q = int(r.get("free_to_sell_amount") or 0)
    api_by_art[a] += q
    api_by_sku[str(r.get("sku"))] += q

out = io.StringIO()
def p(*a): out.write(" ".join("" if x is None else str(x) for x in a) + "\n")

p("%-11s %8s %8s %7s   %s" % ("Артикул","Босс","API","Разн.","Товар"))
p("-"*80)
tb = ta = 0; diffs = 0
for a in sorted(boss_qty, key=lambda x:-boss_qty[x]):
    bq = boss_qty[a]; aq = api_by_art.get(a, 0)
    # also cross-check by SKU
    sq = api_by_sku.get(str(boss_sku[a]), None)
    d = aq - bq
    tb += bq; ta += aq
    if d != 0: diffs += 1
    flag = "" if d == 0 else ("  <<< РАЗН %+d" % d)
    p("%-11s %8d %8d %+7d   %s%s" % (a, bq, aq, d, boss_name[a][:32], flag))
p("-"*80)
p("ИТОГО      %8d %8d %+7d" % (tb, ta, ta-tb))
p("")
p("Артикулов с расхождением по количеству:", diffs, "из", len(boss_qty))
p("Артикулов, которых нет в API:", len([a for a in boss_qty if a not in api_by_art]))
open(REPORT, "w", encoding="utf-8").write(out.getvalue())
print("OK boss=%d api=%d diff=%d diffs_cnt=%d" % (tb, ta, ta-tb, diffs))
