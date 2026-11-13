import os

from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.config["GOOGLE_CLIENT_ID"] = os.environ.get("GOOGLE_CLIENT_ID")
    app.config["AUTH_SETUP_TOKEN_SECRET"] = os.environ.get(
        "AUTH_SETUP_TOKEN_SECRET"
    )
    app.config["AUTH_SESSION_COOKIE_SECURE"] = (
        os.environ.get("AUTH_SESSION_COOKIE_SECURE", "false").lower() == "true"
    )
    origins = os.environ.get(
        "FRONTEND_ORIGINS",
        "http://localhost:5174,http://127.0.0.1:5174",
    )
    CORS(
        app,
        origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
        supports_credentials=True,
    )

    from app.api.v1.auth_routes import auth_v1
    from app.api.v1.routes import api_v1

    app.register_blueprint(api_v1, url_prefix="/api")
    app.register_blueprint(auth_v1, url_prefix="/api")
    return app
