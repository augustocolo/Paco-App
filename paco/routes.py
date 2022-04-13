from flask import render_template
from paco import app


@app.route('/')
def index():
    return render_template("landing_user.html")


@app.route('/login')
def login(methods=["GET"]):
    return render_template("login.html")