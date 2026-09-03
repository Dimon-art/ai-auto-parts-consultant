import sqlite3
import json

DB_NAME = "parts_catalogs.db"
CATALOG_FILE = "catalog.json"


def import_demo_parts():
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        parts = json.load(f)

    conn = sqlite3.connect(DB_NAME)

    conn.execute("DELETE FROM parts")

    for part in parts:
        conn.execute(
            """
            INSERT INTO parts (
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
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
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
            ),
        )

    conn.commit()

    count = conn.execute(
        "SELECT COUNT(*) FROM parts"
    ).fetchone()[0]

    print(f"Демонстрационных запчастей загружено: {count}")

    print("\nЗапчасти:")
    rows = conn.execute(
        "SELECT id, make, model, name, oem FROM parts ORDER BY id"
    ).fetchall()

    for row in rows:
        print(row)

    conn.close()


if __name__ == "__main__":
    import_demo_parts()