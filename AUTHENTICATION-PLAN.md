# Authentication Implementation Plan

## Goal

Allow bookstore users to create an account with a username and password or
with Google, then sign in using either method. Authentication should be
validated by Flask and persist through a secure server-managed session.

This document is a plan only; it does not implement authentication.

## Proposed account behavior

- Require a unique username and email for every account.
- For username-and-password signup, require a username, email, and password.
- For Google signup, verify the Google identity on the backend, then ask the
  user to choose a unique username.
- A Google-created account may initially have no password. Let the user add a
  password later if they want username-and-password sign-in as well.
- Do not automatically link accounts only because their email addresses
  match. Require the user to prove control of both sign-in methods before
  linking them.
- Treat the existing `user_name` as a display name unless review of the
  existing data establishes otherwise; add a separate username field.

These are recommended defaults and should be confirmed before implementation.

## Phases

### 1. Confirm requirements and account model

- Confirm whether email is required for password signup and Google signup.
- Confirm whether Google users choose a username during signup.
- Confirm that account linking requires authentication to both methods.
- Decide whether favorites and reviews should be associated with an account
  and synchronized across devices. They are currently stored in browser
  `localStorage`, so authentication alone will not make them persistent per
  user.

### 2. Design and migrate the database

- Extend the existing `User` schema with a distinct username, a nullable
  password-hash field, and a Google subject identifier.
- Enforce uniqueness for usernames, emails, and non-null Google identifiers.
- Store password hashes only; never store raw passwords.
- Preserve the current review foreign-key relationship to users.
- Provide a migration for existing databases and sample users. Updating
  `init.sql` alone is not enough for a database that has already been
  initialized, because the development database uses a persistent volume.
- Verify the migration against both an empty database and a database
  containing existing rows.

### 3. Implement Flask authentication

- Add endpoints for account registration, username/password sign-in, Google
  sign-in, current-user lookup, and sign-out.
- Validate all input on the backend and use parameterized SQL.
- Hash and verify passwords with a suitable password-hashing library.
- Verify Google credentials server-side and identify Google accounts by their
  stable subject identifier, not by email alone.
- Establish and clear a secure server-managed session. Configure cookie,
  CORS, and CSRF protections appropriately for the app's local and deployed
  origins.
- Return clear, generic authentication errors without exposing whether a
  username or email is registered.

### 4. Implement the React account experience

- Replace the current mock login form with sign-in and signup modes.
- Provide username, email, and password inputs as appropriate, plus a Google
  sign-in option.
- Show validation errors, backend errors, and loading/success states.
- On app startup, ask Flask for the current session instead of treating
  `localStorage` user data as proof of authentication.
- Update logout and account display to use the backend session.
- Preserve the existing logged-out experience and book browsing.

### 5. Test, configure, and document

- Add backend tests for registration, duplicate accounts, password handling,
  valid and invalid sign-in, Google verification outcomes, current-user
  lookup, sign-out, and session behavior.
- Add frontend checks or tests for form modes, validation, error states, and
  session restoration.
- Verify the database migration with existing sample data.
- Document Google Identity configuration, allowed origins, redirect settings
  if used, and required environment variables. Keep any Google client secret
  on the backend; do not put secrets in React or commit them.
- Run the relevant backend tests, frontend lint/build, and the project's
  existing checks.

## Initial scope

The recommended first release includes username/password accounts, Google
sign-in, secure sessions, and a database migration. Password reset, email
verification, and account-linked favorites/reviews can be separate follow-up
work unless they are required for launch.

## Completion criteria

- A new user can register with a unique username and sign in with that
  username and password.
- A user can sign in with Google only after the backend verifies the Google
  identity.
- Google signup collects a unique username.
- A signed-in session is restored after a page reload and is cleared by
  sign-out.
- Client-side storage alone cannot create an authenticated session.
- Existing user and review data survive the database migration.
- Authentication secrets and raw passwords are not stored in the repository,
  browser storage, or database.
