import sqlite3

DB_NAME = "parts_catalogs.db"


def create_parts_table():
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS parts (
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
        )
    """)

    conn.commit()

    count = conn.execute(
        "SELECT COUNT(*) FROM parts"
    ).fetchone()[0]

    print(f"Таблица parts готова. Записей: {count}")

    conn.close()


if __name__ == "__main__":
    create_parts_table()