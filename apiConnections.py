import google.auth
from google.oauth2 import service_account
from googleapiclient.discovery import build
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


# Set up credentials for the Google Books API
api_key = 'AIzaSyAS1ll-qIIwXodwRJZPln_k5mTzMMX7UrA'
google_books_api = build('books', 'v1', developerKey=api_key)

# Set up credentials for the Spotify API
spotify_client_id = '1cd807f73d0442a8946b04796cd45c57'
spotify_client_secret = 'd59d8ca6c4574fa1adf241ff40f770b5'
spotify_credentials = SpotifyClientCredentials(client_id=spotify_client_id, client_secret=spotify_client_secret)
spotify_api = spotipy.Spotify(client_credentials_manager=spotify_credentials)

# Use the Google Books API
result = google_books_api.volumes().list(q='microserfs').execute()
for book in result['items']:
    print(book['volumeInfo']['title'])

second = google_books_api.volumes()

# Use the Spotify API
result = spotify_api.search(q='red queen victoria aveyard', type='playlist', limit=1)
for playlist in result['playlists']['items']:
    print(playlist['name'])
    tracks = spotify_api.playlist_tracks(playlist['id'])['items']
    for track in tracks:
        title = track['track']['name']
        artist = track['track']['artists'][0]['name']
        print(title, "-", artist)

