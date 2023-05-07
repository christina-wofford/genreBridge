from config import *

def get_book_page_count_and_track_popularity():
    cursor.execute("""
        SELECT b.publication_year, 
               AVG(b.page_count) as avg_pages, 
               AVG(t.popularity) as avg_popularity
        FROM books b
        JOIN playlist_book_mapping pbm ON b.book_id = pbm.book_id
        JOIN playlists p ON pbm.playlist_id = p.playlist_id
        JOIN playlist_track_mapping ptm ON p.playlist_id = ptm.playlist_id
        JOIN tracks t ON ptm.track_id = t.track_id
        WHERE b.publication_year IS NOT NULL AND b.page_count IS NOT NULL
        GROUP BY b.publication_year
        ORDER BY b.publication_year
    """)
    return cursor.fetchall()

def plot_book_pages_and_track_popularity_comparison():

    data = get_book_page_count_and_track_popularity()

    publication_years = [row[0] for row in data]
    avg_pages = [row[1] for row in data]
    avg_popularity = [row[2] for row in data]

    # Normalize the data to bring them to the same scale
    avg_pages_normalized = [x / max(avg_pages) for x in avg_pages]
    avg_popularity_normalized = [x / max(avg_popularity) for x in avg_popularity]

    # Create the bar chart
    bar_width = 0.35
    index = np.arange(len(publication_years))

    plt.bar(index, avg_pages_normalized, bar_width, label="Avg Pages per Book")
    plt.bar(index + bar_width, avg_popularity_normalized, bar_width, label="Avg Track Popularity")

    plt.xlabel("Publication Year")
    plt.ylabel("Normalized Value")
    plt.title("Average Pages per Book vs. Average Track Popularity by Year")
    plt.xticks(index + bar_width / 2, publication_years, rotation=45)
    plt.legend()
    plt.show()

def most_frequently_appearing_artists_by_year():
    query = '''
    WITH artist_year_count AS (
        SELECT a.artist_name, al.release_year, COUNT(t.track_id) as track_count
        FROM artists a
        JOIN albums al ON a.artist_id = al.artist_id
        JOIN tracks t ON al.album_id = t.album_id
        GROUP BY a.artist_name, al.release_year
    )
    SELECT artist_name, release_year, track_count
    FROM (
        SELECT artist_year_count.*, ROW_NUMBER() OVER (PARTITION BY release_year ORDER BY track_count DESC) AS row_number
        FROM artist_year_count
    ) ranked
    WHERE row_number = 1
    ORDER BY release_year;
    '''
    cursor.execute(query)
    data = cursor.fetchall()

    years = [row[1] for row in data]
    artists = [row[0] for row in data]

    plt.figure(figsize=(12, 6))
    plt.bar(years, artists)
    plt.xlabel("Release Year")
    plt.ylabel("Most Frequent Artist")
    plt.title("Most Frequently Appearing Artists by Year")
    plt.xticks(rotation=90)
    plt.show()

    # Create a DataFrame from the fetched data
    df = pd.DataFrame(data, columns=['Artist', 'Release Year', 'Track Count'])

    # Create a table figure
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis('off')
    table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 1.5)

    # Save the figure as an image
    plt.savefig('table_figure.png', bbox_inches='tight')

    # Show the figure
    plt.show()
    # Display the table
    print(df)
most_frequently_appearing_artists_by_year()

