# GenreBridge

## Abstract
GenreBridge is a unique application that enhances the reading experience by synchronizing literature with tailored musical soundtracks. It allows users to discover new literary and musical interests and understand current trends in both domains, all without the need for a login, prioritizing user privacy and accessibility.

## Data Modeling
**Core to GenreBridge is its sophisticated data model**, which is crucial for data engineering and analytics engineering roles. The application’s data structure was meticulously designed to reflect real-world relationships and ensure optimal data integrity and query performance.

### ER Diagram
Below is the ER Diagram that outlines the relationships and structure of the database:
![GenreBridge ER Diagram](https://github.com/christina-wofford/genreBridge/assets/1641567/52fd1085-b688-49da-ae1f-5a1e7f551c93)

- **Database Design:** Implemented a relational database schema in PostgreSQL, focusing on normalization to avoid data redundancy. The schema includes tables for books, authors, playlists, and a mapping table to handle the many-to-many relationship between books and authors.
- **SQL Mastery:** Utilized advanced SQL features to create, manipulate, and query the database efficiently. This includes crafting complex queries to aggregate data, implement constraints, and manage database transactions to maintain data consistency and accuracy.
- **Data Integration:** Leveraged Python’s psycopg2 library to integrate data fetched from the Google Books and Spotify APIs into the database, ensuring that the data flows seamlessly from external APIs to our internal systems.

## Technical Skills
- **API Integration:** Python scripts automate the fetching and parsing of data from the Google Books and Spotify APIs, enriching our database with diverse and relevant content.
- **Data Analysis:** Utilized SQL and Python (including libraries like matplotlib for visualization) to analyze data, draw insights, and visualize trends that inform the application’s book-music matching logic.

## Implementation
GenreBridge’s backend is powered by Flask, handling API interactions and data processing. The frontend is designed for simplicity, allowing users to input book titles and authors to receive Spotify playlists, which are then displayed using a Spotify widget integrated into the web interface.

## Results
The application not only matches books with playlists but also provides analytical insights that highlight the interplay between book popularity and music trends. This dual capability showcases the power of effective data modeling and system integration in improving user engagement.

## Conclusions
GenreBridge exemplifies the application of data modeling, system design, and API integration in creating a product that enriches the user experience. This project is a testament to the potential impact of data engineering in bridging data with real-world applications, making it an ideal showcase for roles in data engineering, analytics engineering, and technical product management.

