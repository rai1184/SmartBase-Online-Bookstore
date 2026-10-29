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

  /*
    Search and alternative matching still run in the
    frontend, using the records loaded from the API.
  */
  const handleSearch = (query) => {
    setHasSearched(true);
    setPage("search");

    const title =
      query.title
        .trim()
        .toLowerCase();

    const author =
      query.author
        .trim()
        .toLowerCase();

    const exact =
      books.filter((book) => {
        const titleMatch =
          !title ||
          book.Title
            .toLowerCase()
            .includes(title);

        const authorMatch =
          !author ||
          book.Author
            .toLowerCase()
            .includes(author);

        const genreMatch =
          query.genre === "All" ||
          book.Genre === query.genre;

        const priceMatch =
          !query.maxPrice ||
          book.MSRP <=
            Number(query.maxPrice);

        const ratingMatch =
          !query.minRating ||
          (book.Rating != null &&
            book.Rating >= Number(query.minRating));

        const yearMatch =
          !query.publicationYear ||
          book.PublicationYear ===
            Number(
              query.publicationYear
            );

        return (
          titleMatch &&
          authorMatch &&
          genreMatch &&
          priceMatch &&
          ratingMatch &&
          yearMatch
        );
      });

    setExactMatches(exact);

    const exactISBNs = new Set(
      exact.map((book) => book.ISBN)
    );

    const alternatives =
      books
        .filter(
          (book) =>
            !exactISBNs.has(book.ISBN)
        )

        .map((book) => {
          let score = 1;

          if (
            title &&
            !book.Title
              .toLowerCase()
              .includes(title)
          ) {
            if (!query.relaxTitle) {
              return null;
            }

            score -= 0.2;
          }

          if (
            author &&
            !book.Author
              .toLowerCase()
              .includes(author)
          ) {
            if (!query.relaxAuthor) {
              return null;
            }

            score -= 0.15;
          }

          if (
            query.genre !== "All" &&
            book.Genre !== query.genre
          ) {
            if (!query.relaxGenre) {
              return null;
            }

            score -= 0.12;
          }

          if (
            query.maxPrice &&
            book.MSRP >
              Number(query.maxPrice)
          ) {
            if (!query.relaxPrice) {
              return null;
            }

            const difference =
              book.MSRP -
              Number(query.maxPrice);

            score -= Math.min(
              difference / 100,
              0.2
            );
          }

          if (
            query.minRating &&
            (book.Rating == null ||
              book.Rating < Number(query.minRating))
          ) {
            if (!query.relaxRating) {
              return null;
            }

            score -= 0.1;
          }

          if (
            query.publicationYear &&
            book.PublicationYear !==
              Number(
                query.publicationYear
              )
          ) {
            if (!query.relaxYear) {
              return null;
            }

            score -= 0.08;
          }

          return {
            ...book,

            similarityScore:
              Math.max(
                0.25,
                Math.min(0.99, score)
              ),
          };
        })

        .filter(Boolean)

        .sort(
          (a, b) =>
            b.similarityScore -
            a.similarityScore
        )

        .slice(0, 4);

    setAlternativeMatches(
      alternatives
    );
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
          <section className="hero">
            <div className="hero-content">
              <p className="hero-label">
                CONTEXT-AWARE BOOK SEARCH
              </p>

              <h1>
                Find the right book,
                even without an exact
                match.
              </h1>

              <p>
                SmartBase combines
                traditional database
                searching with contextual
                alternatives to help users
                discover relevant books.
              </p>

              <button
                onClick={() =>
                  setPage("search")
                }
              >
                Start Searching
              </button>
            </div>
          </section>

          <section className="home-info">
            <p className="section-label centered-label">
              WHY SMARTBASE?
            </p>

            <h2>
              What makes SmartBase different?
            </h2>

            <div className="info-grid">
              <article>
                <div className="feature-symbol">
                  ⌕
                </div>

                <h3>
                  Flexible Search
                </h3>

                <p>
                  Search by title,
                  author, genre, price,
                  rating, and publication
                  year.
                </p>
              </article>

              <article>
                <div className="feature-symbol">
                  ↔
                </div>

                <h3>
                  Query Relaxation
                </h3>

                <p>
                  Choose which search
                  requirements may be
                  relaxed when exact
                  results are unavailable.
                </p>
              </article>

              <article>
                <div className="feature-symbol">
                  %
                </div>

                <h3>
                  Smart Suggestions
                </h3>

                <p>
                  View alternative books
                  ranked according to
                  contextual similarity.
                </p>
              </article>

              <article>
                <div className="feature-symbol">
                  ♡
                </div>

                <h3>
                  Favorites & Reviews
                </h3>

                <p>
                  Save books you like and
                  share ratings and
                  reviews.
                </p>
              </article>
            </div>
          </section>

          <FeaturedBooks
            books={featuredBooks}
            loading={booksLoading}
            error={booksError}
            onRetry={loadBooks}
            favorites={favorites}
            toggleFavorite={
              toggleFavorite
            }
            reviews={reviews}
            addReview={addReview}
            user={user}
            goToSearch={() =>
              setPage("search")
            }
          />

          <section className="how-section">
            <p className="section-label centered-label">
              HOW IT WORKS
            </p>

            <h2>
              From search to smart alternatives
            </h2>

            <div className="steps">
              <article>
                <div className="step-number">
                  1
                </div>

                <h3>
                  Enter Your Search
                </h3>

                <p>
                  Search using book title,
                  author, genre, price,
                  rating, or publication
                  year.
                </p>
              </article>

              <div className="step-arrow">
                →
              </div>

              <article>
                <div className="step-number">
                  2
                </div>

                <h3>
                  Choose Relaxations
                </h3>

                <p>
                  Decide which search
                  constraints may be
                  relaxed.
                </p>
              </article>

              <div className="step-arrow">
                →
              </div>

              <article>
                <div className="step-number">
                  3
                </div>

                <h3>
                  Explore Results
                </h3>

                <p>
                  View exact matches and
                  ranked contextual
                  alternatives.
                </p>
              </article>
            </div>
          </section>
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
            📚 SmartBase
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