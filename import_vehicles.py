#!/usr/bin/env python3
"""
Import selected vehicles from vehicles_all.json into parts_catalogs.db.

Creates / refreshes only:
  makes → models → generations → engines

Never modifies parts or catalogs tables.
Default: real import (with backup). Use --dry-run for prepare-only.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
SOURCE_PATH = BASE_DIR / "vehicles_all.json"
DB_PATH = BASE_DIR / "parts_catalogs.db"

# Target set: 21 models from the open vehicle-makes-models source
# Exact names only — do not add siblings (e.g. cee'd) or rename.
TARGET_MODELS: dict[str, set[str]] = {
    "Toyota": {"Corolla", "Camry", "RAV4", "Yaris"},
    "Hyundai": {"Elantra", "Santa Fe", "Sonata"},
    "Kia": {"Ceed", "K5", "Rio", "Sorento", "Sportage"},
    "Ford": {"Explorer", "Fiesta", "Kuga", "Mondeo"},
    "Volkswagen": {"Golf", "Passat", "Polo", "Tiguan", "Touareg"},
}

# Stable make order for deterministic ids / reporting
MAKE_ORDER: list[str] = [
    "Toyota",
    "Hyundai",
    "Kia",
    "Ford",
    "Volkswagen",
]

# Verified against vehicles_all.json (exact TARGET names)
EXPECTED_MAKES = 5
EXPECTED_MODELS = 21
EXPECTED_GENERATIONS = 274
EXPECTED_ENGINES = 1794

VEHICLE_TABLES = ("engines", "generations", "models", "makes")


def load_source() -> list:
    with SOURCE_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _as_optional(value: Any) -> Any:
    """Pass through source values; missing/absent → None."""
    return value if value is not None else None


def build_prepared_catalog(data: list) -> dict[str, list[dict]]:
    """
    Normalize TARGET vehicles into relational tables (in memory only).

    Source field mapping (no invented values):
      make.name              → makes.name
      model.name             → models.name
      generation.name        → generations.name
      generation.yearStart   → generations.year_start
      generation.yearEnd     → generations.year_end   (None if absent)
      generation.bodyType    → generations.body_type  (None if absent/empty)
      engine.label           → engines.label
      engine.fuelType        → engines.fuel_type
      engine.cylinders       → engines.cylinders
      engine.displacementCc  → engines.displacement_cc
      engine.powerHp         → engines.power_hp
      engine.torqueNm        → engines.torque_nm
      engine.transmission    → engines.transmission
      engine.drivetrain      → engines.drivetrain

    Every generation entry and every engine entry from the source is kept as-is
    (no dedup, no merge of models/generations).
    """
    source_index: dict[str, dict[str, dict]] = {}
    for group in data:
        for make in group.get("makes", []):
            make_name = make.get("name")
            if make_name not in TARGET_MODELS:
                continue
            wanted = TARGET_MODELS[make_name]
            bucket = source_index.setdefault(make_name, {})
            for model in make.get("models", []):
                model_name = model.get("name")
                if model_name in wanted and model_name not in bucket:
                    bucket[model_name] = model

    makes: list[dict] = []
    models: list[dict] = []
    generations: list[dict] = []
    engines: list[dict] = []

    next_make_id = 1
    next_model_id = 1
    next_generation_id = 1
    next_engine_id = 1

    for make_name in MAKE_ORDER:
        make_models = source_index.get(make_name, {})
        make_id = next_make_id
        next_make_id += 1
        makes.append({"id": make_id, "name": make_name})

        for model_name in sorted(TARGET_MODELS[make_name]):
            model_obj = make_models.get(model_name)
            if model_obj is None:
                continue

            model_id = next_model_id
            next_model_id += 1
            models.append(
                {
                    "id": model_id,
                    "make_id": make_id,
                    "name": model_name,
                }
            )

            for generation in model_obj.get("generations") or []:
                generation_id = next_generation_id
                next_generation_id += 1

                body_type = generation.get("bodyType")
                if body_type == "":
                    body_type = None

                generations.append(
                    {
                        "id": generation_id,
                        "model_id": model_id,
                        "name": generation.get("name"),
                        "year_start": _as_optional(generation.get("yearStart")),
                        "year_end": _as_optional(generation.get("yearEnd")),
                        "body_type": body_type,
                    }
                )

                for engine in generation.get("engines") or []:
                    engine_id = next_engine_id
                    next_engine_id += 1
                    engines.append(
                        {
                            "id": engine_id,
                            "generation_id": generation_id,
                            "label": engine.get("label"),
                            "fuel_type": _as_optional(engine.get("fuelType")),
                            "cylinders": _as_optional(engine.get("cylinders")),
                            "displacement_cc": _as_optional(
                                engine.get("displacementCc")
                            ),
                            "power_hp": _as_optional(engine.get("powerHp")),
                            "torque_nm": _as_optional(engine.get("torqueNm")),
                            "transmission": _as_optional(engine.get("transmission")),
                            "drivetrain": _as_optional(engine.get("drivetrain")),
                        }
                    )

    return {
        "makes": makes,
        "models": models,
        "generations": generations,
        "engines": engines,
    }


def collect_target_rows(catalog: dict[str, list[dict]]) -> list[dict]:
    """Summary rows: make | model | generations | engines."""
    make_by_id = {m["id"]: m["name"] for m in catalog["makes"]}
    gens_by_model: dict[int, int] = {}
    eng_by_model: dict[int, int] = {}

    gen_to_model = {g["id"]: g["model_id"] for g in catalog["generations"]}
    for g in catalog["generations"]:
        gens_by_model[g["model_id"]] = gens_by_model.get(g["model_id"], 0) + 1
    for e in catalog["engines"]:
        model_id = gen_to_model[e["generation_id"]]
        eng_by_model[model_id] = eng_by_model.get(model_id, 0) + 1

    rows: list[dict] = []
    for model in catalog["models"]:
        rows.append(
            {
                "make": make_by_id[model["make_id"]],
                "model": model["name"],
                "generations": gens_by_model.get(model["id"], 0),
                "engines": eng_by_model.get(model["id"], 0),
            }
        )
    return rows


def print_table(rows: list[dict]) -> None:
    headers = ("Make", "Model", "Generations", "Engines")
    col_make = max(len(headers[0]), max((len(r["make"]) for r in rows), default=0))
    col_model = max(len(headers[1]), max((len(r["model"]) for r in rows), default=0))
    col_gen = max(
        len(headers[2]), max((len(str(r["generations"])) for r in rows), default=0)
    )
    col_eng = max(
        len(headers[3]), max((len(str(r["engines"])) for r in rows), default=0)
    )

    def fmt(make: str, model: str, gen: str, eng: str) -> str:
        return (
            f"{make:<{col_make}} | "
            f"{model:<{col_model}} | "
            f"{gen:>{col_gen}} | "
            f"{eng:>{col_eng}}"
        )

    print(fmt(*headers))
    print("-" * (col_make + col_model + col_gen + col_eng + 9))
    for r in rows:
        print(
            fmt(
                r["make"],
                r["model"],
                str(r["generations"]),
                str(r["engines"]),
            )
        )


def print_schema_preview(catalog: dict[str, list[dict]]) -> None:
    """Show one sample row per table (structure only)."""
    print("PREPARED SCHEMA")
    print("  makes:        id, name")
    print("  models:       id, make_id, name")
    print("  generations:  id, model_id, name, year_start, year_end, body_type")
    print(
        "  engines:      id, generation_id, label, fuel_type, cylinders, "
        "displacement_cc, power_hp, torque_nm, transmission, drivetrain"
    )
    print()
    if catalog["makes"]:
        print("  sample make:       ", catalog["makes"][0])
    if catalog["models"]:
        print("  sample model:      ", catalog["models"][0])
    sample_gen = next(
        (g for g in catalog["generations"] if g["year_end"] is None),
        catalog["generations"][0] if catalog["generations"] else None,
    )
    if sample_gen:
        print("  sample generation: ", sample_gen)
    if catalog["engines"]:
        print("  sample engine:     ", catalog["engines"][0])


def validate_catalog(catalog: dict[str, list[dict]]) -> list[str]:
    """Integrity checks; returns list of problem strings (empty = ok)."""
    problems: list[str] = []

    make_ids = {m["id"] for m in catalog["makes"]}
    model_ids = {m["id"] for m in catalog["models"]}
    generation_ids = {g["id"] for g in catalog["generations"]}

    for model in catalog["models"]:
        if model["make_id"] not in make_ids:
            problems.append(f"model {model['id']} bad make_id={model['make_id']}")

    for generation in catalog["generations"]:
        if generation["model_id"] not in model_ids:
            problems.append(
                f"generation {generation['id']} bad model_id={generation['model_id']}"
            )
        if not generation.get("name"):
            problems.append(f"generation {generation['id']} missing name")

    for engine in catalog["engines"]:
        if engine["generation_id"] not in generation_ids:
            problems.append(
                f"engine {engine['id']} bad generation_id={engine['generation_id']}"
            )
        if not engine.get("label"):
            problems.append(f"engine {engine['id']} missing label")

    found_keys = {
        (
            next(m["name"] for m in catalog["makes"] if m["id"] == model["make_id"]),
            model["name"],
        )
        for model in catalog["models"]
    }
    for make_name, models in TARGET_MODELS.items():
        for model_name in models:
            if (make_name, model_name) not in found_keys:
                problems.append(f"missing TARGET model: {make_name} / {model_name}")

    if len(catalog["makes"]) != EXPECTED_MAKES:
        problems.append(
            f"makes count {len(catalog['makes'])} != {EXPECTED_MAKES}"
        )
    if len(catalog["models"]) != EXPECTED_MODELS:
        problems.append(
            f"models count {len(catalog['models'])} != {EXPECTED_MODELS}"
        )
    if len(catalog["generations"]) != EXPECTED_GENERATIONS:
        problems.append(
            f"generations count {len(catalog['generations'])} != {EXPECTED_GENERATIONS}"
        )
    if len(catalog["engines"]) != EXPECTED_ENGINES:
        problems.append(
            f"engines count {len(catalog['engines'])} != {EXPECTED_ENGINES}"
        )

    return problems


def backup_database(db_path: Path) -> Path:
    """Copy existing DB next to it. Does not delete the original."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_name(f"{db_path.stem}.backup_{stamp}{db_path.suffix}")
    shutil.copy2(db_path, backup_path)
    return backup_path


