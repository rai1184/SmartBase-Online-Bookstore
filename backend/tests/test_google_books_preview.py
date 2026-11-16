import os
from pathlib import Path
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

from app.utils.google_books_preview import (
    fetch_books,
    is_ready_to_seed,
    load_api_key,
    summarize_book,
)


class GoogleBooksPreviewTests(unittest.TestCase):
    def test_load_api_key_reads_only_the_requested_env_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text(
                "OTHER_SETTING=value\nGOOGLE_BOOKS_API_KEY='test-key'\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(load_api_key(env_file), "test-key")

    def test_environment_api_key_takes_precedence_over_env_file(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text(
                "GOOGLE_BOOKS_API_KEY=file-key\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"GOOGLE_BOOKS_API_KEY": "process-key"}):
                self.assertEqual(load_api_key(env_file), "process-key")

    def test_summarize_book_prefers_isbn_13_and_handles_missing_fields(self):
        summary = summarize_book(
            {
                "volumeInfo": {
                    "title": "Sample Book",
                    "authors": ["A. Author", "B. Author"],
                    "industryIdentifiers": [
                        {"type": "ISBN_10", "identifier": "0123456789"},
                        {"type": "ISBN_13", "identifier": "9780123456786"},
                    ],
                    "imageLinks": {"thumbnail": "http://example.test/cover"},
                }
            }
        )

        self.assertEqual(summary["title"], "Sample Book")
        self.assertEqual(summary["authors"], "A. Author, B. Author")
        self.assertEqual(summary["isbn"], "9780123456786")
        self.assertEqual(summary["price"], "not provided")
        self.assertTrue(summary["cover_available"])
        self.assertEqual(
            summary["cover_url"],
            "https://example.test/cover",
        )
        self.assertEqual(summary["description"], "")

    def test_api_error_does_not_expose_key_in_error_message(self):
        api_key = "private-test-key"
        error = urllib.error.HTTPError(
            f"https://example.test/?key={api_key}",
            429,
            "quota exceeded",
            {},
            None,
        )

        with patch(
            "app.utils.google_books_preview.urllib.request.urlopen",
            side_effect=error,
        ):
            with self.assertRaisesRegex(RuntimeError, "HTTP 429") as raised:
                fetch_books("subject:Science Fiction", 5, api_key)

        self.assertNotIn(api_key, str(raised.exception))

    def test_ready_to_seed_requires_isbn_price_and_cover(self):
        complete_item = {
            "volumeInfo": {
                "industryIdentifiers": [
                    {"type": "ISBN_13", "identifier": "9780123456786"}
                ],
                "imageLinks": {"thumbnail": "https://example.test/cover"},
            },
            "saleInfo": {"retailPrice": {"amount": 9.99, "currencyCode": "USD"}},
        }

        self.assertTrue(is_ready_to_seed(complete_item))
        self.assertFalse(is_ready_to_seed({"volumeInfo": {}, "saleInfo": {}}))


if __name__ == "__main__":
    unittest.main()
