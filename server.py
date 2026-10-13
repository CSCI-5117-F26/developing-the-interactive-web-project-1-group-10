from flask import Flask, redirect, render_template, request, url_for
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route("/")
def homepage():
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
        }
    ]
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

    category = request.args.get("category") or "general"
    mission = list(filter(lambda m : m["category"] == category, missions))[0]["mission"]
    return render_template("homepage.html", posts=posts, mission=mission, category=category)

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/profile")
def profile():
    return render_template("profile_own.html")

@app.route("/profile_other")
def profile_other():
    return render_template("profile_other.html")

if __name__ == "__main__":
    app.run(debug=True)
