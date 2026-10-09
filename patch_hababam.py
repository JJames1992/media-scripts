#!/usr/bin/env python3
"""Patch the one 'imdb_mismatch' row: sheet calls it 'Hababam Sinifi' (a Turkish re-release title);
TMDB resolved it to 'The Chaos Class Failed the Class' (1976), imdb tt0252488. They are the same film.
Update the sheet resolve note and the manifest so the search core stays the TMDB title
(which seeds better) while remembering the sheet title as an alt."""
import json

import openpyxl

XLSX = "C:/Users/jonat/OneDrive/Movies.xlsx"
MANIFEST = "C:/Users/jonat/media-scripts/media_catalog.json"

wb = openpyxl.load_workbook(XLSX)
ws = wb["To See"]
for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
    if not row or not row[0]:
        continue
    if row[0].strip() == "Hababam Sinifi":
        # note col = 14 (index 13)
        ws.cell(row=i, column=14, value="Same film as TMDB 'The Chaos Class Failed the Class' (Turkish re-release title)")
        ws.cell(row=i, column=13, value="imdb (alt title)")
        print(f"Patched row {i}")
wb.save(XLSX)

with open(MANIFEST, encoding="utf-8") as f:
    m = json.load(f)
for r in m:
    if r.get("sheet_title") == "Hababam Sinifi":
        r["alt_title"] = "Hababam Sinifi"
        r["resolve"] = "imdb"
        r["note"] = "TMDB title differs from sheet title but same film (Turkish re-release); use search_core for seeding"
        r["search_core"] = "The Chaos Class Failed the Class (1976)"
        r["tmdb_id"] = 31534
        print("Patched manifest record:", r["search_core"])
with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(m, f, indent=1, ensure_ascii=False)

# sanity: re-verify the row reads back
wb2 = openpyxl.load_workbook(XLSX)
ws2 = wb2["To See"]
for i, row in enumerate(ws2.iter_rows(min_row=2, values_only=True), start=2):
    if not row or not row[0]:
        continue
    if row[0].strip() == "Hababam Sinifi":
        print("Verification:", [row[0], row[5], row[6], row[7], row[8], row[10], row[12], row[13]])
