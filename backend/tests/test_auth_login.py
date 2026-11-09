import unittest
from http.cookies import SimpleCookie
from unittest.mock import patch

import mysql.connector
from werkzeug.security import generate_password_hash

from app import create_app


class UsernamePasswordLoginTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    @patch("app.api.v1.routes.get_db_connection")
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

    @patch("app.api.v1.routes.get_db_connection")
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
        self.assertEqual(response.json, {"message": "Invalid username or password"})
        self.assertIsNone(response.headers.get("Set-Cookie"))
        self.assertEqual(cursor.execute.call_count, 1)
        get_connection.return_value.commit.assert_not_called()

    @patch("app.api.v1.routes.get_db_connection")
    def test_unknown_username_has_same_generic_error(self, get_connection):
        cursor = get_connection.return_value.cursor.return_value
        cursor.fetchone.return_value = None

        response = self.client.post(
            "/api/auth/login",
            json={"username": "book_reader", "password": "some password"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json, {"message": "Invalid username or password"})
        self.assertIsNone(response.headers.get("Set-Cookie"))
        cursor.execute.assert_called_once()

    @patch("app.api.v1.routes.get_db_connection")
    def test_malformed_login_payload_is_rejected_before_database_access(
        self, get_connection
    ):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "invalid username", "password": ""},
        )

        self.assertEqual(response.status_code, 400)
        get_connection.assert_not_called()

    @patch(
        "app.api.v1.routes.get_db_connection",
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
        with patch("app.api.v1.routes.get_db_connection") as get_connection:
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


if __name__ == "__main__":
    unittest.main()
