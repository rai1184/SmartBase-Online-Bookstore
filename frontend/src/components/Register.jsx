import { useState, useRef } from "react";

export default function Register({
  user,
  register,
  logout,
  authLoading,
}) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const submittingRef = useRef(false);

  if (user) {
    return (
      <main className="login-page">
        <div className="login-card">
          <p className="section-label">ACCOUNT</p>
          <h1>Welcome, {user.username}</h1>
          <button onClick={logout} disabled={submitting}>Logout</button>
        </div>
      </main>
    );
  }

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    submittingRef.current = true;
    setSubmitting(true);

    try {
      await register(username.trim(), email.trim(), password);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  };

  return (
    <main className="login-page">
      <form className="login-card" onSubmit={submit}>
        <h1>Create Account</h1>
        <p>Register a new local account to get started.</p>

        {error && <p className="auth-error" role="alert">{error}</p>}

        <label>
          Username
          <input
            type="text"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="3–20 letters, numbers, or underscores"
            minLength={3}
            maxLength={20}
            pattern="[A-Za-z0-9_]{3,20}"
            autoComplete="username"
            required
          />
        </label>

        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="Your email address"
            maxLength={255}
            autoComplete="email"
            required
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="At least 12 characters"
            minLength={12}
            maxLength={128}
            autoComplete="new-password"
            required
          />
        </label>

        <button type="submit" disabled={submitting || authLoading}>
          {submitting ? "Creating account..." : "Register"}
        </button>
      </form>
    </main>
  );
}