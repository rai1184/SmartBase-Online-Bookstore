import { useState } from "react";

export default function BookCard({
  book,
  type,
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

  // Determine review count and rating formatted string
  const totalReviews = book.ReviewCount ?? reviews.length;
  const ratingDisplay =
    book.Rating != null && book.Rating > 0
      ? `★ ${book.Rating.toFixed(1)}`
      : "Not rated";

  return (
    <article className="book-card">
      <div className="card-top">
        <div>
          {type === "exact" && (
            <span className="exact-badge">
              Exact Match
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

      {/* Book Cover Image */}
      <div className="book-cover-container">
        <img 
          src={book.CoverImage || "/images/books/default-cover.jpg"} 
          alt={""} 
          className="book-cover-image"
        />
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
            ${book.MSRP ? book.MSRP.toFixed(2) : "0.00"}
          </strong>

          <span>
            {ratingDisplay}
          </span>
        </div>

        <p className="isbn">
          ISBN: {book.ISBN}
        </p>

        <div className="review-header">
          <span>
            {totalReviews} review{totalReviews === 1 ? "" : "s"}
          </span>

          <button
            onClick={() =>
              setShowReview(!showReview)
            }
          >
            {showReview ? "Cancel" : "Write Review"}
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