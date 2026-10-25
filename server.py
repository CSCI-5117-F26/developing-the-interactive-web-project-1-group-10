from functools import wraps
from flask import Flask, abort, redirect, render_template, request, url_for, session
import os
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from urllib.parse import quote_plus, urlencode
from secrets import compare_digest, token_urlsafe
from psycopg.errors import ForeignKeyViolation

from database import subscribe as create_subscription
import database

from s3_utils import upload_video_to_s3, delete_video_from_s3

from weather import get_random_weather
from datetime import date, timedelta
import random

MISSION_OPTIONS = {
    "general": ["bird", "tree", "sunset"],
    "sport": ["baseball", "running", "basketball"],
    "study": ["book", "notes", "library"],
    "hobby": ["drawing", "music", "cooking"],
}

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(24)

class AuthError(Exception):
  def __init__(self, error, status_code):
    self.error = error
    self.status_code = status_code

def get_current_user_id():
    user = session.get("user")
    return user.get("user_id") if user else None

def requires_auth(f):
  """
  Use on routes that require a valid session, otherwise it aborts with a 403
  """
  @wraps(f)
  def decorated(*args, **kwargs):
    if session.get("user") is None:
      return redirect(url_for("login"))

    return f(*args, **kwargs)

  return decorated

@app.context_processor
def inject_weather():
    if request.endpoint not in {"homepage", "profile", "my_profile", "upload_page", "vlog_detail", "liked_videos", "subscription_list"}:
        return {}

    weather = session.get("weather_override")
    weather_auto = weather is None

    if weather_auto:
        weather = {"effect": "none", "intensity": 0, "density": 0, "mode": "day"}

    return {"weather": weather, "weather_auto": weather_auto}


@app.route("/weather/random")
def change_weather_random():
    current_weather = session.get("weather_override")
    excluded_effect = current_weather["effect"] if current_weather else None
    session["weather_override"] = get_random_weather(excluded_effect)
    return redirect(url_for("homepage"))


@app.route("/weather/auto")
def change_weather_auto():
    session.pop("weather_override", None)
    return redirect(url_for("homepage"))


app.secret_key = os.environ["FLASK_SECRET"]

oauth = OAuth(app)

domain = os.environ["AUTH0_DOMAIN"]
client_id = os.environ["AUTH0_CLIENT_ID"]
client_secret = os.environ["AUTH0_CLIENT_SECRET"]

oauth.register(
    "auth0",
    client_id=client_id,
    client_secret=client_secret,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{domain}/.well-known/openid-configuration',
)

@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("homepage"))

    return render_template("login.html")

