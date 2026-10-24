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
}) {
  if (!hasSearched) {
    return (
      <div className="empty-message">
        Enter your search criteria above to start searching.
      </div>
    );
  }

  return (
    <div className="suggestions-section">
      <div className="result-heading">
        <div>
          <p className="section-label">
            SEARCH RESULTS
          </p>

          <h2>Exact Matches</h2>
        </div>

        <span className="result-count">
          {exactMatches.length} found
        </span>
      </div>

      {exactMatches.length === 0 ? (
        <p className="empty-message">
          No exact matches were found.
        </p>
      ) : (
        <div className="book-grid">
          {exactMatches.map((book) => (
            <BookCard
              key={book.ISBN}
              book={book}
              type="exact"
              favorite={favorites.includes(book.ISBN)}
              toggleFavorite={toggleFavorite}
              reviews={reviews[book.ISBN] || []}
              addReview={addReview}
              user={user}
            />
          ))}
        </div>
      )}

      <div className="result-heading alternatives-heading">
        <div>
          <p className="section-label">
            CONTEXTUAL SEARCH
          </p>

          <h2>
            Smart Alternative Suggestions
          </h2>

          <p className="section-description">
            SmartBase relaxes selected search criteria to find
            nearby alternatives when necessary.
          </p>
        </div>

        <span className="result-count">
          {alternativeMatches.length} suggested
        </span>
      </div>

      {alternativeMatches.length === 0 ? (
        <p className="empty-message">
          No alternative suggestions are available with the
          selected relaxation settings.
        </p>
      ) : (
        <div className="book-grid">
          {alternativeMatches.map((book) => (
            <BookCard
              key={book.ISBN}
              book={book}
              type="alternative"
              similarityScore={book.similarityScore}
              favorite={favorites.includes(book.ISBN)}
              toggleFavorite={toggleFavorite}
              reviews={reviews[book.ISBN] || []}
              addReview={addReview}
              user={user}
            />
          ))}
        </div>
      )}
    </div>
  );
}