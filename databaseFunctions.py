from config import *
def store_playlist_info(cursor, playlist_data, book_id, playlist_details,playlist_name, playlist_id, playlist_spotify_id):
        follower_count = playlist_details['followers']['total']

        # Update the query to insert the playlist data with the follower_count field
        cursor.execute("INSERT INTO playlists (title, book_id, spotify_id, follower_count) VALUES (%s, %s, %s, %s)", (playlist_name, book_id, playlist_id, follower_count))
        playlist_id = cursor.fetchone()[0]
        # Get the playlist tracks
        playlist_tracks = spotify_api.playlist_tracks(playlist_id, fields='items(track(name, album(name, id, release_date), artists(name), popularity, duration_ms))')['items']

        # Store each track in the playlist_tracks, artists, and albums tables
        for item in playlist_tracks:
            track = item['track']
            store_track_info(track, playlist_spotify_id, playlist_id)

def store_track_info(cursor, track, playlist_spotify_id, playlist_id):
    # Get artist data
    artist_name = track['artists'][0]['name']
    artist_id = None

    # Check if artist exists in the database, otherwise insert it
    cursor.execute("SELECT artist_id FROM artists WHERE artist_name = %s", (artist_name,))
    result = cursor.fetchone()
    if result:
        artist_id = result[0]
    else:
        cursor.execute("INSERT INTO artists (artist_name) VALUES (%s) RETURNING artist_id", (artist_name,))
        artist_id = cursor.fetchone()[0]

    # Get album data
    album_name = track['album']['name']
    spotify_album_id = track['album']['id']
    release_year = track['album']['release_date'][:4]
    album_id = None

    # Check if album exists in the database, otherwise insert it
    cursor.execute("SELECT album_id FROM albums WHERE spotify_album_id = %s", (spotify_album_id,))
    result = cursor.fetchone()
    if result:
        album_id = result[0]
    else:
        cursor.execute("INSERT INTO albums (artist_id, album_name, spotify_album_id, release_year) VALUES (%s, %s, %s, %s) RETURNING album_id", (artist_id, album_name, spotify_album_id, release_year))
        album_id = cursor.fetchone()[0]

    # Get track data
    track_title = track['name']
    track_popularity = track['popularity']
    track_duration_ms = track['duration_ms']

    # Insert track data into playlist_tracks table
    cursor.execute("INSERT INTO playlist_tracks (artist_id, album_id, playlist_id, title, popularity, duration_ms) VALUES (%s, %s, %s, %s, %s, %s)", (artist_id, album_id, playlist_id, track_title, track_popularity, track_duration_ms))

    # Insert a record in playlist_albums
    cursor.execute("INSERT INTO playlist_albums (playlist_id, album_id) VALUES (%s, %s)", (playlist_id, album_id))

def store_book_info(cursor, book_data, book_title, author_name):
    # Parse Google Books API response from JSON response
    book_title = book_data["title"]
    book_description = book_data.get("description", "")
    book_author = book_data["authors"][0]
    publication_year = book_data["publishedDate"][:4]
    google_books_id = book_data["id"]
    isbn = book_data["industryIdentifiers"][0]["identifier"]

    # Use SQL INSERT statements to add book data to database
    cursor.execute("INSERT INTO authors (author_first_name, author_last_name) VALUES (%s, %s) RETURNING author_id", (book_author.split()[0], book_author.split()[-1]))
    author_id = cursor.fetchone()[0]
    cursor.execute("INSERT INTO books (title, author_id, publication_year, google_books_id, isbn) VALUES (%s, %s, %s, %s, %s) RETURNING book_id", (book_title, author_id, publication_year, google_books_id, isbn))
    book_id = cursor.fetchone()[0]

    # Create set of keywords from book title and description to use for Spotify API search
    stop_words = set(stopwords.words('english'))
    book_title_keywords = set(book_title.lower().split()) - stop_words
    book_description_keywords = set(book_description.lower().split()) - stop_words
    book_keywords = book_title_keywords | book_description_keywords
    # Remove trailing delimiters (period and comma) from book keywords
    book_keywords = {keyword.rstrip('.').rstrip(',') for keyword in book_keywords}

    # Use SQL INSERT statements to add book keywords to database
    for keyword in book_keywords:
        cursor.execute("INSERT INTO keywords (keyword_description) VALUES (%s) ON CONFLICT (keyword_description) DO UPDATE SET keyword_description = EXCLUDED.keyword_description RETURNING keyword_id", (keyword,))
        keyword_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO book_keywords (book_id, keyword_id) VALUES (%s, %s)", (book_id, keyword_id))

    return book_id, book_keywords

