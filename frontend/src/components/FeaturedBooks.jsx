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
  onSelectBook,
}) {
  return (
    <section className="featured-section">
      <div className="featured-heading">
        <div>
          <p className="section-label">CURATED DISCOVERY</p>
          <h2>Featured Books</h2>
          <p>Explore hand-picked selections and top-rated reads across genres.</p>
        </div>
        <button className="browse-button" onClick={goToSearch}>
          Search All Books
        </button>
      </div>

      {loading ? (
        <p className="empty-message" role="status">Loading featured books...</p>
      ) : error ? (
        <div className="empty-message" role="alert">
          <p>{error}</p>
          <button className="standard-button" onClick={onRetry}>Try again</button>
        </div>
      ) : (
        <div className="book-grid">
          {books.map((book) => (
            <BookCard
              key={book.ISBN}
              book={book}
              type="featured"
              favorite={favorites.includes(book.ISBN)}
              toggleFavorite={toggleFavorite}
              reviews={reviews}
              addReview={addReview}
              user={user}
              onSelect={() => onSelectBook(book)}
            />
          ))}
        </div>
      )}
    </section>
  );
}