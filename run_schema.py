import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


load_dotenv()

database_url = os.environ["DATABASE_URL"]

sql = Path("schema.sql").read_text(encoding="utf-8")

with psycopg.connect(database_url) as conn:
    with conn.cursor() as cur:
        cur.execute(sql, prepare=False)

    conn.commit()

print("Schema created successfully.")