# -*- coding: utf-8 -*-
# Анализ отчёта вывоза/утилизации со стока (2843272): сроки до утилизации/выдачи
import json, csv
from datetime import datetime
from collections import Counter

SRC = "util_raw_2843272.json"
OUT = "Вывоз_утилизация_2843272_ноя25_мар26.csv"

data = json.load(open(SRC, encoding="utf-8"))
rows = data["from_stock"]

def parse(ts):
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

print("Всего строк:", len(rows))
print("Статусы возврата:", dict(Counter(r.get("return_state") for r in rows)))
print("Статусы коробки:", dict(Counter(r.get("box_state") for r in rows)))
print("Типы стока:", dict(Counter(r.get("stock_type") for r in rows)))
print("С utilization_date:", sum(1 for r in rows if r.get("utilization_date")))
print("С given_out_date:", sum(1 for r in rows if r.get("given_out_date")))

out = []
utisl_days, giveout_days = [], []
for r in rows:
    created = parse(r.get("return_created_at"))
    delivery = parse(r.get("delivery_date"))
    given = parse(r.get("given_out_date"))
    util = parse(r.get("utilization_date"))
    d_util = (util - created).days if util and created else None
    d_given = (given - created).days if given and created else None
    if d_util is not None:
        utisl_days.append(d_util)
    if d_given is not None:
        giveout_days.append(d_given)
    out.append({
        "offer_id": r.get("offer_id"),
        "name": (r.get("name") or "")[:70],
        "qty": r.get("quantity_for_return"),
        "return_id": r.get("return_id"),
        "stock_type": r.get("stock_type"),
        "return_state": r.get("return_state"),
        "box_state": r.get("box_state"),
        "created": created.date().isoformat() if created else "",
        "delivery_date": delivery.date().isoformat() if delivery else "",
        "given_out": given.date().isoformat() if given else "",
        "utilization": util.date().isoformat() if util else "",
        "days_to_util": d_util,
        "days_to_giveout": d_given,
        "warehouse": r.get("clearing_warehouse_name"),
        "dest": r.get("destination_warehouse_name"),
    })

out.sort(key=lambda x: x["created"])
with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()), delimiter=";")
    w.writeheader()
    w.writerows(out)

def stat(v, label):
    if not v:
        print(label, "— нет данных")
        return
    v = sorted(v)
    print(f"{label}: n={len(v)}, мин {v[0]}, медиана {v[len(v)//2]}, средн {sum(v)/len(v):.0f}, макс {v[-1]}")

stat(utisl_days, "Дней от создания возврата до УТИЛИЗАЦИИ")
stat(giveout_days, "Дней от создания возврата до ВЫДАЧИ продавцу")
print("CSV:", OUT)
