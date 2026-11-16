export default function Navbar({
  page,
  setPage,
  user,
  logout,
  authLoading,
}) {
  return (
    <header className="navbar">
      <button
        className="logo"
        onClick={() => setPage("home")}
      >
        SmartBase
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

        {user && (
          <button 
            className={page === "account" ? "active" : ""} 
            onClick={() => setPage("account")}
          >
            Account
          </button>
        )}

        {user ? (
          <>
            <span className="username">
              Hi, {user.username}
            </span>

            <button onClick={logout}>Logout</button>
          </>
        ) : authLoading ? (
          <span className="username" role="status">Checking session...</span>
        ) : (
          <button
            className={page === "login" ? "active" : ""}
            onClick={() => setPage("login")}
          >
            Login
          </button>
        )}
      </nav>

    </header>
  );
}