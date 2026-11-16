import { useState, useEffect } from "react";
import BookCard from "./BookCard";
import { fetchBooksFromApi, fetchUserReviewsApi, deleteReviewApi, updateReviewApi } from "../services/api";

export default function AccountPage({ user, favorites, toggleFavorite, onSelectBook }) {
  const [favoriteBooks, setFavoriteBooks] = useState([]);
  const [userReviews, setUserReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  // Edit state tracking
  const [editingId, setEditingId] = useState(null);
  const [editScore, setEditScore] = useState(5);
  const [editText, setEditText] = useState("");

  useEffect(() => {
    let active = true;

    async function loadAccountData() {
      try {
        const [books, reviews] = await Promise.all([
          fetchBooksFromApi(),
          fetchUserReviewsApi().catch(() => [])
        ]);

        if (!active) return;
        setFavoriteBooks(books.filter((book) => favorites.includes(book.ISBN)));
        setUserReviews(reviews);
      } catch (err) {
        console.error("Failed to load account data:", err);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadAccountData();
    return () => { active = false; };
  }, [favorites]);

  const handleDelete = async (reviewId) => {
    if (!window.confirm("Are you sure you want to delete this review?")) return;
    try {
      await deleteReviewApi(reviewId);
      setUserReviews((prev) => prev.filter((r) => r.review_id !== reviewId));
    } catch (err) {
      console.error("Failed to delete review:", err);
      alert("Could not delete review.");
    }
  };

  const handleStartEdit = (rev) => {
    setEditingId(rev.review_id);
    setEditScore(rev.score);
    setEditText(rev.text);
  };

  const handleSaveEdit = async (reviewId) => {
    try {
      await updateReviewApi(reviewId, Number(editScore), editText);
      setUserReviews((prev) =>
        prev.map((r) => (r.review_id === reviewId ? { ...r, score: Number(editScore), text: editText } : r))
      );
      setEditingId(null);
    } catch (err) {
      console.error("Failed to update review:", err);
      alert("Could not update review.");
    }
  };

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
                style={{ background: "white", padding: "16px", borderRadius: "8px", border: "1px solid var(--color-border)" }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", alignItems: "center" }}>
                  <strong style={{ cursor: "pointer" }} onClick={() => onSelectBook({ ISBN: rev.isbn, Title: rev.book_title, CoverImage: rev.cover_image })}>
                    {rev.book_title}
                  </strong>
                  {editingId !== rev.review_id && <span>★ {rev.score}</span>}
                </div>

                {editingId === rev.review_id ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "10px" }}>
                    <select value={editScore} onChange={(e) => setEditScore(e.target.value)}>
                      <option value="5">5 stars</option>
                      <option value="4">4 stars</option>
                      <option value="3">3 stars</option>
                      <option value="2">2 stars</option>
                      <option value="1">1 star</option>
                    </select>
                    <textarea 
                      value={editText} 
                      onChange={(e) => setEditText(e.target.value)} 
                      rows={3} 
                      style={{ width: "100%", padding: "8px" }}
                    />
                    <div style={{ display: "flex", gap: "8px" }}>
                      <button onClick={() => handleSaveEdit(rev.review_id)}>Save</button>
                      <button onClick={() => setEditingId(null)} style={{ background: "#ccc" }}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <>
                    <p style={{ color: "var(--color-ink-soft)", margin: "0 0 12px 0" }}>{rev.text}</p>
                    <div style={{ display: "flex", gap: "12px", fontSize: "0.85rem" }}>
                      <button onClick={() => handleStartEdit(rev)} style={{ background: "none", border: "none", color: "var(--color-primary)", cursor: "pointer", padding: 0 }}>
                        Edit
                      </button>
                      <button onClick={() => handleDelete(rev.review_id)} style={{ background: "none", border: "none", color: "#d9534f", cursor: "pointer", padding: 0 }}>
                        Delete
                      </button>
                    </div>
                  </>
                )}
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