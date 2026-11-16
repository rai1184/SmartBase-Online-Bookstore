from contextlib import closing
import mysql.connector
from flask import Blueprint, current_app, jsonify, request
from app.database.connection import get_db_connection
import os
from werkzeug.utils import secure_filename

# The file extensions we accept for images
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

admin_bp = Blueprint("admin_bp", __name__)

# Check if user_id is an admin to gate admin features
def is_admin_user(user_id):
    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("SELECT is_admin FROM User WHERE user_id = %s", (user_id,))
                row = cursor.fetchone()
                return row and row[0] == 1
    except Exception:
        return False

# Insert new book into DB
@admin_bp.post("/admin/books")
def admin_add_book():
    data = request.get_json() or {}
    user_id = data.get("user_id")

    if not user_id or not is_admin_user(user_id):
        return jsonify({"error": "Unauthorized: Admin privileges required."}), 403

    isbn = data.get("isbn")
    title = data.get("title")
    author = data.get("author")
    about = data.get("about", "")
    msrp = data.get("msrp")
    publication_date = data.get("publication_date")
    genre_id = data.get("genre_id")
    cover_image = data.get("cover_image")
    in_stock = data.get("in_stock", 0)
    page_count = data.get("page_count", 0)

    if not isbn or not title or not author or msrp is None:
        return jsonify({"error": "ISBN, title, author, and MSRP are required."}), 400

    query = """
        INSERT INTO Books (isbn, title, author, about, msrp, publication_date, genre_id, cover_image, in_stock, page_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (isbn, title, author, about, msrp, publication_date or None, genre_id or None, cover_image or None, in_stock, page_count)

    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(query, params)
                connection.commit()
        return jsonify({"message": "Book added successfully!"}), 201
    except Exception as e:
        current_app.logger.exception("Failed to add book")
        return jsonify({"error": str(e)}), 500

# Edit book in DB by isbn
@admin_bp.put("/admin/books/<isbn>")
def admin_update_book(isbn):
    data = request.get_json() or {}
    user_id = data.get("user_id")

    if not user_id or not is_admin_user(user_id):
        return jsonify({"error": "Unauthorized: Admin privileges required."}), 403

    title = data.get("title")
    author = data.get("author")
    about = data.get("about", "")
    msrp = data.get("msrp")
    publication_date = data.get("publication_date")
    genre_id = data.get("genre_id")
    cover_image = data.get("cover_image")
    in_stock = data.get("in_stock", 0)
    page_count = data.get("page_count", 0)

    query = """
        UPDATE Books
        SET title = %s, author = %s, about = %s, msrp = %s, publication_date = %s, 
            genre_id = %s, cover_image = %s, in_stock = %s, page_count = %s
        WHERE isbn = %s
    """
    params = (title, author, about, msrp, publication_date or None, genre_id or None, cover_image or None, in_stock, page_count, isbn)

    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(query, params)
                connection.commit()
        return jsonify({"message": "Book updated successfully!"}), 200
    except Exception as e:
        current_app.logger.exception("Failed to update book")
        return jsonify({"error": str(e)}), 500

# Delete book in DB by ISBN
@admin_bp.delete("/admin/books/<isbn>")
def admin_delete_book(isbn):
    user_id = request.args.get("user_id") or (request.get_json() and request.get_json().get("user_id"))

    if not user_id or not is_admin_user(user_id):
        return jsonify({"error": "Unauthorized: Admin privileges required."}), 403

    # Remove the book from tables that reference it (not needed?)
    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("DELETE FROM Reviews WHERE isbn = %s", (isbn,))
                cursor.execute("DELETE FROM Favorites WHERE isbn = %s", (isbn,))
                cursor.execute("DELETE FROM Books WHERE isbn = %s", (isbn,))
                connection.commit()
        return jsonify({"message": "Book deleted successfully!"}), 200
    except Exception as e:
        current_app.logger.exception("Failed to delete book")
        return jsonify({"error": str(e)}), 500

# If image is allowed to be uploaded
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Take image upload and put it in images/books
@admin_bp.post("/admin/upload-image")
def admin_upload_image():
    user_id = request.form.get("user_id")

    if not user_id or not is_admin_user(user_id):
        return jsonify({"error": "Unauthorized: Admin privileges required."}), 403

    if "image" not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No selected file."}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Save directly into static_folder/books/
        upload_folder = os.path.join(current_app.static_folder, "books")
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        # Return relative path so cover_image is stored as 'books/filename.jpg'
        relative_filename = f"books/{filename}"
        return jsonify({"filename": relative_filename, "message": "Image uploaded successfully!"}), 200

    return jsonify({"error": "Invalid file type. Allowed types: png, jpg, jpeg, webp"}), 400