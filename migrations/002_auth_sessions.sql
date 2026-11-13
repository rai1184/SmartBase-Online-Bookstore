-- Add server-side session storage for username/password authentication.
-- Run against an existing database from the repository root:
-- mysql --host="$MYSQL_HOST" --user="$MYSQL_USER" --password "$MYSQL_DATABASE" \
--   < migrations/002_auth_sessions.sql

CREATE TABLE IF NOT EXISTS AuthSessions (
    session_token_hash CHAR(64) NOT NULL PRIMARY KEY,
    user_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    INDEX idx_auth_sessions_user_expires (user_id, expires_at),
    INDEX idx_auth_sessions_expires (expires_at),
    FOREIGN KEY (user_id) REFERENCES `User`(user_id) ON DELETE CASCADE
);
