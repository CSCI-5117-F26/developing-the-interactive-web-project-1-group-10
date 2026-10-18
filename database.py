import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

def create_users_table():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGSERIAL PRIMARY KEY,
                auth0_id TEXT UNIQUE NOT NULL,
                username VARCHAR(80) NOT NULL,
                email TEXT UNIQUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

def initialize_database():
    create_users_table()
    create_videos_table()
    
    
def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set.")

    return psycopg.connect(database_url, row_factory=dict_row)


def create_videos_table():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS videos (
                id BIGSERIAL PRIMARY KEY,
                username VARCHAR(80) NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                video_url TEXT NOT NULL,
                category VARCHAR(50) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def create_video(username, title, description, video_url, category):
    with get_connection() as conn:
        return conn.execute(
            """
            INSERT INTO videos (
                username,
                title,
                description,
                video_url,
                category
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                username,
                title,
                description,
                video_url,
                category,
            ),
        ).fetchone()


def get_videos_by_category(category):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT *
            FROM videos
            WHERE category = %s
            ORDER BY created_at DESC
            """,
            (category,),
        ).fetchall()


if __name__ == "__main__":
    create_videos_table()

    test_video = create_video(
        username="test_user",
        title="Test for the database",
        description="This is a test for the database.",
        video_url="https://farm3.staticflickr.com/2875/9069037713_1752f5daeb.jpg",
        category="general",
    )

    print("Created test video:", test_video)
