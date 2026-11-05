from contextlib import closing

import mysql.connector
from flask import Blueprint, current_app, jsonify, request

from app.database.connection import get_db_connection

api_v1 = Blueprint("api_v1", __name__)


@api_v1.get("/health")
def health_check():
    return jsonify(
        {
            "status": "online",
            "message": "SmartBase Backend is running!",
        }
    )


@api_v1.get("/books")
def list_books():
    query = """
        SELECT
            Books.isbn,
            Books.title,
            Books.author,
            Books.about,
            Books.msrp,
            Books.publication_date,
            Genres.genre_name
        FROM Books
        LEFT JOIN Genres ON Books.genre_id = Genres.genre_id
        ORDER BY Books.title
    """

    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
    except (mysql.connector.Error, RuntimeError):
        current_app.logger.exception("Book list request failed")
        return jsonify({"message": "Books unavailable"}), 503

    books = [
        {
            "isbn": isbn,
            "title": title,
            "author": author,
            "about": about,
            "msrp": float(msrp),
            "publication_date": (
                publication_date.isoformat() if publication_date else None
            ),
            "genre": genre_name,
        }
        for (
            isbn,
            title,
            author,
            about,
            msrp,
            publication_date,
            genre_name,
        ) in rows
    ]
    return jsonify(books)


@api_v1.get("/health/database")
def database_health_check():
    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("SELECT COUNT(*) FROM Books")
                book_count = cursor.fetchone()[0]
    except (mysql.connector.Error, RuntimeError):
        current_app.logger.exception("Database health check failed")
        return jsonify(
            {
                "status": "error",
                "message": "Database unavailable",
            }
        ), 503

    return jsonify(
        {
            "status": "online",
            "book_count": book_count,
        }
    )

# The endpoint for searching. Returns a json object with both exact matches and alternatives
@api_v1.get("/books/search")
def search_books():
    # Grab search parameters from the URL sent by React
    title = request.args.get("title", "").strip()
    author = request.args.get("author", "").strip()
    genre = request.args.get("genre", "All").strip()
    maxPrice = request.args.get("maxPrice", "").strip()
    minRating = request.args.get("minRating", "").strip()
    publicationYear = request.args.get("publicationYear", "").strip()

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
    if maxPrice:
        try:
            exact_query += " AND Books.msrp <= %s"
            exact_params.append(float(maxPrice))
        except ValueError:
            pass
    if publicationYear:
        try:
            exact_query += " AND YEAR(Books.publication_date) = %s"
            exact_params.append(int(publicationYear))
        except ValueError:
            pass

    # Group by the unique book
    exact_query += " GROUP BY Books.isbn"

    # Filter by minimum rating using HAVING 
    if minRating:
        try:
            exact_query += " HAVING AVG(Reviews.review_score) >= %s"
            exact_params.append(float(minRating))
        except ValueError:
            pass

    exact_query += " ORDER BY Books.title"

    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                # Run the exact match query
                cursor.execute(exact_query, tuple(exact_params))
                exact_rows = cursor.fetchall() # all exact matches

    except (mysql.connector.Error, RuntimeError):
        current_app.logger.exception("Book search request failed")
        return jsonify({"message": "Search unavailable"}), 503

    # Convert rows into dictionaries (matching the 8 selected columns)
    def format_rows(rows):
        return [
            {
                "isbn": isbn,
                "title": title,
                "author": author,
                "about": about,
                "msrp": float(msrp) if msrp is not None else 0.0,
                "publication_date": publication_date.isoformat() if publication_date else None,
                "rating": float(avg_rating) if avg_rating is not None else None,
                "genre": genre_name,
            }
            for (isbn, title, author, about, msrp, publication_date, genre_name, avg_rating) in rows
        ]

    # Return both sets of results to React as JSON
    return jsonify({
        "exact_matches": format_rows(exact_rows),
        "alternative_matches": [], 
    })