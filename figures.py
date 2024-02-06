from config import *

#These are a series of standalone functions that generate figures for the report/presentation
#This is not intended to be run as a script but rather to be imported and used in other scripts

def publication_vs_popularity():
    #Query the database for the average popularity of songs in playlists by book publication year
    cursor.execute("""
    SELECT books.publication_year, AVG(tracks.popularity) AS avg_popularity
    FROM books
    JOIN playlist_book_mapping ON books.book_id = playlist_book_mapping.book_id
    JOIN playlists ON playlist_book_mapping.playlist_id = playlists.playlist_id
    JOIN playlist_track_mapping ON playlists.playlist_id = playlist_track_mapping.playlist_id
    JOIN tracks ON playlist_track_mapping.track_id = tracks.track_id
    GROUP BY books.publication_year
    ORDER BY books.publication_year
    """)
    data = cursor.fetchall()

    #Make a dataframe from the data
    df = pd.DataFrame(data, columns=['Publication Year', 'Average Popularity'])

    #Create a scatter plot
    plt.figure(figsize=(10, 5))
    plt.scatter(df['Publication Year'], df['Average Popularity'])
    plt.xlabel('Publication Year')
    plt.ylabel('Average Popularity of Songs in Playlist')
    plt.title('Correlation Between Book Publication Year and Song Popularity')

    #Show the figure
    plt.show()

def playlists_by_follower_count():
    #Execute the SQL query
    query = "SELECT follower_count FROM playlists;"
    cursor.execute(query)

    # Fetch the result
    result = cursor.fetchall()

    #Get follower counts from the result and make ranges
    playlist_follower_counts = [row[0] for row in result]
    ranges = [(0, 500), (501, 1000), (1001, 5000), (5001, 10000),(10001,50000)]

    #Tally playlists in each range
    playlist_counts = [0] * len(ranges)
    for count in playlist_follower_counts:
        for i, (low, high) in enumerate(ranges):
            if low <= count <= high:
                playlist_counts[i] += 1
                break

    #Labels for the pie chart
    labels = [f'{low}-{high} followers' for low, high in ranges]
    fig, ax = plt.subplots()
    ax.pie(playlist_counts, labels=labels, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 10}, pctdistance=0.85)
    ax.axis('equal')

  
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig.gca().add_artist(centre_circle)

    #Save and display the figure
    plt.savefig("playlist_followers_distribution.png")
    plt.show()

