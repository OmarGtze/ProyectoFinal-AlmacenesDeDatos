"""Genera un almacén de datos piloto, reproducible y explícitamente sintético."""
import csv
import json
import random
import sqlite3
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Archivos" / "data-2026-10-19.csv"
DB = ROOT / "data" / "piloto_sintetico.sqlite"
TEMP_DB = ROOT / "data" / "piloto_sintetico.tmp.sqlite"
SUMMARY = ROOT / "data" / "resumen_sintetico.json"
SEED = 20261020
MONTH_FACTOR = (0, .90, .85, .82, .95, 1.14, 1.17, 1.08, 1.00, .90, .88, .95, 1.08)
SLOTS = ((13, .75), (17, 1.00), (20, 1.25))
MOVIES = (
    ("P01", "Horizonte de otoño", 1.18),
    ("P02", "El último faro", 1.08),
    ("P03", "Cartas de medianoche", .91),
    ("P04", "Marea de cristal", 1.04),
    ("P05", "La ciudad invisible", 1.12),
    ("P06", "Ruta al amanecer", .87),
    ("P07", "Órbita azul", 1.23),
    ("P08", "El jardín del tiempo", .97),
)
PRODUCTS = (
    ("palomitas", "Palomitas", 95, .38),
    ("bebidas", "Bebidas", 65, .47),
    ("otros", "Otros alimentos", 72, .20),
)

randomizer = random.Random(SEED)
source_rows = []
with SOURCE.open(encoding="utf-8-sig", newline="") as file:
    for row in csv.DictReader(file):
        name = row["comp_cine_nombre"].casefold()
        if not ("cinépolis" in name or "cinepolis" in name):
            continue
        if row["comp_cine_adscripcion"] != "Cinépolis de México, S.A. de C.V.":
            continue
        source_rows.append(row)

complexes = sorted(source_rows, key=lambda row: int(row["comp_cine_id"]))
assert len(complexes) == 477
assert len({row["comp_cine_id"] for row in complexes}) == 477

DB.parent.mkdir(parents=True, exist_ok=True)
if TEMP_DB.exists():
    TEMP_DB.unlink()
connection = sqlite3.connect(TEMP_DB)
connection.execute("PRAGMA journal_mode = OFF")
connection.execute("PRAGMA synchronous = OFF")
connection.execute("PRAGMA foreign_keys = ON")
connection.executescript("""
CREATE TABLE dim_fecha (
  fecha_id INTEGER PRIMARY KEY, fecha TEXT NOT NULL, anio INTEGER NOT NULL,
  mes INTEGER NOT NULL, dia_semana INTEGER NOT NULL, fin_semana INTEGER NOT NULL
);
CREATE TABLE dim_complejo (
  complejo_id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, estado TEXT NOT NULL,
  municipio TEXT NOT NULL, pantallas_directorio INTEGER NOT NULL, origen TEXT NOT NULL
);
CREATE TABLE dim_sala_modelada (
  sala_id INTEGER PRIMARY KEY, complejo_id INTEGER NOT NULL REFERENCES dim_complejo(complejo_id),
  numero_modelado INTEGER NOT NULL, capacidad_supuesta INTEGER NOT NULL,
  formato_supuesto TEXT NOT NULL, UNIQUE(complejo_id, numero_modelado)
);
CREATE TABLE dim_pelicula_ficticia (
  pelicula_id TEXT PRIMARY KEY, titulo_ficticio TEXT NOT NULL
);
CREATE TABLE hecho_funcion_sintetica (
  funcion_id INTEGER PRIMARY KEY, fecha_id INTEGER NOT NULL REFERENCES dim_fecha(fecha_id),
  complejo_id INTEGER NOT NULL REFERENCES dim_complejo(complejo_id),
  sala_id INTEGER NOT NULL REFERENCES dim_sala_modelada(sala_id),
  pelicula_id TEXT NOT NULL REFERENCES dim_pelicula_ficticia(pelicula_id),
  hora INTEGER NOT NULL, capacidad INTEGER NOT NULL, boletos INTEGER NOT NULL,
  precio_promedio_mxn INTEGER NOT NULL, ingreso_taquilla_mxn INTEGER NOT NULL,
  tipo_dato TEXT NOT NULL CHECK(tipo_dato = 'sintetico'),
  CHECK(boletos >= 0 AND boletos <= capacidad)
);
CREATE TABLE hecho_dulceria_diaria_sintetica (
  fecha_id INTEGER NOT NULL REFERENCES dim_fecha(fecha_id),
  complejo_id INTEGER NOT NULL REFERENCES dim_complejo(complejo_id),
  categoria TEXT NOT NULL, unidades INTEGER NOT NULL,
  precio_supuesto_mxn INTEGER NOT NULL, ingreso_mxn INTEGER NOT NULL,
  tipo_dato TEXT NOT NULL CHECK(tipo_dato = 'sintetico'),
  PRIMARY KEY(fecha_id, complejo_id, categoria)
);
CREATE INDEX idx_funcion_fecha ON hecho_funcion_sintetica(fecha_id);
CREATE INDEX idx_funcion_complejo ON hecho_funcion_sintetica(complejo_id);
""")
connection.executemany(
    "INSERT INTO dim_pelicula_ficticia VALUES (?,?)",
    [(code, title) for code, title, _ in MOVIES],
)
connection.executemany(
    "INSERT INTO dim_complejo VALUES (?,?,?,?,?,?)",
    [(int(row["comp_cine_id"]), row["comp_cine_nombre"], row["nom_ent"],
      row["nom_mun"], int(row["comp_cine_npantallas"]), "SIC: CSV descargado 2026-10-19")
     for row in complexes],
)

