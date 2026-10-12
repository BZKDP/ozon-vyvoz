import os
# -*- coding: utf-8 -*-
import json, urllib.request, urllib.error, collections, io, time

RAW = r"stock_raw.json"
OUT = r"report2.txt"

raw = json.load(open(RAW, encoding="utf-8"))
rows = raw.get("result", {}).get("rows", []) if isinstance(raw, dict) else raw

# unique SKUs + aggregate free by sku/article
sku_free = collections.Counter()
sku_art = {}
sku_name = {}
for r in rows:
    sku = str(r.get("sku"))
    sku_free[sku] += int(r.get("free_to_sell_amount") or 0)
    sku_art[sku] = r.get("item_code")
    sku_name[sku] = r.get("item_name")

skus = [s for s in sku_free if s and s != "None"]

# call turnover with explicit sku list
body = json.dumps({"limit": 1000, "offset": 0, "sku": skus}).encode("utf-8")
req = urllib.request.Request(
    "https://api-seller.ozon.ru/v1/analytics/turnover/stocks",
    data=body,
    headers={"Client-Id": "163276", "Api-Key": os.environ.get("OZON_API_KEY", ""), "Content-Type": "application/json"},
    method="POST",
)
resp = None
for attempt in range(5):
    try:
        resp = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
        break
    except urllib.error.HTTPError as e:
        if e.code == 429:
            wait = 8 * (attempt + 1)
            print("429, waiting %ds (attempt %d)" % (wait, attempt + 1))
            time.sleep(wait)
            # rebuild request (data stream consumed)
            req = urllib.request.Request(
                "https://api-seller.ozon.ru/v1/analytics/turnover/stocks",
                data=body,
                headers={"Client-Id": "163276", "Api-Key": os.environ.get("OZON_API_KEY", ""), "Content-Type": "application/json"},
                method="POST",
            )
        else:
            raise
if resp is None:
    raise SystemExit("Rate limited after retries")
items = {str(it["sku"]): it for it in resp.get("items", [])}

out = io.StringIO()
def p(*a): out.write(" ".join(str(x) for x in a) + "\n")

GRADE_RU = {
    "GRADES_GREEN": "зелёный (быстро продаётся)",
    "GRADES_YELLOW": "жёлтый (норма)",
    "GRADES_RED": "красный (много, продаётся медленно)",
    "GRADES_CRITICAL": "КРИТИЧНО (переизбыток)",
    "GRADES_NOSALES": "НЕТ ПРОДАЖ",
    "GRADES_NONE": "нет данных",
    None: "нет данных",
}

p("Артикул".ljust(14), "Ост.".rjust(5), "Прод/день".rjust(9), "Хватит,дн".rjust(9), "Оценка")
p("-"*90)
dead = 0
for sku in sorted(sku_free, key=lambda x: -sku_free[x]):
    if not sku or sku == "None": continue
    it = items.get(sku, {})
    ads = it.get("ads")
    idc = it.get("idc")
    grade = it.get("idc_grade")
    free = sku_free[sku]
    art = sku_art.get(sku, "?")
    g = GRADE_RU.get(grade, str(grade))
    if grade in ("GRADES_NOSALES", None, "GRADES_NONE") or (ads in (0, 0.0, None)):
        dead += free
    adss = "-" if ads is None else str(ads)
    idcs = "-" if idc is None else str(idc)
    p(str(art).ljust(14), str(free).rjust(5), adss.rjust(9), idcs.rjust(9), " ", g)

p("-"*90)
p("Единиц без продаж / нулевой ADS (кандидаты на вывоз):", dead, "из", sum(sku_free.values()))
open(OUT, "w", encoding="utf-8").write(out.getvalue())
print("OK items_returned=%d dead_units=%d total=%d" % (len(items), dead, sum(sku_free.values())))
