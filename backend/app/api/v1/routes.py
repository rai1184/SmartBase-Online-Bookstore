from contextlib import closing

import mysql.connector
from flask import Blueprint, current_app, jsonify

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
