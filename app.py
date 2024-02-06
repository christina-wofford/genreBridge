from config import * #Import the config file

app = Flask(__name__) #Create the Flask app
CORS(app, resources={r"/*": {"origins": "*"}}) #Had to add this to get the app to work on my local

@app.route('/search', methods=['GET', 'POST']) #Create a route for the search function from the front end

def search():#Search for the book and author entered by the user
    data = json.loads(request.data)
    book_title = data['book_title']
    author_name = data['author_name']

    book_data = query_google_books_api(book_title, author_name)
    book_id = store_book(book_data)
    playlist_name, playlist_id = query_spotify_api(book_id, book_title, author_name)
    return jsonify({"message": "Search complete, match made", "book_title": book_title, "author_name": author_name, "playlist_name": playlist_name, "playlist_id": playlist_id}), 200
 
def query_google_books_api(book_title, author_name): #Perform a query on the Google Books API. Search by title, author, and keywords until a match is made.
    result = google_books_api.volumes().list(q='inauthor:"{}" intitle:"{}"'.format(author_name, book_title)).execute()

    #Parse Google Books API response from JSON response
    book_data = result["items"][0]["volumeInfo"]
    book_title = book_data["title"]
    book_description = book_data.get("description", "")
    book_author = book_data["authors"][0]
    publication_year = book_data["publishedDate"][:4]
    google_books_id = result["items"][0]["id"]
    isbn = book_data["industryIdentifiers"][0]["identifier"]
    page_count = book_data.get("pageCount", None)

    #Remove stop words from book title and description to make useful keywords
    stop_words = set(stopwords.words('english'))
    book_title_keywords = set(book_title.lower().split()) - stop_words
    book_description_keywords = set(book_description.lower().split()) - stop_words
    book_keywords = book_title_keywords | book_description_keywords

    # Remove trailing delimiters (period and comma) from book keywords
    book_keywords = {keyword.rstrip('.').rstrip(',') for keyword in book_keywords}

    return { #Return what's needed for subsequent functions
        'book_title': book_title,
        'book_author': book_author,
        'publication_year': publication_year,
        'google_books_id': google_books_id,
        'isbn': isbn,
        'book_keywords': book_keywords,
        'page_count': page_count
    }

def store_book(book_data): #Put the books in the database
   
    book_title = book_data['book_title']
    book_author = book_data['book_author']
    publication_year = book_data['publication_year']
    google_books_id = book_data['google_books_id']
    isbn = book_data['isbn']
    book_keywords = book_data['book_keywords']

   # Make sure author does not already exist in database
    cursor.execute("SELECT author_id FROM authors WHERE author_first_name = %s AND author_last_name = %s", (book_author.split()[0], book_author.split()[-1]))
    result = cursor.fetchone()

    if result: #If they do, get their ID
        author_id = result[0]
    else:
        #If they don't, add them
        cursor.execute("INSERT INTO authors (author_first_name, author_last_name) SELECT %s, %s WHERE NOT EXISTS (SELECT 1 FROM authors WHERE author_first_name = %s AND author_last_name = %s) RETURNING author_id", 
                       (book_author.split()[0], book_author.split()[-1], book_author.split()[0], book_author.split()[-1]))
        author_id = cursor.fetchone()[0]

    #Store teh book in the database
    cursor.execute("INSERT INTO books (title, author_id, publication_year, google_books_id, isbn, page_count) VALUES (%s, %s, %s, %s, %s, %s) RETURNING book_id", 
                   (book_title, author_id, str(publication_year), google_books_id, isbn, book_data['page_count']))
    book_id = cursor.fetchone()[0]

    #Put the book and author into a mapping table   
    cursor.execute("INSERT INTO book_author_mapping (book_id, author_id) VALUES (%s, %s)", (book_id, author_id))

    #Store the keywords (with stop words removed) in the database and make sure they don't already exist before storing
    for keyword in book_keywords:
        cursor.execute("SELECT keyword_id FROM keywords WHERE keyword_description = %s", (keyword,))
        keyword_id = cursor.fetchone()
        if keyword_id:
            keyword_id = keyword_id[0]
    else:
        cursor.execute("INSERT INTO keywords (keyword_description) VALUES (%s) RETURNING keyword_id", (keyword,))
        keyword_id = cursor.fetchone()[0]
    cursor.execute("INSERT INTO book_keyword_mapping (book_id, keyword_id) VALUES (%s, %s)", (book_id, keyword_id))

    #Commit changes and return the book ID for the next functions
    connection.commit()
    return book_id
    
