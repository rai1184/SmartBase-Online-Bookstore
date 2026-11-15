from contextlib import closing

import mysql.connector
from flask import Blueprint, current_app, jsonify, request
from app.utils.queries import build_alternative_query, build_exact_query, build_insert_review_query
from app.utils.scoring import rank_alternatives
from app.utils.format import format_book

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
            Genres.genre_name,
            AVG(Reviews.review_score) AS avg_rating,
            COUNT(Reviews.review_score) AS review_count,
            Books.cover_image
        FROM Books
        LEFT JOIN Genres ON Books.genre_id = Genres.genre_id
        LEFT JOIN Reviews ON Books.isbn = Reviews.isbn
        GROUP BY Books.isbn
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

    books = [format_book(row) for row in rows]
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

    formatted_exact = [format_book(row) for row in exact_rows]
    formatted_alternatives = [format_book(row) for row in alternate_rows]

    exact_isbns = {book["isbn"] for book in formatted_exact}

    # Target parameters for the alternative search
    target_params = {
        "max_price": max_price,
        "publication_year": publication_year,
        "min_rating": min_rating,
        "genre": genre
    }

    # Whether or not we are relaxing these in particular plays into the alternate ranking
    relaxation_flags = {
        "relax_price": relax_price,
        "relax_year": relax_year,
        "relax_rating": relax_rating,
        "relax_genre": relax_genre
    }

    # Rank alternatives
    scored_alternatives = rank_alternatives(
        formatted_alternatives, exact_isbns, target_params, relaxation_flags
    )

    return jsonify({
        "exact_matches": formatted_exact,
        "alternative_matches": scored_alternatives, 
    })

import hashlib

@api_v1.post("/reviews")
def submit_review():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid request body."}), 400

    isbn = payload.get("isbn")
    rating = payload.get("rating")
    comment = payload.get("comment", "")

    if not isbn or rating is None:
        return jsonify({"error": "ISBN and rating are required fields."}), 400

    session_token = request.cookies.get("smartbase_session")
    if not session_token:
        return jsonify({"error": "Authentication required."}), 401

    session_token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()

    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                # 1. Verify session token against AuthSessions and get user_id
                cursor.execute(
                    """
                    SELECT `User`.user_id
                    FROM AuthSessions
                    JOIN `User` ON `User`.user_id = AuthSessions.user_id
                    WHERE AuthSessions.session_token_hash = %s
                      AND AuthSessions.expires_at > UTC_TIMESTAMP()
                    """,
                    (session_token_hash,),
                )
                user_row = cursor.fetchone()

                if not user_row:
                    return jsonify({"error": "Invalid or expired session."}), 401

                user_id = user_row[0]

                # 2. Insert the review
                cursor.execute(
                    """
                    INSERT INTO Reviews (isbn, user_id, review_score, review_text)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (isbn, user_id, rating, comment),
                )
                connection.commit()

        return jsonify({
            "message": "Review submitted successfully!",
            "review": {
                "isbn": isbn,
                "rating": rating,
                "comment": comment
            }
        }), 201

    except mysql.connector.IntegrityError:
        # Triggered if the user has already reviewed this specific book
        return jsonify({"error": "You have already submitted a review for this book."}), 409

    except Exception as e:
        current_app.logger.exception("Review submission failed")
        return jsonify({"error": "Review submission unavailable"}), 503

# Get all reviews for a book
@api_v1.get("/books/<isbn>/reviews")
def get_book_reviews(isbn):
    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor(dictionary=True)) as cursor:
                cursor.execute(
                    """
                    SELECT 
                        r.review_id, 
                        r.isbn, 
                        r.user_id, 
                        r.review_score AS score, 
                        r.review_text AS text, 
                        u.username AS name
                    FROM Reviews r
                    JOIN User u ON r.user_id = u.user_id
                    WHERE r.isbn = %s
                    """,
                    (isbn,)
                )
                reviews = cursor.fetchall()
        
        # Map using the SQL aliases (name, score, text) and iterate over `reviews`
        formatted_reviews = [
            {
                "name": row["name"],
                "score": row["score"],
                "text": row["text"],
            }
            for row in reviews
        ]
        return jsonify(formatted_reviews)
    except Exception:
        current_app.logger.exception("Failed to fetch book reviews")
        return jsonify({"error": "Reviews unavailable"}), 503