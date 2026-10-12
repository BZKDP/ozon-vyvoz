import os
# -*- coding: utf-8 -*-
# Поиск утилизированных возвратов через /v1/returns/list
import json, urllib.request, urllib.error, sys

CLIENT_ID = sys.argv[1] if len(sys.argv) > 1 else "163276"
API_KEY = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("OZON_API_KEY", "")
BASE = "https://api-seller.ozon.ru"
HEADERS = {"Client-Id": CLIENT_ID, "Api-Key": API_KEY, "Content-Type": "application/json"}

def call(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

items, last_id = [], 0
while True:
    body = {
        "filter": {"created_at": {"time_from": "2025-11-01T00:00:00Z", "time_to": "2026-03-31T23:59:59Z"}},
        "limit": 500,
        "last_id": last_id,
    }
    status, resp = call("/v1/returns/list", body)
    if status != 200:
        print("HTTP", status, str(resp)[:600])
        break
    lst = resp.get("returns", [])
    items.extend(lst)
    print(f"+{len(lst)} (всего {len(items)})")
    if not resp.get("has_next") or not lst:
        break
    last_id = lst[-1].get("id", 0)

with open(f"returns_raw_{CLIENT_ID}.json", "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=1)

# статистика по статусам
from collections import Counter
c = Counter()
for it in items:
    vs = it.get("visual_status") or {}
    name = vs.get("display_name") or vs.get("sys_name") or str(vs)
    c[name] += 1
print("Статусы:", dict(c))
if items:
    print("Пример:", json.dumps(items[0], ensure_ascii=False)[:1500])
