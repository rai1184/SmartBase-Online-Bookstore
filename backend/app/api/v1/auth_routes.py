from contextlib import closing
from datetime import datetime, timedelta, timezone
import hashlib
import re
import secrets
import urllib.error
import urllib.request

from google.auth import exceptions as google_auth_exceptions
from google.oauth2 import id_token as google_id_token
from itsdangerous import BadSignature, URLSafeTimedSerializer
import mysql.connector
from flask import Blueprint, current_app, jsonify, make_response, request
from werkzeug.security import check_password_hash, generate_password_hash

from app.database.connection import get_db_connection

auth_v1 = Blueprint("auth_v1", __name__)
AUTH_SESSION_COOKIE = "smartbase_session"
AUTH_SESSION_LIFETIME = timedelta(days=7)
AUTH_SETUP_TOKEN_SALT = "smartbase-account-setup"
AUTH_SETUP_TOKEN_LIFETIME_SECONDS = 600
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,20}$")


class _GoogleAuthResponse:
    def __init__(self, status, headers, data):
        self.status = status
        self.headers = headers
        self.data = data


def _google_certificate_request(
    url, method="GET", body=None, headers=None, timeout=None
):
    http_request = urllib.request.Request(
        url,
        data=body,
        headers=headers or {},
        method=method,
    )
    try:
        with urllib.request.urlopen(http_request, timeout=timeout or 10) as response:
            return _GoogleAuthResponse(
                response.status,
                response.headers,
                response.read(),
            )
    except urllib.error.HTTPError as error:
        return _GoogleAuthResponse(error.code, error.headers, error.read())
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise google_auth_exceptions.TransportError(error) from error


def _create_auth_session(connection, user_id):
    session_token = secrets.token_urlsafe(32)
    session_token_hash = hashlib.sha256(
        session_token.encode("utf-8")
    ).hexdigest()
    expires_at = datetime.now(timezone.utc) + AUTH_SESSION_LIFETIME

    with closing(connection.cursor()) as cursor:
        cursor.execute(
            """
            INSERT INTO AuthSessions (session_token_hash, user_id, expires_at)
            VALUES (%s, %s, %s)
            """,
            (session_token_hash, user_id, expires_at.replace(tzinfo=None)),
        )
    connection.commit()
    return session_token


def _session_response(user, session_token):
    response = make_response(
        jsonify({"user": {"user_id": user[0], "username": user[1]}})
    )
    response.set_cookie(
        AUTH_SESSION_COOKIE,
        session_token,
        max_age=int(AUTH_SESSION_LIFETIME.total_seconds()),
        httponly=True,
        secure=current_app.config["AUTH_SESSION_COOKIE_SECURE"],
        samesite="Lax",
        path="/",
    )
    return response


@auth_v1.post("/auth/login")
def login():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(
            {"message": "Username or email and password are required"}
        ), 400

    username = payload.get("username")
    password = payload.get("password")
    if (
        not isinstance(username, str)
        or not 1 <= len(username) <= 255
        or not isinstance(password, str)
        or not 1 <= len(password) <= 128
    ):
        return jsonify(
            {"message": "Username or email and password are required"}
        ), 400

    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    """
                    SELECT user_id, username, password_hash
                    FROM `User`
                    WHERE username = %s OR user_email = %s
                    """,
                    (username, username),
                )
                user = cursor.fetchone()

            if user is None or not check_password_hash(user[2], password):
                return jsonify(
                    {"message": "Invalid username/email or password"}
                ), 401

            session_token = _create_auth_session(connection, user[0])
    except (mysql.connector.Error, RuntimeError, ValueError):
        current_app.logger.exception("Username/password login failed")
        return jsonify({"message": "Login unavailable"}), 503

    return _session_response(user, session_token)


