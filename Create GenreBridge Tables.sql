CREATE TABLE authors (
    author_id SERIAL PRIMARY KEY,
    author_first_name VARCHAR(255),
    author_last_name VARCHAR(255),
    create_dttm TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE books (
    book_id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    author_id INTEGER,
    publication_year INTEGER,
    google_books_id VARCHAR(255) UNIQUE,
    isbn VARCHAR(255) UNIQUE,
    create_dttm TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES authors(author_id)
);

CREATE TABLE tags (
    tag_id SERIAL PRIMARY KEY,
    tag_description VARCHAR(255),
    create_dttm TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE artists (
    artist_id SERIAL PRIMARY KEY,
    artist_name VARCHAR(255) UNIQUE,
    create_dttm TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE albums (
    album_id SERIAL PRIMARY KEY,
    artist_id INTEGER,
    album_name VARCHAR(255),
    spotify_album_id VARCHAR(255) UNIQUE,
    release_year INTEGER,
    create_dttm TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
);

CREATE TABLE album_tags (
    album_tag_id SERIAL PRIMARY KEY,
    album_id INTEGER,
    tag_id INTEGER,
    create_dttm TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (album_id) REFERENCES albums(album_id),
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id)
);

CREATE TABLE book_tags (
    book_tag_id SERIAL PRIMARY KEY,
    book_id INTEGER,
    tag_id INTEGER,
    create_dttm TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(book_id),
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id)
);

CREATE TABLE book_album_matches (
    match_id SERIAL PRIMARY KEY,
    book_id INTEGER,
    album_id INTEGER,
    create_dttm TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(book_id),
    FOREIGN KEY (album_id) REFERENCES albums(album_id)
);
