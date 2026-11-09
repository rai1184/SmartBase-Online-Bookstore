# Unpack SQL row and pack it into a dictionary
def format_book(row):
    isbn, title, author, about, msrp, publication_date, genre_name, avg_rating, review_count, cover_image = row
    
    return {
        "isbn": isbn,
        "title": title,
        "author": author,
        "about": about,
        "msrp": float(msrp) if msrp is not None else 0.0,
        "publication_date": publication_date.isoformat() if publication_date else None,
        "genre": genre_name,
        "avg_rating": float(avg_rating) if avg_rating is not None else 0.0,
        "review_count": int(review_count) if review_count is not None else 0,
        "cover_image": cover_image
    }