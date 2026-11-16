import argparse
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request


GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"
API_KEY_ENV_VAR = "GOOGLE_BOOKS_API_KEY"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = REPOSITORY_ROOT / ".env"


def load_api_key(env_file=ENV_FILE):
    api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    if api_key:
        return api_key

    try:
        lines = env_file.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        lines = []

    for line in lines:
        name, separator, value = line.partition("=")
        if separator and name.strip() == API_KEY_ENV_VAR:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            if value:
                return value

    raise RuntimeError(
        f"Set {API_KEY_ENV_VAR} in the environment or repository .env file."
    )


def fetch_books(query, max_results, api_key, start_index=0, book_filter=None):
    params = {
        "q": query,
        "maxResults": max_results,
        "key": api_key,
    }
    if start_index:
        params["startIndex"] = start_index
    if book_filter:
        params["filter"] = book_filter
    params = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{GOOGLE_BOOKS_API_URL}?{params}",
        headers={"Accept": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response_body = response.read()
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
        raise RuntimeError(
            f"Google Books API request failed with HTTP {status}. "
            "Check that the Books API is enabled and the API key is valid, "
            "restricted to the Books API, and within quota."
        ) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise RuntimeError("Could not reach the Google Books API.") from None

    try:
        payload = json.loads(response_body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise RuntimeError("Google Books API returned invalid JSON.") from None

    if not isinstance(payload, dict) or not isinstance(payload.get("items", []), list):
        raise RuntimeError("Google Books API returned an unexpected response.")
    if payload.get("error"):
        raise RuntimeError("Google Books API returned an error response.")

    return payload


def summarize_book(item):
    volume_info = item.get("volumeInfo") or {}
    if not isinstance(volume_info, dict):
        volume_info = {}

    identifiers = volume_info.get("industryIdentifiers") or []
    isbn = ""
    for preferred_type in ("ISBN_13", "ISBN_10"):
        isbn = next(
            (
                identifier.get("identifier", "")
                for identifier in identifiers
                if isinstance(identifier, dict)
                and identifier.get("type") == preferred_type
            ),
            "",
        )
        if isbn:
            break

    authors = volume_info.get("authors") or []
    categories = volume_info.get("categories") or []
    description = " ".join(str(volume_info.get("description") or "").split())

    sale_info = item.get("saleInfo") or {}
    retail_price = sale_info.get("retailPrice") or {}
    price = "not provided"
    if isinstance(retail_price, dict) and retail_price.get("amount") is not None:
        currency = retail_price.get("currencyCode", "")
        price = f"{currency} {retail_price['amount']}".strip()

    image_links = volume_info.get("imageLinks") or {}
    cover_url = ""
    if isinstance(image_links, dict):
        cover_url = image_links.get("thumbnail") or ""
        if cover_url.startswith("http://"):
            cover_url = f"https://{cover_url[7:]}"

    return {
        "title": volume_info.get("title") or "(untitled)",
        "authors": ", ".join(str(author) for author in authors) or "not provided",
        "isbn": isbn or "not provided",
        "published": volume_info.get("publishedDate") or "not provided",
        "categories": ", ".join(str(category) for category in categories)
        or "not provided",
        "price": price,
        "cover_available": bool(cover_url),
        "cover_url": cover_url,
        "description": description[:240] + ("..." if len(description) > 240 else ""),
    }


def is_ready_to_seed(item):
    summary = summarize_book(item)
    return (
        summary["isbn"] != "not provided"
        and summary["price"] != "not provided"
        and bool(summary["cover_url"])
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Preview Google Books results without writing to the database."
    )
    parser.add_argument(
        "--query",
        default="subject:Science Fiction",
        help="Google Books search query (default: subject:Science Fiction)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Number of results to preview (1-10; default: 5)",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="Starting result offset for paging through search results (default: 0).",
    )
    parser.add_argument(
        "--paid-ebooks",
        action="store_true",
        help="Restrict results to paid Google eBooks, which may have eBook prices.",
    )
    parser.add_argument(
        "--show-cover-urls",
        action="store_true",
        help="Print Google Books cover URLs for returned books.",
    )
    parser.add_argument(
        "--ready-to-seed",
        action="store_true",
        help=(
            "Show only returned books with an ISBN, Google retail price, "
            "and cover URL."
        ),
    )
    args = parser.parse_args(argv)
    if not 1 <= args.max_results <= 10:
        parser.error("--max-results must be between 1 and 10")
    if args.start_index < 0:
        parser.error("--start-index must be zero or greater")

    try:
        api_key = load_api_key()
        payload = fetch_books(
            args.query,
            args.max_results,
            api_key,
            start_index=args.start_index,
            book_filter="paid-ebooks" if args.paid_ebooks else None,
        )
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1

    items = payload.get("items", [])
    print(f"Google Books reports {payload.get('totalItems', 0)} matching books.")
    if args.paid_ebooks:
        print("Google Books filter: paid-ebooks")
    if not items:
        print("No results were returned.")
        return 0

    if args.ready_to_seed:
        returned_count = len(items)
        items = [item for item in items if is_ready_to_seed(item)]
        print(
            f"{len(items)} of the {returned_count} returned results have "
            "an ISBN, price, and cover."
        )
        if not items:
            print("No returned results meet all three requirements.")
            return 0

    for index, item in enumerate(items, start=1):
        summary = summarize_book(item)
        print(f"\n{index}. {summary['title']}")
        print(f"   Author(s): {summary['authors']}")
        print(f"   ISBN: {summary['isbn']}")
        print(f"   Published: {summary['published']}")
        print(f"   Categories: {summary['categories']}")
        print(f"   Price: {summary['price']}")
        print(f"   Cover available: {'yes' if summary['cover_available'] else 'no'}")
        if args.show_cover_urls and summary["cover_url"]:
            print(f"   Cover URL: {summary['cover_url']}")
        if summary["description"]:
            print(f"   Description: {summary['description']}")

    print("\nPreview only: no database records were changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
