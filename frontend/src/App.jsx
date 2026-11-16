import { useCallback, useEffect, useMemo, useState } from "react";
import "./App.css";

import Navbar from "./components/Navbar";
import SearchBox from "./components/SearchBox";
import BookSuggestions from "./components/BookSuggestions";
import FeaturedBooks from "./components/FeaturedBooks";
import Login from "./components/Login";
import BookDetailModal from "./components/BookDetailModal";
import AccountPage from "./components/AccountPage";
import AdminDashboard from "./components/AdminDashboard";

import {
  accountSetupApi,
  checkHealthApi,
  fetchBooksFromApi,
  getCurrentUserApi,
  googleLoginApi,
  loginApi,
  logoutApi,
  searchBooksApi,
  submitReviewApi
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

  const [selectedBook, setSelectedBook] = useState(null);

  const loadBooks = useCallback(() => {
    setBooksLoading(true);
    setBooksError("");

    fetchBooksFromApi()
      .then(setBooks)
      .catch((error) => setBooksError(error.message))
      .finally(() => setBooksLoading(false));
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

  const handleSearch = async (query) => {
    setHasSearched(true);
    setPage("search");

    try {
      const params = new URLSearchParams({
        title: query.title || "",
        author: query.author || "",
        genre: query.genre || "All",
        max_price: query.maxPrice || "",
        min_rating: query.minRating || "",
        publication_year: query.publicationYear || "",
        page_count: query.pageCount || "",
        in_stock: query.inStock || "",
        relax_title: query.relaxTitle,
        relax_author: query.relaxAuthor,
        relax_genre: query.relaxGenre,
        relax_price: query.relaxPrice,
        relax_rating: query.relaxRating,
        relax_year: query.relaxYear,
        relax_page_count: query.relaxPageCount,
        relax_in_stock: query.relaxInStock,
      });

      const results = await searchBooksApi(params);
      setExactMatches(results.exact_matches);
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

  const addReview = async (isbn, score, text) => {
    if (!user) {
      setPage("login");
      return;
    }

    try {
      await submitReviewApi(isbn, score, text);
      loadBooks();
    } catch (error) {
      console.error("Error submitting review:", error);
      alert(error.message);
    }
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
            reviews={[]}
            addReview={addReview}
            user={user}
            goToSearch={() => setPage("search")}
            onSelectBook={setSelectedBook}
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
                reviews={[]}
                addReview={addReview}
                user={user}
                onSelectBook={setSelectedBook}
              />
            </>
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
          authLoading={authLoading}
        />
      )}

      {page === "account" && user && (
        <AccountPage 
          user={user} 
          favorites={favorites} 
          toggleFavorite={toggleFavorite} 
          onSelectBook={setSelectedBook} 
        />
      )}

      {/* Admin Dashboard Page Routing */}
      {page === "admin" && (
        <AdminDashboard 
          user={user} 
          books={books} 
          refreshBooks={loadBooks} 
        />
      )}

      {/* Root-Level Full-Screen Two-Column Modal Overlay */}
      {selectedBook && (
        <BookDetailModal
          book={selectedBook}
          onClose={() => setSelectedBook(null)}
          addReview={addReview}
          user={user}
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