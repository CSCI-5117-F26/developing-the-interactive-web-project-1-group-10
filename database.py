import os

import psycopg
from psycopg.rows import dict_row


# =========================================================
# Database Connection
# =========================================================

def get_connection():
    """
    Create and return a connection to the PostgreSQL database.

    DATABASE_URL should be stored in:
    - .env for local development
    - Render Environment Variables for deployment
    """

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set."
        )

    return psycopg.connect(
        database_url,
        row_factory=dict_row
    )


# =========================================================
# Users
# =========================================================

def create_user(username, password_hash, email=None):
    """
    Create a new user and return the newly created user.
    """

    with get_connection() as conn:
        return conn.execute(
            """
            INSERT INTO users (
                username,
                password_hash,
                email
            )
            VALUES (%s, %s, %s)
            RETURNING *
            """,
            (
                username,
                password_hash,
                email
            )
        ).fetchone()


def get_user_by_id(user_id):
    """
    Get a user by ID.
    """

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT *
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        ).fetchone()


def get_user_by_username(username):
    """
    Get a user by username.
    """

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT *
            FROM users
            WHERE username = %s
            """,
            (username,)
        ).fetchone()


def get_user_by_email(email):
    """
    Get a user by email.
    """

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = %s
            """,
            (email,)
        ).fetchone()


def update_user_profile(user_id, username=None, bio=None):
    """
    Update a user's username and/or bio.
    """

    with get_connection() as conn:
        return conn.execute(
            """
            UPDATE users
            SET
                username = COALESCE(%s, username),
                bio = COALESCE(%s, bio)
            WHERE id = %s
            RETURNING *
            """,
            (
                username,
                bio,
                user_id
            )
        ).fetchone()


def delete_user(user_id):
    """
    Delete a user.
    """

    with get_connection() as conn:
        result = conn.execute(
            """
            DELETE FROM users
            WHERE id = %s
            RETURNING id
            """,
            (user_id,)
        ).fetchone()

        return result is not None


# =========================================================
# Videos
# =========================================================

def create_video(
    user_id,
    title,
    description,
    video_url,
    thumbnail_url=None
):
    """
    Create a new video and return it.
    """

    with get_connection() as conn:
        return conn.execute(
            """
            INSERT INTO videos (
                user_id,
                title,
                description,
                video_url,
                thumbnail_url
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                user_id,
                title,
                description,
                video_url,
                thumbnail_url
            )
        ).fetchone()


def get_video(video_id):
    """
    Get one video by ID.
    """

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT
                videos.*,
                users.username
            FROM videos
            JOIN users
                ON videos.user_id = users.id
            WHERE videos.id = %s
            """,
            (video_id,)
        ).fetchone()


def get_all_videos():
    """
    Get all videos, newest first.
    """

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT
                videos.*,
                users.username
            FROM videos
            JOIN users
                ON videos.user_id = users.id
            ORDER BY videos.created_at DESC
            """
        ).fetchall()


def get_videos_by_user(user_id):
    """
    Get all videos uploaded by a specific user.
    """

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT *
            FROM videos
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()


def search_videos(search_text):
    """
    Search videos by title or description.
    """

    search_pattern = f"%{search_text}%"

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT
                videos.*,
                users.username
            FROM videos
            JOIN users
                ON videos.user_id = users.id
            WHERE
                videos.title ILIKE %s
                OR videos.description ILIKE %s
            ORDER BY videos.created_at DESC
            """,
            (
                search_pattern,
                search_pattern
            )
        ).fetchall()


def update_video(
    video_id,
    title=None,
    description=None,
    thumbnail_url=None
):
    """
    Update a video's editable information.
    """

    with get_connection() as conn:
        return conn.execute(
            """
            UPDATE videos
            SET
                title = COALESCE(%s, title),
                description = COALESCE(%s, description),
                thumbnail_url = COALESCE(%s, thumbnail_url)
            WHERE id = %s
            RETURNING *
            """,
            (
                title,
                description,
                thumbnail_url,
                video_id
            )
        ).fetchone()


