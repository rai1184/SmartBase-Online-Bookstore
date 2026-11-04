import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import "./App.css";

import Navbar from "./components/Navbar";
import SearchBox from "./components/SearchBox";
import BookSuggestions from "./components/BookSuggestions";
import BookCard from "./components/BookCard";
import FeaturedBooks from "./components/FeaturedBooks";

const API_BASE_URL = "http://localhost:5001/api";

async function fetchBooksFromApi() {
  const response = await fetch(`${API_BASE_URL}/books`);
  if (!response.ok) {
    throw new Error(`Could not load books (HTTP ${response.status}).`);
  }

  const data = await response.json();
  if (!Array.isArray(data)) {
    throw new Error("The books API returned an unexpected response.");
  }

  return data.map((book) => ({
    ISBN: book.isbn,
    Title: book.title,
    Author: book.author,
    Genre: book.genre || "Uncategorized",
    MSRP: Number(book.msrp),
    Rating: null,
    Pages: null,
    PublicationYear: book.publication_date
      ? Number(book.publication_date.slice(0, 4))
      : null,
    About: book.about,
  }));
}

function App() {
  const [page, setPage] = useState("home");

  const [books, setBooks] = useState([]);
  const [booksLoading, setBooksLoading] = useState(true);
  const [booksError, setBooksError] = useState("");

  const [backendStatus, setBackendStatus] =
    useState("Checking...");

  const [hasSearched, setHasSearched] =
    useState(false);

  const [exactMatches, setExactMatches] =
    useState([]);

  const [
    alternativeMatches,
    setAlternativeMatches,
  ] = useState([]);

  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem(
      "smartbase-user"
    );

    return stored
      ? JSON.parse(stored)
      : null;
  });

  const [favorites, setFavorites] =
    useState(() => {
      const stored = localStorage.getItem(
        "smartbase-favorites"
      );

      return stored
        ? JSON.parse(stored)
        : [];
    });

  const [reviews, setReviews] =
    useState(() => {
      const stored = localStorage.getItem(
        "smartbase-reviews"
      );

      return stored
        ? JSON.parse(stored)
        : {};
    });

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

    fetchBooksFromApi()
      .then((loadedBooks) => {
        if (active) {
          setBooks(loadedBooks);
        }
      })
      .catch((error) => {
        if (active) {
          setBooksError(error.message);
        }
      })
      .finally(() => {
        if (active) {
          setBooksLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    fetch(`${API_BASE_URL}/health`)
      .then((response) => {
        if (!response.ok) {
          throw new Error();
        }

        return response.json();
      })

      .then((data) => {
        setBackendStatus(
          data.message || "Online"
        );
      })

      .catch(() => {
        setBackendStatus("Offline");
      });
  }, []);

  const genres = useMemo(() => {
    return [
      ...new Set(
        books.map(
          (book) => book.Genre
        )
      ),
    ];
  }, [books]);

  const featuredBooks =
    books.slice(0, 4);

  // Update state with searched for books
  const handleSearch = async (query) => {
    setHasSearched(true);
    setPage("search");

    try {
      // Build the query parameters from what the user typed and selected
      const params = new URLSearchParams({
        title: query.title || "",
        author: query.author || "",
        genre: query.genre || "All",
      });

      // Fetch results from your Flask backend search endpoint
      const response = await fetch(`${API_BASE_URL}/books/search?${params.toString()}`);
      if (!response.ok) {
        throw new Error("Failed to fetch search results from the server.");
      }

      // Data returned from query
      const data = await response.json();

      // Put data in correct format
      const formatBook = (book) => ({
        ISBN: book.isbn,
        Title: book.title,
        Author: book.author,
        Genre: book.genre || "Uncategorized",
        MSRP: Number(book.msrp),
        Rating: null,
        Pages: null,
        PublicationYear: book.publication_date
          ? Number(book.publication_date.slice(0, 4))
          : null,
        About: book.about,
      });

      // Update state with the books
      setExactMatches(data.exact_matches.map(formatBook));
      setAlternativeMatches(data.alternative_matches.map(formatBook));

    } catch (error) {
      console.error("Search error:", error);
      setExactMatches([]);
      setAlternativeMatches([]);
    }
  };

  const toggleFavorite = (isbn) => {
    setFavorites((current) => {
      const updated =
        current.includes(isbn)
          ? current.filter(
              (item) => item !== isbn
            )
          : [...current, isbn];

      localStorage.setItem(
        "smartbase-favorites",
        JSON.stringify(updated)
      );

      return updated;
    });
  };

  const addReview = (
    isbn,
    score,
    text
  ) => {
    if (!user) {
      setPage("login");
      return;
    }

    setReviews((current) => {
      const newReview = {
        name: user.name,
        score,
        text,
      };

      const updated = {
        ...current,

        [isbn]: [
          ...(current[isbn] || []),
          newReview,
        ],
      };

      localStorage.setItem(
        "smartbase-reviews",
        JSON.stringify(updated)
      );

      return updated;
    });
  };

  const login = (name, email) => {
    const account = {
      name,
      email,
    };

    setUser(account);

    localStorage.setItem(
      "smartbase-user",
      JSON.stringify(account)
    );

    setPage("home");
  };

  const logout = () => {
    setUser(null);

    localStorage.removeItem(
      "smartbase-user"
    );

    setPage("home");
  };

  const favoriteBooks =
    books.filter((book) =>
      favorites.includes(book.ISBN)
    );

  return (
    <div className="app-container">
      <Navbar
        page={page}
        setPage={setPage}
        user={user}
        logout={logout}
        favoriteCount={
          favorites.length
        }
        backendStatus={
          backendStatus
        }
      />

      {/* HOME */}
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

      {/* SEARCH */}
      {page === "search" && (
        <main className="page">
          <div className="page-heading">
            <p className="section-label">
              SMART SEARCH
            </p>

            <h1>Search Books</h1>

            <p>
              Enter the criteria you want
              SmartBase to use and choose
              which conditions may be
              relaxed.
            </p>
          </div>

          {booksLoading ? (
            <p className="empty-message" role="status">
              Loading books...
            </p>
          ) : booksError ? (
            <div className="empty-message" role="alert">
              <p>{booksError}</p>
              <button className="standard-button" onClick={loadBooks}>
                Try again
              </button>
            </div>
          ) : (
            <>
              <SearchBox
                onSearch={handleSearch}
                genres={genres}
              />

              <BookSuggestions
                hasSearched={hasSearched}
                exactMatches={
                  exactMatches
                }
                alternativeMatches={
                  alternativeMatches
                }
                favorites={favorites}
                toggleFavorite={
                  toggleFavorite
                }
                reviews={reviews}
                addReview={addReview}
                user={user}
              />
            </>
          )}
        </main>
      )}

      {/* FAVORITES */}
      {page === "favorites" && (
        <main className="page">
          <div className="page-heading">
            <p className="section-label">
              YOUR LIBRARY
            </p>

            <h1>
              Favorite Books
            </h1>

            <p>
              Books you save will appear
              here.
            </p>
          </div>

          {booksLoading ? (
            <p className="empty-message" role="status">
              Loading books...
            </p>
          ) : booksError ? (
            <div className="empty-message" role="alert">
              <p>{booksError}</p>
              <button className="standard-button" onClick={loadBooks}>
                Try again
              </button>
            </div>
          ) : favoriteBooks.length ===
          0 ? (
            <div className="empty-message">
              <h3>
                No favorites yet.
              </h3>

              <p>
                Search or browse books and
                click the heart to save
                them.
              </p>

              <button
                className="standard-button"
                onClick={() =>
                  setPage("search")
                }
              >
                Browse Books
              </button>
            </div>
          ) : (
            <div className="book-grid">
              {favoriteBooks.map(
                (book) => (
                  <BookCard
                    key={book.ISBN}
                    book={book}
                    type="featured"
                    favorite={true}
                    toggleFavorite={
                      toggleFavorite
                    }
                    reviews={
                      reviews[
                        book.ISBN
                      ] || []
                    }
                    addReview={
                      addReview
                    }
                    user={user}
                  />
                )
              )}
            </div>
          )}
        </main>
      )}

      {/* LOGIN */}
      {page === "login" && (
        <Login
          user={user}
          login={login}
          logout={logout}
        />
      )}

      <footer>
        <div>
          <strong>
            SmartBase
          </strong>

          <p>
            Context-aware online bookstore
            search.
          </p>
        </div>

      </footer>
    </div>
  );
}

