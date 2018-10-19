import requests
from requests.auth import HTTPBasicAuth
from flask import Flask, request

app = Flask(__name__)
token = 'TOKEN'  # insert your GitHub API token

def create_issue(song, artist):
    json = {
		"title": "{song} by {artist} unsupported.".format(song=song, artist=artist),
		"body": "Check if issue with swaglyrics or whether song lyrics unavailable on Genius.",
		"labels": ["unsupported song"]
}
    r = requests.post('https://api.github.com/repos/aadibajpai/swaglyrics-for-spotify/issues', auth=HTTPBasicAuth('GITHUB_USERNAME', token), json=json)
    return r.status_code

@app.route('/unsupported', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        song = request.form['song']
        artist = request.form['artist']
        with open('unsupported.txt', 'a') as f:
	        f.write('{song} by {artist} \n '.format(song=song, artist=artist))
	        f.close()
        if create_issue(song, artist) == 201:
            return 'Created issue on the Github repo for {song} by {artist}.'.format(song=song, artist=artist)
        else:
            return 'Logged {song} by {artist} in the server.'.format(song=song, artist=artist)