def songs_by_popularity(): 
    cursor = connection.cursor()

    query = "SELECT popularity FROM tracks;"
    cursor.execute(query)
   
    result = cursor.fetchall()

 # Get popularity scores from the result and make ranges
    song_popularity = [row[0] for row in result]

    ranges = [(0, 20), (21, 40), (41, 60), (61, 80), (81, 100)]

    #Tally songs in each range
    song_counts = [0] * len(ranges)
    for popularity in song_popularity:
        for i, (low, high) in enumerate(ranges):
            if low <= popularity <= high:
                song_counts[i] += 1
                break

    #Create and label the pie chart
    labels = [f'{low}-{high} popularity score' for low, high in ranges]

 
    fig, ax = plt.subplots()
    ax.pie(song_counts, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    #Save and display the figure
    plt.savefig("song_popularity_distribution.png")
    plt.show()

def song_popularity_vs_playlist_popularity():
    #Execute the SQL query
    query = """
    WITH playlist_avg_popularity AS (
        SELECT
            p.playlist_id,
            p.follower_count,
            AVG(t.popularity) AS avg_popularity
        FROM
            playlists p
            JOIN playlist_track_mapping ptm ON p.playlist_id = ptm.playlist_id
            JOIN tracks t ON ptm.track_id = t.track_id
        GROUP BY
            p.playlist_id
    )
    SELECT
        CASE
            WHEN follower_count BETWEEN 0 AND 500 THEN '0-500 followers'
            WHEN follower_count BETWEEN 501 AND 1000 THEN '501-1000 followers'
            WHEN follower_count BETWEEN 1001 AND 5000 THEN '1001-5000 followers'
            WHEN follower_count BETWEEN 5001 AND 10000 THEN '5001-10000 followers'
            ELSE '10001-50000 followers'
        END AS follower_range,
        AVG(avg_popularity) AS avg_popularity
    FROM
        playlist_avg_popularity
    GROUP BY
        follower_range
    ORDER BY
        MIN(follower_count);
    """

    cursor.execute(query)

    #Fetch the result
    result = cursor.fetchall()

    #Extract the data for the bar chart and create it
    follower_ranges = [row[0] for row in result]
    avg_popularity = [row[1] for row in result]

    plt.bar(follower_ranges, avg_popularity)
    plt.xlabel('Follower Range')
    plt.ylabel('Average Song Popularity')
    plt.title('Average Song Popularity by Follower Range')
    plt.xticks(rotation=45)

    #Display the figure
    plt.savefig("song_popularity_vs_playlist_popularity.png")
    plt.show()

def implied_popularity():
    #Query the database to get the book_id, book_title, playlist_id, follower_count, and average song popularity
    query = '''
    SELECT b.book_id, b.title, p.playlist_id, p.follower_count, AVG(s.popularity) AS avg_song_popularity
    FROM playlist_book_mapping pbm
    JOIN playlists p ON pbm.playlist_id = p.playlist_id
    JOIN books b ON pbm.book_id = b.book_id
    JOIN playlist_track_mapping ps ON p.playlist_id = ps.playlist_id
    JOIN tracks s ON ps.track_id = s.track_id
    WHERE b.book_id != 179
    GROUP BY b.book_id, b.title, p.playlist_id, p.follower_count
    '''

    #Read the data into a DataFrame
    df = pd.read_sql_query(query, connection)

    # Calculate the average follower_count and average song popularity for each book
    book_popularity = df.groupby(['book_id', 'title']).agg({'follower_count': 'mean', 'avg_song_popularity': 'mean'}).reset_index()

    # Calculate the implied popularity
    book_popularity['implied_popularity'] = book_popularity['follower_count'] * book_popularity['avg_song_popularity']

    # Sort the books by implied popularity
    book_popularity_sorted = book_popularity.sort_values('implied_popularity', ascending=False)

    # Create a bar chart of the implied popularity by book title
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(book_popularity_sorted['title'], book_popularity_sorted['implied_popularity'])
    ax.set_xlabel('Implied Popularity')
    ax.set_ylabel('Book Title')
    ax.set_title('Implied Book Popularity Based on Playlist Follower Count and Average Song Popularity')

    #Save and display the figure
    plt.savefig("implied_book_popularity.png")
    plt.show()

def average_release_year():

    #Query the database to get the year a book was published and the average song release year in its playlist
    query = '''
        SELECT b.publication_year, AVG(CAST(a.release_year AS INTEGER)) AS avg_song_release_year
        FROM playlist_book_mapping pbm
        JOIN playlists p ON pbm.playlist_id = p.playlist_id
        JOIN books b ON pbm.book_id = b.book_id
        JOIN playlist_track_mapping ptm ON p.playlist_id = ptm.playlist_id
        JOIN tracks t ON ptm.track_id = t.track_id
        JOIN albums a ON t.album_id = a.album_id
        GROUP BY b.publication_year
    '''

    cursor.execute(query)
    results = cursor.fetchall()

    #Get the data and create a scatter plot
    book_years = [result[0] for result in results]
    avg_song_years = [result[1] for result in results]

    fig, ax = plt.subplots()
    ax.scatter(book_years, avg_song_years)
    ax.set_xlabel('Year Book Published')
    ax.set_ylabel('Average Song Release Year in Playlist')

    #Save and display the figure
    plt.savefig("book_year_vs_avg_song_year.png")
    plt.show()

def plot_track_release_year_distribution():
     # Execute the query
    cursor.execute("""
        SELECT DATE_PART('year', TO_DATE(a.release_year, 'YYYY'))::INTEGER AS release_year
        FROM albums a
    """)

    # Fetch the results
    results = cursor.fetchall()

    # Close the cursor and connection
    cursor.close()
    connection.close()

    # Extract the data
    release_years = [row[0] for row in results]

    # Create a histogram
    fig, ax = plt.subplots()
    ax.hist(release_years, bins='auto', edgecolor='black')

    # Set the chart title and labels
    ax.set_title('Track Release Year Distribution')
    ax.set_xlabel('Release Year')
    ax.set_ylabel('Frequency')

    # Save the figure
    plt.savefig("track_release_year_distribution.png")

    # Show the figure
    plt.show()

