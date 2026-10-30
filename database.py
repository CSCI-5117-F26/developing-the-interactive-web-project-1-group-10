import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

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

def create_video(author_id, title, description, video_url, category,
                 media_type="video", mission_date=None):
    with get_connection() as conn:
        return conn.execute(
            """
            INSERT INTO videos (author_id, title, description, video_url,
                                category, media_type, mission_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (author_id, title, description, video_url, category, media_type, mission_date),
        ).fetchone()


def get_videos_by_category(category, user_id=None):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT videos.*, users.username AS "userName",
                   (SELECT COUNT(*) FROM video_likes
                    WHERE video_likes.video_id = videos.video_id) AS like_count,
                   (SELECT COUNT(*) FROM comments
                    WHERE comments.video_id = videos.video_id) AS comment_count,
                   EXISTS (SELECT 1 FROM video_likes
                           WHERE video_likes.video_id = videos.video_id
                             AND video_likes.user_id = %s) AS liked
            FROM videos
            JOIN users ON videos.author_id = users.user_id
            WHERE videos.category = %s
            ORDER BY videos.created_at DESC, videos.video_id DESC
            """,
            (user_id, category),
        ).fetchall()

def get_video_by_id(video_id, user_id=None):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT videos.*, users.username AS "userName", users.profile_url AS "profile_url",
                   videos.video_url AS video,
                   (SELECT COUNT(*) FROM video_likes
                    WHERE video_likes.video_id = videos.video_id) AS like_count,
                   EXISTS (SELECT 1 FROM video_likes
                           WHERE video_likes.video_id = videos.video_id
                             AND video_likes.user_id = %s) AS liked
            FROM videos
            JOIN users ON users.user_id = videos.author_id
            WHERE videos.video_id = %s
            """,
            (user_id, video_id),
        ).fetchone()


def get_comments(video_id):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT comments.*, users.username
            FROM comments
            JOIN users ON users.user_id = comments.author_id
            WHERE comments.video_id = %s
            ORDER BY comments.created_at DESC, comments.comment_id DESC
            """,
            (video_id,),
        ).fetchall()


def create_comment(video_id, author_id, content):
    with get_connection() as conn:
        comment = conn.execute(
            """
            WITH inserted AS (
                INSERT INTO comments (video_id, author_id, content)
                VALUES (%s, %s, %s)
                RETURNING *
            )
            SELECT inserted.*, users.username
            FROM inserted JOIN users ON users.user_id = inserted.author_id
            """,
            (video_id, author_id, content),
        ).fetchone()
        comment["comment_count"] = conn.execute(
            "SELECT COUNT(*) AS total FROM comments WHERE video_id = %s",
            (video_id,),
        ).fetchone()["total"]
        return comment


def delete_comment(comment_id, author_id):
    with get_connection() as conn:
        deleted = conn.execute(
            """
            DELETE FROM comments
            WHERE comment_id = %s AND author_id = %s
            RETURNING comment_id, video_id
            """,
            (comment_id, author_id),
        ).fetchone()
        if deleted is not None:
            deleted["comment_count"] = conn.execute(
                "SELECT COUNT(*) AS total FROM comments WHERE video_id = %s",
                (deleted["video_id"],),
            ).fetchone()["total"]
        return deleted


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

def get_liked_videos(user_id):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT videos.*,
            (SELECT COUNT(*) FROM video_likes
                WHERE video_likes.video_id = videos.video_id) AS like_count,
            (SELECT COUNT(*) FROM comments
                WHERE comments.video_id = videos.video_id) AS comment_count,
                EXISTS (SELECT 1 FROM video_likes
                        WHERE video_likes.video_id = videos.video_id
                            AND video_likes.user_id = %s) AS liked
            FROM videos JOIN video_likes ON videos.video_id = video_likes.video_id
            WHERE video_likes.user_id = %s
            """,
            (user_id, user_id,),
        ).fetchall()

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

def get_profile_url(user_id):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT profile_url
            FROM users
            WHERE user_id = %s
            """,
            (user_id,),
        ).fetchone()

        if row is None:
            return None
        return row["profile_url"]

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

def get_following_lists(my_id):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT users.*,
            (SELECT COUNT(*) AS subscribed_count
            FROM subscription
            WHERE subscription.user_id = users.user_id
            ),
            EXISTS (
            SELECT 1 FROM subscription
            WHERE subscription.user_id = users.user_id AND subscription.my_id = %s
            ) AS subscribed
            FROM subscription
            INNER JOIN users on subscription.user_id = users.user_id
            WHERE subscription.my_id = %s
            """,
            (my_id, my_id,),
        ).fetchall()

def get_following_videos(my_id):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT videos.*,
            (SELECT COUNT(*) FROM video_likes
                WHERE video_likes.video_id = videos.video_id) AS like_count,
            (SELECT COUNT(*) FROM comments
                WHERE comments.video_id = videos.video_id) AS comment_count,
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

def get_daily_mission(mission_date, category):
    with get_connection() as conn:
        mission = conn.execute(
            """
            SELECT mission
            FROM daily_missions
            WHERE mission_date = %s AND category = %s
            """,
            (mission_date, category),
        ).fetchone()

    return mission

def search_videos(query, user_id=None):
    validation_list= "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    word = ""
    processed_words = []

    for char in query + " ":
        if char in validation_list:
            word += char
        else:
            if word != "":
                processed_words.append(word + ":*")
                word = ""

    if not processed_words:
        return []
    queryWithLegalWords = " & ".join(processed_words)

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT videos.*, users.username AS "userName",
                   (SELECT COUNT(*) FROM video_likes
                    WHERE video_likes.video_id = videos.video_id) AS like_count,
                   (SELECT COUNT(*) FROM comments
                    WHERE comments.video_id = videos.video_id) AS comment_count,
                   EXISTS (
                       SELECT 1 FROM video_likes
                       WHERE video_likes.video_id = videos.video_id
                         AND video_likes.user_id = %s
                   ) AS liked
            FROM videos
            JOIN users ON videos.author_id = users.user_id
            WHERE (
                to_tsvector(
                    'english',
                    COALESCE(users.username, '') || ' ' ||
                    COALESCE(videos.title, '') || ' ' ||
                    COALESCE(videos.description, '')
                ) @@ plainto_tsquery('english', %s)

                OR

                to_tsvector(
                    'english',
                    COALESCE(users.username, '') || ' ' ||
                    COALESCE(videos.title, '') || ' ' ||
                    COALESCE(videos.description, '')
                ) @@ to_tsquery('english', %s)
            )
            AND (%s OR videos.category = 'general')
            ORDER BY videos.created_at DESC, videos.video_id DESC
            """,
            (user_id, query, queryWithLegalWords, user_id is not None),
        ).fetchall()