def query_spotify_api(book_id, book_title, author_name): #Search spotify API for the playlist   
    #Initialize variables for Spotify API search
    playlist_id = None
    playlist_name = None
    playlist_spotify_id = None
    follower_count = None

    #Query Spotify API for playlists matching book title
    playlists = spotify_api.search(q=book_title, type='playlist', limit=10)['playlists']['items']
    print("Retrieved???")
    for playlist in playlists:
        print(" - ", playlist['id'], playlist['name']) 
    for playlist in playlists:
        if book_title.lower() in playlist['name'].lower():
            playlist_id = playlist['id']
            playlist_name = playlist['name']
            playlist_tracks = spotify_api.playlist_tracks(playlist_id, fields='items(track(name,album(name),artists(name)))')['items']
            break
    
    #Try author name if book title search returns no results
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
    
    #Final attempt: search for playlists matching keywords
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

    #Give up if nothing is returned
    if not playlist_id:
        pass
        return None,None

    #When a match is found, extract the necessary information from the playlist and return it    
    if playlist_id:
        follower_count = spotify_api.playlist(playlist_id, fields='followers(total)')['followers']['total']
        store_playlist(book_id, playlist_id, playlist_name, follower_count)
        return playlist_name, playlist_id
    
def store_playlist(book_id, playlist_id, playlist_name,follower_count): #Put the playlist in the database
        #Add playlist to the playlists table
        cursor.execute("INSERT INTO playlists (title, spotify_id, follower_count) VALUES (%s, %s, %s) RETURNING playlist_id", 
                       (playlist_name, playlist_id, follower_count))
        db_playlist_id = cursor.fetchone()[0]
    
        #Add the book and playlist to a mapping table
        cursor.execute("INSERT INTO playlist_book_mapping (book_id, playlist_id) VALUES (%s, %s)", (book_id, db_playlist_id))

        #Fetch the tracks from the playlist
        playlist_tracks = spotify_api.playlist_tracks(playlist_id, fields='items(track(name, album(name, id, release_date), artists(name), popularity, duration_ms))')['items']

    #Add the tracks to the database
        for item in playlist_tracks:
            track = item['track']
            store_playlist_details(track, db_playlist_id)  # Pass the database playlist ID
        return playlist_name, playlist_id

def store_playlist_details(track, db_playlist_id): #STore all of the other playlist details
    #Artist name
    artist_name = track['artists'][0]['name']
    artist_id = None

    #Make sure artist dosn't exist before inserting
    cursor.execute("SELECT artist_id FROM artists WHERE artist_name = %s", (artist_name,))
    result = cursor.fetchone()
    if result:
        artist_id = result[0]
    else:
        cursor.execute("INSERT INTO artists (artist_name) VALUES (%s) RETURNING artist_id", (artist_name,))
        artist_id = cursor.fetchone()[0]

    #Fetch the album data
    album_name = track['album']['name']
    if 'id' in track['album']:
        spotify_album_id = track['album']['id']
    else:
        #Skip tracks with no album ID
        return
    release_year = track['album']['release_date'][:4]
    album_id = None

    #Make sure album isn't in database before inserting
    cursor.execute("SELECT album_id FROM albums WHERE spotify_album_id = %s", (spotify_album_id,))
    result = cursor.fetchone()
    if result:
        album_id = result[0]
    else:
        cursor.execute("INSERT INTO albums (artist_id, album_name, spotify_album_id, release_year) VALUES (%s, %s, %s, %s) RETURNING album_id", 
                       (artist_id, album_name, spotify_album_id, release_year))
        album_id = cursor.fetchone()[0]
    
    #Fetch the track data
    track_title = track['name']
    track_popularity = track['popularity']
    track_duration_ms = track['duration_ms']

    #Add the track to the database
    cursor.execute("INSERT INTO tracks (artist_id, album_id, title, popularity, duration_ms) VALUES (%s, %s, %s, %s, %s) RETURNING track_id", 
               (artist_id, album_id, track_title, track_popularity, track_duration_ms))
    track_id = cursor.fetchone()[0]

    #Add playlist and track to mapping table
    cursor.execute("INSERT INTO playlist_track_mapping (playlist_id, track_id) VALUES (%s, %s)", (db_playlist_id, track_id))
    connection.commit()

if __name__ == '__main__': #Run the app
    app.run(debug=True, use_reloader=False)
