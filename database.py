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


def get_videos_by_category(category, user_id=None):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT videos.*,
                   (SELECT COUNT(*) FROM video_likes
                    WHERE video_likes.video_id = videos.video_id) AS like_count,
                   EXISTS (SELECT 1 FROM video_likes
                           WHERE video_likes.video_id = videos.video_id
                             AND video_likes.user_id = %s) AS liked
            FROM videos
            WHERE category = %s
            ORDER BY created_at DESC
            """,
            (user_id, category),
        ).fetchall()

def get_videos_by_id(user_id):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT *
            FROM videos
            WHERE author_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()

def get_users_by_id(user_id):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT *
            FROM users
            WHERE user_id = %s
            """,
            (user_id,),
        ).fetchone()


def like_video(user_id, video_id):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO video_likes (user_id, video_id)
            VALUES (%s, %s)
            ON CONFLICT (user_id, video_id) DO NOTHING
            """,
            (user_id, video_id),
        )


def unlike_video(user_id, video_id):
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM video_likes
            WHERE user_id = %s AND video_id = %s
            """,
            (user_id, video_id),
        )


def get_video_like_state(user_id, video_id):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT COUNT(*) AS like_count,
                   COALESCE(BOOL_OR(user_id = %s), FALSE) AS liked
            FROM video_likes
            WHERE video_id = %s
            """,
            (user_id, video_id),
        ).fetchone()


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
