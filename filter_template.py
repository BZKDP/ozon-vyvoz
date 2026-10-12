# -*- coding: utf-8 -*-
"""
Фильтрует скачанный из Ozon шаблон вывоза, оставляя ТОЛЬКО артикулы из
списка босса (Забрать.xlsx / Лист1). Остальные строки удаляются.
Количество не трогаем = вывозим весь остаток по каждой позиции.

Использование:
    python filter_template.py "C:\\path\\to\\Остатки_XX.xlsx"
Если путь не передан — берёт последний Остатки_*.xlsx из Downloads.
Результат: рядом с исходником файл  <имя>_К_ВЫВОЗУ.xlsx
"""
import openpyxl, os, sys, glob

DL = r"."
BOSS = os.path.join(DL, "Забрать.xlsx")
DATA_START = 6  # 1-based: строки 1..5 = шапка Ozon, данные с 6-й

def num(x):
    try: return str(int(round(float(x))))
    except: return None

# --- список босса ---
wb = openpyxl.load_workbook(BOSS, data_only=True)
ws = wb["Лист1"]
boss_arts, boss_skus, boss_names = set(), set(), {}
for r in list(ws.iter_rows(values_only=True))[1:]:
    if not r[1] or (isinstance(r[1], str) and ("ИТОГО" in r[1] or "ещё" in r[1])): continue
    a = str(r[1]).strip().upper(); boss_arts.add(a); boss_names[a] = str(r[9] or "")
    s = num(r[0])
    if s: boss_skus.add(s)

# --- шаблон ---
path = sys.argv[1] if len(sys.argv) > 1 else None
if not path:
    cands = sorted(glob.glob(os.path.join(DL, "Остатки*.xlsx")), key=os.path.getmtime)
    if not cands: print("Не найден Остатки*.xlsx в Downloads"); sys.exit(1)
    path = cands[-1]
print("Шаблон:", path)

tb = openpyxl.load_workbook(path)
t = tb.active

kept, kept_arts = 0, set()
for row in range(t.max_row, DATA_START - 1, -1):
    art = t.cell(row, 3).value  # C = Артикул
    sku = t.cell(row, 1).value  # A = SKU
    a = str(art).strip().upper() if art else ""
    s = num(sku)
    if a in boss_arts or (s and s in boss_skus):
        kept += 1; kept_arts.add(a)
    else:
        t.delete_rows(row, 1)

out = os.path.splitext(path)[0] + "_К_ВЫВОЗУ.xlsx"
tb.save(out)

wh = "?"
for row in range(DATA_START, DATA_START + 1):
    v = t.cell(row, 4).value  # D = Склад отправки (первая оставшаяся строка)
    if v: wh = v
missing = sorted(boss_arts - kept_arts)
print("Склад в шаблоне:", wh)
print("Строк оставлено (совпало с боссом):", kept)
print("Артикулов босса найдено здесь:", len(kept_arts), sorted(kept_arts) or "—")
print("Артикулов босса НЕТ на этом складе:", len(missing))
print("Файл к загрузке:", out if kept else "(пусто — на этом складе/фильтре нет боссовских товаров, НЕ загружай)")
