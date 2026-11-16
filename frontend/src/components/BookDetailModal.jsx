import { useState, useEffect } from "react";
import { fetchBookReviewsApi } from "../services/api";

export default function BookDetailModal({ book, onClose, addReview, user }) {
  const [reviewText, setReviewText] = useState("");
  const [reviewScore, setReviewScore] = useState("5");
  const [reviews, setReviews] = useState(null); // null means "loading"

  useEffect(() => {
    let active = true;

    fetchBookReviewsApi(book.ISBN)
      .then((data) => {
        if (active) {
          setReviews(data);
        }
      })
      .catch((err) => {
        console.error("Failed to load reviews:", err);
        if (active) setReviews([]); // Fallback to empty array on error
      });

    return () => {
      active = false;
    };
  }, [book.ISBN]);

  if (!book) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reviewText.trim()) return;

    await addReview(book.ISBN, Number(reviewScore), reviewText.trim());
    setReviewText("");
    setReviewScore("5");

    try {
      const updatedReviews = await fetchBookReviewsApi(book.ISBN);
      setReviews(updatedReviews);
    } catch (err) {
      console.error("Failed to refresh reviews:", err);
    }
  };

  const ratingDisplay =
    book.Rating != null && book.Rating > 0
      ? `★ ${book.Rating.toFixed(1)}`
      : "Not rated";

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-btn" onClick={onClose}>
          &times;
        </button>

        <div className="modal-grid-layout">
          {/* LEFT PANE: Book Info */}
          <div className="modal-left-pane">
            <div className="book-cover-container" style={{ height: "220px", marginBottom: "1.5rem" }}>
              <img 
                src={book.CoverImage ? `/images/books/${book.CoverImage}` : "/images/books/default-cover.jpg"} 
                className="book-cover-image"
                alt={book.Title}
              />
            </div>

            <h2 style={{ fontFamily: "Georgia, serif", fontSize: "1.8rem", marginBottom: "0.25rem" }}>{book.Title}</h2>
            <p className="book-author" style={{ fontSize: "1rem", marginBottom: "1rem" }}>by {book.Author}</p>

            {book.About && (
              <p style={{ color: "var(--color-ink-soft)", fontSize: "0.95rem", lineHeight: "1.6", marginBottom: "1.5rem" }}>
                {book.About}
              </p>
            )}

            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "10px", background: "white", padding: "12px", borderRadius: "6px", border: "1px solid var(--color-border)" }}>
              <div><strong>Genre:</strong> {book.Genre || "N/A"}</div>
              <div><strong>Pages:</strong> {book.Pages || "N/A"}</div>
              <div><strong>Published:</strong> {book.PublicationYear || "N/A"}</div>
              <div><strong>Price:</strong> ${book.MSRP ? book.MSRP.toFixed(2) : "0.00"}</div>
              <div><strong>Rating:</strong> {ratingDisplay}</div>
              <div><strong>In Stock:</strong> {book.InStock ?? 0} copies</div>
              <div style={{ gridColumn: "span 2" }}><strong>ISBN:</strong> {book.ISBN}</div>
            </div>
          </div>

          {/* RIGHT PANE: User Reviews & Submission */}
          <div className="modal-right-pane">
            <h3 style={{ fontFamily: "Georgia, serif", fontSize: "1.35rem", marginBottom: "1rem" }}>
              User Reviews {reviews ? `(${reviews.length})` : ""}
            </h3>

            <div className="modal-reviews-scroll">
              {reviews === null ? (
                <p className="empty-message" style={{ padding: "16px", textAlign: "center" }}>Loading reviews...</p>
              ) : reviews.length > 0 ? (
                reviews.map((rev, idx) => (
                  <div key={idx} className="review" style={{ marginBottom: "10px" }}>
                    <strong>{rev.name || rev.Username} · ★ {rev.score || rev.Score}</strong>
                    <p>{rev.text || rev.Text}</p>
                  </div>
                ))
              ) : (
                <p className="empty-message" style={{ padding: "16px", textAlign: "center" }}>No reviews yet. Be the first to review this book!</p>
              )}
            </div>

            <form onSubmit={handleSubmit} className="review-form" style={{ borderTop: "1px solid var(--color-border)", paddingTop: "1rem" }}>
              <h4 style={{ margin: "0 0 8px 0" }}>Write a Review</h4>
              {!user && (
                <p className="warning">Please log in before submitting a review.</p>
              )}

              <select
                value={reviewScore}
                onChange={(e) => setReviewScore(e.target.value)}
              >
                <option value="5">5 stars</option>
                <option value="4">4 stars</option>
                <option value="3">3 stars</option>
                <option value="2">2 stars</option>
                <option value="1">1 star</option>
              </select>

              <textarea
                placeholder="Share your thoughts on this book..."
                value={reviewText}
                onChange={(e) => setReviewText(e.target.value)}
              />

              <button type="submit" disabled={!user}>
                Post Review
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}