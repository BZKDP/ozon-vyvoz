import os
# -*- coding: utf-8 -*-
# Выгрузка отчётов о вывозе/утилизации Ozon (со стока и с поставки) за период
import json, urllib.request, urllib.error, sys

CLIENT_ID = sys.argv[1] if len(sys.argv) > 1 else "163276"
API_KEY = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("OZON_API_KEY", "")
OUT = sys.argv[3] if len(sys.argv) > 3 else f"util_raw_{CLIENT_ID}.json"
BASE = "https://api-seller.ozon.ru"

HEADERS = {"Client-Id": CLIENT_ID, "Api-Key": API_KEY, "Content-Type": "application/json"}

def call(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

PERIODS = [("2025-11-01", "2026-01-31"), ("2026-02-01", "2026-03-31")]

def pull(path):
    items = []
    for date_from, date_to in PERIODS:
        last_id = ""
        while True:
            body = {"date_from": date_from, "date_to": date_to, "limit": 500}
            if last_id:
                body["last_id"] = last_id
            status, resp = call(path, body)
            if status != 200:
                print(f"{path} [{date_from}..{date_to}] -> HTTP {status}: {str(resp)[:500]}")
                break
            if isinstance(resp, dict):
                lst = resp.get("returns_summary_report_rows") or resp.get("rows") or resp.get("items") or resp.get("result") or []
                if isinstance(lst, dict):
                    lst = lst.get("rows") or lst.get("items") or []
            else:
                lst = []
            items.extend(lst)
            print(f"{path} [{date_from}..{date_to}]: +{len(lst)} (всего {len(items)})")
            last_id = resp.get("last_id") if isinstance(resp, dict) else None
            if not lst or not last_id:
                if not lst and isinstance(resp, dict):
                    print("Пустой ответ, ключи:", list(resp.keys()), json.dumps(resp, ensure_ascii=False)[:600])
                break
    return items

data = {
    "from_stock": pull("/v1/removal/from-stock/list"),
    "from_supply": pull("/v1/removal/from-supply/list"),
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
print("Сохранено:", OUT)
print("Со стока:", len(data["from_stock"]), "| С поставки:", len(data["from_supply"]))
if data["from_stock"]:
    print("Пример записи:", json.dumps(data["from_stock"][0], ensure_ascii=False)[:1200])
