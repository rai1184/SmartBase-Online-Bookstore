import os
import unittest
from unittest.mock import patch

import mysql.connector

from app import create_app
from app.database.connection import get_db_connection


class DatabaseConnectionTests(unittest.TestCase):
    def test_connection_uses_compose_environment_settings(self):
        settings = {
            "MYSQL_HOST": "db",
            "MYSQL_USER": "root",
            "MYSQL_PASSWORD": "secret",
            "MYSQL_DATABASE": "smartbase_db",
        }

        with patch.dict(os.environ, settings, clear=True):
            with patch("mysql.connector.connect") as connect:
                get_db_connection()

        connect.assert_called_once_with(
            host="db",
            user="root",
            password="secret",
            database="smartbase_db",
        )

    def test_connection_requires_all_environment_settings(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "MYSQL_HOST"):
                get_db_connection()


class DatabaseHealthRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_flask_health_route_remains_available(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "online")

    @patch("app.api.v1.routes.get_db_connection")
    def test_database_health_returns_book_count(self, get_connection):
        cursor = get_connection.return_value.cursor.return_value
        cursor.fetchone.return_value = (30,)

        response = self.client.get("/api/health/database")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {"status": "online", "book_count": 30},
        )
        cursor.execute.assert_called_once_with("SELECT COUNT(*) FROM Books")
        cursor.close.assert_called_once()
        get_connection.return_value.close.assert_called_once()

    @patch(
        "app.api.v1.routes.get_db_connection",
        side_effect=mysql.connector.Error("database details"),
    )
    def test_database_health_returns_generic_error(self, _get_connection):
        response = self.client.get("/api/health/database")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json,
            {"status": "error", "message": "Database unavailable"},
        )
        self.assertNotIn("database details", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
