# -*- coding: utf-8 -*-
"""Клик по элементу с текстом (из argv, UTF-8) на активной ozon-вкладке.
python -X utf8 step.py click "Товары со стока"
python -X utf8 step.py next            # кнопка Далее
python -X utf8 step.py text            # вывести текст страницы
"""
import sys
from playwright.sync_api import sync_playwright

cmd = sys.argv[1]
arg = sys.argv[2] if len(sys.argv) > 2 else ""

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = None
    for pg in ctx.pages:
        if "seller.ozon.ru" in (pg.url or ""):
            page = pg; break
    if not page:
        sys.exit("no ozon page")
    page.set_default_timeout(8000)
    if cmd == "click":
        loc = page.get_by_text(arg, exact=False).first
        loc.scroll_into_view_if_needed()
        loc.click()
        print("clicked:", arg)
    elif cmd == "next":
        page.get_by_role("button", name="Далее").first.click()
        print("clicked next")
    elif cmd == "text":
        print(page.evaluate("() => document.body.innerText")[:4000])
    page.wait_for_timeout(1500)
