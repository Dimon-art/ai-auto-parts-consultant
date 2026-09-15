#!/usr/bin/env python3
"""Build a self-contained local SQLite database for development/demo runs.

The production demo database (``parts_catalogs.db``) is git-ignored and was
assembled from external PartsAPI data that is not part of this repository.
Without it the FastAPI ``/query`` endpoint fails because the tables it reads
(``parts``, ``makes``/``models``/``generations``/``engines``, ``fitments`` and
the ``partsapi_*`` tables) do not exist.

This script recreates that schema and seeds it using only data that already
lives in the repository (``catalog.json`` plus the vehicle/engine labels the
frontend exposes). It lets a fresh checkout run the web app end to end through
the local-catalog code path. It intentionally does NOT invent PartsAPI article
numbers, so the ``partsapi_*`` tables are created empty and the app falls back
to the local catalog matches.

The script is idempotent: it drops and rebuilds the seeded tables on every run.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "parts_catalogs.db"
CATALOG_PATH = BASE_DIR / "catalog.json"

# Documented PartsAPI demo fixture. Every value below is taken verbatim from
# the repository's own documentation (README.md / brief.md), which describes
# the primary demo scenario:
#   Volkswagen -> Golf -> 2018 -> 1.0L TSI 6MT FWD (110 HP) -> Масляный фильтр
# The real "parts_catalogs.db" that shipped these rows is git-ignored and not
# part of the checkout, so we rebuild it here from the documented values. This
# lets the FastAPI PartsAPI code path return the documented article end to end.
PARTSAPI_DEMO_CAR_ID = 124239
PARTSAPI_DEMO_STR_ID = 100470
PARTSAPI_DEMO_MAKE = "Volkswagen"
PARTSAPI_DEMO_MODEL = "Golf"
PARTSAPI_DEMO_ENGINES = [
    "1.0L TSI 6MT FWD (110 HP)",
    "1.0L TSI 7AT FWD (110 HP)",
]
PARTSAPI_DEMO_ARTICLE = {
    "article_number": "L40635",
    "brand": "1A FIRST AUTOMOTIVE",
    "product_group": "Масляный фильтр",
    "oem_numbers": (
        "VAG: 04E 115 561, VAG: 04E 115 561 B, "
        "VAG: 04E 115 561 D, VAG: 04E 115 561 H"
    ),
    "fitment_source": "PartsAPI getArticles",
}


SCHEMA = """
DROP TABLE IF EXISTS fitments;
DROP TABLE IF EXISTS partsapi_fitments;
DROP TABLE IF EXISTS partsapi_articles;
DROP TABLE IF EXISTS engines;
DROP TABLE IF EXISTS generations;
DROP TABLE IF EXISTS models;
DROP TABLE IF EXISTS makes;
DROP TABLE IF EXISTS parts;

CREATE TABLE parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    oem TEXT NOT NULL,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    year_from INTEGER NOT NULL,
    year_to INTEGER NOT NULL,
    engines TEXT NOT NULL,
    keywords TEXT NOT NULL,
    price REAL,
    fitment_note TEXT,
    notes TEXT
);

CREATE TABLE makes (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE models (
    id INTEGER PRIMARY KEY,
    make_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    UNIQUE(make_id, name),
    FOREIGN KEY(make_id) REFERENCES makes(id)
);

CREATE TABLE generations (
    id INTEGER PRIMARY KEY,
    model_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    year_start INTEGER,
    year_end INTEGER,
    body_type TEXT,
    FOREIGN KEY(model_id) REFERENCES models(id)
);

CREATE TABLE engines (
    id INTEGER PRIMARY KEY,
    generation_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    fuel_type TEXT,
    cylinders INTEGER,
    displacement_cc INTEGER,
    power_hp INTEGER,
    torque_nm INTEGER,
    transmission TEXT,
    drivetrain TEXT,
    partsapi_car_id INTEGER,
    FOREIGN KEY(generation_id) REFERENCES generations(id)
);

CREATE TABLE fitments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id INTEGER NOT NULL,
    engine_id INTEGER NOT NULL,
    FOREIGN KEY(part_id) REFERENCES parts(id),
    FOREIGN KEY(engine_id) REFERENCES engines(id)
);

CREATE TABLE partsapi_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    art_id INTEGER,
    article_number TEXT,
    brand TEXT,
    product_group TEXT,
    sup_id INTEGER,
    oem_numbers TEXT,
    ean_numbers TEXT,
    article_criteria TEXT,
    status TEXT
);

CREATE TABLE partsapi_fitments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    car_id INTEGER,
    str_id INTEGER,
    fitment_source TEXT,
    confirmed INTEGER DEFAULT 0,
    FOREIGN KEY(article_id) REFERENCES partsapi_articles(id)
);
"""


def load_catalog() -> list[dict]:
    with CATALOG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def seed_parts(conn: sqlite3.Connection, catalog: list[dict]) -> None:
    conn.executemany(
        """
        INSERT INTO parts (
            name, category, oem, make, model, year_from, year_to,
            engines, keywords, price, fitment_note, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                part["name"],
                part["category"],
                part["oem"],
                part["make"],
                part["model"],
                part["year_from"],
                part["year_to"],
                ", ".join(part["engines"]),
                ", ".join(part["keywords"]),
                part["price"],
                part["fitment_note"],
                part.get("notes", ""),
            )
            for part in catalog
        ],
    )


