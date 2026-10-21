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

def create_user(sub_id, username, email):
  with get_connection() as conn:
    with conn.cursor() as cur:
      cur.execute("SELECT user_id, username FROM users WHERE auth0_id = %s;", (sub_id,))
      user = cur.fetchone()

      if user:
          user_id = user["user_id"]
          username = user["username"]
          return user_id, username
      else:
        cur.execute(
          """
          INSERT INTO users (auth0_id, username, email)
          VALUES (%s, %s, %s)
          RETURNING user_id;
          """,
          (sub_id, username, email)
        )
        new_user = cur.fetchone()
        user_id = new_user["user_id"]

        conn.commit()
        return user_id, username

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

def get_users_by_id(user_id, my_id=None):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT users.*,
            (SELECT COUNT(*) FROM subscription
                                WHERE subscription.user_id = users.user_id) AS subscribed_count,
                               EXISTS (SELECT 1 FROM subscription
                                       WHERE subscription.user_id = users.user_id
                                         AND subscription.my_id = %s) AS subscribed
            FROM users
            WHERE user_id = %s
            """,
            (my_id, user_id,),
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

def subscribe(my_id, user_id):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO subscription (my_id, user_id)
            VALUES (%s, %s)
            ON CONFLICT (my_id, user_id) DO NOTHING
            """,
            (my_id, user_id),
        )


def unsubscribe(my_id, user_id):
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM subscription
            WHERE my_id = %s AND user_id = %s
            """,
            (my_id, user_id),
        )


def get_subscription_state(my_id, user_id):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT COUNT(*) AS subscribed_count,
                   COALESCE(BOOL_OR(my_id = %s), FALSE) AS subscribed
            FROM subscription
            WHERE user_id = %s
            """,
            (my_id, user_id),
        ).fetchone()

def get_following_videos(my_id):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT videos.*,
            (SELECT COUNT(*) FROM video_likes
                WHERE video_likes.video_id = videos.video_id) AS like_count,
                EXISTS (SELECT 1 FROM video_likes
                        WHERE video_likes.video_id = videos.video_id
                            AND video_likes.user_id = %s) AS liked
            FROM subscription
            INNER JOIN videos on subscription.user_id = videos.author_id
            WHERE subscription.my_id = %s
            ORDER BY created_at DESC
            """,
            (my_id, my_id,),
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
