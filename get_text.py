# -*- coding: utf-8 -*-
"""Снять текст текущей страницы (или таблицы) из Chrome по CDP."""
import sys
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = None
    for pg in ctx.pages:
        if "seller.ozon.ru" in (pg.url or ""):
            page = pg; break
    if not page:
        sys.exit("no ozon page")
    txt = page.evaluate("() => document.body.innerText")
    print(txt)
