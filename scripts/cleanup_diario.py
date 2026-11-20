#!/usr/bin/env python3
"""Remove the entry from 2026-11-27 and renumber the diary entries."""

import json
import os

diario_path = "data/diario.json"

# Load the diary
with open(diario_path, "r", encoding="utf-8") as f:
    diario = json.load(f)

# Find and remove the entry with fecha "2026-11-27"
for i, entrada in enumerate(diario["entradas"]):
    if entrada.get("fecha") == "2026-11-27":
        print(f"🗑️ Removing entry Nº {entrada.get('numero')} ({entrada['fecha']})")
        del diario["entradas"][i]
        break

# Recalculate the numbers: the first entry is 1, second is 2, etc.
for i, entrada in enumerate(diario["entradas"]):
    diario["entradas"][i]["numero"] = i + 1

# Save the file
with open(diario_path, "w", encoding="utf-8") as f:
    json.dump(diario, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(f"✅ Diary cleaned and renumbered. Total entries: {len(diario['entradas'])}")