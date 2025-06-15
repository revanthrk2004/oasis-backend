import os

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
    from . import models  # <-- moved up
    migrate.init_app(app, db)
    jwt.init_app(app)

    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        user = models.User.query.get(int(identity))
        return {"role": user.role}

    CORS(app)

    try:
        from .routes import main
        from .auth import auth
        from .menu import menu
        from .orders import orders
        from .bookings import bookings
        from .wallet import wallet
        from .tab import tab
        from .admin import admin
        from .discounts import discounts
        from .happy_hour import happy_hour

        app.register_blueprint(main)
        app.register_blueprint(auth, url_prefix='')
        app.register_blueprint(menu)
        app.register_blueprint(orders)
        app.register_blueprint(bookings)
        app.register_blueprint(wallet)
        app.register_blueprint(tab)
        app.register_blueprint(admin)
        app.register_blueprint(discounts)
        app.register_blueprint(happy_hour)




    except Exception as e:
        app.logger.error(f"App creation error: {e}")

    return app
