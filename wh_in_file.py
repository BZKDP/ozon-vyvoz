# -*- coding: utf-8 -*-
import openpyxl, sys, collections
path = sys.argv[1]
def num(x):
    try: return int(round(float(x)))
    except: return 0
t = openpyxl.load_workbook(path, data_only=True)
ws = t.active
wh = collections.Counter()
arts = set()
for r in list(ws.iter_rows(values_only=True))[5:]:
    if not r or not r[2]: continue
    wh[r[3]] += num(r[6]) + num(r[7])
    arts.add(str(r[2]).strip().upper())
print("Складов:", len(wh), "| Артикулов:", len(arts), "| Итого шт:", sum(wh.values()))
for w in sorted(wh, key=lambda x:-wh[x]):
    print("  %-28s %5d" % (w, wh[w]))
