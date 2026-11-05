def build_exact_query(title, author, genre, max_price, min_rating, publication_year):
    # Base SQL query structure
    # Join books with genres so we can get the genre name
    # Join books with reviews so we can use the average function to get the avg review score
    base_select = """
    SELECT
            Books.isbn,
            Books.title,
            Books.author,
            Books.about,
            Books.msrp,
            Books.publication_date,
            Genres.genre_name,
            AVG(Reviews.review_score) AS avg_rating
        FROM Books
        LEFT JOIN Genres ON Books.genre_id = Genres.genre_id
        LEFT JOIN Reviews ON Books.isbn = Reviews.isbn
    """

    # Building the exact match query
    exact_query = base_select + " WHERE 1=1"
    exact_params = []

    # MySQL has a "LIKE" keyword we can use
    if title:
        exact_query += " AND Books.title LIKE %s"
        exact_params.append(f"%{title}%")
    if author:
        exact_query += " AND Books.author LIKE %s"
        exact_params.append(f"%{author}%")
    if genre and genre != "All":
        exact_query += " AND Genres.genre_name = %s"
        exact_params.append(genre)
    if max_price:
        try:
            exact_query += " AND Books.msrp <= %s"
            exact_params.append(float(max_price))
        except ValueError:
            pass
    if publication_year:
        try:
            exact_query += " AND YEAR(Books.publication_date) = %s"
            exact_params.append(int(publication_year))
        except ValueError:
            pass

    # Group by unique books. After this the average review score will be calculated
    exact_query += " GROUP BY Books.isbn"

    # Filter by minimum rating using HAVING 
    if min_rating:
        try:
            exact_query += " HAVING AVG(Reviews.review_score) >= %s"
            exact_params.append(float(min_rating))
        except ValueError:
            pass

    exact_query += " ORDER BY Books.title"

    return exact_query, exact_params

# Returns alternative book suggestions based on relaxed parameters
def build_alternative_query(title, author, genre, max_price, min_rating, publication_year,
                            r_title, r_author, r_genre, r_price, r_rating, r_year):
    return 