rooms = {}
for row in complexes:
    complex_id = int(row["comp_cine_id"])
    rooms[complex_id] = []
    room_templates = ((1, 100, "Tradicional"),
                      (2, 140, "Tradicional"),
                      (3, 180, "Formato especial"))
    registered_screens = int(row["comp_cine_npantallas"])
    modeled_rooms = min(3, max(1, registered_screens))
    for number, capacity, format_name in room_templates[:modeled_rooms]:
        room_id = complex_id * 10 + number
        connection.execute("INSERT INTO dim_sala_modelada VALUES (?,?,?,?,?)",
                           (room_id, complex_id, number, capacity, format_name))
        rooms[complex_id].append((room_id, capacity, format_name))

monthly = defaultdict(lambda: {"funciones": 0, "boletos": 0, "taquilla_mxn": 0,
                                "capacidad": 0, "dulceria_mxn": 0})
date_cursor = date(2025, 1, 1)
end = date(2026, 1, 1)
function_id = 0
candy_count = 0
while date_cursor < end:
    function_rows, candy_rows = [], []
    date_id = int(date_cursor.strftime("%Y%m%d"))
    weekend = int(date_cursor.weekday() >= 5)
    connection.execute("INSERT INTO dim_fecha VALUES (?,?,?,?,?,?)",
                       (date_id, date_cursor.isoformat(), 2025, date_cursor.month,
                        date_cursor.weekday(), weekend))
    for row in complexes:
        complex_id = int(row["comp_cine_id"])
        daily_tickets = 0
        for room_id, capacity, format_name in rooms[complex_id]:
            for hour, slot_factor in SLOTS:
                movie = MOVIES[(date_cursor.toordinal() + room_id + hour) % len(MOVIES)]
                demand = (.33 * MONTH_FACTOR[date_cursor.month] *
                          (1.32 if weekend else 1.0) * slot_factor * movie[2])
                occupancy = min(.97, max(.04, demand + randomizer.gauss(0, .075)))
                tickets = min(capacity, round(capacity * occupancy))
                price = (75 if format_name == "Tradicional" else 115) + (8 if weekend else 0)
                revenue = tickets * price
                function_id += 1
                function_rows.append((function_id, date_id, complex_id, room_id,
                                      movie[0], hour, capacity, tickets, price, revenue, "sintetico"))
                daily_tickets += tickets
                month = monthly[date_cursor.month]
                month["funciones"] += 1
                month["boletos"] += tickets
                month["taquilla_mxn"] += revenue
                month["capacidad"] += capacity
        for code, _, price, attach_rate in PRODUCTS:
            units = max(0, round(randomizer.gauss(daily_tickets * attach_rate,
                                                  max(2, daily_tickets * .035))))
            revenue = units * price
            candy_rows.append((date_id, complex_id, code, units, price, revenue, "sintetico"))
            monthly[date_cursor.month]["dulceria_mxn"] += revenue
    connection.executemany("INSERT INTO hecho_funcion_sintetica VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                           function_rows)
    connection.executemany("INSERT INTO hecho_dulceria_diaria_sintetica VALUES (?,?,?,?,?,?,?)",
                           candy_rows)
    candy_count += len(candy_rows)
    date_cursor += timedelta(days=1)

connection.commit()
assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
expected_functions = sum(len(value) for value in rooms.values()) * 365 * len(SLOTS)
expected_candy = len(complexes) * 365 * len(PRODUCTS)
assert function_id == expected_functions
assert candy_count == expected_candy
assert connection.execute("SELECT COUNT(*) FROM hecho_funcion_sintetica").fetchone()[0] == expected_functions
assert connection.execute("SELECT COUNT(*) FROM hecho_dulceria_diaria_sintetica").fetchone()[0] == expected_candy
connection.close()
TEMP_DB.replace(DB)

SUMMARY.write_text(json.dumps({
    "tipo_dato": "sintetico",
    "semilla": SEED,
    "periodo": "2025",
    "complejos_modelados": len(complexes),
    "salas_modeladas": sum(len(value) for value in rooms.values()),
    "complejos_sin_pantallas_registradas": sum(int(row["comp_cine_npantallas"]) == 0 for row in complexes),
    "salas_modeladas_por_complejo": "entre 1 y 3",
    "funciones_por_sala_y_dia": 3,
    "meses": [{"mes": month, **monthly[month]} for month in range(1, 13)],
}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Generadas {function_id:,} funciones y {candy_count:,} filas de dulcería para {len(complexes)} complejos.")
print(f"Base: {DB}")
