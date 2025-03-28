import os
import logging
from flask import Blueprint, render_template, request, jsonify, current_app

logging.basicConfig(level=logging.DEBUG)
from werkzeug.utils import secure_filename
from .services import ExcelProcessorService

excel_processor_bp = Blueprint('excel_processor', __name__,
                             url_prefix='/excel-processor',
                             template_folder='.')  # Look for templates in the current directory

service = ExcelProcessorService()

ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'csv'}

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@excel_processor_bp.route('/')
def index():
    """Render the index page for Excel processing."""
    return render_template('./template/index.html')

@excel_processor_bp.route('/upload', methods=['POST'])
def upload_excel():
    """Handle Excel file upload and processing."""
    logging.debug("Received request to upload file.")
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    logging.debug(f"File selected: {file.filename}")
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(file_path)
            logging.debug(f"File saved to {file_path}")
        except Exception as e:
            logging.error(f"Error saving file: {e}")
            return jsonify({'error': 'Failed to save file'}), 500
        
        try:
            logging.debug("Processing file...")
            result = service.process_excel(file_path)
            logging.debug("File processed successfully.")
            os.remove(file_path)  # Clean up the uploaded file
            
            return jsonify({
                'filename': filename,
                'summary': result
            })
        except Exception as e:
            logging.error(f"Error processing file: {e}")
            return jsonify({'error': 'Failed to process file'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400
