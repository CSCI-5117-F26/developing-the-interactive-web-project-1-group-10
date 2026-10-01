import os
import psycopg

def get_connection():
    return psycopg.connect(os.getenv("DATABASE_URL"))


def get_all_videos():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM videos ORDER BY id DESC")
            return cur.fetchall()


def add_video(title, url, user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO videos (title, url, user_id)
                VALUES (%s, %s, %s)
                """,
                (title, url, user_id)
            )