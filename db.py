import sqlite3
from db import get_parts
from app import find_matches

DB_NAME = "parts_catalogs.db"


def get_parts():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT
            id,
            name,
            category,
            oem,
            make,
            model,
            year_from,
            year_to,
            engines,
            keywords,
            price,
            fitment_note,
            notes
        FROM parts
        ORDER BY id
    """).fetchall()

    conn.close()

    parts = []

    for row in rows:
        part = dict(row)

        part["engines"] = [
            x.strip()
            for x in (part["engines"] or "").split(",")
            if x.strip()
        ]

        part["keywords"] = [
            x.strip()
            for x in (part["keywords"] or "").split(",")
            if x.strip()
        ]

        parts.append(part)

    return parts

def normalize(value):
    value = str(value).lower().strip()
    value = value.replace(",", ".")
    return " ".join(value.split())

def find_parts(make, model, year, engine, part_request):
    make_n = normalize(make)
    model_n = normalize(model)
    engine_n = normalize(engine)
    request_n = normalize(part_request)

    parts = get_parts()
    matches = []

    for part in parts:

        if normalize(part["make"]) != make_n:
            continue

        if normalize(part["model"]) != model_n:
            continue

        if not (
            part["year_from"] <= year <= part["year_to"]
        ):
            continue

        if engine_n:
            engine_ok = any(
                engine_n in normalize(e)
                for e in part["engines"]
            )

            if not engine_ok:
                continue

        request_ok = any(
            request_n in normalize(keyword)
            or normalize(keyword) in request_n
            for keyword in part["keywords"]
        )

        if not request_ok:
            continue

        matches.append(part)

    return matches


if __name__ == "__main__":
    parts = get_parts()

    print(f"Запчастей в базе: {len(parts)}")

    for part in parts:
        print(
            f"{part['id']}: "
            f"{part['make']} {part['model']} | "
            f"{part['name']} | OEM: {part['oem']}"
        )