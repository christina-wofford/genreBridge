from config import *

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/search', methods=['GET', 'POST'])
def search():
    data = json.loads(request.data)
    book_title = data['book_title']
    author_name = data['author_name']
    
    #Query Google Books API
    result = google_books_api.volumes().list(q='inauthor:"{}" intitle:"{}"'.format(author_name, book_title)).execute()

    #Parse Google Books API response from JSON response
    book_data = result["items"][0]["volumeInfo"]
    book_title = book_data["title"]
    book_description = book_data.get("description", "")
    book_author = book_data["authors"][0]
    publication_year = book_data["publishedDate"][:4]
    google_books_id = result["items"][0]["id"]
    isbn = book_data["industryIdentifiers"][0]["identifier"]

    #Create set of keywords from book title and description to use for Spotify API search
    stop_words = set(stopwords.words('english'))
    book_title_keywords = set(book_title.lower().split()) - stop_words
    book_description_keywords = set(book_description.lower().split()) - stop_words
    book_keywords = book_title_keywords | book_description_keywords
    # Remove trailing delimiters (period and comma) from book keywords
    book_keywords = {keyword.rstrip('.').rstrip(',') for keyword in book_keywords}

   # Check if author already exists
    cursor.execute("SELECT author_id FROM authors WHERE author_first_name = %s AND author_last_name = %s", (book_author.split()[0], book_author.split()[-1]))
    result = cursor.fetchone()

    if result:
        author_id = result[0]
    else:
        # Insert new author if not a duplicate
        cursor.execute("INSERT INTO authors (author_first_name, author_last_name) SELECT %s, %s WHERE NOT EXISTS (SELECT 1 FROM authors WHERE author_first_name = %s AND author_last_name = %s) RETURNING author_id", (book_author.split()[0], book_author.split()[-1], book_author.split()[0], book_author.split()[-1]))
        author_id = cursor.fetchone()[0]

# Insert book
    cursor.execute("INSERT INTO books (title, author_id, publication_year, google_books_id, isbn) VALUES (%s, %s, %s, %s, %s) RETURNING book_id", (book_title, author_id, str(publication_year), google_books_id, isbn))
    book_id = cursor.fetchone()[0]

    # Insert book-author mapping
    cursor.execute("INSERT INTO book_author_mapping (book_id, author_id) VALUES (%s, %s)", (book_id, author_id))

    #Use SQL INSERT statements to add book keywords to database
    for keyword in book_keywords:
        cursor.execute("SELECT keyword_id FROM keywords WHERE keyword_description = %s", (keyword,))
        keyword_id = cursor.fetchone()
    if keyword_id:
        # The keyword already exists
        keyword_id = keyword_id[0]
    else:
        # The keyword doesn't exist, insert it
        cursor.execute("INSERT INTO keywords (keyword_description) VALUES (%s) RETURNING keyword_id", (keyword,))
        keyword_id = cursor.fetchone()[0]
    cursor.execute("INSERT INTO book_keyword_mapping (book_id, keyword_id) VALUES (%s, %s)", (book_id, keyword_id))

    #Commit changes to database
    connection.commit()
    
    #Initialize variables for Spotify API search
    playlist_id = None
    playlist_name = None
    playlist_spotify_id = None
    follower_count = None

    # Search for playlist matching book title
    playlists = spotify_api.search(q=book_title, type='playlist', limit=10)['playlists']['items']
    print("Searching for playlist matching book title:")
    for playlist in playlists:
        print(" - ", playlist['id'], playlist['name']) 
    for playlist in playlists:
        if book_title.lower() in playlist['name'].lower():
            playlist_id = playlist['id']
            playlist_name = playlist['name']
            playlist_tracks = spotify_api.playlist_tracks(playlist_id, fields='items(track(name,album(name),artists(name)))')['items']
            break
    
    # If no matching playlist found, search for playlist matching author name
    if not playlist_id:
        playlists = spotify_api.search(q=author_name, type='playlist', limit=10)['playlists']['items']
        print("Searching for playlist matching author name:")
        for playlist in playlists:
            print(" - ", playlist['name'])
        for playlist in playlists:
            if author_name.lower() in playlist['name'].lower():
                playlist_id = playlist['id']
                playlist_name = playlist['name']
                print(playlist_name)
                playlist_tracks = spotify_api.playlist_tracks(playlist_id, fields='items(track(name,album(name),artists(name)))')['items']
                break
    
    # If still no matching playlist found, search for playlists matching book keywords
    if not playlist_id:
        stop_words = set(stopwords.words('english'))
        book_keywords = set(book_title.lower().replace(',', '').replace('.', '').split()) - stop_words
        playlist_ids = []
        for keyword in book_keywords:
            playlists = spotify_api.search(q=keyword, type='playlist', limit=10)['playlists']['items']
        for playlist in playlists:
            if playlist['id'] not in playlist_ids:
                playlist_ids.append(playlist['id'])
                playlist_tracks = spotify_api.playlist_tracks(playlist['id'], fields='items(track(name,album(name),artists(name)))')['items']

    if not playlist_id:
        pass
        
    if playlist_id:
    # Update the query to insert the playlist data with the follower_count field
        cursor.execute("INSERT INTO playlists (title, spotify_id, follower_count) VALUES (%s, %s, %s) RETURNING playlist_id", (playlist_name, playlist_id, follower_count))
        db_playlist_id = cursor.fetchone()[0]
    
        # Insert book_id and playlist_id into the playlist_book_mapping table
        cursor.execute("INSERT INTO playlist_book_mapping (book_id, playlist_id) VALUES (%s, %s)", (book_id, db_playlist_id))

        # Get the playlist tracks
        playlist_tracks = spotify_api.playlist_tracks(playlist_id, fields='items(track(name, album(name, id, release_date), artists(name), popularity, duration_ms))')['items']

    # Store each track in the playlist_tracks, artists, and albums tables
    for item in playlist_tracks:
        track = item['track']
        store_track_info(track, db_playlist_id)  # Pass the database playlist ID

    return jsonify({"message": "Data received and processed", "book_title": book_title, "author_name": author_name, "playlist_name": playlist_name, "playlist_id": playlist_id})

def store_track_info(track, db_playlist_id):
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
    if 'id' in track['album']:
        spotify_album_id = track['album']['id']
    else:
        # Skipping the track if the album id is missing
        return
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

    # Insert track data into tracks table
    cursor.execute("INSERT INTO tracks (artist_id, album_id, title, popularity, duration_ms) VALUES (%s, %s, %s, %s, %s)", (artist_id, album_id, track_title, track_popularity, track_duration_ms))

    # Insert a record in playlist_albums
    cursor.execute("INSERT INTO playlist_albums (playlist_id, album_id) VALUES (%s, %s)", (db_playlist_id, album_id))
    connection.commit

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
