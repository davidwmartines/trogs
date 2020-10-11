from flask import Flask, render_template

from . import app


@app.route("/")
def home():
    return "hello"

@app.route("/artist/<id>")
def artist(id):
    # get artist by id
   return render_template("artist.html", name=id)

@app.route("/track/<id>")
def track(id):
   return "track"

@app.route("/album/<id>")
def album(id):
   return "album"
