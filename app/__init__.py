import os
import configparser
from flask import Flask
from flask_wtf import CSRFProtect
from .extensions import cache, db
from .admin_routes import admin_bp
from .main_routes import main_bp

def create_app():
    app = Flask(__name__)

    # Load config.ini
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
    config.read(config_path)

    # Set Flask config from config.ini
    app.secret_key = config['flask']['SECRET_KEY']
    app.config['SQLALCHEMY_DATABASE_URI'] = config['database']['URI']
    app.config['CACHE_TYPE'] = config['cache']['TYPE']
    app.config['CACHE_DEFAULT_TIMEOUT'] = int(config['cache']['DEFAULT_TIMEOUT'])

    # Init extensions
    CSRFProtect(app)
    print("Initializing db with app")
    db.init_app(app)
    cache.init_app(app)

    # Register blueprints
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(main_bp)  # quiz + other public routes

    return app