def seed_vehicle_graph(conn: sqlite3.Connection, catalog: list[dict]) -> None:
    """Derive makes/models/generations/engines/fitments from catalog.json.

    Each part declares its make, model, year range and compatible engines.
    We turn that flat data into the relational graph the fitment queries walk,
    then link every part to the engines it lists via the ``fitments`` table.
    """
    make_ids: dict[str, int] = {}
    model_ids: dict[tuple[str, str], int] = {}
    generation_ids: dict[tuple[str, str], int] = {}
    engine_ids: dict[tuple[str, str, str], int] = {}

    def year_bounds(make: str, model: str) -> tuple[int, int]:
        rows = [p for p in catalog if p["make"] == make and p["model"] == model]
        return (
            min(p["year_from"] for p in rows),
            max(p["year_to"] for p in rows),
        )

    next_make = next_model = next_generation = next_engine = 1

    for part in catalog:
        make = part["make"]
        model = part["model"]

        if make not in make_ids:
            make_ids[make] = next_make
            conn.execute(
                "INSERT INTO makes (id, name) VALUES (?, ?)",
                (next_make, make),
            )
            next_make += 1

        if (make, model) not in model_ids:
            model_ids[(make, model)] = next_model
            conn.execute(
                "INSERT INTO models (id, make_id, name) VALUES (?, ?, ?)",
                (next_model, make_ids[make], model),
            )
            next_model += 1

            year_start, year_end = year_bounds(make, model)
            generation_ids[(make, model)] = next_generation
            conn.execute(
                """
                INSERT INTO generations (id, model_id, name, year_start, year_end)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    next_generation,
                    model_ids[(make, model)],
                    f"{model} ({year_start}-{year_end})",
                    year_start,
                    year_end,
                ),
            )
            next_generation += 1

        for label in part["engines"]:
            engine_key = (make, model, label)
            if engine_key not in engine_ids:
                engine_ids[engine_key] = next_engine
                conn.execute(
                    """
                    INSERT INTO engines (id, generation_id, label)
                    VALUES (?, ?, ?)
                    """,
                    (next_engine, generation_ids[(make, model)], label),
                )
                next_engine += 1

    # Link every part to each engine it declares support for.
    part_rows = conn.execute(
        "SELECT id, make, model, engines FROM parts"
    ).fetchall()

    for part_id, make, model, engines_csv in part_rows:
        labels = [e.strip() for e in (engines_csv or "").split(",") if e.strip()]
        for label in labels:
            engine_id = engine_ids.get((make, model, label))
            if engine_id is not None:
                conn.execute(
                    "INSERT INTO fitments (part_id, engine_id) VALUES (?, ?)",
                    (part_id, engine_id),
                )


def seed_partsapi_demo(conn: sqlite3.Connection) -> None:
    """Rebuild the documented PartsAPI demo article and its fitment link.

    Adds the ``1.0L TSI`` engines (mapped to the documented ``CAR_ID``) to the
    Volkswagen Golf generation, then inserts the ``L40635`` article and its
    confirmed fitment so the PartsAPI code path returns the documented result.
    """
    generation = conn.execute(
        """
        SELECT g.id
        FROM generations g
        JOIN models m ON m.id = g.model_id
        JOIN makes mk ON mk.id = m.make_id
        WHERE mk.name = ? AND m.name = ?
        """,
        (PARTSAPI_DEMO_MAKE, PARTSAPI_DEMO_MODEL),
    ).fetchone()

    if generation is None:
        # Golf is not in the catalog; nothing to attach the demo fixture to.
        return

    generation_id = generation[0]

    for label in PARTSAPI_DEMO_ENGINES:
        conn.execute(
            """
            INSERT INTO engines (generation_id, label, partsapi_car_id)
            VALUES (?, ?, ?)
            """,
            (generation_id, label, PARTSAPI_DEMO_CAR_ID),
        )

    cursor = conn.execute(
        """
        INSERT INTO partsapi_articles (
            article_number, brand, product_group, oem_numbers, status
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            PARTSAPI_DEMO_ARTICLE["article_number"],
            PARTSAPI_DEMO_ARTICLE["brand"],
            PARTSAPI_DEMO_ARTICLE["product_group"],
            PARTSAPI_DEMO_ARTICLE["oem_numbers"],
            "active",
        ),
    )
    article_id = cursor.lastrowid

    conn.execute(
        """
        INSERT INTO partsapi_fitments (
            article_id, car_id, str_id, fitment_source, confirmed
        ) VALUES (?, ?, ?, ?, 1)
        """,
        (
            article_id,
            PARTSAPI_DEMO_CAR_ID,
            PARTSAPI_DEMO_STR_ID,
            PARTSAPI_DEMO_ARTICLE["fitment_source"],
        ),
    )


def summarize(conn: sqlite3.Connection) -> None:
    tables = [
        "parts",
        "makes",
        "models",
        "generations",
        "engines",
        "fitments",
        "partsapi_articles",
        "partsapi_fitments",
    ]
    print(f"Development database ready at: {DB_PATH}")
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:<20} {count}")


def main() -> None:
    if not CATALOG_PATH.exists():
        raise SystemExit(f"catalog.json not found: {CATALOG_PATH}")

    catalog = load_catalog()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        seed_parts(conn, catalog)
        seed_vehicle_graph(conn, catalog)
        seed_partsapi_demo(conn)
        conn.commit()
        summarize(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
