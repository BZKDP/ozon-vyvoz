# -*- coding: utf-8 -*-
# Анализ: через сколько дней утилизируются возвраты (Ozon)
import json, sys, csv
from datetime import datetime, timezone
from collections import Counter

CLIENT_ID = sys.argv[1] if len(sys.argv) > 1 else "163276"
SRC = f"returns_raw_{CLIENT_ID}.json"
OUT = f"Утилизация_{CLIENT_ID}_ноя25_мар26.csv"

items = json.load(open(SRC, encoding="utf-8"))

def parse(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None

P_FROM = datetime(2025, 11, 1, tzinfo=timezone.utc)
P_TO = datetime(2026, 3, 31, 23, 59, 59, tzinfo=timezone.utc)

# общая картина по статусам
c = Counter()
for it in items:
    st = (it.get("visual") or {}).get("status") or {}
    c[st.get("sys_name") or "?"] += 1
print("Все статусы за всю историю:", dict(c.most_common()))

rows = []
for it in items:
    vis = it.get("visual") or {}
    st = (vis.get("status") or {}).get("sys_name")
    if st != "Utilized":
        continue
    util_dt = parse(vis.get("change_moment"))
    if not util_dt or not (P_FROM <= util_dt <= P_TO):
        continue
    stor = it.get("storage") or {}
    log = it.get("logistic") or {}
    prod = it.get("product") or {}
    arrived = parse(stor.get("arrived_moment"))
    ret_date = parse(log.get("return_date"))
    tarif = parse(stor.get("tariffication_first_date"))
    base = arrived or ret_date or tarif
    days = (util_dt - base).days if base else None
    rows.append({
        "posting_number": it.get("posting_number"),
        "offer_id": prod.get("offer_id"),
        "name": (prod.get("name") or "")[:80],
        "schema": it.get("schema"),
        "return_date": ret_date.date().isoformat() if ret_date else "",
        "arrived_on_wh": arrived.date().isoformat() if arrived else "",
        "utilized_at": util_dt.date().isoformat(),
        "days_to_util": days,
        "storage_days": stor.get("days"),
        "util_sum": (stor.get("utilization_sum") or {}).get("price"),
        "price": (prod.get("price") or {}).get("price"),
    })

rows.sort(key=lambda r: r["utilized_at"])
with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["-"], delimiter=";")
    w.writeheader()
    w.writerows(rows)

print(f"\nУтилизировано в период 01.11.2025–31.03.2026: {len(rows)} шт.")
vals = [r["days_to_util"] for r in rows if r["days_to_util"] is not None]
if vals:
    vals.sort()
    print(f"Дней от прибытия до утилизации: мин {vals[0]}, медиана {vals[len(vals)//2]}, средн {sum(vals)/len(vals):.0f}, макс {vals[-1]}")
    by_month = Counter(r["utilized_at"][:7] for r in rows)
    print("По месяцам:", dict(sorted(by_month.items())))
print("CSV:", OUT)

# также посмотрим прогнозные даты утилизации (ещё не утилизированные)
fc = []
for it in items:
    stor = it.get("storage") or {}
    f_dt = parse(stor.get("utilization_forecast_date"))
    st = ((it.get("visual") or {}).get("status") or {}).get("sys_name")
    if f_dt and st != "Utilized":
        fc.append((f_dt.date().isoformat(), st))
print(f"\nС прогнозной датой утилизации (не утилизированы): {len(fc)}")
for d, s in sorted(fc)[:10]:
    print(" ", d, s)
