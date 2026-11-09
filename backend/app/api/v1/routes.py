from contextlib import closing
from datetime import datetime, timedelta, timezone
import hashlib
import re
import secrets

import mysql.connector
from flask import Blueprint, current_app, jsonify, make_response, request
from app.utils.queries import build_exact_query, build_alternative_query
from werkzeug.security import check_password_hash

from app.database.connection import get_db_connection

api_v1 = Blueprint("api_v1", __name__)
AUTH_SESSION_COOKIE = "smartbase_session"
AUTH_SESSION_LIFETIME = timedelta(days=7)
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,20}$")


@api_v1.get("/health")
def health_check():
    return jsonify(
        {
            "status": "online",
            "message": "SmartBase Backend is running!",
        }
    )


@api_v1.post("/auth/login")
def login():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"message": "Username and password are required"}), 400

    username = payload.get("username")
    password = payload.get("password")
    if (
        not isinstance(username, str)
        or not USERNAME_PATTERN.fullmatch(username)
        or not isinstance(password, str)
        or not 1 <= len(password) <= 128
    ):
        return jsonify({"message": "Username and password are required"}), 400

    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    """
                    SELECT user_id, username, password_hash
                    FROM `User`
                    WHERE username = %s
                    """,
                    (username,),
                )
                user = cursor.fetchone()

            if user is None or not check_password_hash(user[2], password):
                return jsonify({"message": "Invalid username or password"}), 401

            session_token = secrets.token_urlsafe(32)
            session_token_hash = hashlib.sha256(
                session_token.encode("utf-8")
            ).hexdigest()
            expires_at = datetime.now(timezone.utc) + AUTH_SESSION_LIFETIME

            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    """
                    INSERT INTO AuthSessions (session_token_hash, user_id, expires_at)
                    VALUES (%s, %s, %s)
                    """,
                    (session_token_hash, user[0], expires_at.replace(tzinfo=None)),
                )
            connection.commit()
    except (mysql.connector.Error, RuntimeError, ValueError):
        current_app.logger.exception("Username/password login failed")
        return jsonify({"message": "Login unavailable"}), 503

    response = make_response(
        jsonify({"user": {"user_id": user[0], "username": user[1]}})
    )
    response.set_cookie(
        AUTH_SESSION_COOKIE,
        session_token,
        max_age=int(AUTH_SESSION_LIFETIME.total_seconds()),
        httponly=True,
        secure=current_app.config["AUTH_SESSION_COOKIE_SECURE"],
        samesite="Lax",
        path="/",
    )
    return response


@api_v1.get("/auth/me")
def current_session():
    session_token = request.cookies.get(AUTH_SESSION_COOKIE)
    if not session_token:
        return jsonify({"message": "Authentication required"}), 401

    session_token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    """
                    SELECT `User`.user_id, `User`.username
                    FROM AuthSessions
                    JOIN `User` ON `User`.user_id = AuthSessions.user_id
                    WHERE AuthSessions.session_token_hash = %s
                      AND AuthSessions.expires_at > UTC_TIMESTAMP()
                    """,
                    (session_token_hash,),
                )
                user = cursor.fetchone()
    except (mysql.connector.Error, RuntimeError):
        current_app.logger.exception("Current session lookup failed")
        return jsonify({"message": "Session lookup unavailable"}), 503

    if user is None:
        response = make_response(
            jsonify({"message": "Authentication required"}),
            401,
        )
        response.delete_cookie(
            AUTH_SESSION_COOKIE,
            path="/",
            secure=current_app.config["AUTH_SESSION_COOKIE_SECURE"],
            httponly=True,
            samesite="Lax",
        )
        return response

    return jsonify({"user": {"user_id": user[0], "username": user[1]}})


@api_v1.post("/auth/logout")
def logout():
    session_token = request.cookies.get(AUTH_SESSION_COOKIE)
    if session_token:
        session_token_hash = hashlib.sha256(
            session_token.encode("utf-8")
        ).hexdigest()
        try:
            with closing(get_db_connection()) as connection:
                with closing(connection.cursor()) as cursor:
                    cursor.execute(
                        """
                        DELETE FROM AuthSessions
                        WHERE session_token_hash = %s
                        """,
                        (session_token_hash,),
                    )
                connection.commit()
        except (mysql.connector.Error, RuntimeError):
            current_app.logger.exception("Logout failed")
            return jsonify({"message": "Logout unavailable"}), 503

    response = make_response(jsonify({"message": "Signed out"}))
    response.delete_cookie(
        AUTH_SESSION_COOKIE,
        path="/",
        secure=current_app.config["AUTH_SESSION_COOKIE_SECURE"],
        httponly=True,
        samesite="Lax",
    )
    return response


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

# The endpoint for searching. Returns a json object with both exact matches and alternatives
@api_v1.get("/books/search")
def search_books():
    # Grab search parameters from the URL sent by React
    title = request.args.get("title", "").strip()
    author = request.args.get("author", "").strip()
    genre = request.args.get("genre", "All").strip()
    max_price = request.args.get("maxPrice", "").strip()
    min_rating = request.args.get("minRating", "").strip()
    publication_year = request.args.get("publicationYear", "").strip()
    relax_title = request.args.get("relaxTitle","").strip()
    relax_author = request.args.get("relaxAuthor","").strip()
    relax_genre = request.args.get("relaxGenre","").strip()
    relax_price = request.args.get("relaxPrice","").strip()
    relax_rating = request.args.get("relaxRating","").strip()
    relax_year = request.args.get("relaxYear","").strip()

    # From this information, build our two queries
    exact_query, exact_params = build_exact_query(title, author, genre, max_price, min_rating, publication_year)
    #alternative_query, alternative_params = build_alternative_query(title, author, genre, max_price, min_rating, publication_year,
    #                                            relax_title, relax_author, relax_genre, relax_price, relax_rating, relax_year
    #                                            )

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