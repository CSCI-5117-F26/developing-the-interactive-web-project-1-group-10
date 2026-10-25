from pathlib import Path

from database import get_connection


if __name__ == "__main__":
    sql = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.execute(sql, prepare=False)
    print("Database ready.")
