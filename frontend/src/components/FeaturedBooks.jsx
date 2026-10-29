import BookCard from "./BookCard";

export default function FeaturedBooks({
  books,
  loading,
  error,
  onRetry,
  favorites,
  toggleFavorite,
  reviews,
  addReview,
  user,
  goToSearch,
}) {
  return (
    <section className="featured-section">
      <div className="featured-heading">
        <div>
          <p className="section-label">DISCOVER</p>
          <h2>Featured Books</h2>
          <p>
            Browse a few books from SmartBase or use Smart Search
            to find something specific.
          </p>
        </div>

        <button
          className="browse-button"
          onClick={goToSearch}
        >
          Browse All Books
        </button>
      </div>

      {loading ? (
        <p className="empty-message" role="status">
          Loading books...
        </p>
      ) : error ? (
        <div className="empty-message" role="alert">
          <p>{error}</p>
          <button className="standard-button" onClick={onRetry}>
            Try again
          </button>
        </div>
      ) : books.length === 0 ? (
        <p className="empty-message">
          No books are available yet.
        </p>
      ) : (
        <div className="book-grid">
          {books.map((book) => (
            <BookCard
              key={book.ISBN}
              book={book}
              type="featured"
              favorite={favorites.includes(book.ISBN)}
              toggleFavorite={toggleFavorite}
              reviews={reviews[book.ISBN] || []}
              addReview={addReview}
              user={user}
            />
          ))}
        </div>
      )}
    </section>
  );
}