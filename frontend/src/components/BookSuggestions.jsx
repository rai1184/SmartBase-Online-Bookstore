import BookCard from "./BookCard";

export default function BookSuggestions({
  hasSearched,
  exactMatches,
  alternativeMatches,
  favorites,
  toggleFavorite,
  reviews,
  addReview,
  user,
  onSelectBook,
}) {
  if (!hasSearched) {
    return null;
  }

  return (
    <div className="suggestions-section">
      {exactMatches.length > 0 && (
        <>
          <div className="result-heading">
            <h2>Exact Matches</h2>
            <span className="result-count">{exactMatches.length} found</span>
          </div>
          <div className="book-grid">
            {exactMatches.map((book) => (
              <BookCard
                key={book.ISBN}
                book={book}
                type="exact"
                favorite={favorites.includes(book.ISBN)}
                toggleFavorite={toggleFavorite}
                reviews={reviews}
                addReview={addReview}
                user={user}
                onSelect={() => onSelectBook(book)}
              />
            ))}
          </div>
        </>
      )}

      {alternativeMatches.length > 0 && (
        <>
          <div className="result-heading alternatives-heading">
            <h2>Relaxed Criteria Matches</h2>
            <span className="result-count">{alternativeMatches.length} found</span>
          </div>
          <div className="book-grid">
            {alternativeMatches.map((book) => (
              <BookCard
                key={book.ISBN}
                book={book}
                type="match"
                favorite={favorites.includes(book.ISBN)}
                toggleFavorite={toggleFavorite}
                reviews={reviews}
                addReview={addReview}
                user={user}
                onSelect={() => onSelectBook(book)}
              />
            ))}
          </div>
        </>
      )}

      {exactMatches.length === 0 && alternativeMatches.length === 0 && (
        <div className="empty-message">
          <h3>No books found</h3>
          <p>Try adjusting your search filters or relaxing more criteria.</p>
        </div>
      )}
    </div>
  );
}