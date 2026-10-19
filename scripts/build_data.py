"""Prepara el directorio público del SIC para el tablero académico."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Archivos" / "data-2026-10-19.csv"
OUTPUT = ROOT / "data" / "complejos.json"
OPERATOR = "Cinépolis de México, S.A. de C.V."

selected = []
with SOURCE.open(encoding="utf-8-sig", newline="") as file:
    for row in csv.DictReader(file):
        name = row["comp_cine_nombre"].casefold()
        if "cinépolis" not in name and "cinepolis" not in name:
            continue
        if row["comp_cine_adscripcion"] != OPERATOR:
            continue
        try:
            screens = int(row["comp_cine_npantallas"])
        except (TypeError, ValueError):
            continue
        selected.append({
            "id": row["comp_cine_id"],
            "name": row["comp_cine_nombre"],
            "state": row["nom_ent"],
            "city": row["nom_mun"],
            "screens": screens,
        })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"{len(selected)} complejos; {sum(row['screens'] for row in selected)} pantallas; {len({row['state'] for row in selected})} entidades")
