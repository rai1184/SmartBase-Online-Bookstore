from contextlib import closing

import mysql.connector
from flask import Blueprint, current_app, jsonify, request
from app.utils.queries import build_exact_query, build_alternative_query
from app.utils.scoring import rank_alternatives

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

# Import your scoring functions at the top of your route file
from app.utils.scoring import rank_alternatives

@api_v1.get("/books/search")
def search_books():
    # Grab search parameters from the URL sent by React
    title = request.args.get("title", "").strip()
    author = request.args.get("author", "").strip()
    genre = request.args.get("genre", "All").strip()
    max_price = request.args.get("max_price", "").strip()
    min_rating = request.args.get("min_rating", "").strip()
    publication_year = request.args.get("publication_year", "").strip()
    
    relax_title = request.args.get("relax_title", "").strip() == "true"
    relax_author = request.args.get("relax_author", "").strip() == "true"
    relax_genre = request.args.get("relax_genre", "").strip() == "true"
    relax_price = request.args.get("relax_price", "").strip() == "true"
    relax_rating = request.args.get("relax_rating", "").strip() == "true"
    relax_year = request.args.get("relax_year", "").strip() == "true"

    # Create queries
    exact_query, exact_params = build_exact_query(title, author, genre, max_price, min_rating, publication_year)
    alternative_query, alternative_params = build_alternative_query(
        title, author, genre, max_price, min_rating, publication_year,
        relax_title, relax_author, relax_genre, relax_price, relax_rating, relax_year
    )

    # Run the created queries
    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(exact_query, tuple(exact_params))
                exact_rows = cursor.fetchall()
                cursor.execute(alternative_query, tuple(alternative_params))
                alternate_rows = cursor.fetchall()

    except (mysql.connector.Error, RuntimeError):
        current_app.logger.exception("Book search request failed")
        return jsonify({"message": "Search unavailable"}), 503

    def format_rows(rows):
        return [
            {
                "isbn": isbn,
                "title": title_val,
                "author": author_val,
                "about": about,
                "msrp": float(msrp) if msrp is not None else 0.0,
                "publication_date": publication_date.isoformat() if publication_date else None,
                "rating": float(avg_rating) if avg_rating is not None else None,
                "genre": genre_name,
            }
            for (isbn, title_val, author_val, about, msrp, publication_date, genre_name, avg_rating) in rows
        ]

    formatted_exact = format_rows(exact_rows)
    formatted_alternatives = format_rows(alternate_rows)

    exact_isbns = {book["isbn"] for book in formatted_exact}

    # Target parameters for the alternative search
    target_params = {
        "max_price": max_price,
        "publication_year": publication_year
    }

    # Whether or not we are relaxing these in particular plays into the alternate ranking
    relaxation_flags = {
        "relax_price": relax_price,
        "relax_year": relax_year
    }

    # Rank alternatives
    scored_alternatives = rank_alternatives(
        formatted_alternatives, exact_isbns, target_params, relaxation_flags
    )

    return jsonify({
        "exact_matches": formatted_exact,
        "alternative_matches": scored_alternatives, 
    })