from flask import Flask, render_template
import os
import glob

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Configure upload folder
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Import and register blueprints for features
    from app.features.pdf_processor.views import pdf_processor_bp
    
    app.register_blueprint(pdf_processor_bp)
    app.register_blueprint(excel_processor_bp)
    
    # Register home page route
    @app.route('/')
    def home():
        # Dynamically list all features
        features_path = os.path.join(app.root_path, 'features')
        features = []
        
        # Get all directories in the features folder that aren't __pycache__
        for item in os.listdir(features_path):
            full_path = os.path.join(features_path, item)
            if os.path.isdir(full_path) and not item.startswith('__') and not item.startswith('.'):
                # Check if this directory contains a views.py file (indicating it's a feature module)
                if os.path.exists(os.path.join(full_path, 'views.py')):
                    features.append(item)
        
        # Create a dictionary of available features with their route availability
        available_features = {}
        for feature in features:
            route_name = feature + '.index'
            available_features[feature] = route_name in app.view_functions
        
        return render_template('home.html', features=features, available_features=available_features)
    
    return app