def delete_video(video_id):
    """
    Delete a video.
    """

    with get_connection() as conn:
        result = conn.execute(
            """
            DELETE FROM videos
            WHERE id = %s
            RETURNING id
            """,
            (video_id,)
        ).fetchone()

        return result is not None


# =========================================================
# Comments
# =========================================================

def create_comment(user_id, video_id, content):
    """
    Add a comment to a video.
    """

    with get_connection() as conn:
        return conn.execute(
            """
            INSERT INTO comments (
                user_id,
                video_id,
                content
            )
            VALUES (%s, %s, %s)
            RETURNING *
            """,
            (
                user_id,
                video_id,
                content
            )
        ).fetchone()


def get_comments(video_id):
    """
    Get all comments for a video.
    """

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT
                comments.*,
                users.username
            FROM comments
            JOIN users
                ON comments.user_id = users.id
            WHERE comments.video_id = %s
            ORDER BY comments.created_at ASC
            """,
            (video_id,)
        ).fetchall()


def update_comment(comment_id, content):
    """
    Update a comment.
    """

    with get_connection() as conn:
        return conn.execute(
            """
            UPDATE comments
            SET content = %s
            WHERE id = %s
            RETURNING *
            """,
            (
                content,
                comment_id
            )
        ).fetchone()


def delete_comment(comment_id):
    """
    Delete a comment.
    """

    with get_connection() as conn:
        result = conn.execute(
            """
            DELETE FROM comments
            WHERE id = %s
            RETURNING id
            """,
            (comment_id,)
        ).fetchone()

        return result is not None


# =========================================================
# Likes
# =========================================================

def like_video(user_id, video_id):
    """
    Like a video.

    ON CONFLICT prevents duplicate likes from the same user.
    """

    with get_connection() as conn:
        return conn.execute(
            """
            INSERT INTO likes (
                user_id,
                video_id
            )
            VALUES (%s, %s)
            ON CONFLICT (user_id, video_id)
            DO NOTHING
            RETURNING *
            """,
            (
                user_id,
                video_id
            )
        ).fetchone()


def unlike_video(user_id, video_id):
    """
    Remove a like from a video.
    """

    with get_connection() as conn:
        result = conn.execute(
            """
            DELETE FROM likes
            WHERE
                user_id = %s
                AND video_id = %s
            RETURNING id
            """,
            (
                user_id,
                video_id
            )
        ).fetchone()

        return result is not None


def has_user_liked_video(user_id, video_id):
    """
    Check whether a user has liked a video.
    """

    with get_connection() as conn:
        result = conn.execute(
            """
            SELECT id
            FROM likes
            WHERE
                user_id = %s
                AND video_id = %s
            """,
            (
                user_id,
                video_id
            )
        ).fetchone()

        return result is not None


def get_video_like_count(video_id):
    """
    Get total number of likes for a video.
    """

    with get_connection() as conn:
        result = conn.execute(
            """
            SELECT COUNT(*) AS like_count
            FROM likes
            WHERE video_id = %s
            """,
            (video_id,)
        ).fetchone()

        return result["like_count"]


# =========================================================
# Feed
# =========================================================

def get_video_feed(limit=20, offset=0):
    """
    Get videos for the home page feed.
    """

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT
                videos.*,
                users.username,
                COUNT(DISTINCT likes.id) AS like_count,
                COUNT(DISTINCT comments.id) AS comment_count
            FROM videos

            JOIN users
                ON videos.user_id = users.id

            LEFT JOIN likes
                ON likes.video_id = videos.id

            LEFT JOIN comments
                ON comments.video_id = videos.id

            GROUP BY
                videos.id,
                users.username

            ORDER BY videos.created_at DESC

            LIMIT %s
            OFFSET %s
            """,
            (
                limit,
                offset
            )
        ).fetchall()