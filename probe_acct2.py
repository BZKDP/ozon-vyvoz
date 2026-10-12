import os
# -*- coding: utf-8 -*-
import json, urllib.request, urllib.error, time, collections, io, os
import openpyxl

CID = "2843272"; KEY = os.environ.get("OZON_API_KEY", "")
OUTDIR = r"."
REPORT = os.path.join(OUTDIR, "acct2_report.txt")

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

def num(x):
    try: return int(round(float(x)))
    except: return None

def cluster_of(wh):
    w = (wh or "").upper()
    T = [("Москва, МО",["ПУШКИНО","ДОМОДЕД","ПЕТРОВСК","ХОРУГВИНО","ЖУКОВСК","ГРИВНО","НОГИНСК","КОЛЕД","СОФЬИНО","ТВЕР","ТУЛА","РЯЗАН","КАЛУГ","ВЛАДИМИР","ЯРОСЛАВ","ОРЕХОВ","ЭЛЕКТРО","МОСК"]),
         ("Санкт-Петербург и СЗО",["СПБ","ПЕТЕРБУРГ","ПАРГОЛОВ","ШУШАР","БУГРЫ","КОЛПИНО"]),
         ("Приволжье (Казань)",["КАЗАН","ЗЕЛЕНОДОЛЬ"]),
         ("Приволжье (Самара)",["САМАР","ТОЛЬЯТ"]),
         ("Приволжье (Уфа)",["УФА"]),
         ("Приволжье (Н.Новгород)",["НИЖН"]),
         ("Приволжье (Пермь)",["ПЕРМ"]),
         ("Урал (Екатеринбург)",["ЕКАТЕРИН","ЕКБ","БЕРЕЗОВ","ТЮМЕН"]),
         ("Сибирь (Новосибирск)",["НОВОСИБ","КОЛЬЦОВ","ОМСК","КРАСНОЯР","БАРНАУЛ"]),
         ("Дальний Восток",["ХАБАРОВ","ВЛАДИВОСТ","АРТЕМ"]),
         ("Юг (Ростов)",["РОСТОВ","БАТАЙСК","АКСАЙ"]),
         ("Юг (Краснодар)",["КРАСНОДАР","АДЫГЕ"]),
         ("Юг (Волгоград)",["ВОЛГОГРАД"]),
         ("Черноземье (Воронеж)",["ВОРОНЕЖ"]),
         ("Калининград",["КАЛИНИНГРАД"]),
         ("Зарубеж (KZ/BY)",["АЛМАТ","АСТАНА","МИНСК"]) ]
    for name, keys in T:
        if any(k in w for k in keys): return name
    return "Прочее: "+(wh or "?")

# --- boss list ---
wb = openpyxl.load_workbook(r"Забрать.xlsx", data_only=True)
ws = wb["Лист1"]
boss = []
for r in list(ws.iter_rows(values_only=True))[1:]:
    if not r[1] or (isinstance(r[1], str) and ("ИТОГО" in r[1] or "ещё" in r[1])): continue
    boss.append(dict(sku=num(r[0]), art=str(r[1]).strip().upper(), qty=num(r[2]) or 0, name=str(r[9] or "")))
boss_arts = {b["art"] for b in boss}
boss_skus = {str(b["sku"]) for b in boss if b["sku"]}

out = io.StringIO()
def p(*a): out.write(" ".join("" if x is None else str(x) for x in a) + "\n")

# --- acct2 stock_on_warehouses ---
resp = api("/v2/analytics/stock_on_warehouses", {"limit": 1000, "offset": 0, "warehouse_type": "ALL"})
rows = resp.get("result", {}).get("rows", [])
json.dump(rows, open(os.path.join(OUTDIR, "stock2_raw.json"), "w", encoding="utf-8"), ensure_ascii=False)
p("Аккаунт 2843272: строк в stock_on_warehouses:", len(rows))
p("Всего free_to_sell в аккаунте 2843272:", sum(int(r.get("free_to_sell_amount") or 0) for r in rows))

stock_art_sku = {}   # article -> sku
stock_by_art = collections.Counter()
for r in rows:
    a = str(r.get("item_code")).strip().upper()
    stock_by_art[a] += int(r.get("free_to_sell_amount") or 0)
    stock_art_sku[a] = r.get("sku")
acct2_stock_arts = set(stock_by_art)
acct2_stock_skus = set(str(r.get("sku")) for r in rows)

# --- acct2 full catalog (incl archived) via product/list ---
cat_offers = set()
last_id = ""
for _ in range(20):
    pr = api("/v3/product/list", {"filter": {"visibility": "ALL"}, "last_id": last_id, "limit": 1000})
    res = pr.get("result", {})
    items = res.get("items", [])
    for it in items:
        if it.get("offer_id"): cat_offers.add(str(it["offer_id"]).strip().upper())
    last_id = res.get("last_id", "")
    if len(items) < 1000: break
p("Аккаунт 2843272: всего товаров в каталоге (вкл. архив):", len(cat_offers))
p("")

# --- matching ---
in_stock = sorted(boss_arts & acct2_stock_arts)
in_cat   = sorted(boss_arts & cat_offers)
sku_stock = sorted(boss_skus & acct2_stock_skus)
p("="*80); p("СВЕРКА СПИСКА БОССА С АККАУНТОМ 2843272"); p("="*80)
p("Боссовских артикулов ВСЕГО:", len(boss_arts))
p("  -> найдено в остатках (free_to_sell) 2843272:", len(in_stock), in_stock or "—")
p("  -> найдено в КАТАЛОГЕ 2843272 (вкл. снятые/архив):", len(in_cat), in_cat or "—")
p("  -> совпало по SKU в остатках:", len(sku_stock), sku_stock or "—")
p("")
missing_all = sorted(boss_arts - cat_offers - acct2_stock_arts)
p("Артикулов босса, которых НЕТ ни в остатках, ни в каталоге 2843272:", len(missing_all), missing_all or "—")
p("")

# --- per-cluster breakdown of boss items that ARE in acct2 stock ---
p("="*80); p("РАЗБИВКА ПО КЛАСТЕРАМ (боссовские товары, что видны в остатках 2843272)"); p("="*80)
cl_units = collections.Counter()
cl_art = collections.defaultdict(lambda: collections.Counter())
found_units = 0
for r in rows:
    a = str(r.get("item_code")).strip().upper()
    if a not in boss_arts and str(r.get("sku")) not in boss_skus: continue
    q = int(r.get("free_to_sell_amount") or 0)
    cl = cluster_of(r.get("warehouse_name"))
    cl_units[cl] += q; cl_art[cl][a] += q; found_units += q
p("Единиц боссовских товаров видно в остатках 2843272:", found_units)
for cl in sorted(cl_units, key=lambda x: -cl_units[x]):
    p("  %-26s %5d шт" % (cl[:26], cl_units[cl]))
p("")

open(REPORT, "w", encoding="utf-8").write(out.getvalue())
print("OK acct2_rows=%d free=%d catalog=%d | boss_in_stock=%d boss_in_catalog=%d boss_units_seen=%d" % (
    len(rows), sum(int(r.get('free_to_sell_amount') or 0) for r in rows), len(cat_offers),
    len(in_stock), len(in_cat), found_units))
