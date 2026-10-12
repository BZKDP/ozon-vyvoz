import os
# -*- coding: utf-8 -*-
# Пробник эндпоинтов Ozon Seller API по вывозу/утилизации
import json, urllib.request, urllib.error

CLIENT_ID = "163276"
API_KEY = os.environ.get("OZON_API_KEY", "")
BASE = "https://api-seller.ozon.ru"

HEADERS = {
    "Client-Id": CLIENT_ID,
    "Api-Key": API_KEY,
    "Content-Type": "application/json",
}

def call(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            payload = e.read().decode()
        except Exception:
            payload = ""
        return e.code, payload
    except Exception as e:
        return -1, str(e)

DATE_FROM = "2025-11-01T00:00:00Z"
DATE_TO = "2026-03-31T23:59:59Z"

candidates = [
    ("/v1/removal/from-stock/list", {"filter": {"date_from": DATE_FROM, "date_to": DATE_TO}, "limit": 500}),
    ("/v1/removal/from-supply/list", {"filter": {"date_from": DATE_FROM, "date_to": DATE_TO}, "limit": 500}),
    ("/v1/disposal/report/list", {"filter": {"date_from": DATE_FROM, "date_to": DATE_TO}, "limit": 100}),
    ("/v1/returns/company/fbo", {"filter": {"status": "Utilized"}, "limit": 100, "offset": 0}),
]

for path, body in candidates:
    status, resp = call(path, body)
    print("=" * 70)
    print(path, "->", status)
    s = resp if isinstance(resp, str) else json.dumps(resp, ensure_ascii=False)
    print(s[:1500])
