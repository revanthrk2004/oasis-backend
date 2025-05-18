from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from .config import Config


# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    try:
        from . import models
        from .routes import main
        from .auth import auth
        from .menu import menu
        app.register_blueprint(main)
        app.register_blueprint(auth)
        app.register_blueprint(menu)
    except Exception as e:
        app.logger.error(f"App creation error: {e}")

    return app
