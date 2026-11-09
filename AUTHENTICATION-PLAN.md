# Authentication Implementation Plan

## Goal

Allow new users to create an account by continuing with Google, then choosing
a username and an app-specific password. On later visits, they can sign in
with Google or with their username and bookstore password. Authentication
should be validated by Flask and persist through a secure server-managed
session.

This document tracks the authentication plan, completed work, and remaining
steps.

## Current progress

- The Google Cloud project `SmartBase-Online-Bookstore` has been created and
  selected.
- Google Auth Platform branding/consent setup is complete. The app is External
  and remains in Testing mode; a test user has been added.
- A Web application OAuth client named `SmartBase local web` was created with
  `http://localhost:5174` as an authorized JavaScript origin. No redirect URI
  was added because the planned browser flow uses a Google ID token.
- The client ID was created, but its value is intentionally not recorded here.
  Do not put a client secret in this repository. The planned ID-token
  verification flow uses the client ID as the token audience and does not
  require a client secret.
- The original database migration and the `AuthSessions` table migration have
  been run and verified on `smartbase_db`.
- Flask username/password login, current-session lookup, and logout endpoints
  are implemented and covered by backend tests. The React app is not yet
  connected to them.
- Google token verification and account creation are not implemented yet.
- `google-auth` has now been installed into the backend virtual environment.
  The first attempt using `backend/venv/bin/python -m pip` failed because this
  project creates its virtual environment with `--without-pip`. The successful
  command used the system Python's pip launcher:

  ```bash
  python3 -m pip --python backend/venv/bin/python install google-auth
  ```

- `scripts/dev-tasks.sh` now checks for `google.auth` and includes `google-auth`
  in the dependency installation command, so `devup` will restore it if the
  backend virtual environment is recreated.

## Proposed account behavior

- A new user selects **Continue with Google** and chooses a Google account
  using Google's account picker.
- The backend verifies the Google credential and its verified email before
  creating an account. Use the verified email provided by Google; do not ask
  the user to type it into the app.
- After successful Google verification, route a new user to account setup to
  choose a unique username and an app-specific password. This is not their
  Google password.
- Require both a username and app password during this setup so the new
  account can use either Google sign-in or username-and-password sign-in.
- Returning Google users sign in with Google and go directly to the app; they
  should not repeat account setup.
- No separate confirmation email is needed for Google signup because the
  verified Google identity establishes control of that account. The app does
  not need an email-sending service for this flow.
- Do not automatically link accounts only because their email addresses
  match. Require the user to prove control of both sign-in methods before
  linking them.
- Use `display_name` for the optional name from the Google profile and a
  separate `username` for sign-in.

Direct username-and-password registration without Google is outside the
initial flow. If it is added later, decide separately whether those accounts
need email verification.

## Phases

### 1. Confirm account model

- Usernames are 3–20 characters, using letters, numbers, and underscores.
- App passwords are 12–128 characters, with no additional composition rules.
- New account creation starts with Google; after setup, both Google and
  username/password sign-in are available.
- Accounts are not automatically linked based only on matching emails;
  linking requires proving control of both sign-in methods.
- Favorites and reviews are in scope for the first release and should be
  associated with the signed-in account and synchronized across devices.
  They are currently stored in browser `localStorage`.

### 2. Design and migrate the database

- The fresh-install schema in `init.sql` includes the account fields, review
  text, and account-scoped favorites table. A separate migration is still
  required to apply these changes to an already-initialized database.
- The one-time migration in
  `migrations/001_auth_favorites_reviews.sql` removes the original sample users
  and their reviews, then applies the new account, review, and favorites
  schema. It stops if it finds users outside the original sample accounts.
- Back up the database before running the migration. It is not safe to run on
  a database containing real user data.
- Enforce uniqueness for usernames, emails, and Google subject identifiers;
  store password hashes only, never raw passwords.
- Create `Favorites` with a composite `(user_id, isbn)` primary key and
  foreign keys to users and books.
- Browser-local favorites and reviews are not imported by this migration;
  decide how the frontend should handle that data when account sync is added.
- Verify the migration against both an empty database and a database
  containing existing rows.

