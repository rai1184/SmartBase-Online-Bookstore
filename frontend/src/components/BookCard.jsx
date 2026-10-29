import { useState } from "react";

export default function BookCard({
  book,
  type,
  similarityScore,
  favorite,
  toggleFavorite,
  reviews = [],
  addReview,
  user,
}) {
  const [showReview, setShowReview] = useState(false);
  const [reviewText, setReviewText] = useState("");
  const [reviewScore, setReviewScore] = useState("5");

  const submitReview = (event) => {
    event.preventDefault();

    if (!reviewText.trim()) {
      return;
    }

    addReview(
      book.ISBN,
      Number(reviewScore),
      reviewText.trim()
    );

    setReviewText("");
    setReviewScore("5");
    setShowReview(false);
  };

  return (
    <article className="book-card">
      <div className="card-top">
        <div>
          {type === "exact" && (
            <span className="exact-badge">
              Exact Match
            </span>
          )}

          {type === "alternative" && (
            <span className="match-badge">
              {Math.round(similarityScore * 100)}% Match
            </span>
          )}

          {type === "featured" && (
            <span className="featured-badge">
              Featured
            </span>
          )}
        </div>

        <button
          className={
            favorite
              ? "heart favorite"
              : "heart"
          }
          onClick={() => toggleFavorite(book.ISBN)}
          title={
            favorite
              ? "Remove from favorites"
              : "Add to favorites"
          }
        >
          {favorite ? "♥" : "♡"}
        </button>
      </div>

      <div className="book-cover-placeholder">
        <span>{book.Genre}</span>

        <strong>
          {book.Title.charAt(0)}
        </strong>
      </div>

      <div className="book-information">
        <h3>{book.Title}</h3>

        <p className="book-author">
          by {book.Author}
        </p>

        {book.About && (
          <p className="book-description">
            {book.About}
          </p>
        )}

        <div className="book-tags">
          <span>{book.Genre}</span>
          {book.Pages && <span>{book.Pages} pages</span>}
          {book.PublicationYear && (
            <span>{book.PublicationYear}</span>
          )}
        </div>

        <div className="book-price-row">
          <strong>
            ${book.MSRP.toFixed(2)}
          </strong>

          <span>
            {book.Rating == null ? "Not rated" : `★ ${book.Rating}`}
          </span>
        </div>

        <p className="isbn">
          ISBN: {book.ISBN}
        </p>

        <div className="review-header">
          <span>
            {reviews.length} review
            {reviews.length === 1 ? "" : "s"}
          </span>

          <button
            onClick={() =>
              setShowReview(!showReview)
            }
          >
            Write Review
          </button>
        </div>

        {reviews.length > 0 && (
          <div className="review-list">
            {reviews.slice(-2).map((review, index) => (
              <div
                className="review"
                key={`${review.name}-${index}`}
              >
                <strong>
                  {review.name} · ★ {review.score}
                </strong>

                <p>{review.text}</p>
              </div>
            ))}
          </div>
        )}

        {showReview && (
          <form
            className="review-form"
            onSubmit={submitReview}
          >
            {!user && (
              <p className="warning">
                Please login before submitting a review.
              </p>
            )}

            <select
              value={reviewScore}
              onChange={(event) =>
                setReviewScore(event.target.value)
              }
            >
              <option value="5">5 stars</option>
              <option value="4">4 stars</option>
              <option value="3">3 stars</option>
              <option value="2">2 stars</option>
              <option value="1">1 star</option>
            </select>

            <textarea
              placeholder="Write your review..."
              value={reviewText}
              onChange={(event) =>
                setReviewText(event.target.value)
              }
            />

            <button type="submit">
              Submit Review
            </button>
          </form>
        )}
      </div>
    </article>
  );
}