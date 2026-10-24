import BookCard from "./BookCard";

export default function FeaturedBooks({
  books,
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
    </section>
  );
}