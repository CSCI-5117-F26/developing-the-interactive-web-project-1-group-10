from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

@app.route("/")
def homepage():
    return "Missions is running!"


if __name__ == "__main__":
    app.run(debug=True)