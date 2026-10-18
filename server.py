from functools import wraps
from flask import Flask, redirect, render_template, request, url_for, session
import os
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from urllib.parse import quote_plus, urlencode

from database import get_videos_by_category, get_connection
from weather import get_random_weather

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(24)

class AuthError(Exception):
  def __init__(self, error, status_code):
    self.error = error
    self.status_code = status_code

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
    if request.endpoint not in {"homepage", "profile", "profile_other"}:
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

    with get_connection() as conn:
      with conn.cursor() as cur:
        cur.execute("SELECT user_id, username FROM users WHERE auth0_id = %s;", (sub_id,))
        user = cur.fetchone()

        if user:
            user_id = user["user_id"]
            username = user["username"]
        else:
          username = name
          cur.execute(
            """
            INSERT INTO users (auth0_id, username, email)
            VALUES (%s, %s, %s)
            RETURNING user_id;
            """,
            (sub_id, username, email)
          )
          user_id = cur.fetchone()
          conn.commit()

    session["user"] = token
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

    posts = [
        {
            "userName": "user1",
            "title": "title1",
            "category": "sport",
            "description": "description1",
            "video": "http://farm3.staticflickr.com/2875/9069037713_1752f5daeb.jpg",
        },
        {
            "userName": "user2",
            "title": "test_title",
            "category": "study",
            "description": "test",
            "video": "http://farm3.staticflickr.com/2813/9069585985_80da8db54f.jpg"
        },
        {
            "userName": "user3",
            "title": "bird!!",
            "category": "general",
            "description": "Look at this bird!!!",
            "video": "http://farm3.staticflickr.com/2813/9069585985_80da8db54f.jpg"
        },
        {
            "userName": "user4",
            "title": "bird!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",
            "category": "general",
            "description": "Look at this bird!!!",
            "video": "http://farm3.staticflickr.com/2813/9069585985_80da8db54f.jpg"
        }
    ]

    database_videos = get_videos_by_category(category)
    posts.extend(
        {
            "userName": video["username"],
            "title": video["title"],
            "category": video["category"],
            "description": video["description"],
            "video": video["video_url"],
        }
        for video in database_videos
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
    return render_template("homepage.html", posts=posts, mission=mission, category=category)

@app.route("/profile")
@requires_auth
def profile():
    return render_template("profile_own.html")

@app.route("/profile_other")
@requires_auth
def profile_other():
    return render_template("profile_other.html")

if __name__ == "__main__":
    app.run(debug=True)
