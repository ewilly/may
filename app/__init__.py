from flask import Flask, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel, gettext as _
from config import Config
import os
import secrets

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
babel = Babel()
csrf = CSRFProtect()

# Supported languages
LANGUAGES = {
    'en': 'English',
    'de': 'Deutsch',
    'es': 'Español',
    'fr': 'Français',
    'it': 'Italiano',
    'nl': 'Nederlands',
    'pt': 'Português',
    'pl': 'Polski',
    'sv': 'Svenska',
    'da': 'Dansk',
    'no': 'Norsk',
    'fi': 'Suomi',
    'ja': '日本語',
    'zh': '中文',
    'ko': '한국어'
}


def get_locale():
    """Select the best language for the user"""
    # If user is logged in and has a language preference, use it
    if current_user.is_authenticated and current_user.language:
        return current_user.language

    # Otherwise, try to match browser language
    return request.accept_languages.best_match(LANGUAGES.keys(), default='en')


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Babel configuration
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_SUPPORTED_LOCALES'] = list(LANGUAGES.keys())

    # Ensure data directories exist
    os.makedirs(os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')), exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    babel.init_app(app, locale_selector=get_locale)

    # Exempt API endpoints from CSRF (they use API key auth)
    from app.routes import api
    csrf.exempt(api.bp)

    from app.models import User, AppSettings

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Make languages and branding available in templates
    @app.context_processor
    def inject_globals():
        branding = AppSettings.get_all_branding()
        return {
            'LANGUAGES': LANGUAGES,
            'APP_NAME': branding.get('app_name', 'May'),
            'APP_TAGLINE': branding.get('app_tagline', 'Vehicle Management'),
            'APP_LOGO': branding.get('logo_filename'),
            'PRIMARY_COLOR': branding.get('primary_color', '#0284c7'),
        }

    from app.routes import main, auth, vehicles, fuel, expenses, api, reminders, maintenance, documents, stations, recurring, homeassistant, calendar, trips, charging
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(vehicles.bp)
    app.register_blueprint(fuel.bp)
    app.register_blueprint(expenses.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(reminders.bp)
    app.register_blueprint(maintenance.bp)
    app.register_blueprint(documents.bp)
    app.register_blueprint(stations.bp)
    app.register_blueprint(recurring.bp)
    app.register_blueprint(homeassistant.bp)
    app.register_blueprint(calendar.bp)
    app.register_blueprint(trips.bp)
    app.register_blueprint(charging.bp)

    # Health check endpoint for container orchestration
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}, 200

    # Security headers
    @app.after_request
    def add_security_headers(response):
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Enable XSS filter in browsers
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Permissions policy (formerly feature policy)
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response

    with app.app_context():
        db.create_all()
        # Create default admin user if no users exist
        if User.query.count() == 0:
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
            admin_password = os.environ.get('ADMIN_PASSWORD')

            if not admin_password:
                # Generate a secure random password
                admin_password = secrets.token_urlsafe(16)
                print("=" * 60)
                print("SECURITY NOTICE: Default admin account created")
                print(f"Username: {admin_username}")
                print(f"Password: {admin_password}")
                print("Please change this password immediately after first login!")
                print("Set ADMIN_PASSWORD environment variable to avoid this message.")
                print("=" * 60)

            admin = User(username=admin_username, email=admin_email, is_admin=True)
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()

    return app
