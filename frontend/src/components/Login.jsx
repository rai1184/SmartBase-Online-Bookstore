import { useState } from "react";

export default function Login({ user, login, logout }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");

  if (user) {
    return (
      <main className="login-page">
        <div className="login-card">
          <p className="section-label">ACCOUNT</p>
          <h1>Welcome, {user.name}</h1>
          <p>{user.email}</p>
          <button onClick={logout}>Logout</button>
        </div>
      </main>
    );
  }

  const submit = (event) => {
    event.preventDefault();
    if (!name.trim() || !email.trim()) {
      return;
    }
    login(name.trim(), email.trim());
  };

  return (
    <main className="login-page">
      <form className="login-card" onSubmit={submit}>
        <p className="section-label">SMARTBASE ACCOUNT</p>
        <h1>Login</h1>
        <p>Sign in to manage favorites and reviews.</p>

        <label>
          Name
          <input
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Your name"
          />
        </label>

        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
          />
        </label>

        <button type="submit">Login</button>
      </form>
    </main>
  );
}