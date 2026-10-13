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
            "description": "description1",
            "video": "http://farm3.staticflickr.com/2875/9069037713_1752f5daeb.jpg",
        },
        {
            "userName": "user2",
            "title": "test_title",
            "description": "test",
            "video": "http://farm3.staticflickr.com/2813/9069585985_80da8db54f.jpg"
        }
    ]
    missions = ["bird", "baseball", "book", "computer"]
    return render_template("homepage.html", posts = posts, missions = missions)

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/profile")
def profile():
    return render_template("profile_own.html")

if __name__ == "__main__":
    app.run(debug=True)