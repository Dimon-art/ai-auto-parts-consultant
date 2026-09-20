"""Демо-наполнение БД для ai-auto-parts-consultant.
Создаёт: makes, models, generations, engines, fitments.
Связывает существующие 6 запчастей с двигателями.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("/app/data/parts_catalogs.db")
if not DB_PATH.exists():
    DB_PATH = Path(__file__).resolve().parent / "parts_catalogs.db"

conn = sqlite3.connect(DB_PATH)

# ---- Пересоздаём таблицы, чтобы гарантировать правильные колонки ----
conn.executescript("""
DROP TABLE IF EXISTS fitments;
DROP TABLE IF EXISTS engines;
DROP TABLE IF EXISTS generations;
DROP TABLE IF EXISTS models;
DROP TABLE IF EXISTS makes;

CREATE TABLE makes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY(make_id) REFERENCES makes(id)
);

CREATE TABLE generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    year_start INTEGER NOT NULL,
    year_end INTEGER NOT NULL,
    FOREIGN KEY(model_id) REFERENCES models(id)
);

CREATE TABLE engines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generation_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    code TEXT,
    FOREIGN KEY(generation_id) REFERENCES generations(id)
);

CREATE TABLE fitments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id INTEGER NOT NULL,
    engine_id INTEGER NOT NULL,
    note TEXT,
    FOREIGN KEY(part_id) REFERENCES parts(id),
    FOREIGN KEY(engine_id) REFERENCES engines(id)
);
""")
conn.commit()

# ---- Марки ----
conn.execute("INSERT INTO makes (name) VALUES (?)", ("Volkswagen",))
conn.execute("INSERT INTO makes (name) VALUES (?)", ("Nissan",))
conn.commit()

vw_id = conn.execute("SELECT id FROM makes WHERE name=?", ("Volkswagen",)).fetchone()[0]
ni_id = conn.execute("SELECT id FROM makes WHERE name=?", ("Nissan",)).fetchone()[0]

# ---- Модели ----
conn.execute("INSERT INTO models (make_id, name) VALUES (?, ?)", (vw_id, "Golf"))
conn.execute("INSERT INTO models (make_id, name) VALUES (?, ?)", (ni_id, "Qashqai"))
conn.commit()

golf_id = conn.execute("SELECT id FROM models WHERE name=?", ("Golf",)).fetchone()[0]
qash_id = conn.execute("SELECT id FROM models WHERE name=?", ("Qashqai",)).fetchone()[0]

# ---- Поколения ----
conn.execute("INSERT INTO generations (model_id, name, year_start, year_end) VALUES (?, ?, ?, ?)",
             (golf_id, "Mk7", 2012, 2020))
conn.execute("INSERT INTO generations (model_id, name, year_start, year_end) VALUES (?, ?, ?, ?)",
             (qash_id, "J11", 2014, 2021))
conn.commit()

golf_gen = conn.execute("SELECT id FROM generations WHERE model_id=?", (golf_id,)).fetchone()[0]
qash_gen = conn.execute("SELECT id FROM generations WHERE model_id=?", (qash_id,)).fetchone()[0]

# ---- Двигатели (label вместо name) ----
conn.execute("INSERT INTO engines (generation_id, label, code) VALUES (?, ?, ?)",
             (golf_gen, "1.4 TSI", "CZDA"))
conn.execute("INSERT INTO engines (generation_id, label, code) VALUES (?, ?, ?)",
             (golf_gen, "1.0 TSI", "CHZD"))
conn.execute("INSERT INTO engines (generation_id, label, code) VALUES (?, ?, ?)",
             (qash_gen, "1.2 DIG-T", "HRA2"))
conn.execute("INSERT INTO engines (generation_id, label, code) VALUES (?, ?, ?)",
             (qash_gen, "2.0 CVT", "MR20"))
conn.commit()

engines = {row[1]: row[0] for row in conn.execute("SELECT id, label FROM engines").fetchall()}

# ---- Fitments: связываем все 6 запчастей ----
parts = conn.execute("SELECT id, make, model, name FROM parts").fetchall()

for part_id, make, model, name in parts:
    if make == "Volkswagen" and model == "Golf":
        for eng in ["1.4 TSI", "1.0 TSI"]:
            conn.execute("INSERT INTO fitments (part_id, engine_id, note) VALUES (?, ?, ?)",
                         (part_id, engines[eng], "Подходит для Golf Mk7"))
    elif make == "Nissan" and model == "Qashqai":
        for eng in ["1.2 DIG-T", "2.0 CVT"]:
            conn.execute("INSERT INTO fitments (part_id, engine_id, note) VALUES (?, ?, ?)",
                         (part_id, engines[eng], "Подходит для Qashqai J11"))

conn.commit()

# ---- Отчёт ----
print("=== ГОТОВО ===")
print(f"makes: {conn.execute('SELECT COUNT(*) FROM makes').fetchone()[0]}")
print(f"models: {conn.execute('SELECT COUNT(*) FROM models').fetchone()[0]}")
print(f"generations: {conn.execute('SELECT COUNT(*) FROM generations').fetchone()[0]}")
print(f"engines: {conn.execute('SELECT COUNT(*) FROM engines').fetchone()[0]}")
print(f"fitments: {conn.execute('SELECT COUNT(*) FROM fitments').fetchone()[0]}")
print(f"parts: {conn.execute('SELECT COUNT(*) FROM parts').fetchone()[0]}")
conn.close()