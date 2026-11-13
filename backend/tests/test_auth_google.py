import unittest
from http.cookies import SimpleCookie
import hashlib
from unittest.mock import patch

import google.auth.exceptions
import mysql.connector
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import check_password_hash

from app import create_app
from app.api.v1.auth_routes import (
    AUTH_SETUP_TOKEN_LIFETIME_SECONDS,
    AUTH_SETUP_TOKEN_SALT,
)


class GoogleLoginTests(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.config["GOOGLE_CLIENT_ID"] = "test-google-client-id"
        app.config["AUTH_SETUP_TOKEN_SECRET"] = "test-setup-token-secret"
        self.client = app.test_client()

    @staticmethod
    def google_claims(**overrides):
        claims = {
            "sub": "google-sub-123",
            "email": "reader@example.com",
            "email_verified": True,
            "name": "Book Reader",
        }
        claims.update(overrides)
        return claims

    @patch("app.api.v1.auth_routes.get_db_connection")
    @patch("app.api.v1.auth_routes.google_id_token.verify_oauth2_token")
    def test_existing_google_account_receives_server_session(
        self, verify_token, get_connection
    ):
        verify_token.return_value = self.google_claims()
        cursor = get_connection.return_value.cursor.return_value
        cursor.fetchone.return_value = (7, "book_reader")

        response = self.client.post(
            "/api/auth/google",
            json={"id_token": "google-id-token"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {"user": {"user_id": 7, "username": "book_reader"}},
        )
        verify_token.assert_called_once()
        self.assertEqual(
            verify_token.call_args.kwargs["audience"],
            "test-google-client-id",
        )
        query, params = cursor.execute.call_args_list[0].args
        self.assertIn("WHERE google_sub = %s", query)
        self.assertEqual(params, ("google-sub-123",))
        session_query, session_params = cursor.execute.call_args_list[1].args
        self.assertIn("INSERT INTO AuthSessions", session_query)
        self.assertEqual(session_params[1], 7)
        self.assertEqual(
            len(session_params[0]),
            64,
        )
        cookie = SimpleCookie()
        cookie.load(response.headers["Set-Cookie"])
        self.assertEqual(
            hashlib.sha256(
                cookie["smartbase_session"].value.encode("utf-8")
            ).hexdigest(),
            session_params[0],
        )

    @patch("app.api.v1.auth_routes.get_db_connection")
    @patch("app.api.v1.auth_routes.google_id_token.verify_oauth2_token")
    def test_new_google_identity_receives_signed_setup_token_without_account(
        self, verify_token, get_connection
    ):
        verify_token.return_value = self.google_claims()
        get_connection.return_value.cursor.return_value.fetchone.return_value = None

        response = self.client.post(
            "/api/auth/google",
            json={"id_token": "google-id-token"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["account_setup_required"])
        serializer = URLSafeTimedSerializer(
            "test-setup-token-secret",
            salt=AUTH_SETUP_TOKEN_SALT,
        )
        self.assertEqual(
            serializer.loads(response.json["account_setup_token"]),
            {
                "google_sub": "google-sub-123",
                "email": "reader@example.com",
                "display_name": "Book Reader",
            },
        )
        self.assertEqual(
            response.json["expires_in"],
            AUTH_SETUP_TOKEN_LIFETIME_SECONDS,
        )
        query = get_connection.return_value.cursor.return_value.execute.call_args.args[0]
        self.assertIn("SELECT user_id, username", query)
        self.assertNotIn("INSERT INTO", query)
        self.assertIsNone(response.headers.get("Set-Cookie"))

    @patch("app.api.v1.auth_routes.get_db_connection")
    @patch("app.api.v1.auth_routes.google_id_token.verify_oauth2_token")
    def test_unverified_email_is_rejected(self, verify_token, get_connection):
        verify_token.return_value = self.google_claims(email_verified=False)

        response = self.client.post(
            "/api/auth/google",
            json={"id_token": "google-id-token"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json, {"message": "Invalid Google credential"})
        get_connection.assert_not_called()

    @patch("app.api.v1.auth_routes.google_id_token.verify_oauth2_token")
    def test_invalid_google_credential_is_rejected(self, verify_token):
        verify_token.side_effect = ValueError("invalid signature")

        response = self.client.post(
            "/api/auth/google",
            json={"id_token": "invalid-token"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json, {"message": "Invalid Google credential"})
        self.assertNotIn("invalid signature", response.get_data(as_text=True))

    @patch("app.api.v1.auth_routes.google_id_token.verify_oauth2_token")
    def test_google_verification_service_error_returns_unavailable(
        self, verify_token
    ):
        verify_token.side_effect = google.auth.exceptions.TransportError(
            "Google unavailable"
        )

        response = self.client.post(
            "/api/auth/google",
            json={"id_token": "google-id-token"},
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json,
            {"message": "Google sign-in unavailable"},
        )

    @patch("app.api.v1.auth_routes.google_id_token.verify_oauth2_token")
    def test_missing_client_id_returns_unavailable_without_verifying(
        self, verify_token
    ):
        self.client.application.config["GOOGLE_CLIENT_ID"] = None

        response = self.client.post(
            "/api/auth/google",
            json={"id_token": "google-id-token"},
        )

        self.assertEqual(response.status_code, 503)
        verify_token.assert_not_called()

    @patch("app.api.v1.auth_routes.google_id_token.verify_oauth2_token")
    def test_missing_id_token_is_rejected_before_verification(self, verify_token):
        response = self.client.post("/api/auth/google", json={})

        self.assertEqual(response.status_code, 400)
        verify_token.assert_not_called()


class GoogleAccountSetupTests(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.config["AUTH_SETUP_TOKEN_SECRET"] = "test-setup-token-secret"
        self.client = app.test_client()

    @staticmethod
    def account_setup_token():
        serializer = URLSafeTimedSerializer(
            "test-setup-token-secret",
            salt=AUTH_SETUP_TOKEN_SALT,
        )
        return serializer.dumps(
            {
                "google_sub": "google-sub-123",
                "email": "reader@example.com",
                "display_name": "Book Reader",
            }
        )

    @patch("app.api.v1.auth_routes.get_db_connection")
    def test_valid_setup_creates_hashed_account_and_session(self, get_connection):
        password = "a-long-app-password"
        cursor = get_connection.return_value.cursor.return_value
        cursor.lastrowid = 42

        response = self.client.post(
            "/api/auth/account-setup",
            json={
                "account_setup_token": self.account_setup_token(),
                "username": "book_reader",
                "password": password,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {"user": {"user_id": 42, "username": "book_reader"}},
        )
        insert_query, insert_params = cursor.execute.call_args_list[0].args
        self.assertIn("INSERT INTO `User`", insert_query)
        self.assertEqual(
            (insert_params[0], insert_params[1], insert_params[3], insert_params[4]),
            (
                "book_reader",
                "reader@example.com",
                "google-sub-123",
                "Book Reader",
            ),
        )
        self.assertTrue(check_password_hash(insert_params[2], password))
        self.assertNotEqual(insert_params[2], password)
        session_query, session_params = cursor.execute.call_args_list[1].args
        self.assertIn("INSERT INTO AuthSessions", session_query)
        self.assertEqual(session_params[1], 42)
        cookie = SimpleCookie()
        cookie.load(response.headers["Set-Cookie"])
        self.assertTrue(cookie["smartbase_session"]["httponly"])
        get_connection.return_value.commit.assert_called_once()

    @patch("app.api.v1.auth_routes.get_db_connection")
    def test_invalid_setup_token_is_rejected_without_database_access(
        self, get_connection
    ):
        response = self.client.post(
            "/api/auth/account-setup",
            json={
                "account_setup_token": "tampered-token",
                "username": "book_reader",
                "password": "a-long-app-password",
            },
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json,
            {"message": "Invalid or expired account setup token"},
        )
        get_connection.assert_not_called()

    @patch("app.api.v1.auth_routes.get_db_connection")
    def test_invalid_username_and_password_are_rejected(self, get_connection):
        response = self.client.post(
            "/api/auth/account-setup",
            json={
                "account_setup_token": self.account_setup_token(),
                "username": "no spaces",
                "password": "short",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json,
            {"message": "Account setup details are invalid"},
        )
        get_connection.assert_not_called()

    @patch("app.api.v1.auth_routes.get_db_connection")
    def test_duplicate_account_data_returns_generic_conflict(self, get_connection):
        cursor = get_connection.return_value.cursor.return_value
        cursor.execute.side_effect = mysql.connector.IntegrityError(
            "duplicate key detail"
        )

        response = self.client.post(
            "/api/auth/account-setup",
            json={
                "account_setup_token": self.account_setup_token(),
                "username": "book_reader",
                "password": "a-long-app-password",
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json,
            {"message": "Account setup could not be completed"},
        )
        self.assertNotIn("duplicate key detail", response.get_data(as_text=True))
        get_connection.return_value.commit.assert_not_called()

    @patch(
        "app.api.v1.auth_routes.get_db_connection",
        side_effect=mysql.connector.Error("database detail"),
    )
    def test_database_failure_returns_generic_error(self, _get_connection):
        response = self.client.post(
            "/api/auth/account-setup",
            json={
                "account_setup_token": self.account_setup_token(),
                "username": "book_reader",
                "password": "a-long-app-password",
            },
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json,
            {"message": "Account setup unavailable"},
        )
        self.assertNotIn("database detail", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
