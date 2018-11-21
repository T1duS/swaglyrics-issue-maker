import requests
import os
from requests.auth import HTTPBasicAuth
from flask import Flask, request

app = Flask(__name__)
gh_token = os.environ['GITHUB_TOKEN']  # import your GitHub API token as system variable
username = 'aadibajpai'
spotify_token = 'token'


def create_issue(song, artist):
    json = {
        "title": "{song} by {artist} unsupported.".format(song=song, artist=artist),
        "body": "Check if issue with swaglyrics or whether song lyrics unavailable on Genius.",
        "labels": ["unsupported song"]
}
    r = requests.post('https://api.github.com/repos/aadibajpai/swaglyrics-for-spotify/issues',
                      auth=HTTPBasicAuth(username, gh_token), json=json)
    return {
        'status_code': r.status_code,
        'link': r.json()['html_url']
    }


def new_spotify_token():
    """
    Generates new access token when previous expires
    :return: new access token
    """
    c_id = 'CLIENT_ID'
    secret = 'SECRET'
    r = requests.post('https://accounts.spotify.com/api/token', data={'grant_type': 'client_credentials'},
                      auth=HTTPBasicAuth(c_id, secret))
    return r.json()['access_token']


def check_spotify(song, artist, token=spotify_token):
    global spotify_token
    try:
        headers = {"Authorization": "Bearer {}".format(token)}
        r = requests.get('https://api.spotify.com/v1/search', headers=headers,
                         params={'q': '{song} {artist}'.format(song=song, artist=artist), 'type': 'track'})
        r.raise_for_status()
        data = r.json()['tracks']['items']  # should be [] if song not on spotify
        if data:
            if data[0]['artists'][0]['name'] == artist:
                return True
        return False
    except requests.exceptions.HTTPError:
        spotify_token = new_spotify_token()
        check_spotify(song, artist)


@app.route('/unsupported', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        song = request.form['song']
        artist = request.form['artist']
        if not check_spotify(song, artist):
            return "That song-artist pair doesn't exist on Spotify lol. \nIf you feel there's an error, open a " \
                   "ticket at https://github.com/aadibajpai/SwagLyrics-For-Spotify/issues"
        with open('unsupported.txt', 'r') as f:
            data = f.read()
            f.close()
        if '{song} by {artist}'.format(song=song, artist=artist) in data:
            return 'Issue already exists on the GitHub repo. \n' \
                   'https://github.com/aadibajpai/SwagLyrics-For-Spotify/issues'

        with open('unsupported.txt', 'a') as f:
            f.write('{song} by {artist} \n'.format(song=song, artist=artist))
            f.close()
        issue = create_issue(song, artist)
        if issue['status_code'] == 201:
            return 'Created issue on the Github repo for {song} by {artist}. \n{link}'.format(song=song,
                                                                                              artist=artist,
                                                                                              link=issue['link'])
        else:
            return 'Logged {song} by {artist} in the server.'.format(song=song, artist=artist)
