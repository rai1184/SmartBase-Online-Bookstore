-- One-time migration from the original bookstore schema.
-- Back up the database before running this file.
--
-- This intentionally deletes the original sample users and all reviews. It
-- refuses to continue if it finds an account other than the two sample users
-- from the original init.sql.
--
-- Run against the existing database from the repository root, for example:
-- mysql --host="$MYSQL_HOST" --user="$MYSQL_USER" --password "$MYSQL_DATABASE" \
--   < migrations/001_auth_favorites_reviews.sql

DROP PROCEDURE IF EXISTS assert_legacy_auth_migration_state;

DELIMITER //
CREATE PROCEDURE assert_legacy_auth_migration_state()
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_name = 'User'
    ) OR NOT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_name = 'Reviews'
    ) OR NOT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_name = 'Books'
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Expected legacy User, Reviews, and Books tables.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = 'User'
          AND column_name = 'user_name'
    ) OR NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = 'User'
          AND column_name = 'user_password'
    ) OR EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = 'User'
          AND column_name IN ('username', 'password_hash', 'google_sub')
    ) OR EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = 'Reviews'
          AND column_name = 'review_text'
    ) OR EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_name = 'Favorites'
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Database is not in the expected legacy schema or was already migrated.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM `User`
        WHERE user_email NOT IN ('alice@example.com', 'bob@example.com')
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Unexpected users found; inspect the database before migrating.';
    END IF;
END//
DELIMITER ;

CALL assert_legacy_auth_migration_state();
DROP PROCEDURE assert_legacy_auth_migration_state;

DELETE FROM Reviews;
DELETE FROM `User`;

ALTER TABLE `User`
    DROP COLUMN user_name,
    DROP COLUMN user_password,
    ADD COLUMN username VARCHAR(20) NOT NULL,
    ADD COLUMN password_hash VARCHAR(255) NOT NULL,
    ADD COLUMN google_sub VARCHAR(255) NOT NULL,
    ADD COLUMN display_name VARCHAR(255) NULL,
    ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD CONSTRAINT uq_user_username UNIQUE (username),
    ADD CONSTRAINT uq_user_email UNIQUE (user_email),
    ADD CONSTRAINT uq_user_google_sub UNIQUE (google_sub),
    ADD CONSTRAINT chk_user_username_length
        CHECK (CHAR_LENGTH(username) BETWEEN 3 AND 20);

ALTER TABLE Reviews
    MODIFY COLUMN review_score INT NOT NULL,
    ADD COLUMN review_text TEXT NOT NULL;

CREATE TABLE Favorites (
    user_id INT NOT NULL,
    isbn VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, isbn),
    FOREIGN KEY (user_id) REFERENCES `User`(user_id) ON DELETE CASCADE,
    FOREIGN KEY (isbn) REFERENCES Books(isbn) ON DELETE CASCADE
);
