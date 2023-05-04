from config import *


def search_google_books(book_title, author_name): 
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

def search_spotify_playlists(book_title, author_name):
    # Search for playlist matching book title
    playlists = spotify_api.search(q=book_title, type='playlist', limit=10)['playlists']['items']
    print("Searching for playlist matching book title:")
    for playlist in playlists:
        print(" - ", playlist['name']) 
    for playlist in playlists:
        if book_title.lower() in playlist['name'].lower():
            playlist_id = playlist['id']
            playlist_name = playlist['name']
            playlist_details = spotify_api.playlist(playlist_id)
            playlist_tracks = spotify_api.playlist_tracks(playlist_id, fields='items(track(name,album(name),artists(name)))')['items']
            break
    
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

        if not playlist_ids:
            pass