@auth_v1.post("/auth/google")
def google_login():
    payload = request.get_json(silent=True)
    id_token_value = payload.get("id_token") if isinstance(payload, dict) else None
    if not isinstance(id_token_value, str) or not 1 <= len(id_token_value) <= 8192:
        return jsonify({"message": "A Google credential is required"}), 400

    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    if not client_id:
        current_app.logger.error("Google sign-in is unavailable: client ID is missing")
        return jsonify({"message": "Google sign-in unavailable"}), 503

    try:
        claims = google_id_token.verify_oauth2_token(
            id_token_value,
            _google_certificate_request,
            audience=client_id,
        )
    except ValueError:
        return jsonify({"message": "Invalid Google credential"}), 401
    except google_auth_exceptions.GoogleAuthError:
        current_app.logger.exception("Google credential verification failed")
        return jsonify({"message": "Google sign-in unavailable"}), 503

    if not isinstance(claims, dict):
        return jsonify({"message": "Invalid Google credential"}), 401

    google_sub = claims.get("sub")
    email = claims.get("email")
    display_name = claims.get("name")
    if (
        not isinstance(google_sub, str)
        or not 1 <= len(google_sub) <= 255
        or not isinstance(email, str)
        or not 1 <= len(email) <= 255
        or claims.get("email_verified") is not True
        or (
            display_name is not None
            and (not isinstance(display_name, str) or len(display_name) > 255)
        )
    ):
        return jsonify({"message": "Invalid Google credential"}), 401

    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    """
                    SELECT user_id, username
                    FROM `User`
                    WHERE google_sub = %s
                    """,
                    (google_sub,),
                )
                user = cursor.fetchone()

            if user is not None:
                session_token = _create_auth_session(connection, user[0])
    except (mysql.connector.Error, RuntimeError, ValueError):
        current_app.logger.exception("Google account lookup failed")
        return jsonify({"message": "Google sign-in unavailable"}), 503

    if user is not None:
        return _session_response(user, session_token)

    setup_secret = current_app.config.get("AUTH_SETUP_TOKEN_SECRET")
    if not setup_secret:
        current_app.logger.error(
            "Google sign-in is unavailable: account setup token secret is missing"
        )
        return jsonify({"message": "Google sign-in unavailable"}), 503

    serializer = URLSafeTimedSerializer(
        setup_secret,
        salt=AUTH_SETUP_TOKEN_SALT,
    )
    setup_token = serializer.dumps(
        {
            "google_sub": google_sub,
            "email": email,
            "display_name": display_name,
        }
    )
    return jsonify(
        {
            "account_setup_required": True,
            "account_setup_token": setup_token,
            "expires_in": AUTH_SETUP_TOKEN_LIFETIME_SECONDS,
        }
    )


