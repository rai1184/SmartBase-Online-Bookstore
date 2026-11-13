import unittest
from http.cookies import SimpleCookie
import hashlib
from unittest.mock import patch

import mysql.connector
from werkzeug.security import generate_password_hash

from app import create_app


class UsernamePasswordLoginTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    @patch("app.api.v1.auth_routes.get_db_connection")
    def test_valid_credentials_create_a_hashed_server_session(
        self, get_connection
    ):
        cursor = get_connection.return_value.cursor.return_value
        cursor.fetchone.return_value = (
            7,
            "book_reader",
            generate_password_hash("correct horse battery staple"),
        )

        response = self.client.post(
            "/api/auth/login",
            json={
                "username": "book_reader",
                "password": "correct horse battery staple",
            },
            headers={"Origin": "http://localhost:5174"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {"user": {"user_id": 7, "username": "book_reader"}},
        )
        self.assertIn("Access-Control-Allow-Credentials", response.headers)
        self.assertEqual(response.headers["Access-Control-Allow-Credentials"], "true")
        self.assertEqual(
            len(cursor.execute.call_args_list),
            2,
        )
        session_insert_args = cursor.execute.call_args_list[1].args
        self.assertIn("INSERT INTO AuthSessions", session_insert_args[0])
        self.assertEqual(session_insert_args[1][1], 7)
        self.assertEqual(len(session_insert_args[1][0]), 64)
        get_connection.return_value.commit.assert_called_once()

        cookie = SimpleCookie()
        cookie.load(response.headers["Set-Cookie"])
        session_cookie = cookie["smartbase_session"]
        self.assertTrue(session_cookie["httponly"])
        self.assertEqual(session_cookie["samesite"], "Lax")
        self.assertEqual(session_cookie["path"], "/")
        self.assertFalse(session_cookie["secure"])
        self.assertNotEqual(
            session_insert_args[1][0],
            session_cookie.value,
        )

    @patch("app.api.v1.auth_routes.get_db_connection")
    def test_valid_email_credentials_create_a_server_session(self, get_connection):
        cursor = get_connection.return_value.cursor.return_value
        cursor.fetchone.return_value = (
            7,
            "book_reader",
            generate_password_hash("correct horse battery staple"),
        )

        response = self.client.post(
            "/api/auth/login",
            json={
                "username": "reader@example.com",
                "password": "correct horse battery staple",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {"user": {"user_id": 7, "username": "book_reader"}},
        )
        query, params = cursor.execute.call_args_list[0].args
        self.assertIn("username = %s OR user_email = %s", query)
        self.assertEqual(params, ("reader@example.com", "reader@example.com"))

    @patch("app.api.v1.auth_routes.get_db_connection")
    def test_invalid_credentials_return_generic_error_without_session(
        self, get_connection
    ):
        cursor = get_connection.return_value.cursor.return_value
        cursor.fetchone.return_value = (
            7,
            "book_reader",
            generate_password_hash("correct horse battery staple"),
        )

        response = self.client.post(
            "/api/auth/login",
            json={"username": "book_reader", "password": "wrong password"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json,
            {"message": "Invalid username/email or password"},
        )
        self.assertIsNone(response.headers.get("Set-Cookie"))
        self.assertEqual(cursor.execute.call_count, 1)
        get_connection.return_value.commit.assert_not_called()

    @patch("app.api.v1.auth_routes.get_db_connection")
    def test_unknown_username_has_same_generic_error(self, get_connection):
        cursor = get_connection.return_value.cursor.return_value
        cursor.fetchone.return_value = None

        response = self.client.post(
            "/api/auth/login",
            json={"username": "book_reader", "password": "some password"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json,
            {"message": "Invalid username/email or password"},
        )
        self.assertIsNone(response.headers.get("Set-Cookie"))
        cursor.execute.assert_called_once()

    @patch("app.api.v1.auth_routes.get_db_connection")
    def test_malformed_login_payload_is_rejected_before_database_access(
        self, get_connection
    ):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "", "password": ""},
        )

        self.assertEqual(response.status_code, 400)
        get_connection.assert_not_called()

    @patch(
        "app.api.v1.auth_routes.get_db_connection",
        side_effect=mysql.connector.Error("database details"),
    )
    def test_database_failure_returns_generic_error(self, _get_connection):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "book_reader", "password": "some password"},
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json, {"message": "Login unavailable"})
        self.assertNotIn("database details", response.get_data(as_text=True))

    @patch.dict("os.environ", {"AUTH_SESSION_COOKIE_SECURE": "true"})
    def test_secure_cookie_can_be_enabled_for_https(self):
        client = create_app().test_client()
        with patch("app.api.v1.auth_routes.get_db_connection") as get_connection:
            cursor = get_connection.return_value.cursor.return_value
            cursor.fetchone.return_value = (
                7,
                "book_reader",
                generate_password_hash("correct horse battery staple"),
            )
            response = client.post(
                "/api/auth/login",
                json={
                    "username": "book_reader",
                    "password": "correct horse battery staple",
                },
            )

        cookie = SimpleCookie()
        cookie.load(response.headers["Set-Cookie"])
        self.assertTrue(cookie["smartbase_session"]["secure"])


class AuthSessionEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    @patch("app.api.v1.auth_routes.get_db_connection")
    def test_current_session_returns_user_for_valid_cookie(self, get_connection):
        token = "valid-session-token"
        cursor = get_connection.return_value.cursor.return_value
        cursor.fetchone.return_value = (7, "book_reader")
        self.client.set_cookie("smartbase_session", token)

        response = self.client.get("/api/auth/me")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {"user": {"user_id": 7, "username": "book_reader"}},
        )
        cursor.execute.assert_called_once()
        query, params = cursor.execute.call_args.args
        self.assertIn("AuthSessions.expires_at > UTC_TIMESTAMP()", query)
        self.assertEqual(
            params,
            (hashlib.sha256(token.encode("utf-8")).hexdigest(),),
        )

    @patch("app.api.v1.auth_routes.get_db_connection")
    def test_current_session_rejects_missing_cookie_without_database_access(
        self, get_connection
    ):
        response = self.client.get("/api/auth/me")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json, {"message": "Authentication required"})
        get_connection.assert_not_called()

    @patch("app.api.v1.auth_routes.get_db_connection")
    def test_current_session_clears_cookie_for_expired_or_unknown_token(
        self, get_connection
    ):
        cursor = get_connection.return_value.cursor.return_value
        cursor.fetchone.return_value = None
        self.client.set_cookie("smartbase_session", "stale-token")

        response = self.client.get("/api/auth/me")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json, {"message": "Authentication required"})
        self.assertIn("smartbase_session=", response.headers["Set-Cookie"])
        self.assertIn("Max-Age=0", response.headers["Set-Cookie"])

    @patch(
        "app.api.v1.auth_routes.get_db_connection",
        side_effect=mysql.connector.Error("database details"),
    )
    def test_current_session_returns_service_error_on_database_failure(
        self, _get_connection
    ):
        self.client.set_cookie("smartbase_session", "valid-token")
        response = self.client.get("/api/auth/me")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json,
            {"message": "Session lookup unavailable"},
        )
        self.assertNotIn("database details", response.get_data(as_text=True))

    @patch("app.api.v1.auth_routes.get_db_connection")
    def test_logout_deletes_server_session_and_clears_cookie(
        self, get_connection
    ):
        token = "valid-session-token"
        cursor = get_connection.return_value.cursor.return_value
        self.client.set_cookie("smartbase_session", token)

        response = self.client.post("/api/auth/logout")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"message": "Signed out"})
        cursor.execute.assert_called_once()
        query, params = cursor.execute.call_args.args
        self.assertIn("DELETE FROM AuthSessions", query)
        self.assertEqual(
            params,
            (hashlib.sha256(token.encode("utf-8")).hexdigest(),),
        )
        get_connection.return_value.commit.assert_called_once()
        self.assertIn("Max-Age=0", response.headers["Set-Cookie"])

    @patch("app.api.v1.auth_routes.get_db_connection")
    def test_logout_without_cookie_is_idempotent(self, get_connection):
        response = self.client.post("/api/auth/logout")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"message": "Signed out"})
        self.assertIn("Max-Age=0", response.headers["Set-Cookie"])
        get_connection.assert_not_called()

    @patch(
        "app.api.v1.auth_routes.get_db_connection",
        side_effect=mysql.connector.Error("database details"),
    )
    def test_logout_database_failure_does_not_claim_success(
        self, _get_connection
    ):
        self.client.set_cookie("smartbase_session", "valid-token")
        response = self.client.post("/api/auth/logout")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json, {"message": "Logout unavailable"})
        self.assertIsNone(response.headers.get("Set-Cookie"))
        self.assertNotIn("database details", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
