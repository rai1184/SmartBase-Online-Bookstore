from contextlib import closing
import mysql.connector
from flask import current_app
from app.database.connection import get_db_connection

def initialize_database():
    """Automatically runs on app startup to ensure tables and seed data exist."""
    current_app.logger.info("Checking database tables and seed data...")
    
    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                # Disable foreign key checks temporarily during setup
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

                # 1. Genres Table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS Genres (
                        genre_id INT PRIMARY KEY,
                        genre_name VARCHAR(255) NOT NULL,
                        genre_parent_id INT,
                        FOREIGN KEY (genre_parent_id) REFERENCES Genres(genre_id)
                    );
                    """
                )

                # 2. Books Table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS Books (
                        isbn VARCHAR(20) PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        author VARCHAR(255) NOT NULL,
                        about VARCHAR(2048),
                        msrp DECIMAL(10, 2) NOT NULL,
                        publication_date DATE,
                        genre_id INT,
                        FOREIGN KEY (genre_id) REFERENCES Genres(genre_id)
                    );
                    """
                )

                # 3. User Table (with google_sub allowing NULL for local registration)
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS User (
                        user_id INT PRIMARY KEY AUTO_INCREMENT,
                        username VARCHAR(20) NOT NULL UNIQUE,
                        user_email VARCHAR(255) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        google_sub VARCHAR(255) UNIQUE NULL,
                        display_name VARCHAR(255),
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT chk_user_username_length
                            CHECK (CHAR_LENGTH(username) BETWEEN 3 AND 20)
                    );
                    """
                )

                # 4. Reviews Table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS Reviews (
                        review_id INT PRIMARY KEY AUTO_INCREMENT,
                        isbn VARCHAR(20) NOT NULL,
                        user_id INT NOT NULL,
                        review_score INT NOT NULL CHECK (review_score BETWEEN 1 AND 5),
                        review_text TEXT NOT NULL,
                        FOREIGN KEY (isbn) REFERENCES Books(isbn),
                        FOREIGN KEY (user_id) REFERENCES User(user_id)
                    );
                    """
                )

                # 5. Favorites Table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS Favorites (
                        user_id INT NOT NULL,
                        isbn VARCHAR(20) NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, isbn),
                        FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
                        FOREIGN KEY (isbn) REFERENCES Books(isbn) ON DELETE CASCADE
                    );
                    """
                )

                # 6. AuthSessions Table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS AuthSessions (
                        session_token_hash CHAR(64) NOT NULL PRIMARY KEY,
                        user_id INT NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        expires_at DATETIME NOT NULL,
                        INDEX idx_auth_sessions_user_expires (user_id, expires_at),
                        INDEX idx_auth_sessions_expires (expires_at),
                        FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
                    );
                    """
                )

                cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
                connection.commit()

                # Seed Genres
                genres_data = [
                    (1, "Fiction", None),
                    (2, "Non-Fiction", None),
                    (3, "Children's Books", None),
                    (10, "Science Fiction", 1),
                    (11, "Fantasy", 1),
                    (12, "Mystery & Thriller", 1),
                    (13, "Historical Fiction", 1),
                    (20, "Biography & Memoir", 2),
                    (21, "Science & Nature", 2),
                    (22, "Self-Help", 2),
                    (30, "Picture Books", 3),
                ]
                cursor.executemany(
                    """
                    INSERT IGNORE INTO Genres (genre_id, genre_name, genre_parent_id)
                    VALUES (%s, %s, %s)
                    """,
                    genres_data,
                )

                # Seed Books
                books_data = [
                    ('978-0441172719', 'Dune', 'Frank Herbert', 'Set on the desert planet Arrakis, this epic follows young Paul Atreides as his family accepts stewardship of the valuable spice resource, leading to betrayal and destiny.', 18.99, '1965-08-01', 10),
                    ('978-0553293357', 'Foundation', 'Isaac Asimov', 'A visionary mathematician uses psychohistory to predict the collapse of a galactic empire and creates a sanctuary of knowledge to shorten the coming dark age.', 14.99, '1951-05-01', 10),
                    ('978-0385531139', 'The Martian', 'Andy Weir', 'An astronaut is accidentally stranded alone on Mars after a fierce dust storm and must use his ingenuity and scientific wit to survive.', 16.00, '2014-02-11', 10),
                    ('978-0441569595', 'Neuromancer', 'William Gibson', 'A washed-up computer hacker is hired by a mysterious employer for one last dangerous run into cyberspace, shaping cyberpunk culture.', 15.50, '1984-07-01', 10),
                    ('978-0553573404', 'Snow Crash', 'Neal Stephenson', 'In a futuristic corporate-franchised America, a hacker and pizza delivery driver investigates a computer virus that affects human brains.', 17.25, '1992-06-01', 10),
                    ('978-0261102217', 'The Hobbit', 'J.R.R. Tolkien', 'A comfort-loving hobbit gets swept into an unexpected quest with a wizard and a band of dwarves to reclaim stolen treasure from a dragon.', 14.99, '1937-09-21', 11),
                    ('978-0756404741', 'The Name of the Wind', 'Patrick Rothfuss', 'A notorious wizard, musician, and thief recounts the legendary hardships and triumphs of his youth in his own quiet tavern voice.', 18.00, '2007-03-27', 11),
                    ('978-0765350381', 'Mistborn: The Final Empire', 'Brandon Sanderson', 'A crew of talented thieves plans an elaborate heist to overthrow an immortal ruler who has oppressed the world for a millennium.', 16.50, '2006-07-17', 11),
                    ('978-0765326357', 'The Way of Kings', 'Brandon Sanderson', 'Soldiers, slaves, and scholars navigate a massive, magical storm-torn continent caught in a cyclical war.', 24.99, '2010-08-31', 11),
                    ('978-0062080363', 'American Gods', 'Neil Gaiman', 'An ex-convict released from prison finds himself working for a mysterious con man as old mythological deities walk the American landscape.', 16.99, '2001-06-19', 11),
                    ('978-0307454546', 'The Girl with the Dragon Tattoo', 'Stieg Larsson', 'A disgraced journalist and a brilliant punk hacker team up to investigate a wealthy family disappearance spanning four decades.', 15.95, '2005-08-01', 12),
                    ('978-0307588371', 'Gone Girl', 'Gillian Flynn', 'On his fifth wedding anniversary, a man becomes the primary suspect when his wife mysteriously vanishes from their home.', 16.00, '2012-05-24', 12),
                    ('978-0312924584', 'The Silence of the Lambs', 'Thomas Harris', 'A young FBI trainee seeks the guidance of an imprisoned, highly intelligent serial killer to track down another active murderer.', 14.50, '1988-05-01', 12),
                    ('978-0307474279', 'The Da Vinci Code', 'Dan Brown', 'A symbologist and a cryptologist race across Europe to decode a trail of religious mysteries linked to a shocking murder.', 16.00, '2003-03-18', 12),
                    ('978-0399159848', 'Big Little Lies', 'Liane Moriarty', 'Three mothers in a coastal town bond over young children, but their seemingly perfect lives unravel into a dark local murder investigation.', 17.00, '2014-07-29', 12),
                    ('978-1501173219', 'All the Light We Cannot See', 'Anthony Doerr', 'The paths of a blind French girl and a young German soldier collide in occupied France during the turmoil of World War II.', 18.00, '2014-05-06', 13),
                    ('978-1250080401', 'The Nightingale', 'Kristin Hannah', 'Two sisters living in German-occupied France display incredible courage and resilience as they navigate survival and resistance.', 17.99, '2015-02-03', 13),
                    ('978-0375842207', 'The Book Thief', 'Markus Zusak', 'Narrated by Death, this story follows a foster girl in Nazi Germany who finds solace by stealing books and sharing them.', 13.99, '2005-09-01', 13),
                    ('978-0451166890', 'The Pillars of the Earth', 'Ken Follett', 'A sweeping epic centered around the construction of a massive cathedral in a twelfth-century English town torn apart by civil war.', 22.00, '1989-10-01', 13),
                    ('978-1455563920', 'Pachinko', 'Min Jin Lee', 'A multi-generational saga detailing the struggles and triumphs of a Korean immigrant family living in 20th-century Japan.', 17.00, '2017-02-07', 13),
                    ('978-1524763138', 'Becoming', 'Michelle Obama', 'The former First Lady shares her deep roots on the South Side of Chicago, balancing work, family, and life in the White House.', 19.00, '2018-11-13', 20),
                    ('978-0399590504', 'Educated', 'Tara Westover', 'A memoir about a young woman who grows up isolated from society by survivalist parents and eventually escapes to earn a PhD.', 18.50, '2018-02-20', 20),
                    ('978-0553296983', 'The Diary of a Young Girl', 'Anne Frank', 'The authentic, deeply moving journal of a Jewish teenager hiding with her family from the Nazi regime in Amsterdam.', 10.99, '1947-06-25', 20),
                    ('978-0399588176', 'Born a Crime', 'Trevor Noah', 'Comedian Trevor Noah recounts his turbulent childhood growing up biracial in South Africa during and right after apartheid.', 18.00, '2016-11-15', 20),
                    ('978-0553380163', 'A Brief History of Time', 'Stephen Hawking', 'A landmark exploration of cosmology, black holes, space-time, and the fundamental forces shaping our universe.', 16.00, '1988-04-01', 21),
                    ('978-0345539434', 'Cosmos', 'Carl Sagan', 'A stunning voyage through space and time, illuminating the history of science, astronomy, and our place in the universe.', 20.00, '1980-10-01', 21),
                    ('978-0618249060', 'Silent Spring', 'Rachel Carson', 'A groundbreaking environmental science text examining the widespread impact of chemical pesticides on ecosystems and wildlife.', 15.00, '1962-09-27', 21),
                    ('978-0735211292', 'Atomic Habits', 'James Clear', 'A practical, actionable framework for building good habits, breaking bad ones, and mastering small behavioral changes.', 16.00, '2018-10-16', 22),
                    ('978-0684839395', 'The 7 Habits of Highly Effective People', 'Stephen Covey', 'A timeless, principle-centered approach for solving personal and professional problems and improving effectiveness.', 18.00, '1989-08-15', 22),
                    ('978-0060254926', 'Where the Wild Things Are', 'Maurice Sendak', 'A mischievous young boy named Max is sent to his room without supper, lets his imagination run wild, and sails to an island of monsters.', 18.95, '1963-11-09', 30)
                ]
                cursor.executemany(
                    """
                    INSERT IGNORE INTO Books (isbn, title, author, about, msrp, publication_date, genre_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    books_data,
                )

                connection.commit()
                current_app.logger.info("Database initialized and seeded successfully on startup!")

    except Exception as e:
        current_app.logger.exception("Database initialization failed")
        print(f"Startup DB Error: {e}")