import psycopg2
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Set up credentials for the Spotify API
spotify_client_id = '1cd807f73d0442a8946b04796cd45c57'
spotify_client_secret = 'd59d8ca6c4574fa1adf241ff40f770b5'
spotify_credentials = SpotifyClientCredentials(client_id=spotify_client_id, client_secret=spotify_client_secret)
spotify_api = spotipy.Spotify(client_credentials_manager=spotify_credentials)

# Set up credentials for the Postgres database
conn = psycopg2.connect(
    host="localhost",
    database="genrebridge",
    user="christina",
    password="dispute"
)
cur = conn.cursor()

book_id = cur.fetchone()[0]

# Get the tags for a book
cur.execute(
    """
    SELECT tag
    FROM tags
    WHERE tag_id IN (
        SELECT tag_id
        FROM pairings
        WHERE book_id = %s
    )
    """,
    (book_id,)
)

tags = [row[0] for row in cur.fetchall()]

# Search for playlists that match the tags for the book
playlist_ids = []
for tag in tags:
    playlists = spotify_api.search(q='tag:"{}"'.format(tag), type='playlist')['playlists']['items']
    for playlist in playlists:
        playlist_ids.append(playlist['id'])

# Get the names of the playlists
playlist_names = []
for playlist_id in playlist_ids:
    playlist = spotify_api.playlist(playlist_id)
    playlist_names.append(playlist['name'])

# Print out the names of the playlists
print("Playlists that match the tags for the book:")
for playlist_name in playlist_names:
    print("- " + playlist_name)

# Close the Postgres database connection
cur.close()
conn.close()