def count_table(conn: sqlite3.Connection, table: str) -> int | None:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    if row is None:
        return None
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def create_vehicle_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS makes (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY,
            make_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            UNIQUE(make_id, name),
            FOREIGN KEY(make_id) REFERENCES makes(id)
        );

        CREATE TABLE IF NOT EXISTS generations (
            id INTEGER PRIMARY KEY,
            model_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            year_start INTEGER,
            year_end INTEGER,
            body_type TEXT,
            FOREIGN KEY(model_id) REFERENCES models(id)
        );

        CREATE TABLE IF NOT EXISTS engines (
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
            FOREIGN KEY(generation_id) REFERENCES generations(id)
        );
        """
    )


def clear_vehicle_tables(conn: sqlite3.Connection) -> None:
    """Remove only vehicle rows so re-import does not duplicate. Never touches parts/catalogs."""
    for table in VEHICLE_TABLES:
        conn.execute(f"DELETE FROM {table}")


def insert_catalog(conn: sqlite3.Connection, catalog: dict[str, list[dict]]) -> None:
    conn.executemany(
        "INSERT INTO makes (id, name) VALUES (?, ?)",
        [(m["id"], m["name"]) for m in catalog["makes"]],
    )
    conn.executemany(
        "INSERT INTO models (id, make_id, name) VALUES (?, ?, ?)",
        [(m["id"], m["make_id"], m["name"]) for m in catalog["models"]],
    )
    conn.executemany(
        """
        INSERT INTO generations (
            id, model_id, name, year_start, year_end, body_type
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                g["id"],
                g["model_id"],
                g["name"],
                g["year_start"],
                g["year_end"],
                g["body_type"],
            )
            for g in catalog["generations"]
        ],
    )
    conn.executemany(
        """
        INSERT INTO engines (
            id, generation_id, label, fuel_type, cylinders,
            displacement_cc, power_hp, torque_nm, transmission, drivetrain
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                e["id"],
                e["generation_id"],
                e["label"],
                e["fuel_type"],
                e["cylinders"],
                e["displacement_cc"],
                e["power_hp"],
                e["torque_nm"],
                e["transmission"],
                e["drivetrain"],
            )
            for e in catalog["engines"]
        ],
    )


def verify_fk_integrity(conn: sqlite3.Connection) -> list[str]:
    problems: list[str] = []
    orphan_models = conn.execute(
        """
        SELECT COUNT(*) FROM models m
        LEFT JOIN makes mk ON mk.id = m.make_id
        WHERE mk.id IS NULL
        """
    ).fetchone()[0]
    if orphan_models:
        problems.append(f"orphan models: {orphan_models}")

    orphan_gens = conn.execute(
        """
        SELECT COUNT(*) FROM generations g
        LEFT JOIN models m ON m.id = g.model_id
        WHERE m.id IS NULL
        """
    ).fetchone()[0]
    if orphan_gens:
        problems.append(f"orphan generations: {orphan_gens}")

    orphan_engines = conn.execute(
        """
        SELECT COUNT(*) FROM engines e
        LEFT JOIN generations g ON g.id = e.generation_id
        WHERE g.id IS NULL
        """
    ).fetchone()[0]
    if orphan_engines:
        problems.append(f"orphan engines: {orphan_engines}")

    # SQLite foreign_key_check on vehicle tables only
    for table in ("makes", "models", "generations", "engines"):
        rows = conn.execute(f"PRAGMA foreign_key_check({table})").fetchall()
        if rows:
            problems.append(f"foreign_key_check({table}): {rows}")

    return problems


def import_into_sqlite(catalog: dict[str, list[dict]], db_path: Path) -> Path:
    """
    Backup DB, create vehicle tables if needed, replace vehicle data only.
    Rolls back vehicle writes on failure; never deletes parts/catalogs.
    """
    backup_path = backup_database(db_path)
    print(f"Backup created: {backup_path.name}")

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")

        parts_before = count_table(conn, "parts")
        catalogs_before = count_table(conn, "catalogs")
        print(f"Before import — parts: {parts_before}, catalogs: {catalogs_before}")

        if parts_before != 6:
            raise RuntimeError(
                f"Refusing import: expected 6 parts, found {parts_before}"
            )
        if catalogs_before != 19:
            raise RuntimeError(
                f"Refusing import: expected 19 catalogs, found {catalogs_before}"
            )

        create_vehicle_tables(conn)
        clear_vehicle_tables(conn)
        insert_catalog(conn, catalog)
        conn.commit()

        parts_after = count_table(conn, "parts")
        catalogs_after = count_table(conn, "catalogs")
        n_makes = count_table(conn, "makes")
        n_models = count_table(conn, "models")
        n_generations = count_table(conn, "generations")
        n_engines = count_table(conn, "engines")

        if parts_after != parts_before or catalogs_after != catalogs_before:
            raise RuntimeError(
                "parts/catalogs changed unexpectedly — rolling back vehicle import"
            )

        if (
            n_makes != EXPECTED_MAKES
            or n_models != EXPECTED_MODELS
            or n_generations != EXPECTED_GENERATIONS
            or n_engines != EXPECTED_ENGINES
        ):
            raise RuntimeError(
                "vehicle counts mismatch after insert: "
                f"makes={n_makes}, models={n_models}, "
                f"generations={n_generations}, engines={n_engines}"
            )

        fk_problems = verify_fk_integrity(conn)
        if fk_problems:
            raise RuntimeError("FK integrity failed: " + "; ".join(fk_problems))

        print("Import committed.")
        print(f"  makes:        {n_makes}")
        print(f"  models:       {n_models}")
        print(f"  generations:  {n_generations}")
        print(f"  engines:      {n_engines}")
        print(f"  parts:        {parts_after}")
        print(f"  catalogs:     {catalogs_after}")
        return backup_path
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def run_dry_run(catalog: dict[str, list[dict]]) -> None:
    print("DRY RUN — prepare vehicle catalog from vehicles_all.json")
    print("No SQLite writes.\n")
    print_schema_preview(catalog)
    print()
    print_table(collect_target_rows(catalog))
    print()
    print("TOTALS")
    print(f"  Makes:        {len(catalog['makes'])}  (expected {EXPECTED_MAKES})")
    print(f"  Models:       {len(catalog['models'])}  (expected {EXPECTED_MODELS})")
    print(
        f"  Generations:  {len(catalog['generations'])}  "
        f"(expected {EXPECTED_GENERATIONS})"
    )
    print(f"  Engines:      {len(catalog['engines'])}  (expected {EXPECTED_ENGINES})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import vehicle catalog into SQLite")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Prepare and validate only; do not write to SQLite",
    )
    args = parser.parse_args()

    if not SOURCE_PATH.exists():
        raise SystemExit(f"Source file not found: {SOURCE_PATH}")

    data = load_source()
    catalog = build_prepared_catalog(data)

    problems = validate_catalog(catalog)
    if problems:
        print("VALIDATION PROBLEMS — aborting, no DB writes:")
        for item in problems:
            print(f"  - {item}")
        raise SystemExit(1)

    if args.dry_run:
        run_dry_run(catalog)
        print("\nVALIDATION: OK")
        return

    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    print("IMPORT - vehicles_all.json -> parts_catalogs.db")
    print("Only tables makes/models/generations/engines will be written.\n")
    print_table(collect_target_rows(catalog))
    print()

    backup_path = import_into_sqlite(catalog, DB_PATH)
    print()
    print(f"Done. Backup file: {backup_path.name}")


if __name__ == "__main__":
    main()