### 3. Implement Flask authentication

- Implemented `POST /api/auth/login` for existing accounts. It verifies the
  password hash and stores only a hash of a random seven-day session token in
  `AuthSessions`; the browser receives the token in an HttpOnly, SameSite=Lax
  cookie. For existing databases that have already run migration 001, run
  `migrations/002_auth_sessions.sql` before using this endpoint. Set
  `AUTH_SESSION_COOKIE_SECURE=true` when serving over HTTPS.
- Implemented `GET /api/auth/me` to return the account associated with a valid,
  unexpired session cookie, and `POST /api/auth/logout` to revoke the session
  and clear the cookie. The React app is not yet connected to these endpoints.
- Next: implement and test the Google ID-token verification endpoint using the
  installed `google-auth` dependency.
- Add an endpoint that accepts a Google ID token and verifies it on the
  backend, including its signature, audience (the OAuth client ID), issuer,
  expiry, and verified-email claim.
- For an existing Google subject, create the normal server session and return
  the account. For a new verified Google identity, do not create an account
  yet; return a short-lived, signed account-setup token so the user can choose
  a unique username and app password.
- Add the account-setup endpoint. It must validate that token, validate the
  username and 12–128-character app password, hash the password, and create
  the account with Google's verified email, stable subject, and optional
  display name. Then create the server session.
- Validate all input on the backend and use parameterized SQL.
- Add authenticated endpoints for reading and updating the user's favorites
  and reviews so data is scoped to the signed-in account.
- Hash and verify passwords with a suitable password-hashing library.
- Verify Google credentials server-side, require Google's verified-email
  claim, and identify Google accounts by their stable subject identifier, not
  by email alone. Only create a new account after the user completes username
  and password setup.
- Establish and clear a secure server-managed session. Configure cookie,
  CORS, and CSRF protections appropriately for the app's local and deployed
  origins.
- Return clear, generic authentication errors without exposing whether a
  username or email is registered.

### 4. Implement the React account experience

- Replace the current mock login form with sign-in and signup modes.
- Provide username/password sign-in and a Google sign-in option. For a new
  Google identity, show an account-setup page for a username and
  app-specific password; do not ask the user to re-enter the Google email.
- Show validation errors, backend errors, and loading/success states.
- On app startup, ask Flask for the current session instead of treating
  `localStorage` user data as proof of authentication.
- Update logout and account display to use the backend session.
- Load and save favorites and reviews through the authenticated API so they
  follow the user across devices.
- Preserve the existing logged-out experience and book browsing.

### 5. Test, configure, and document

- Backend tests already cover username/password login, current-session lookup,
  logout, and relevant failure cases. Add tests for Google token verification,
  unverified email, wrong audience/issuer/expiry, new-account setup, duplicate
  usernames, and Google sign-in for existing accounts.
- Add frontend checks or tests for form modes, validation, error states, and
  session restoration.
- Verify the database migration with existing sample data.
- The local Google JavaScript origin is configured as
  `http://localhost:5174`; add the production frontend origin to the Google
  OAuth client before deployment. No redirect URI is currently used.
- Document required environment variables and keep credentials out of Git.
  The planned ID-token flow does not use a client secret.
- Run the relevant backend tests, frontend lint/build, and the project's
  existing checks.

## Initial scope

The first release includes Google verification, required username/password
setup for new Google accounts, both sign-in methods, secure sessions, a
database migration, and account-synced favorites and reviews. It does not send
confirmation emails. Direct password-only registration, password reset, and
email verification for non-Google signup can be separate follow-up work.

## Completion criteria

- A new user can complete signup only after the backend verifies their Google
  identity and verified email.
- Google signup collects a unique username and an app-specific password after
  Google verification.
- The user can later sign in with either Google or their username and
  app-specific password.
- Google signup does not require the app to send a separate confirmation
  email.
- Favorites and reviews are stored against the signed-in account and remain
  available across devices.
- A signed-in session is restored after a page reload and is cleared by
  sign-out.
- Client-side storage alone cannot create an authenticated session.
- Existing user and review data survive the database migration.
- Authentication secrets and raw passwords are not stored in the repository,
  browser storage, or database.
