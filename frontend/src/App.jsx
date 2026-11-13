import { useCallback, useEffect, useMemo, useState } from "react";
import "./App.css";

import Navbar from "./components/Navbar";
import SearchBox from "./components/SearchBox";
import BookSuggestions from "./components/BookSuggestions";
import BookCard from "./components/BookCard";
import FeaturedBooks from "./components/FeaturedBooks";
import Login from "./components/Login";

import {
  accountSetupApi,
  checkHealthApi,
  fetchBooksFromApi,
  getCurrentUserApi,
  googleLoginApi,
  loginApi,
  logoutApi,
  searchBooksApi,
} from "./services/api";

function App() {
  const [page, setPage] = useState("home");

  const [books, setBooks] = useState([]);
  const [booksLoading, setBooksLoading] = useState(true);
  const [booksError, setBooksError] = useState("");

  const [backendStatus, setBackendStatus] = useState("Checking...");
  const [hasSearched, setHasSearched] = useState(false);
  const [exactMatches, setExactMatches] = useState([]);
  const [alternativeMatches, setAlternativeMatches] = useState([]);

  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [sessionError, setSessionError] = useState("");

  const [favorites, setFavorites] = useState(() => {
    const stored = localStorage.getItem("smartbase-favorites");
    return stored ? JSON.parse(stored) : [];
  });

  const [reviews, setReviews] = useState(() => {
    const stored = localStorage.getItem("smartbase-reviews");
    return stored ? JSON.parse(stored) : {};
  });

  const loadBooks = useCallback(() => {
    setBooksLoading(true);
    setBooksError("");

    fetchBooksFromApi()
      .then(setBooks)
      .catch((error) => setBooksError(error.message))
      .finally(() => setBooksLoading(false));
  }, []);

  const restoreSession = useCallback(async () => {
    setAuthLoading(true);
    setSessionError("");
    try {
      setUser(await getCurrentUserApi());
      setSessionError("");
    } catch (error) {
      setUser(null);
      setSessionError(error.message);
    } finally {
      setAuthLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    getCurrentUserApi()
      .then((account) => {
        if (active) {
          setUser(account);
          setSessionError("");
        }
      })
      .catch((error) => {
        if (active) {
          setUser(null);
          setSessionError(error.message);
        }
      })
      .finally(() => {
        if (active) setAuthLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    fetchBooksFromApi()
      .then((loadedBooks) => {
        if (active) setBooks(loadedBooks);
      })
      .catch((error) => {
        if (active) setBooksError(error.message);
      })
      .finally(() => {
        if (active) setBooksLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    checkHealthApi()
      .then(setBackendStatus)
      .catch(() => setBackendStatus("Offline"));
  }, []);

  const genres = useMemo(() => {
    return [...new Set(books.map((book) => book.Genre))];
  }, [books]);

  const featuredBooks = books.slice(0, 4);

  // Given query, which is a form, populate exact and alternative matches
  const handleSearch = async (query) => {
    setHasSearched(true);
    setPage("search");

    try {
      // Pack all fields and relaxation flags into a URLSearchParams, to be sent to backend
      const params = new URLSearchParams({
        title: query.title || "",
        author: query.author || "",
        genre: query.genre || "All",
        max_price: query.maxPrice || "",
        min_rating: query.minRating || "",
        publication_year: query.publicationYear || "",
        relax_title: query.relaxTitle,
        relax_author: query.relaxAuthor,
        relax_genre: query.relaxGenre,
        relax_price: query.relaxPrice,
        relax_rating: query.relaxRating,
        relax_year: query.relaxYear,
      });

      const results = await searchBooksApi(params);
      setExactMatches(results.exact_matches); // set state
      setAlternativeMatches(results.alternative_matches);
    } catch (error) {
      console.error("Search error:", error);
      setExactMatches([]);
      setAlternativeMatches([]);
    }
  };

  const toggleFavorite = (isbn) => {
    setFavorites((current) => {
      const updated = current.includes(isbn)
        ? current.filter((item) => item !== isbn)
        : [...current, isbn];

      localStorage.setItem("smartbase-favorites", JSON.stringify(updated));
      return updated;
    });
  };

  const addReview = (isbn, score, text) => {
    if (!user) {
      setPage("login");
      return;
    }

    setReviews((current) => {
      const newReview = { name: user.username, score, text };
      const updated = {
        ...current,
        [isbn]: [...(current[isbn] || []), newReview],
      };

      localStorage.setItem("smartbase-reviews", JSON.stringify(updated));
      return updated;
    });
  };

  const login = useCallback(async (username, password) => {
    const account = await loginApi(username, password);
    setUser(account);
    setSessionError("");
    setPage("home");
  }, []);

  const googleLogin = useCallback(async (idToken) => {
    const result = await googleLoginApi(idToken);
    if (result.user) {
      setUser(result.user);
      setSessionError("");
      setPage("home");
    } else if (
      result.account_setup_required !== true ||
      typeof result.account_setup_token !== "string"
    ) {
      throw new Error("The Google sign-in response was incomplete.");
    }
    return result;
  }, []);

  const completeAccountSetup = useCallback(async (setupToken, username, password) => {
    const account = await accountSetupApi(setupToken, username, password);
    setUser(account);
    setSessionError("");
    setPage("home");
  }, []);

  const logout = useCallback(async () => {
    try {
      await logoutApi();
      setUser(null);
      setSessionError("");
      setPage("home");
    } catch (error) {
      setSessionError(error.message);
    }
  }, []);

  const favoriteBooks = books.filter((book) => favorites.includes(book.ISBN));

  return (
    <div className="app-container">
      <Navbar
        page={page}
        setPage={setPage}
        user={user}
        logout={logout}
        authLoading={authLoading}
        favoriteCount={favorites.length}
        backendStatus={backendStatus}
      />
      {user && sessionError && (
        <p className="auth-global-error" role="alert">{sessionError}</p>
      )}

      {page === "home" && (
        <main>
          <FeaturedBooks
            books={featuredBooks}
            loading={booksLoading}
            error={booksError}
            onRetry={loadBooks}
            favorites={favorites}
            toggleFavorite={toggleFavorite}
            reviews={reviews}
            addReview={addReview}
            user={user}
            goToSearch={() => setPage("search")}
          />
        </main>
      )}

      {page === "search" && (
        <main className="page">
          <div className="page-heading">
            <p className="section-label">SMART SEARCH</p>
            <h1>Search Books</h1>
            <p>Enter the criteria you want SmartBase to use.</p>
          </div>

          {booksLoading ? (
            <p className="empty-message" role="status">Loading books...</p>
          ) : booksError ? (
            <div className="empty-message" role="alert">
              <p>{booksError}</p>
              <button className="standard-button" onClick={loadBooks}>Try again</button>
            </div>
          ) : (
            <>
              <SearchBox onSearch={handleSearch} genres={genres} />
              <BookSuggestions
                hasSearched={hasSearched}
                exactMatches={exactMatches}
                alternativeMatches={alternativeMatches}
                favorites={favorites}
                toggleFavorite={toggleFavorite}
                reviews={reviews}
                addReview={addReview}
                user={user}
              />
            </>
          )}
        </main>
      )}

      {page === "favorites" && (
        <main className="page">
          <div className="page-heading">
            <p className="section-label">YOUR LIBRARY</p>
            <h1>Favorite Books</h1>
            <p>Books you save will appear here.</p>
          </div>

          {booksLoading ? (
            <p className="empty-message" role="status">Loading books...</p>
          ) : booksError ? (
            <div className="empty-message" role="alert">
              <p>{booksError}</p>
              <button className="standard-button" onClick={loadBooks}>Try again</button>
            </div>
          ) : favoriteBooks.length === 0 ? (
            <div className="empty-message">
              <h3>No favorites yet.</h3>
              <p>Search or browse books and click the heart to save them.</p>
              <button className="standard-button" onClick={() => setPage("search")}>
                Browse Books
              </button>
            </div>
          ) : (
            <div className="book-grid">
              {favoriteBooks.map((book) => (
                <BookCard
                  key={book.ISBN}
                  book={book}
                  type="featured"
                  favorite={true}
                  toggleFavorite={toggleFavorite}
                  reviews={reviews[book.ISBN] || []}
                  addReview={addReview}
                  user={user}
                />
              ))}
            </div>
          )}
        </main>
      )}

      {page === "login" && (
        <Login
          user={user}
          login={login}
          googleLogin={googleLogin}
          completeAccountSetup={completeAccountSetup}
          logout={logout}
          sessionError={sessionError}
          retrySession={restoreSession}
          authLoading={authLoading}
        />
      )}

      <footer>
        <div>
          <strong>SmartBase</strong>
          <p>Context-aware online bookstore search.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;