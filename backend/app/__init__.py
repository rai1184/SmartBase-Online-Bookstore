import os
from flask import Flask
from flask_cors import CORS


def create_app():
    # Get the absolute path of the current file
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Point to the 'images' folder at the root of the project
    # This is so that images work
    images_dir = os.path.abspath(os.path.join(basedir, "../../images"))

    app = Flask(
        __name__,
        static_folder=images_dir,
        static_url_path="/images"
    )
    CORS(app)

    from app.api.v1.routes import api_v1

    app.register_blueprint(api_v1, url_prefix="/api")
    return app