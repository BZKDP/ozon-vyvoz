# -*- coding: utf-8 -*-
"""Пульт управления Chrome по CDP (порт 9222), минуя MCP.
python -X utf8 cdp.py <cmd> [args]
  url                     список вкладок
  shot                    скрин активной ozon-вкладки -> shot.png
  goto <url>              перейти + скрин
  snap                    список кликабельных элементов (индекс|тег|текст) -> _els.json
  clicki <N>              клик по элементу N из последнего snap (по координатам)
  clickxy <x> <y>         клик по координатам
  scroll <dy>             прокрутка
  back                    назад
  file <path>             прикрепить файл в первый видимый input[type=file]
  wait <ms>               подождать + скрин
"""
import sys, json
from playwright.sync_api import sync_playwright

BASE = r"."
SHOT = BASE + r"\shot.png"
ELS  = BASE + r"\_els.json"
CDP  = "http://127.0.0.1:9222"

def pick_page(ctx):
    for pg in ctx.pages:
        if "seller.ozon.ru" in (pg.url or ""):
            return pg
    return ctx.pages[0] if ctx.pages else None

def do_snap(page):
    sel = "button, a, [role=button], [role=tab], [role=checkbox], [role=radio], input, label, [role=menuitem]"
    els = page.query_selector_all(sel)
    out = []
    for e in els:
        try:
            if not e.is_visible():
                continue
            bb = e.bounding_box()
            if not bb or bb["width"] < 3 or bb["height"] < 3:
                continue
            tag = e.evaluate("el=>el.tagName")
            txt = "" if tag == "INPUT" else (e.inner_text() or "")
            txt = txt.strip().replace("\n", " ")[:70]
            ph = e.get_attribute("placeholder") or ""
            out.append({"i": len(out), "x": bb["x"]+bb["width"]/2, "y": bb["y"]+bb["height"]/2,
                        "t": txt or ph, "tag": tag})
        except Exception:
            pass
    json.dump(out, open(ELS, "w", encoding="utf-8"), ensure_ascii=False)
    for o in out:
        print(o["i"], "|", o["tag"], "|", o["t"])

def main():
    a = sys.argv[1:]
    cmd = a[0] if a else "shot"
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(CDP)
        ctx = b.contexts[0]
        page = pick_page(ctx)
        if cmd == "url":
            for i, pg in enumerate(ctx.pages):
                print(i, "|", pg.url)
            return
        if not page:
            print("НЕТ ВКЛАДОК"); return
        page.bring_to_front()
        if cmd == "goto":
            page.goto(a[1], wait_until="domcontentloaded"); page.wait_for_timeout(2800)
        elif cmd == "snap":
            do_snap(page); page.screenshot(path=SHOT); print("URL:", page.url); return
        elif cmd == "clicki":
            o = json.load(open(ELS, encoding="utf-8"))[int(a[1])]
            page.mouse.click(o["x"], o["y"]); page.wait_for_timeout(1800)
        elif cmd == "clickxy":
            page.mouse.click(float(a[1]), float(a[2])); page.wait_for_timeout(1600)
        elif cmd == "clicktext":
            page.get_by_text(a[1], exact=False).first.click(timeout=6000); page.wait_for_timeout(2500)
        elif cmd == "clickrole":
            name = open(BASE + r"\_cmd.txt", encoding="utf-8").read().strip()
            page.get_by_role("button", name=name, exact=False).first.click(timeout=8000); page.wait_for_timeout(3000)
        elif cmd == "clicktf":
            name = open(BASE + r"\_cmd.txt", encoding="utf-8").read().strip()
            page.get_by_text(name, exact=False).first.click(timeout=8000); page.wait_for_timeout(3000)
        elif cmd == "vp":
            print("VP", page.evaluate("()=>[window.innerWidth,window.innerHeight]")); return
        elif cmd == "eval":
            print(json.dumps(page.evaluate(a[1]), ensure_ascii=False)); return
        elif cmd == "find":
            js = ("(q)=>{const n=[...document.querySelectorAll('a,td,div,span,button')]"
                  ".find(e=>e.textContent && e.textContent.trim()===q);"
                  "if(!n)return null;const r=n.getBoundingClientRect();"
                  "return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),tag:n.tagName};}")
            print(json.dumps(page.evaluate(js, a[1]), ensure_ascii=False)); return
        elif cmd == "scroll":
            page.mouse.wheel(0, int(a[1])); page.wait_for_timeout(800)
        elif cmd == "back":
            page.go_back(); page.wait_for_timeout(1800)
        elif cmd == "file":
            inp = page.query_selector("input[type=file]")
            inp.set_input_files(a[1]); page.wait_for_timeout(2500)
        elif cmd == "wait":
            page.wait_for_timeout(int(a[1]))
        elif cmd == "press":
            page.keyboard.press(a[1]); page.wait_for_timeout(1200)
        elif cmd == "pvzsearch":
            text = open(BASE + r"\_cmd.txt", encoding="utf-8").read().strip()
            box = page.get_by_placeholder("Название или адрес точки").first
            box.click(); box.fill(text); page.wait_for_timeout(2000)
            page.keyboard.press("Enter"); page.wait_for_timeout(3000)
        page.screenshot(path=SHOT)
        print("URL:", page.url)

main()
