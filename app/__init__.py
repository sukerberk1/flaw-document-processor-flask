from flask import Flask
from app.features.web import pdf_blueprint

def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure the app
    app.config.from_mapping(
        SECRET_KEY='dev',
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max upload size
    )
    
    if config:
        app.config.from_mapping(config)
    
    # Register blueprints
    app.register_blueprint(pdf_blueprint)
    
    # Register a simple index route
    @app.route('/')
    def index():
        return app.send_static_file('index.html')
    
    return app
