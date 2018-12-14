import time
import re
import requests
import os
from requests.auth import HTTPBasicAuth
from flask import Flask, request
from unidecode import unidecode
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
username = os.environ['USERNAME']
gh_token = 'GH_TOKEN'
token = ''
t_expiry = 0

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{username}.mysql.pythonanywhere-services.com/{username}${databasename}".format(
    username="USERNAME",
    password="PASSWORD",
    databasename="DB_NAME",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 280
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Lyrics(db.Model):
    __tablename__ = "stripper"

    id = db.Column(db.Integer, primary_key=True)
    song = db.Column(db.String(4096))
    artist = db.Column(db.String(4096))
    stripper = db.Column(db.String(4096))

    def __init__(self, song, artist, stripper):
        self.song = song
        self.artist = artist
        self.stripper = stripper

db.create_all()

def update_token():
    global token, t_expiry
    c_id = 'SPOTIFY_ID'
    secret = 'SPOTIFY_SECRET'
    r = requests.post('https://accounts.spotify.com/api/token', data={
        'grant_type': 'client_credentials'}, auth=HTTPBasicAuth(c_id, secret))
    token = r.json()['access_token']
    t_expiry = time.time()
    print('updated token', token)


update_token()


def stripper(song, artist):
    song = re.sub(r'\([^)]*\)', '', song).strip()  # remove braces and included text
    song = re.sub('- .*', '', song).strip()  # remove text after '- '
    song_data = artist + '-' + song
    # Remove special characters and spaces
    url_data = song_data.replace('&', 'and')
    url_data = url_data.replace(' ', '-')  # hyphenate the words together
    for ch in [',', '\'', '!', '.', '’', '"', '+', '?']:
        if ch in url_data:
            url_data = url_data.replace(ch, '')
    url_data = unidecode(url_data)  # remove accents and other diacritics
    return url_data


def create_issue(song, artist, stripper='not supported yet'):
    json = {
        "title": "{song} by {artist} unsupported.".format(song=song, artist=artist),
        "body": "Check if issue with swaglyrics or whether song lyrics "
                "unavailable on Genius. \n<hr>\n <tt><b>stripper -> {stripper}</b></tt>".format(
            stripper=stripper),
        "labels": ["unsupported song"]
    }
    r = requests.post('https://api.github.com/repos/aadibajpai/swaglyrics-for-spotify/issues',
                      auth=HTTPBasicAuth(username, gh_token), json=json)
    return {
        'status_code': r.status_code,
        'link': r.json()['html_url']
    }


def check_song(song, artist):
    global token, t_expiry
    print('using token', token)
    if t_expiry + 3600 - 300 < time.time():  # check if token expired ( - 300 to add buffer of 5 minutes)
        update_token()
    headers = {"Authorization": "Bearer {}".format(token)}
    r = requests.get('https://api.spotify.com/v1/search', headers=headers, params={
        'q': '{song} {artist}'.format(song=song, artist=artist), 'type': 'track'})
    data = r.json()['tracks']['items']
    if data:
        print(data[0]['artists'][0]['name'])
        print(data[0]['name'])
        if data[0]['name'] == song and data[0]['artists'][0]['name'] == artist:
            return True
    return False


@app.route('/unsupported', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        song = request.form['song']
        artist = request.form['artist']
        stripped = stripper(song, artist)
        print(song, artist, stripped)

        with open('unsupported.txt', 'r') as f:
            data = f.read()
        if '{song} by {artist}'.format(song=song, artist=artist) in data:
            return 'Issue already exists on the GitHub repo. \n' \
                   'https://github.com/aadibajpai/SwagLyrics-For-Spotify/issues'

        if check_song(song, artist):
            with open('unsupported.txt', 'a') as f:
                f.write('{song} by {artist} \n'.format(song=song, artist=artist))
                f.close()

            issue = create_issue(song, artist, stripped)
            if issue['status_code'] == 201:
                return 'Created issue on the GitHub repo for {song} by {artist}. \n{link}'.format(song=song,
                                                                                                  artist=artist,
                                                                                                  link=issue['link']
                                                                                                  )
            else:
                return 'Logged {song} by {artist} in the server.'.format(song=song, artist=artist)

        return "fak u nibba that's a fishy request \nIf you feel there's an error, open a " \
               "ticket at https://github.com/aadibajpai/SwagLyrics-For-Spotify/issues"
    
@app.route("/stripper", methods=["GET", "POST"])
def add_stripper():
    song = request.form['song']
    artist = request.form['artist']
    lyrics = Lyrics.query.filter(Lyrics.song==song).filter(Lyrics.artist==artist).first()
    if lyrics:
        return lyrics.stripper
    else:
        return "Stripper Not Found"

@app.route("/add_song", methods=["GET", "POST"])
def add_song():
    song = request.form['song']
    artist = request.form['artist']
    stripper = request.form['stripper']
    lyrics = Lyrics(song=song, artist=artist, stripper=stripper)
    db.session.add(lyrics)
    db.session.commit()
    with open('unsupported.txt', 'r') as f:
        lines = f.readlines()
    with open('unsupported.txt', 'w') as f:
        for line in lines:
            if line != "{song} by {artist}\n".format(song=song, artist=artist):
                f.write(line)           
    return "Added stripper for {song} by {artist} to database".format(song=song, artist=artist)

@app.route("/master_unsupported", methods=["GET", "POST"])
def master_unsupported():
    with open('unsupported.txt', 'r') as f:
        data = f.read()
    return data
