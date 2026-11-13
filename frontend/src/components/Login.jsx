import { useEffect, useRef, useState } from "react";

const GOOGLE_SCRIPT_ID = "google-identity-services";

export default function Login({
  user,
  login,
  googleLogin,
  completeAccountSetup,
  logout,
  sessionError,
  retrySession,
  authLoading,
}) {
  const [mode, setMode] = useState("login");
  const [setupToken, setSetupToken] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [googleError, setGoogleError] = useState("");
  const googleButton = useRef(null);
  const submittingRef = useRef(false);

  useEffect(() => {
    if (mode !== "login" || authLoading) {
      return undefined;
    }

    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!clientId) {
      return undefined;
    }

    const handleGoogleReady = () => {
      if (!window.google?.accounts?.id || !googleButton.current) {
        setGoogleError("Google sign-in could not be loaded. Please try again.");
        return;
      }

      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async ({ credential }) => {
          if (!credential || submittingRef.current) {
            return;
          }

          submittingRef.current = true;
          setSubmitting(true);
          setError("");
          try {
            const result = await googleLogin(credential);
            if (result.account_setup_required) {
              setSetupToken(result.account_setup_token);
              setMode("setup");
            }
          } catch (requestError) {
            setError(requestError.message);
          } finally {
            submittingRef.current = false;
            setSubmitting(false);
          }
        },
      });
      window.google.accounts.id.renderButton(googleButton.current, {
        theme: "outline",
        size: "large",
        text: "continue_with",
        shape: "rectangular",
        width: 350,
      });
    };

    if (window.google?.accounts?.id) {
      handleGoogleReady();
      return undefined;
    }

    let script = document.getElementById(GOOGLE_SCRIPT_ID);
    const onLoad = () => handleGoogleReady();
    const onError = () => setGoogleError("Google sign-in could not be loaded.");
    if (!script) {
      script = document.createElement("script");
      script.id = GOOGLE_SCRIPT_ID;
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.addEventListener("load", onLoad);
      script.addEventListener("error", onError);
      document.head.appendChild(script);
    } else {
      script.addEventListener("load", onLoad);
      script.addEventListener("error", onError);
    }

    return () => {
      script.removeEventListener("load", onLoad);
      script.removeEventListener("error", onError);
    };
  }, [authLoading, googleLogin, mode]);

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
      if (mode === "setup") {
        await completeAccountSetup(setupToken, username.trim(), password);
      } else {
        await login(username.trim(), password);
      }
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
        <p className="section-label">SMARTBASE ACCOUNT</p>
        <h1>{mode === "setup" ? "Set up your account" : "Login"}</h1>
        <p>
          {mode === "setup"
            ? "Choose a username and an app-specific password."
            : "Sign in to manage favorites and reviews."}
        </p>

        {sessionError && (
          <div className="auth-error" role="alert">
            <p>{sessionError}</p>
            <button type="button" className="auth-retry" onClick={retrySession}>
              Retry session check
            </button>
          </div>
        )}
        {error && <p className="auth-error" role="alert">{error}</p>}

        {mode === "login" ? (
          <>
            <label>
              Username
              <input
                type="text"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="Your username"
                minLength={3}
                maxLength={20}
                pattern="[A-Za-z0-9_]{3,20}"
                autoComplete="username"
                required
              />
            </label>

            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                required
              />
            </label>

            <button type="submit" disabled={submitting || authLoading}>
              {submitting ? "Signing in..." : "Login"}
            </button>

            <div className="auth-divider">or</div>
            <div ref={googleButton} className="google-signin-button" />
            {(googleError || !import.meta.env.VITE_GOOGLE_CLIENT_ID) && (
              <p className="auth-error" role="alert">
                {googleError || "Google sign-in is not configured."}
              </p>
            )}
            {submitting && <p className="auth-status" role="status">Signing in...</p>}
          </>
        ) : (
          <>
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
              App password
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                minLength={12}
                maxLength={128}
                autoComplete="new-password"
                required
              />
            </label>

            <button type="submit" disabled={submitting}>
              {submitting ? "Creating account..." : "Create account"}
            </button>
            <button
              type="button"
              className="auth-secondary"
              onClick={() => {
                setMode("login");
                setSetupToken("");
                setPassword("");
                setError("");
              }}
              disabled={submitting}
            >
              Back to login
            </button>
          </>
        )}
      </form>
    </main>
  );
}