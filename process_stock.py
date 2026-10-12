# -*- coding: utf-8 -*-
import json, csv, collections, io

RAW = r"stock_raw.json"
REPORT = r"report.txt"
CSV_OUT = r"stock.csv"

raw = json.load(open(RAW, encoding="utf-8"))
if isinstance(raw, dict):
    rows = raw.get("result", {}).get("rows", [])
else:
    rows = raw

out = io.StringIO()
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")

p("ROWS:", len(rows))
if rows:
    p("FIELDS:", ", ".join(rows[0].keys()))
    p("SAMPLE ROW:", json.dumps(rows[0], ensure_ascii=False))
p("")

# generic field access
def g(r, *names, default=0):
    for n in names:
        if n in r and r[n] is not None:
            return r[n]
    return default

# Cluster mapping (from Ozon FBO warehouse -> cluster), extend as needed
CLUSTER = {}
def cluster_of(wh):
    w = (wh or "").upper()
    if any(k in w for k in ["ПУШКИНО","ДОМОДЕДОВО","ПЕТРОВСК","ХОРУГВИНО","ЖУКОВСК","ГРИВНО","ТВЕР","ТУЛА","РЯЗАН","КАЛУГ","ВЛАДИМИР","ЯРОСЛАВ","МОСК"]):
        return "Москва, МО и Дальние регионы"
    if "КАЗАН" in w or "ЗЕЛЕНОДОЛЬ" in w:
        return "Казань"
    if any(k in w for k in ["СПБ","ПЕТЕРБУРГ","ПАРГОЛОВО","ШУШАРЫ","БУГРЫ","КОЛПИНО"]):
        return "Санкт-Петербург и СЗО"
    if "УФА" in w:
        return "Уфа"
    if any(k in w for k in ["ЕКАТЕРИН","ЕКБ","БЕРЕЗОВ"]):
        return "Екатеринбург"
    if any(k in w for k in ["НОВОСИБ","КОЛЬЦОВО"]):
        return "Новосибирск"
    if "КРАСНОДАР" in w or "АДЫГЕ" in w:
        return "Краснодар"
    if "РОСТОВ" in w:
        return "Ростов"
    if "САМАР" in w:
        return "Самара"
    if "ВОРОНЕЖ" in w:
        return "Воронеж"
    if "НИЖН" in w and "НОВГОРОД" in w:
        return "Нижний Новгород"
    if "ХАБАРОВ" in w or "ДАЛЬН" in w:
        return "Дальний Восток"
    return "Прочее / не определён"

by_wh = collections.defaultdict(lambda: collections.Counter())
by_art = collections.defaultdict(lambda: {"name":"", "free":0, "reserved":0, "promised":0, "wh":set()})
by_cluster = collections.defaultdict(lambda: collections.Counter())
totals = collections.Counter()

records = []
for r in rows:
    wh   = g(r, "warehouse_name", default="")
    art  = g(r, "item_code", "offer_id", default="")
    name = g(r, "item_name", "name", default="")
    sku  = g(r, "sku", default="")
    free = int(g(r, "free_to_sell_amount", "free_to_sell", default=0) or 0)
    resv = int(g(r, "reserved_amount", "reserved", default=0) or 0)
    prom = int(g(r, "promised_amount", "promised", default=0) or 0)
    cl = cluster_of(wh)

    by_wh[wh]["free"] += free; by_wh[wh]["reserved"] += resv; by_wh[wh]["promised"] += prom
    by_cluster[cl]["free"] += free; by_cluster[cl]["reserved"] += resv; by_cluster[cl]["promised"] += prom
    a = by_art[art]; a["name"]=name or a["name"]; a["free"]+=free; a["reserved"]+=resv; a["promised"]+=prom; a["wh"].add(wh)
    totals["free"]+=free; totals["reserved"]+=resv; totals["promised"]+=prom
    records.append({"cluster":cl,"warehouse":wh,"article":art,"sku":sku,"name":name,"free_to_sell":free,"reserved":resv,"promised":prom})

p("="*70)
p("ИТОГО ПО МАГАЗИНУ (весь FBO-сток)")
p("="*70)
p("Доступно к продаже (free_to_sell): ", totals["free"])
p("В резерве под заказы (reserved):   ", totals["reserved"])
p("Ожидается приёмка (promised):      ", totals["promised"])
p("Всего физически на складах ~ free+reserved = ", totals["free"]+totals["reserved"])
p("Уникальных артикулов:", len([a for a in by_art if by_art[a]["free"]+by_art[a]["reserved"]>0]))
p("Складов задействовано:", len([w for w in by_wh if w]))
p("")

p("="*70)
p("ПО КЛАСТЕРАМ (как в интерфейсе вывоза)")
p("="*70)
p("%-38s %8s %8s %8s" % ("Кластер","Доступно","Резерв","Приёмка"))
for cl in sorted(by_cluster, key=lambda x: -by_cluster[x]["free"]):
    c=by_cluster[cl]
    p("%-38s %8d %8d %8d" % (cl[:38], c["free"], c["reserved"], c["promised"]))
p("")

p("="*70)
p("ПО СКЛАДАМ")
p("="*70)
p("%-28s %-30s %8s %8s %8s" % ("Кластер","Склад","Доступно","Резерв","Приёмка"))
for wh in sorted(by_wh, key=lambda x: -by_wh[x]["free"]):
    c=by_wh[wh]
    p("%-28s %-30s %8d %8d %8d" % (cluster_of(wh)[:28], (wh or "?")[:30], c["free"], c["reserved"], c["promised"]))
p("")

p("="*70)
p("ПО АРТИКУЛАМ (это то, чего не видно на шаге выбора склада)")
p("="*70)
p("%-16s %8s %8s %-40s %s" % ("Артикул","Доступно","Резерв","Название","Склады"))
for art in sorted(by_art, key=lambda x: -by_art[x]["free"]):
    a=by_art[art]
    p("%-16s %8d %8d %-40s %s" % ((art or "?")[:16], a["free"], a["reserved"], (a["name"] or "")[:40], ", ".join(sorted(w for w in a["wh"] if w))))
p("")

open(REPORT, "w", encoding="utf-8").write(out.getvalue())

with open(CSV_OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["cluster","warehouse","article","sku","name","free_to_sell","reserved","promised"])
    w.writeheader()
    for rec in sorted(records, key=lambda x:(x["cluster"], x["article"])):
        w.writerow(rec)

print("OK rows=%d free=%d reserved=%d arts=%d wh=%d" % (len(rows), totals["free"], totals["reserved"], len(by_art), len([w for w in by_wh if w])))
