from flask import Flask, render_template
import os

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Configure upload folder
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Import and register blueprints for features
    from app.features.feature_one.views import feature_one_bp
    from app.features.feature_two.views import feature_two_bp
    from app.features.pdf_processor.views import pdf_processor_bp
    
    app.register_blueprint(feature_one_bp)
    app.register_blueprint(feature_two_bp)
    app.register_blueprint(pdf_processor_bp)
    
    # Register home page route
    @app.route('/')
    def home():
        return render_template('home.html')
    
    return app
