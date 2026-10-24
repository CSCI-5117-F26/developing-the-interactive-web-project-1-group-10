import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


load_dotenv()
database_url = os.environ["DATABASE_URL"]

sql_path = Path(__file__).parent / "add_daily_missions.sql"
sql = sql_path.read_text(encoding="utf-8")

with psycopg.connect(database_url) as conn:
    with conn.cursor() as cur:
        cur.execute(sql)

        cur.execute("""
            SELECT mission_date, category, mission
            FROM daily_missions
            LIMIT 1
        """)
        print("Table check:", cur.fetchone())

    conn.commit()

print("create check")