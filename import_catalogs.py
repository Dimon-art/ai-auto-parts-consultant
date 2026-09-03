import sqlite3
from parts_api import get_catalogs

DB_NAME = "parts_catalogs.db"


def create_database():
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS catalogs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            image TEXT
        )
    """)

    conn.commit()
    return conn


def import_catalogs():
    data = get_catalogs()
    catalogs = data.get("list", [])

    conn = create_database()

    for catalog in catalogs:
        conn.execute(
            """
            INSERT OR REPLACE INTO catalogs (id, name, image)
            VALUES (?, ?, ?)
            """,
            (
                catalog.get("id"),
                catalog.get("name"),
                catalog.get("image"),
            ),
        )

    conn.commit()

    count = conn.execute(
        "SELECT COUNT(*) FROM catalogs"
    ).fetchone()[0]

    print(f"Каталогов загружено в базу: {count}")

    rows = conn.execute(
        "SELECT id, name FROM catalogs ORDER BY id"
    ).fetchall()

    print("\nКаталоги:")
    for catalog_id, name in rows:
        print(f"- {catalog_id}: {name}")

    conn.close()


if __name__ == "__main__":
    import_catalogs()