from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app)

    from app.api.v1.routes import api_v1

    app.register_blueprint(api_v1, url_prefix="/api")
    return app
