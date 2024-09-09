from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config

# Initialize database
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Import routes
    from .app_routes import main
    app.register_blueprint(main)

    return app