@auth_v1.post("/auth/account-setup")
def create_account():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"message": "Account setup details are required"}), 400

    setup_token = payload.get("account_setup_token")
    username = payload.get("username")
    password = payload.get("password")
    if (
        not isinstance(setup_token, str)
        or not 1 <= len(setup_token) <= 4096
        or not isinstance(username, str)
        or not USERNAME_PATTERN.fullmatch(username)
        or not isinstance(password, str)
        or not 12 <= len(password) <= 128
    ):
        return jsonify({"message": "Account setup details are invalid"}), 400

    setup_secret = current_app.config.get("AUTH_SETUP_TOKEN_SECRET")
    if not setup_secret:
        current_app.logger.error(
            "Account setup is unavailable: account setup token secret is missing"
        )
        return jsonify({"message": "Account setup unavailable"}), 503

    serializer = URLSafeTimedSerializer(
        setup_secret,
        salt=AUTH_SETUP_TOKEN_SALT,
    )
    try:
        identity = serializer.loads(
            setup_token,
            max_age=AUTH_SETUP_TOKEN_LIFETIME_SECONDS,
        )
    except BadSignature:
        return jsonify({"message": "Invalid or expired account setup token"}), 401

    if not isinstance(identity, dict):
        return jsonify({"message": "Invalid or expired account setup token"}), 401

    google_sub = identity.get("google_sub")
    email = identity.get("email")
    display_name = identity.get("display_name")
    if (
        not isinstance(google_sub, str)
        or not 1 <= len(google_sub) <= 255
        or not isinstance(email, str)
        or not 1 <= len(email) <= 255
        or (
            display_name is not None
            and (not isinstance(display_name, str) or len(display_name) > 255)
        )
    ):
        return jsonify({"message": "Invalid or expired account setup token"}), 401

    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    """
                    INSERT INTO `User`
                        (username, user_email, password_hash, google_sub, display_name)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        username,
                        email,
                        generate_password_hash(password),
                        google_sub,
                        display_name,
                    ),
                )
                user = (cursor.lastrowid, username)

            session_token = _create_auth_session(connection, user[0])
    except mysql.connector.IntegrityError:
        return jsonify({"message": "Account setup could not be completed"}), 409
    except (mysql.connector.Error, RuntimeError, ValueError):
        current_app.logger.exception("Account setup failed")
        return jsonify({"message": "Account setup unavailable"}), 503

    return _session_response(user, session_token)


@auth_v1.get("/auth/me")
def current_session():
    session_token = request.cookies.get(AUTH_SESSION_COOKIE)
    if not session_token:
        return jsonify({"message": "Authentication required"}), 401

    session_token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    """
                    SELECT `User`.user_id, `User`.username
                    FROM AuthSessions
                    JOIN `User` ON `User`.user_id = AuthSessions.user_id
                    WHERE AuthSessions.session_token_hash = %s
                      AND AuthSessions.expires_at > UTC_TIMESTAMP()
                    """,
                    (session_token_hash,),
                )
                user = cursor.fetchone()
    except (mysql.connector.Error, RuntimeError):
        current_app.logger.exception("Current session lookup failed")
        return jsonify({"message": "Session lookup unavailable"}), 503

    if user is None:
        response = make_response(
            jsonify({"message": "Authentication required"}),
            401,
        )
        response.delete_cookie(
            AUTH_SESSION_COOKIE,
            path="/",
            secure=current_app.config["AUTH_SESSION_COOKIE_SECURE"],
            httponly=True,
            samesite="Lax",
        )
        return response

    return jsonify({"user": {"user_id": user[0], "username": user[1]}})


@auth_v1.post("/auth/logout")
def logout():
    session_token = request.cookies.get(AUTH_SESSION_COOKIE)
    if session_token:
        session_token_hash = hashlib.sha256(
            session_token.encode("utf-8")
        ).hexdigest()
        try:
            with closing(get_db_connection()) as connection:
                with closing(connection.cursor()) as cursor:
                    cursor.execute(
                        """
                        DELETE FROM AuthSessions
                        WHERE session_token_hash = %s
                        """,
                        (session_token_hash,),
                    )
                connection.commit()
        except (mysql.connector.Error, RuntimeError):
            current_app.logger.exception("Logout failed")
            return jsonify({"message": "Logout unavailable"}), 503

    response = make_response(jsonify({"message": "Signed out"}))
    response.delete_cookie(
        AUTH_SESSION_COOKIE,
        path="/",
        secure=current_app.config["AUTH_SESSION_COOKIE_SECURE"],
        httponly=True,
        samesite="Lax",
    )
    return response

# Endpoint for registration
@auth_v1.post("/auth/register")
def register():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"message": "Registration details are required"}), 400

    username = payload.get("username")
    email = payload.get("email")
    password = payload.get("password")

    # Validate inputs
    if (
        not isinstance(username, str)
        or not USERNAME_PATTERN.fullmatch(username)
        or not isinstance(email, str)
        or not 1 <= len(email) <= 255
        or not isinstance(password, str)
        or not 12 <= len(password) <= 128
    ):
        return jsonify({"message": "Invalid registration details"}), 400

    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    """
                    INSERT INTO `User` (username, user_email, password_hash, google_sub)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        username,
                        email,
                        generate_password_hash(password),
                        None,  # Local registration leaves google_sub as NULL
                    ),
                )
                connection.commit()
                user = (cursor.lastrowid, username)

            session_token = _create_auth_session(connection, user[0])
    except mysql.connector.IntegrityError:
        return jsonify({"message": "Username or email already exists"}), 409
    except (mysql.connector.Error, RuntimeError, ValueError):
        current_app.logger.exception("Registration failed")
        return jsonify({"message": "Registration unavailable"}), 503

    return _session_response(user, session_token), 201