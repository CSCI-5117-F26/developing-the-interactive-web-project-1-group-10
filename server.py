from functools import wraps
from flask import Flask, redirect, render_template, request, url_for, session
import os
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth

from database import get_videos_by_category
from weather import get_minneapolis_weather, get_random_weather

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(24)


@app.context_processor
def inject_weather():
    weather = session.get("weather_override") or get_minneapolis_weather()
    return {"weather": weather}


@app.route("/weather/random")
def change_weather_random():
    current_weather = session.get("weather_override") or get_minneapolis_weather()
    session["weather_override"] = get_random_weather(current_weather["effect"])
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
    return render_template("homepage.html")
  return render_template("login.html")

@app.route("/callback", methods=["GET", "POST"])
def callback():
    """
    Callback redirect from Auth0
    """
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    # The app assumes for a /profile path to be available, change here if it's not
    return redirect("/homepage")

@app.route("/login", methods=["POST"])
def login():
    """
    Redirects the user to the Auth0 Universal Login (https://auth0.com/docs/authenticate/login/auth0-universal-login)
    """
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/signup")
def signup():
  return render_template("signup.html")

@app.route("/homepage")
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
def profile():
    return render_template("profile_own.html")

@app.route("/profile_other")
def profile_other():
    return render_template("profile_other.html")

if __name__ == "__main__":
    app.run(debug=True)
