export default function Navbar({
  page,
  setPage,
  user,
  logout,
  favoriteCount,
  backendStatus,
}) {
  return (
    <header className="navbar">
      <button
        className="logo"
        onClick={() => setPage("home")}
      >
        📚 SmartBase
      </button>

      <nav>
        <button
          className={page === "home" ? "active" : ""}
          onClick={() => setPage("home")}
        >
          Home
        </button>

        <button
          className={page === "search" ? "active" : ""}
          onClick={() => setPage("search")}
        >
          Search
        </button>

        <button
          className={page === "favorites" ? "active" : ""}
          onClick={() => setPage("favorites")}
        >
          Favorites ({favoriteCount})
        </button>

        {user ? (
          <>
            <span className="username">
              Hi, {user.name}
            </span>

            <button onClick={logout}>Logout</button>
          </>
        ) : (
          <button
            className={page === "login" ? "active" : ""}
            onClick={() => setPage("login")}
          >
            Login
          </button>
        )}
      </nav>

      <div className="backend-small">
        Backend: {backendStatus}
      </div>
    </header>
  );
}