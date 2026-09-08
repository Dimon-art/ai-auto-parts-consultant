import sqlite3

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
    return "".join(value.split())


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


def find_parts_by_fitment(make, model, year, engine, part_request):
    make_n = normalize(make)
    model_n = normalize(model)
    engine_n = normalize(engine)
    request_n = normalize(part_request)

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT DISTINCT
            p.id,
            p.name,
            p.category,
            p.oem,
            p.make,
            p.model,
            p.year_from,
            p.year_to,
            p.engines,
            p.keywords,
            p.price,
            p.fitment_note,
            p.notes
        FROM parts p
        JOIN fitments f ON f.part_id = p.id
        JOIN engines e ON e.id = f.engine_id
        JOIN generations g ON g.id = e.generation_id
        JOIN models mo ON mo.id = g.model_id
        JOIN makes m ON m.id = mo.make_id
        WHERE m.name = ?
          AND mo.name = ?
          AND g.year_start <= ?
          AND g.year_end >= ?
    """, (make, model, year, year)).fetchall()

    conn.close()

    matches = []

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

        if normalize(part["make"]) != make_n:
            continue

        if normalize(part["model"]) != model_n:
            continue

        if engine_n:
            engine_match = any(
                engine_n in normalize(e)
                or normalize(e).replace("l", "") == engine_n
                for e in part["engines"]
            )

            if not engine_match:
                # Проверка будет выполнена ниже
                # по реальным fitment-двигателям.
                pass

        request_ok = any(
            request_n in normalize(keyword)
            or normalize(keyword) in request_n
            for keyword in part["keywords"]
        )

        if not request_ok:
            continue

        matches.append(part)

    # Повторно проверяем двигатель
    # по реальным связям fitments.
    if engine_n:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row

        engine_rows = conn.execute("""
            SELECT DISTINCT
                f.part_id,
                e.label
            FROM fitments f
            JOIN engines e ON e.id = f.engine_id
            JOIN generations g ON g.id = e.generation_id
            JOIN models mo ON mo.id = g.model_id
            JOIN makes m ON m.id = mo.make_id
            WHERE m.name = ?
              AND mo.name = ?
              AND g.year_start <= ?
              AND g.year_end >= ?
        """, (make, model, year, year)).fetchall()

        conn.close()

        valid_part_ids = set()

        for row in engine_rows:
            catalog_engine = normalize(row["label"])

            if (
                engine_n in catalog_engine
                or catalog_engine.startswith(engine_n)
                or catalog_engine.replace("l", "").startswith(engine_n)
            ):
                valid_part_ids.add(row["part_id"])

        matches = [
            part for part in matches
            if part["id"] in valid_part_ids
        ]

    return matches


def find_partsapi_articles(
    article_number=None,
    brand=None,
    oem=None,
    product_group=None,
):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT
            id,
            art_id,
            article_number,
            brand,
            product_group,
            sup_id,
            oem_numbers,
            ean_numbers,
            article_criteria,
            status
        FROM partsapi_articles
        WHERE 1 = 1
    """

    params = []

    if article_number:
        query += " AND LOWER(article_number) LIKE LOWER(?)"
        params.append(f"%{article_number}%")

    if brand:
        query += " AND LOWER(brand) LIKE LOWER(?)"
        params.append(f"%{brand}%")

    if oem:
        query += " AND LOWER(oem_numbers) LIKE LOWER(?)"
        params.append(f"%{oem}%")

    if product_group:
        query += " AND LOWER(product_group) LIKE LOWER(?)"
        params.append(f"%{product_group}%")

    query += " ORDER BY id"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return [dict(row) for row in rows]


if __name__ == "__main__":
    parts = get_parts()

    print(f"Запчастей в базе: {len(parts)}")

    for part in parts:
        print(
            f"{part['id']}: "
            f"{part['make']} {part['model']} | "
            f"{part['name']} | OEM: {part['oem']}"
        )