@app.route("/callback", methods=["GET", "POST"])
def callback():
    """
    Callback redirect from Auth0
    """
    token = oauth.auth0.authorize_access_token()
    userinfo = token.get("userinfo")

    sub_id = userinfo["sub"]
    name = userinfo["name"]
    email = userinfo["email"]

    user_id, username = database.create_user(sub_id, name, email)
    print(f"User: {user_id}, {username}")

    session["user"] = {
       "user_id": user_id,
       "username": username
    }
    # The app assumes for a /profile path to be available, change here if it's not
    return redirect("/homepage")

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Redirects the user to the Auth0 Universal Login (https://auth0.com/docs/authenticate/login/auth0-universal-login)
    """
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/signup")
def signup():
    """
    Redirects the user to the Auth0 Universal Login (https://auth0.com/docs/authenticate/login/auth0-universal-login)
    """
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True),
        screen_hint="signup"
    )

@app.route("/logout")
@requires_auth
def logout():
  session.clear()
  return redirect(
    "https://" + domain
    + "/v2/logout?"
    + urlencode(
      {
        "returnTo": url_for("index", _external=True),
        "client_id": client_id,
      },
      quote_via=quote_plus
    )
  )

@app.route("/homepage")
@requires_auth
def homepage():
    category = request.args.get("category") or "general"

    valid_categories = ["general", "sport", "study", "hobby", "following"]
    if category not in valid_categories:
        abort(404)
    if "csrf_token" not in session:
        session["csrf_token"] = token_urlsafe(32)

    posts = []

    database_videos = database.get_videos_by_category(category, get_current_user_id())
    posts.extend(
        {
            "video_id": video["video_id"],
            "liked": video["liked"],
            "like_count": video["like_count"],
            "comment_count": video["comment_count"],
            "userName": video["userName"],
            "author_id": video["author_id"],
            "title": video["title"],
            "category": video["category"],
            "description": video["description"],
            "video": video["video_url"],
        }
        for video in database_videos
    )

    following_videos = database.get_following_videos(get_current_user_id())
    following_posts = []

    following_posts.extend(
        {
            "video_id": video["video_id"],
            "liked": video["liked"],
            "like_count": video["like_count"],
            "comment_count": video["comment_count"],
            "userName": database.get_users_by_id(video["author_id"])["username"],
            "author_id": video["author_id"],
            "title": video["title"],
            "category": video["category"],
            "description": video["description"],
            "video": video["video_url"],
        }
        for video in following_videos
    )

    missions = [
        {
            "category": "following",
            "mission": "None",
        },
        {
            "category": "general",
            "mission": "bird",
        },
        {
            "category": "sport",
            "mission": "baseball",
        },
        {
            "category": "study",
            "mission": "book",
        },
        {
            "category": "hobby",
            "mission": "online",
        },
    ]

    mission = list(filter(lambda m : m["category"] == category, missions))[0]["mission"]
    print(following_posts)
    return render_template("homepage.html", posts=posts, mission=mission, category=category, following_posts=following_posts)

@app.route("/upload", methods=["GET"])
@requires_auth
def upload_page():
  return render_template("upload.html")

@app.route("/upload", methods=["POST"])
@requires_auth
def upload_submit():
  author_id = session["user"].get("user_id")

  if not author_id:
    return "Unauthorized", 401

  title = request.form.get("title")
  description = request.form.get("description", "")
  category = request.form.get("category", "General")
  file = request.files.get("video_file")

  if not file or file.filename == "":
    return "No video file selected", 400

  if not title:
    return "Title is required", 400

  try:
    video_url = upload_video_to_s3(file)

    with database.get_connection() as conn:
      with conn.cursor() as cur:
        cur.execute(
          """
          INSERT INTO videos (author_id, title, description, video_url, category)
          VALUES (%s, %s, %s, %s, %s);
          """,
          (author_id, title, description, video_url, category)
        )
        conn.commit()

  except Exception as e:
    print(f"Failed to process video upload: {e}")
    return f"Error: {e}", 500

  return redirect(url_for("homepage", category=category))

@app.route("/videos/<int:video_id>")
@requires_auth
def vlog_detail(video_id):
    post = database.get_video_by_id(video_id, get_current_user_id())
    if post is None:
        abort(404)

    if "csrf_token" not in session:
        session["csrf_token"] = token_urlsafe(32)

    return render_template(
        "vlog_detail.html", post=post, category=post["category"], is_detail=True,
        comments=database.get_comments(video_id), current_user_id=get_current_user_id(),
    )


def comment_data(comment, user_id):
    return {
        "comment_id": comment["comment_id"],
        "video_id": comment["video_id"],
        "author_id": comment["author_id"],
        "username": comment["username"],
        "content": comment["content"],
        "created_at": comment["created_at"].isoformat(),
        "profile_url": url_for("profile", id=comment["author_id"]),
        "delete_url": url_for("comment_delete", comment_id=comment["comment_id"])
        if comment["author_id"] == user_id else None,
    }


@app.route("/api/videos/<int:video_id>/comments", methods=["GET", "POST"])
def video_comments(video_id):
    user_id = get_current_user_id()
    if user_id is None:
        return {"error": "Please log in to view or post comments."}, 401

    if request.method == "POST":
        csrf_token = session.get("csrf_token")
        if not csrf_token or not compare_digest(csrf_token.encode(), request.headers.get("X-CSRF-Token", "").encode()):
            return {"error": "Please refresh the page and try again."}, 403
        payload = request.get_json(silent=True)
        content = payload.get("content") if isinstance(payload, dict) else None
        if not isinstance(content, str) or not 1 <= len(content.strip()) <= 1000:
            return {"error": "Comments must contain 1–1000 characters."}, 400
        content = content.strip()
        try:
            content.encode("utf-8")
        except UnicodeEncodeError:
            return {"error": "The comment contains invalid text."}, 400
        if "\x00" in content:
            return {"error": "The comment contains invalid text."}, 400

    with database.get_connection() as conn:
        exists = conn.execute(
            """
            SELECT EXISTS (SELECT 1 FROM users WHERE user_id = %s) AS user_exists,
                   EXISTS (SELECT 1 FROM videos WHERE video_id = %s) AS video_exists
            """,
            (user_id, video_id),
        ).fetchone()
    if not exists["user_exists"]:
        return {"error": "Please log in again."}, 401
    if not exists["video_exists"]:
        return {"error": "This video is no longer available."}, 404

    if request.method == "GET":
        comments = database.get_comments(video_id)
        return {"comments": [comment_data(comment, user_id) for comment in comments], "comment_count": len(comments)}

    try:
        comment = database.create_comment(video_id, user_id, content)
    except ForeignKeyViolation:
        return {"error": "The video or account is no longer available. Please refresh the page."}, 404
    return {"comment": comment_data(comment, user_id), "comment_count": comment["comment_count"]}, 201


@app.route("/api/comments/<int:comment_id>", methods=["DELETE"])
def comment_delete(comment_id):
    user_id = get_current_user_id()
    if user_id is None:
        return {"error": "Please log in to delete comments."}, 401
    csrf_token = session.get("csrf_token")
    if not csrf_token or not compare_digest(csrf_token.encode(), request.headers.get("X-CSRF-Token", "").encode()):
        return {"error": "Please refresh the page and try again."}, 403

    with database.get_connection() as conn:
        state = conn.execute(
            """
            SELECT EXISTS (SELECT 1 FROM users WHERE user_id = %s) AS user_exists,
                   (SELECT author_id FROM comments WHERE comment_id = %s) AS author_id
            """,
            (user_id, comment_id),
        ).fetchone()
    if not state["user_exists"]:
        return {"error": "Please log in again."}, 401
    if state["author_id"] is None:
        return {"error": "This comment is no longer available."}, 404
    if state["author_id"] != user_id:
        return {"error": "You can only delete your own comments."}, 403
    deleted = database.delete_comment(comment_id, user_id)
    if deleted is None:
        return {"error": "This comment is no longer available."}, 404
    return deleted


@app.route("/liked_videos")
@requires_auth
def liked_videos():
    liked_videos = database.get_liked_videos(get_current_user_id())
    
    posts = []

    posts.extend(
        {
            "video_id": video["video_id"],
            "liked": video["liked"],
            "like_count": video["like_count"],
            "comment_count": video["comment_count"],
            "userName": database.get_users_by_id(video["author_id"])["username"],
            "author_id": video["author_id"],
            "title": video["title"],
            "category": video["category"],
            "description": video["description"],
            "video": video["video_url"],
        }
        for video in liked_videos
    )

    if "csrf_token" not in session:
        session["csrf_token"] = token_urlsafe(32)

    return render_template(
        "liked_videos.html", posts=posts, is_detail=False
    )

@app.route("/subscription_list")
@requires_auth
def subscription_list():
    list = database.get_following_lists(get_current_user_id())

    if "csrf_token" not in session:
        session["csrf_token"] = token_urlsafe(32)

    return render_template(
        "subscription_list.html", user_lists=list
    )

@app.route("/api/videos/<int:video_id>/like", methods=["POST", "DELETE"])
def video_like(video_id):
    user_id = get_current_user_id()
    if user_id is None:
        return {"error": "Please log in to like videos."}, 401

    csrf_token = session.get("csrf_token")
    if not csrf_token or not compare_digest(csrf_token.encode(), request.headers.get("X-CSRF-Token", "").encode()):
        return {"error": "Please refresh the page and try again."}, 403

    with database.get_connection() as conn:
        exists = conn.execute(
            """
            SELECT EXISTS (SELECT 1 FROM users WHERE user_id = %s) AS user_exists,
                   EXISTS (SELECT 1 FROM videos WHERE video_id = %s) AS video_exists
            """,
            (user_id, video_id),
        ).fetchone()

    if not exists["user_exists"]:
        return {"error": "Please log in again."}, 401
    if not exists["video_exists"]:
        return {"error": "This video is no longer available."}, 404

    if request.method == "POST":
        database.like_video(user_id, video_id)
    else:
        database.unlike_video(user_id, video_id)

    return database.get_video_like_state(user_id, video_id)

@app.route("/profile")
@requires_auth
def my_profile():
    return profile(get_current_user_id())

@app.route("/profile/<int:id>")
@requires_auth
def profile(id):
    user_id = id or get_current_user_id()
    my_id = get_current_user_id()
    user_info = database.get_users_by_id(user_id, my_id=my_id)
    posts = database.get_videos_by_id(user_id)
    return render_template("profile.html", user_info=user_info, posts=posts, my_id = my_id)

@app.route("/api/subscribe/<int:user_id>", methods=["POST", "DELETE"])
def subscribe(user_id):
    my_id = get_current_user_id()
    if user_id is None:
        return {"error": "Please log in to subscribe."}, 401
    if my_id == user_id:
        return {"error": "Cannot subscribe my account."}, 401

    csrf_token = session.get("csrf_token")
    if not csrf_token or not compare_digest(csrf_token.encode(), request.headers.get("X-CSRF-Token", "").encode()):
        return {"error": "Please refresh the page and try again."}, 403

    if request.method == "POST":
        create_subscription(my_id, user_id)
    else:
        database.unsubscribe(my_id, user_id)

    return database.get_subscription_state(my_id, user_id)

def get_daily_mission(mission_date, category):
    with database.get_connection() as conn:
        mission = conn.execute(
            """
            SELECT mission
            FROM daily_missions
            WHERE mission_date = %s AND category = %s
            """,
            (mission_date, category),
        ).fetchone()

    return mission

def get_or_create_daily_mission(mission_date, category):
    today_mission = get_daily_mission(mission_date, category)

    if today_mission is not None:
        return today_mission["mission"]

    yesterday = mission_date - timedelta(days=1)
    yesterday_mission = get_daily_mission(yesterday, category)

    options_list = MISSION_OPTIONS[category].copy()

    if yesterday_mission is not None:
        previous = yesterday_mission["mission"]

        if previous in options_list:
            options_list.remove(previous)

    selected_mission = random.choice(options_list)
    with database.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO daily_missions (mission_date, category, mission)
            VALUES (%s, %s, %s)
            """,
            (mission_date, category, selected_mission),
        )
    return selected_mission

def generate_daily_missions():
    today = date.today()

    for category in MISSION_OPTIONS:
        mission = get_or_create_daily_mission(today, category)
        print(category, mission)

if __name__ == "__main__":
    app.run(debug=True)
