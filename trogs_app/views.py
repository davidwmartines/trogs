from flask import Flask, render_template

from . import app
from . import artists


@app.route("/")
def home():

   #show all artists on home page
   allArtists  = artists.list_all()
   return render_template("home.html", artists=allArtists)

@app.route("/artist/<id>")
def artist(id):
    # get artist by id
   return render_template("artist.html", name=id)

@app.route("/track/<id>")
def track(id):
   # get track by id
   return render_template("track.html", title="Moonlight Serenade", url="https://dxffd4gk9zzvk2.s3.us-east-2.amazonaws.com/solos/moonlight+serenade.flac")

@app.route("/album/<id>")
def album(id):
   # get album by id
   return render_template("album.html", title=id)
