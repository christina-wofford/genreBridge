import google.auth 
from googleapiclient.discovery import build
import psycopg2
import configparser

#set up config file to hide crendentials
config = configparser.ConfigParser()
config.read('config.ini')

host = config.get('database', 'host')
database = config.get('database', 'database')
user = config.get('database', 'user')
password = config.get('database', 'password')
api_key = config.get('google_books_api', 'api_key')

google_books_api = build('books', 'v1', developerKey=api_key)
#connect to postgres
conn = psycopg2.connect(
    host="host",
    database="database",
    user="user",
    password="password"
)
cur = conn.cursor()

#search for book title and author (this will eventually need to be connected to the frontend to accept user input)
result = google_books_api.volumes().list(q='inauthor:"rowling" intitle:"harry potter"').execute()

#pull book title, author, Google Books volume id, and ISBN
for book in result['items'][:1]:
    volume_ID = book['id']
    title = book['volumeInfo']['title']
    
    author = book['volumeInfo'].get('authors', [])
    if author:
        author_name = str(author)[1:-1]
    else:
        author_name = ""

    publication_year = book['volumeInfo'].get('publishedDate', 'N/A')
    isbn = book['volumeInfo'].get('industryIdentifiers', [])[0].get('identifier', '') if book['volumeInfo'].get('industryIdentifiers', []) else ''
    tags = book['volumeInfo'].get('categories', [])
        
    try:  #store books in DB
        cur.execute("INSERT INTO books (title, author, publication_year, isbn, volume_id) VALUES (%s, %s, %s, %s, %s) RETURNING book_id",
        (title, author, publication_year, isbn, volume_ID))
        book_id = cur.fetchone()[0]
        conn.commit()
        
        #pull authors
        for author in author[:20]:
            cur.execute("SELECT author_id FROM authors WHERE author_name=%s", (author,))
            result = cur.fetchone()
            
            if result is not None:
                #check for existing authors
                author_id = result[0]
            else:
                #insert non-existent authors
                cur.execute("INSERT INTO authors (author_name) VALUES (%s) RETURNING author_id", (author,))
                author_id = cur.fetchone()[0]
                conn.commit()
            
            #store book/author pairings
            cur.execute(
                "INSERT INTO author_pairings (book_id, author_id) VALUES (%s, %s)",
                (book_id, author_id)
            )
            conn.commit()


        #handle and store tags
        for tag in tags[:20]:
            #determine whether tag exists
            cur.execute("SELECT tag_id FROM tags WHERE tag=%s", (tag,))
            result = cur.fetchone()
            
            if result is not None:
                #use existing tag if it exists
                tag_id = result[0]
            else:
                #insert non-exsistent tags
                cur.execute("INSERT INTO tags (tag) VALUES (%s) RETURNING tag_id", (tag,))
                tag_id = cur.fetchone()[0]
                conn.commit()
            
           #store book/tag pairings
            cur.execute(
                "INSERT INTO book_tags (book_id, tag_id) VALUES (%s, %s)",
                (book_id, tag_id)
            )
            conn.commit()
    
    except psycopg2.errors.UniqueViolation:
        #handle errors from violated unique constraints on DB
        conn.rollback()
        continue

cur.close()
conn.close()

