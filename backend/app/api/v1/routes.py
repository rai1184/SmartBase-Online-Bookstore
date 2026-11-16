from contextlib import closing

import mysql.connector
import hashlib
from flask import Blueprint, current_app, jsonify, request
from app.utils.queries import build_alternative_query, build_exact_query, build_insert_review_query
from app.utils.scoring import rank_alternatives
from app.utils.format import format_book

from app.database.connection import get_db_connection

api_v1 = Blueprint("api_v1", __name__)


# Reusable auth helper
def get_current_user_id():
    """Validates the session cookie and returns the user_id if valid, otherwise None."""
    session_token = request.cookies.get("smartbase_session")
    if not session_token:
        return None

    session_token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor(dictionary=True)) as cursor:
                cursor.execute(
                    """
                    SELECT user_id 
                    FROM AuthSessions 
                    WHERE session_token_hash = %s 
                      AND expires_at > UTC_TIMESTAMP()
                    """,
                    (session_token_hash,)
                )
                session_row = cursor.fetchone()
                if session_row:
                    return session_row["user_id"]
    except Exception:
        current_app.logger.exception("Session validation failed")
    
    return None


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
            Books.cover_image,
            Books.in_stock,
            Books.page_count
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


# Book search endpoint, takes all parameters and returns exact and alternate matches
@api_v1.get("/books/search")
def search_books():
    title = request.args.get("title", "").strip()
    author = request.args.get("author", "").strip()
    genre = request.args.get("genre", "All").strip()
    max_price = request.args.get("max_price", "").strip()
    min_rating = request.args.get("min_rating", "").strip()
    publication_year = request.args.get("publication_year", "").strip()
    in_stock = request.args.get("in_stock", "").strip()
    page_count = request.args.get("page_count", "").strip()
    
    relax_title = request.args.get("relax_title", "").strip() == "true"
    relax_author = request.args.get("relax_author", "").strip() == "true"
    relax_genre = request.args.get("relax_genre", "").strip() == "true"
    relax_price = request.args.get("relax_price", "").strip() == "true"
    relax_rating = request.args.get("relax_rating", "").strip() == "true"
    relax_year = request.args.get("relax_year", "").strip() == "true"
    relax_in_stock = request.args.get("relax_in_stock", "").strip() == "true"
    relax_page_count = request.args.get("relax_page_count", "").strip() == "true"

    exact_query, exact_params = build_exact_query(
        title, author, genre, max_price, min_rating, publication_year, page_count, in_stock
    )
    alternative_query, alternative_params = build_alternative_query(
        title, author, genre, max_price, min_rating, publication_year, page_count,
        relax_title, relax_author, relax_genre, relax_price, relax_rating, relax_year, relax_page_count, relax_in_stock
    )

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

    target_params = {
        "max_price": max_price,
        "publication_year": publication_year,
        "min_rating": min_rating,
        "genre": genre
    }

    relaxation_flags = {
        "relax_price": relax_price,
        "relax_year": relax_year,
        "relax_rating": relax_rating,
        "relax_genre": relax_genre
    }

    scored_alternatives = rank_alternatives(
        formatted_alternatives, exact_isbns, target_params, relaxation_flags
    )

    return jsonify({
        "exact_matches": formatted_exact,
        "alternative_matches": scored_alternatives, 
    })


# Post review of book
@api_v1.post("/reviews")
def submit_review():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Authentication required."}), 401

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid request body."}), 400

    isbn = payload.get("isbn")
    rating = payload.get("rating")
    comment = payload.get("comment", "")

    if not isbn or rating is None:
        return jsonify({"error": "ISBN and rating are required fields."}), 400

    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
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
        return jsonify({"error": "You have already submitted a review for this book."}), 409

    except Exception:
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


# Get all reviews for the currently logged-in user
@api_v1.get("/user/reviews")
def get_user_reviews():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Authentication required"}), 401

    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor(dictionary=True)) as cursor:
                cursor.execute(
                    """
                    SELECT 
                        r.review_id, 
                        r.isbn, 
                        r.review_score AS score, 
                        r.review_text AS text, 
                        b.title AS book_title,
                        b.cover_image AS cover_image
                    FROM Reviews r
                    JOIN Books b ON r.isbn = b.isbn
                    WHERE r.user_id = %s
                    """,
                    (user_id,)
                )
                reviews = cursor.fetchall()
        
        return jsonify(reviews)
    except Exception:
        current_app.logger.exception("Failed to fetch user reviews")
        return jsonify({"error": "Reviews unavailable"}), 503


# Delete a review by ID
@api_v1.delete("/reviews/<int:review_id>")
def delete_review(review_id):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Authentication required"}), 401

    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor(dictionary=True)) as cursor:
                cursor.execute(
                    "DELETE FROM Reviews WHERE review_id = %s AND user_id = %s",
                    (review_id, user_id)
                )
                connection.commit()
                
                if cursor.rowcount == 0:
                    return jsonify({"message": "Review not found or unauthorized"}), 404

        return jsonify({"message": "Review deleted successfully"})
    except Exception:
        current_app.logger.exception("Failed to delete review")
        return jsonify({"error": "Operation unavailable"}), 503


# Update a review by ID
@api_v1.put("/reviews/<int:review_id>")
def update_review(review_id):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Authentication required"}), 401

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"message": "Invalid payload"}), 400

    score = payload.get("score")
    text = payload.get("text")

    if not score or not text or not text.strip():
        return jsonify({"message": "Score and text are required"}), 400

    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor(dictionary=True)) as cursor:
                cursor.execute(
                    """
                    UPDATE Reviews 
                    SET review_score = %s, review_text = %s 
                    WHERE review_id = %s AND user_id = %s
                    """,
                    (score, text.strip(), review_id, user_id)
                )
                connection.commit()

                if cursor.rowcount == 0:
                    return jsonify({"message": "Review not found or unauthorized"}), 404

        return jsonify({"message": "Review updated successfully"})
    except Exception:
        current_app.logger.exception("Failed to update review")
        return jsonify({"error": "Operation unavailable"}), 503