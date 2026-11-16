import { useState, useEffect } from "react";
import BookCard from "./BookCard";
import { fetchBooksFromApi, fetchUserReviewsApi } from "../services/api";

export default function AccountPage({ user, favorites, toggleFavorite, onSelectBook }) {
  const [favoriteBooks, setFavoriteBooks] = useState([]);
  const [userReviews, setUserReviews] = useState([]); // <--- State for user reviews
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadAccountData() {
      try {
        // Fetch favorite books catalog data and user's reviews in parallel
        const [books, reviews] = await Promise.all([
          fetchBooksFromApi(),
          fetchUserReviewsApi().catch((err) => {
            console.error("Failed to load user reviews:", err);
            return []; // Fallback to empty array if reviews fail
          })
        ]);

        if (!active) return;

        // Filter catalog down to favorited items
        const favs = books.filter((book) => favorites.includes(book.ISBN));
        setFavoriteBooks(favs);
        setUserReviews(reviews);
      } catch (err) {
        console.error("Failed to load account data:", err);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadAccountData();

    return () => {
      active = false;
    };
  }, [favorites]);

  if (!user) {
    return (
      <div className="page">
        <div className="empty-message">
          <h3>Access Denied</h3>
          <p>Please log in to view your account dashboard.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-heading">
        <p className="section-label">USER PROFILE</p>
        <h1>Welcome back, {user.username || user.name}</h1>
        <p>Manage your favorite reads and check out the reviews you have shared.</p>
      </div>

      {/* FAVORITES SECTION */}
      <section style={{ marginBottom: "48px" }}>
        <div className="result-heading">
          <h2>My Favorite Books</h2>
          <span className="result-count">{favoriteBooks.length} saved</span>
        </div>

        {loading ? (
          <p className="empty-message">Loading your favorites...</p>
        ) : favoriteBooks.length > 0 ? (
          <div className="book-grid">
            {favoriteBooks.map((book) => (
              <BookCard
                key={book.ISBN}
                book={book}
                type="favorite"
                favorite={true}
                toggleFavorite={toggleFavorite}
                user={user}
                onSelect={() => onSelectBook(book)}
              />
            ))}
          </div>
        ) : (
          <div className="empty-message">
            <h3>No favorites yet</h3>
            <p>Click the heart icon on any book card to save it to your wishlist.</p>
          </div>
        )}
      </section>

      {/* REVIEWS SECTION */}
      <section>
        <div className="result-heading">
          <h2>My Reviews</h2>
          <span className="result-count">{userReviews.length} posted</span>
        </div>

        {loading ? (
          <p className="empty-message">Loading your reviews...</p>
        ) : userReviews.length > 0 ? (
          <div className="reviews-list" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {userReviews.map((rev) => (
              <div 
                key={rev.review_id} 
                style={{ 
                  background: "white", 
                  padding: "16px", 
                  borderRadius: "8px", 
                  border: "1px solid var(--color-border)" 
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                  <strong>{rev.book_title}</strong>
                  <span>★ {rev.score}</span>
                </div>
                <p style={{ color: "var(--color-ink-soft)", margin: 0 }}>{rev.text}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-message">
            <h3>No reviews posted yet</h3>
            <p>Reviews you write in any book detail modal will show up right here.</p>
          </div>
        )}
      </section>
    </div>
  );
}