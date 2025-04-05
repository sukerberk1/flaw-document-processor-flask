from flask import Flask, render_template, request, redirect, url_for, flash
import os
import glob
import zipfile
import shutil
from werkzeug.utils import secure_filename

def create_app(config_name='default'):
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_flask_app')
    
    # Configure upload folder
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Import and register blueprints for features
    from app.features.pdf_processor.views import pdf_processor_bp
    from app.features.excel_processor.views import excel_processor_bp
    
    app.register_blueprint(pdf_processor_bp)
    app.register_blueprint(excel_processor_bp)
    
    # Helper function to get all files and directories recursively
    def get_file_structure(directory):
        # Collect all files and directories
        all_items = []
        for root, dirs, files in os.walk(directory):
            rel_path = os.path.relpath(root, directory)
            if rel_path != '.':  # Skip the root directory itself
                # Calculate the depth for indentation
                depth = rel_path.count(os.sep)
                all_items.append({'type': 'directory', 'path': rel_path, 'depth': depth})
            
            for file in files:
                file_path = os.path.join(rel_path, file)
                if rel_path == '.':
                    file_path = file
                    depth = 0
                else:
                    depth = rel_path.count(os.sep) + 1
                    
                all_items.append({'type': 'file', 'path': file_path, 'depth': depth})
        
        # Create a tree structure to properly organize folders and their children
        def path_key(path):
            # Create a key for sorting that puts parent directories first,
            # then ensures files within a directory are grouped together
            parts = path.split(os.sep)
            # For each part, if it's a file keep it as is, otherwise add a trailing slash
            # to ensure directories come before files in lexicographic sorting
            return tuple([(p + '/') if i < len(parts)-1 or './' not in path else p for i, p in enumerate(parts)])
        
        # Sort all items so folders appear directly above their children
        # First by path depth, then by path components
        sorted_items = sorted(all_items, key=lambda x: (x['depth'], path_key(x['path'])))
        
        # Process the sorted list to ensure each folder is followed by its immediate children
        result = []
        path_map = {}
        
        # First pass: build a map of all paths to their items
        for item in sorted_items:
            path_map[item['path']] = item
        
        # Second pass: reorganize to ensure proper folder-file grouping
        for item in sorted_items:
            if item['type'] == 'directory':
                result.append(item)
                # Find all files that are direct children of this directory
                dir_path = item['path']
                dir_depth = item['depth']
                for child in sorted_items:
                    if child['type'] == 'file' and os.path.dirname(child['path']) == dir_path:
                        # This ensures files that are direct children come right after their parent directory
                        result.append(child)
        
        # Add any remaining files at the root level
        for item in sorted_items:
            if item['type'] == 'file' and item not in result:
                result.append(item)
                
        return result

    # Register home page route
    @app.route('/')
    def home():
        files = get_file_structure(app.config['UPLOAD_FOLDER'])
        return render_template('home.html', files=files)
    
    # Helper function to extract zip files recursively
    def extract_zip(zip_path, extract_to):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
            
        # Process nested zip files
        for root, _, files in os.walk(extract_to):
            for file in files:
                if file.lower().endswith('.zip'):
                    nested_zip_path = os.path.join(root, file)
                    
                    # Use the parent directory as the extraction path instead of creating a new one
                    nested_extract_path = os.path.dirname(nested_zip_path)
                    
                    # Extract the nested zip to its current directory
                    try:
                        with zipfile.ZipFile(nested_zip_path, 'r') as zip_ref:
                            zip_ref.extractall(nested_extract_path)
                            
                        # Remove the nested zip file after extraction
                        os.remove(nested_zip_path)
                    except Exception as e:
                        # If there's an error with a nested zip, continue with the rest
                        print(f"Error extracting nested zip {nested_zip_path}: {str(e)}")
                        continue
    
    # File upload route
    @app.route('/upload', methods=['POST'])
    def upload_file():
        if 'file' not in request.files:
            flash('No file part')
            return redirect(url_for('home'))
            
        files = request.files.getlist('file')
        
        if not files or all(file.filename == '' for file in files):
            flash('No files selected')
            return redirect(url_for('home'))
        
        uploaded_count = 0
        
        for file in files:
            if file.filename == '':
                continue
                
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Create directory structure if needed
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)
                
            file.save(file_path)
            uploaded_count += 1
            
            # Handle zip files
            if filename.lower().endswith('.zip'):
                extract_dir = os.path.join(app.config['UPLOAD_FOLDER'], os.path.splitext(filename)[0])
                
                try:
                    # Create directory for extraction
                    if not os.path.exists(extract_dir):
                        os.makedirs(extract_dir)
                        
                    # Extract the zip recursively
                    extract_zip(file_path, extract_dir)
                    flash(f'Zip file {filename} extracted successfully')
                    
                    # Delete the original zip file after extraction
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    flash(f'Error extracting zip file: {str(e)}')
        
        if uploaded_count > 0:
            flash(f'{uploaded_count} files uploaded successfully')
        
        return redirect(url_for('home'))
        
    # File delete route
    @app.route('/delete', methods=['POST'])
    def delete_file():
        file_path = request.form.get('filepath')
        
        if not file_path:
            flash('No file path provided')
            return redirect(url_for('home'))
            
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], file_path)
        
        if os.path.exists(full_path):
            try:
                if os.path.isfile(full_path):
                    # Delete a single file
                    os.remove(full_path)
                    flash(f'File {file_path} deleted successfully')
                else:
                    # Delete a directory and all its contents
                    shutil.rmtree(full_path)
                    flash(f'Directory {file_path} and all contents deleted successfully')
            except Exception as e:
                flash(f'Error deleting: {str(e)}')
        else:
            flash(f'Path {file_path} not found')
            
        return redirect(url_for('home'))
    
    # Register features page route
    @app.route('/features')
    def features():
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
        
        return render_template('features.html', features=features, available_features=available_features)
    
    return app

# Create the application instance
app = create_app()
