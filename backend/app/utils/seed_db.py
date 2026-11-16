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

                # 2. Books Table (including cover_image, in_stock, and page_count)
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
                        cover_image VARCHAR(255) NULL,
                        in_stock INT DEFAULT 0,
                        page_count INT DEFAULT 0,
                        FOREIGN KEY (genre_id) REFERENCES Genres(genre_id)
                    );
                    """
                )

                # 3. User Table
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
                        is_admin BOOLEAN DEFAULT FALSE,
                        CONSTRAINT chk_user_username_length
                            CHECK (CHAR_LENGTH(username) BETWEEN 3 AND 20)
                    );
                    """
                )

                # 4. Reviews Table, people can only have one review per book
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS Reviews (
                        review_id INT PRIMARY KEY AUTO_INCREMENT,
                        isbn VARCHAR(20) NOT NULL,
                        user_id INT NOT NULL,
                        review_score INT NOT NULL CHECK (review_score BETWEEN 1 AND 5),
                        review_text TEXT NOT NULL,
                        UNIQUE KEY unique_user_book (isbn, user_id),
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

                # Seed Books (Format: isbn, title, author, about, msrp, publication_date, genre_id, cover_image, in_stock, page_count)
                # Some books have stock set to 0 to test out-of-stock states.
                books_data = [
                    ('978-0441172719', 'Dune', 'Frank Herbert', 'Set on the desert planet Arrakis, this epic follows young Paul Atreides as his family accepts stewardship of the valuable spice resource, leading to betrayal and destiny.', 18.99, '1965-08-01', 10, "/images/bookes/dune.jpg", 15, 412),
                    ('978-0553896954', 'Dune: House Corrino', 'Brian Herbert, Kevin J. Anderson', 'A prequel set in the Dune universe, centered on political conflict surrounding House Corrino.', 7.99, '2002-08-27', 10, "https://books.google.com/books/content?id=--8cBYaNlA4C&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 0, 528),  # Out of stock
                    ('978-1429955904', 'Dune: The Butlerian Jihad', 'Brian Herbert, Kevin J. Anderson', "A Dune-universe prequel about the conflict that shaped humanity's rejection of thinking machines.", 9.99, '2010-04-01', 10, "https://books.google.com/books/content?id=f8gTJ3-MWzEC&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 8, 624),
                    ('978-0553293357', 'Foundation', 'Isaac Asimov', 'A visionary mathematician uses psychohistory to predict the collapse of a galactic empire and creates a sanctuary of knowledge to shorten the coming dark age.', 14.99, '1951-05-01', 10, None, 12, 255),
                    ('978-0385531139', 'The Martian', 'Andy Weir', 'An astronaut is accidentally stranded alone on Mars after a fierce dust storm and must use his ingenuity and scientific wit to survive.', 16.00, '2014-02-11', 10, None, 0, 369),  # Out of stock
                    ('978-0441569595', 'Neuromancer', 'William Gibson', 'A washed-up computer hacker is hired by a mysterious employer for one last dangerous run into cyberspace, shaping cyberpunk culture.', 15.50, '1984-07-01', 10, None, 8, 271),
                    ('978-0553573404', 'Snow Crash', 'Neal Stephenson', 'In a futuristic corporate-franchised America, a hacker and pizza delivery driver investigates a computer virus that affects human brains.', 17.25, '1992-06-01', 10, None, 10, 440),
                    ('978-1429959629', 'The Light of Other Days', 'Arthur C. Clarke, Stephen Baxter', 'Quantum wormhole technology lets people observe distant places and moments, transforming privacy and society.', 19.99, '2010-01-11', 10, "https://books.google.com/books/content?id=3XunMr9D2k4C&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 7, 320),
                    ('978-0795325397', 'A Fall of Moondust', 'Arthur C. Clarke', 'After a lunar tour boat becomes trapped beneath the Moon\'s surface, its passengers must find a way to survive and be rescued.', 9.99, '2012-11-30', 10, "https://books.google.com/books/content?id=qckpAAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 0, 248),  # Out of stock
                    ('978-0795324970', 'Childhood\'s End', 'Arthur C. Clarke', 'Alien visitors bring peace to Earth, but humanity\'s future takes an unsettling turn.', 9.99, '2012-11-30', 10, "https://books.google.com/books/content?id=OcspAAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 11, 224),
                    ('978-1473379510', 'The Skull', 'Philip K. Dick', 'A science fiction story of time travel and a mission that puts a man\'s destiny in question.', 6.99, '2016-01-18', 10, "https://books.google.com/books/content?id=hL1mCwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 14, 110),
                    ('978-1648370007', 'The Best of Philip K. Dick', 'Philip K. Dick', 'A collection of thirteen short stories exploring speculative futures and the effects of technology and social change.', 14.99, '2019-01-01', 10, "https://books.google.com/books/content?id=wN1UEAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 6, 400),
                    ('978-0544040601', 'Selected Stories Of Philip K. Dick', 'Philip K. Dick, Jonathan Lethem', 'A collection of twenty-one stories spanning Philip K. Dick\'s career and exploring speculative worlds and alternate realities.', 10.99, '2013-04-16', 10, "https://books.google.com/books/content?id=ie0Vw7ygOj4C&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 10, 480),
                    ('978-0261102217', 'The Hobbit', 'J.R.R. Tolkien', 'A comfort-loving hobbit gets swept into an unexpected quest with a wizard and a band of dwarves to reclaim stolen treasure from a dragon.', 14.99, '1937-09-21', 11, None, 25, 310),
                    ('978-0756404741', 'The Name of the Wind', 'Patrick Rothfuss', 'A notorious wizard, musician, and thief recounts the legendary hardships and triumphs of his youth in his own quiet tavern voice.', 18.00, '2007-03-27', 11, None, 5, 662),
                    ('978-0765350381', 'Mistborn: The Final Empire', 'Brandon Sanderson', 'A crew of talented thieves plans an elaborate heist to overthrow an immortal ruler who has oppressed the world for a millennium.', 16.50, '2006-07-17', 11, None, 14, 541),
                    ('978-0765326357', 'The Way of Kings', 'Brandon Sanderson', 'Soldiers, slaves, and scholars navigate a massive, magical storm-torn continent caught in a cyclical war.', 24.99, '2010-08-31', 11, None, 7, 1007),
                    ('978-0062080363', 'American Gods', 'Neil Gaiman', 'An ex-convict released from prison finds himself working for a mysterious con man as old mythological deities walk the American landscape.', 16.99, '2001-06-19', 11, None, 11, 465),
                    ('978-1524796297', 'Fire & Blood', 'George R. R. Martin', 'A fictional chronicle of House Targaryen and its rise and internal conflicts in Westeros.', 7.99, '2018-11-20', 11, "https://books.google.com/books/content?id=Mj5XDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 13, 736),
                    ('978-0345535535', "George R. R. Martin's A Game of Thrones 5-Book Boxed Set (Song of Ice and Fire Series)", 'George R. R. Martin', 'An eBook bundle collecting the first five novels in the A Song of Ice and Fire fantasy series.', 39.99, '2012-09-10', 11, "https://books.google.com/books/content?id=i9PvStUdWz8C&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 4, 5000),
                    ('978-0307454546', 'The Girl with the Dragon Tattoo', 'Stieg Larsson', 'A disgraced journalist and a brilliant punk hacker team up to investigate a wealthy family disappearance spanning four decades.', 15.95, '2005-08-01', 12, None, 9, 465),
                    ('978-0061753824', 'Murder on the Orient Express', 'Agatha Christie', "Belgian detective Hercule Poirot investigates a passenger's murder aboard the Orient Express.", 4.99, '2003-10-28', 12, "https://books.google.com/books/content?id=cdC69SemSyIC&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 16, 256),
                    ('978-1250301710', 'The Silent Patient', 'Alex Michaelides', 'A psychotherapist investigates why a famous painter stopped speaking after her husband is murdered.', 12.99, '2019-02-05', 12, "https://books.google.com/books/content?id=tLdiDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 12, 336),
                    ('978-0307588371', 'Gone Girl', 'Gillian Flynn', 'On his fifth wedding anniversary, a man becomes the primary suspect when his wife mysteriously vanishes from their home.', 16.00, '2012-05-24', 12, None, 13, 415),
                    ('978-0312924584', 'The Silence of the Lambs', 'Thomas Harris', 'A young FBI trainee seeks the guidance of an imprisoned, highly intelligent serial killer to track down another active murderer.', 14.50, '1988-05-01', 12, None, 6, 338),
                    ('978-0307474279', 'The Da Vinci Code', 'Dan Brown', 'A symbologist and a cryptologist race across Europe to decode a trail of religious mysteries linked to a shocking murder.', 16.00, '2003-03-18', 12, None, 18, 454),
                    ('978-0399159848', 'Big Little Lies', 'Liane Moriarty', 'Three mothers in a coastal town bond over young children, but their seemingly perfect lives unravel into a dark local murder investigation.', 17.00, '2014-07-29', 12, None, 10, 390),
                    ('978-1501173219', 'All the Light We Cannot See', 'Anthony Doerr', 'The paths of a blind French girl and a young German soldier collide in occupied France during the turmoil of World War II.', 18.00, '2014-05-06', 13, None, 12, 531),
                    ('978-1250080401', 'The Nightingale', 'Kristin Hannah', 'Two sisters living in German-occupied France display incredible courage and resilience as they navigate survival and resistance.', 17.99, '2015-02-03', 13, None, 8, 440),
                    ('978-0375842207', 'The Book Thief', 'Markus Zusak', 'Narrated by Death, this story follows a foster girl in Nazi Germany who finds solace by stealing books and sharing them.', 13.99, '2005-09-01', 13, None, 15, 552),
                    ('978-0451166890', 'The Pillars of the Earth', 'Ken Follett', 'A sweeping epic centered around the construction of a massive cathedral in a twelfth-century English town torn apart by civil war.', 22.00, '1989-10-01', 13, None, 4, 973),
                    ('978-1455563920', 'Pachinko', 'Min Jin Lee', 'A multi-generational saga detailing the struggles and triumphs of a Korean immigrant family living in 20th-century Japan.', 17.00, '2017-02-07', 13, None, 11, 496),
                    ('978-0062671202', 'The Night Watchman', 'Louise Erdrich', 'A historical novel following a Chippewa community in 1950s North Dakota as they confront a federal policy threatening tribal rights.', 14.99, '2020-03-03', 13, "https://books.google.com/books/content?id=ZECbDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 9, 464),
                    ('978-1718502192', 'The Art of Clean Code', 'Christian Mayer', 'A practical guide to simplifying software design through focused coding principles.', 28.99, '2022-08-02', 2, "https://books.google.com/books/content?id=FTlTEAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 15, 250),
                    ('978-1800562097', 'Clean Code in Python', 'Mariano Anaya', 'A guide to writing maintainable Python applications using refactoring, design principles, and practical code organization.', 31.91, '2021-01-06', 2, "https://books.google.com/books/content?id=UbQSEAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 12, 390),
                    ('978-1593279677', 'Beyond the Basic Stuff with Python', 'Al Sweigart', 'A practical guide to developing stronger programming habits and moving beyond introductory Python techniques.', 23.99, '2020-12-22', 2, "https://books.google.com/books/content?id=BG_cDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 18, 384),
                    ('979-8868810046', 'Crafting Clean Code with JavaScript and React', 'Héla Ben Khalfallah', 'A guide to applying clean-code principles to JavaScript and React, including accessibility and performance.', 43.44, '2024-11-20', 2, "https://books.google.com/books/content?id=7bsyEQAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 5, 320),
                    ('978-1837632992', 'Clean Code with C#', 'Jason Alls', 'A C# programming guide focused on code reviews, testing practices, API design, and maintainable software.', 31.19, '2023-12-22', 2, "https://books.google.com/books/content?id=1HjqEAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 7, 450),
                    ('978-1524763138', 'Becoming', 'Michelle Obama', 'The former First Lady shares her deep roots on the South Side of Chicago, balancing work, family, and life in the White House.', 19.00, '2018-11-13', 20, None, 22, 448),
                    ('978-0399590504', 'Educated', 'Tara Westover', 'A memoir about a young woman who grows up isolated from society by survivalist parents and eventually escapes to earn a PhD.', 18.50, '2018-02-20', 20, None, 16, 334),
                    ('978-0553296983', 'The Diary of a Young Girl', 'Anne Frank', 'The authentic, deeply moving journal of a Jewish teenager hiding with her family from the Nazi regime in Amsterdam.', 10.99, '1947-06-25', 20, None, 30, 283),
                    ('978-0399588176', 'Born a Crime', 'Trevor Noah', 'Comedian Trevor Noah recounts his turbulent childhood growing up biracial in South Africa during and right after apartheid.', 18.00, '2016-11-15', 20, None, 19, 304),
                    ('978-1620872512', 'The FBI File on Steve Jobs', 'The Federal Bureau of Investigation', 'A documentary-style compilation of declassified FBI records concerning Steve Jobs.', 8.99, '2012-02-20', 20, "https://books.google.com/books/content?id=hG6CDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 10, 400),
                    ('978-0385347419', 'Becoming Steve Jobs', 'Brent Schlender, Rick Tetzeli', "A biography exploring Steve Jobs's growth as a leader and entrepreneur through the perspectives of people who knew him.", 12.99, '2015-03-24', 20, "https://books.google.com/books/content?id=9ntoBAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 14, 448),
                    ('978-0553380163', 'A Brief History of Time', 'Stephen Hawking', 'A landmark exploration of cosmology, black holes, space-time, and the fundamental forces shaping our universe.', 16.00, '1988-04-01', 21, None, 14, 212),
                    ('978-0345539434', 'Cosmos', 'Carl Sagan', 'A stunning voyage through space and time, illuminating the history of science, astronomy, and our place in the universe.', 20.00, '1980-10-01', 21, None, 8, 365),
                    ('978-0618249060', 'Silent Spring', 'Rachel Carson', 'A groundbreaking environmental science text examining the widespread impact of chemical pesticides on ecosystems and wildlife.', 15.00, '1962-09-27', 21, None, 6, 368),
                    ('978-1771642491', 'The Hidden Life of Trees', 'Peter Wohlleben', 'An introduction to forest ecology that explores how trees interact and respond to their environments.', 18.95, '2016-09-13', 21, "https://books.google.com/books/content?id=WEn4DAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 12, 288),
                    ('978-0735211292', 'Atomic Habits', 'James Clear', 'A practical, actionable framework for building good habits, breaking bad ones, and mastering small behavioral changes.', 16.00, '2018-10-16', 22, None, 35, 320),
                    ('978-0684839395', 'The 7 Habits of Highly Effective People', 'Stephen Covey', 'A timeless, principle-centered approach for solving personal and professional problems and improving effectiveness.', 18.00, '1989-08-15', 22, None, 12, 381),
                    ('978-1455586660', 'Deep Work', 'Cal Newport', 'A practical guide to focused work habits and reducing distractions to improve professional output.', 2.99, '2016-01-05', 22, "https://books.google.com/books/content?id=4QTzCAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 20, 304),
                    ('978-0060254926', 'Where the Wild Things Are', 'Maurice Sendak', 'A mischievous young boy named Max is sent to his room without supper, lets his imagination run wild, and sails to an island of monsters.', 18.95, '1963-11-09', 30, None, 0, 48),  # Out of stock
                    ('979-8217050154', "The Very Hungry Caterpillar's First Signs", 'Eric Carle', 'A board book introducing young children to ten everyday American Sign Language signs.', 6.99, '2025-07-15', 30, "https://books.google.com/books/content?id=GRMqEQAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 30, 26),
                    ('978-0593520284', "The Very Hungry Caterpillar's First Fall", 'Eric Carle', 'A picture book following the caterpillar and friends through autumn activities and seasonal changes.', 4.99, '2022-08-02', 30, "https://books.google.com/books/content?id=DWpiEAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api", 22, 32)
                ]
                
                cursor.executemany(
                    """
                    INSERT IGNORE INTO Books (isbn, title, author, about, msrp, publication_date, genre_id, cover_image, in_stock, page_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    books_data,
                )

                cover_updates = [
                    (cover_image, isbn)
                    for isbn, _, _, _, _, _, _, cover_image, _, _ in books_data
                    if cover_image
                ]
                cursor.executemany(
                    """
                    UPDATE Books
                    SET cover_image = %s
                    WHERE isbn = %s AND (cover_image IS NULL OR cover_image = '')
                    """,
                    cover_updates,
                )

                connection.commit()
                current_app.logger.info("Database initialized and seeded successfully on startup!")

    except Exception as e:
        current_app.logger.exception("Database initialization failed")
        print(f"Startup DB Error: {e}")