function Login({
  user,
  login,
  logout,
}) {
  const [name, setName] =
    useState("");

  const [email, setEmail] =
    useState("");

  if (user) {
    return (
      <main className="login-page">
        <div className="login-card">
          <p className="section-label">
            ACCOUNT
          </p>

          <h1>
            Welcome, {user.name}
          </h1>

          <p>{user.email}</p>

          <button onClick={logout}>
            Logout
          </button>
        </div>
      </main>
    );
  }

  const submit = (event) => {
    event.preventDefault();

    if (
      !name.trim() ||
      !email.trim()
    ) {
      return;
    }

    login(
      name.trim(),
      email.trim()
    );
  };

  return (
    <main className="login-page">
      <form
        className="login-card"
        onSubmit={submit}
      >
        <p className="section-label">
          SMARTBASE ACCOUNT
        </p>

        <h1>Login</h1>

        <p>
          Sign in to manage favorites
          and reviews.
        </p>

        <label>
          Name

          <input
            type="text"
            value={name}
            onChange={(event) =>
              setName(
                event.target.value
              )
            }
            placeholder="Your name"
          />
        </label>

        <label>
          Email

          <input
            type="email"
            value={email}
            onChange={(event) =>
              setEmail(
                event.target.value
              )
            }
            placeholder="you@example.com"
          />
        </label>

        <button type="submit">
          Login
        </button>
      </form>
    </main>
  );
}

export default App;