from pathlib import Path
import sqlite3


DB_PATH = Path(__file__).resolve().parent / "parts_catalogs.db"


def _db_path():
    docker_db = Path("/app/data/parts_catalogs.db")
    if docker_db.exists():
        return docker_db
    return DB_PATH


def _normalize_engine(value):
    return (
        str(value or "")
        .lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )


def _engine_matches(requested, actual):
    requested = _normalize_engine(requested)
    actual = _normalize_engine(actual)

    if not requested:
        return True

    if requested in actual:
        return True

    aliases = {
        "1.0tsi": "1.0ltsi",
        "1.0ltsi": "1.0tsi",
    }

    alias = aliases.get(requested)

    return bool(alias and alias in actual)


def find_partsapi_fitment(make, model, year, engine, part_request):
    """
    Возвращает статьи PartsAPI из локально сохранённых fitment-связей.

    Для MVP используется уже подтверждённая связка:
        CAR_ID -> STR_ID -> article

    Новые запросы к PartsAPI здесь НЕ выполняются.
    """

    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row

    engine_rows = conn.execute(
        """
        SELECT
            e.id,
            e.label,
            e.partsapi_car_id,
            mk.name AS make_name,
            m.name AS model_name,
            g.year_start,
            g.year_end
        FROM engines e
        JOIN generations g
          ON g.id = e.generation_id
        JOIN models m
          ON m.id = g.model_id
        JOIN makes mk
          ON mk.id = m.make_id
        WHERE e.partsapi_car_id IS NOT NULL
          AND LOWER(mk.name) = LOWER(?)
          AND LOWER(m.name) = LOWER(?)
        """,
        (make.strip(), model.strip()),
    ).fetchall()

    result = []
    seen = set()

    for engine_row in engine_rows:

        if engine_row["year_start"] is not None:
            if int(year) < int(engine_row["year_start"]):
                continue

        if engine_row["year_end"] is not None:
            if int(year) > int(engine_row["year_end"]):
                continue

        if not _engine_matches(engine, engine_row["label"]):
            continue

        car_id = engine_row["partsapi_car_id"]

        rows = conn.execute(
            """
            SELECT
                pa.id,
                pa.art_id,
                pa.article_number,
                pa.brand,
                pa.product_group,
                pa.sup_id,
                pa.oem_numbers,
                pa.ean_numbers,
                pa.article_criteria,
                pa.status,
                pf.car_id,
                pf.str_id,
                pf.fitment_source
            FROM partsapi_articles pa
            JOIN partsapi_fitments pf
              ON pf.article_id = pa.id
            WHERE pf.car_id = ?
              AND pf.confirmed = 1
            ORDER BY pa.id
            """,
            (car_id,),
        ).fetchall()

        for row in rows:

            key = (
                row["id"],
                row["car_id"],
                row["str_id"],
            )

            if key in seen:
                continue

            seen.add(key)

            result.append(
                {
                    "source": "PartsAPI",
                    "fitment_confirmed": True,
                    "fitment_source": row["fitment_source"],
                    "car_id": row["car_id"],
                    "str_id": row["str_id"],
                    "article_id": row["id"],
                    "art_id": row["art_id"],
                    "article_number": row["article_number"],
                    "brand": row["brand"],
                    "product_group": row["product_group"],
                    "sup_id": row["sup_id"],
                    "oem_numbers": row["oem_numbers"],
                    "ean_numbers": row["ean_numbers"],
                    "article_criteria": row["article_criteria"],
                    "status": row["status"],
                    "engine": engine_row["label"],
                }
            )

    conn.close()

    return result
