export default function BookCard({
  book,
  type,
  favorite,
  toggleFavorite,
  reviews = [],
  onSelect,
}) {
  const totalReviews = book.ReviewCount ?? reviews.length;
  const ratingDisplay =
    book.Rating != null && book.Rating > 0
      ? `★ ${book.Rating.toFixed(1)}`
      : "Not rated";

  return (
    <article className="book-card clickable" onClick={onSelect}>
      <div className="card-top" onClick={(e) => e.stopPropagation()}>
        <div>
          {type === "exact" && (
            <span className="exact-badge">Exact Match</span>
          )}
        </div>

        <button
          className={favorite ? "heart favorite" : "heart"}
          onClick={() => toggleFavorite(book.ISBN)}
          title={favorite ? "Remove from favorites" : "Add to favorites"}
        >
          {favorite ? "♥" : "♡"}
        </button>
      </div>

      {/* Book Cover Image */}
      <div className="book-cover-container">
        <img 
          src={
            !book.CoverImage
              ? "/images/books/default-cover.jpg"
              : book.CoverImage.startsWith("http://") || book.CoverImage.startsWith("https://")
              ? book.CoverImage
              : `/images/books/${book.CoverImage}`
          } 
          className="book-cover-image"
          alt={book.Title}
        />
      </div>
      
      <div className="book-information">
        <h3>{book.Title}</h3>
        <p className="book-author">by {book.Author}</p>

        {/* Stock status */}
        {book.InStock !== undefined && (
          <p style={{ margin: "4px 0 10px 0", fontSize: "0.85rem" }}>
            <span style={{ color: book.InStock === 0 ? "var(--color-danger, #9b3d49)" : "inherit" }}>
              {book.InStock > 0 ? `● ${book.InStock} in stock` : "✕ Out of stock"}
            </span>
          </p>
        )}

        {book.About && (
          <p className="book-description">{book.About}</p>
        )}

        <div className="book-tags">
          <span>{book.Genre}</span>
          {book.Pages && <span>{book.Pages} pages</span>}
          {book.PublicationYear && <span>{book.PublicationYear}</span>}
        </div>

        <div className="book-price-row">
          <strong>${book.MSRP ? book.MSRP.toFixed(2) : "0.00"}</strong>
          <span>{ratingDisplay}</span>
        </div>

        <p className="isbn">ISBN: {book.ISBN}</p>

        <div className="review-header">
          <span>{totalReviews} review{totalReviews === 1 ? "" : "s"}</span>
        </div>

        {reviews.length > 0 && (
          <div className="review-list">
            {reviews.slice(-2).map((review, index) => (
              <div className="review" key={`${review.name}-${index}`}>
                <strong>{review.name} · ★ {review.score}</strong>
                <p>{review.text}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </article>
  );
}