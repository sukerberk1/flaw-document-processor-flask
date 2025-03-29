import os
import logging
from flask import Blueprint, render_template, request, jsonify, current_app

logging.basicConfig(level=logging.DEBUG)
from werkzeug.utils import secure_filename
from app.features.excel_processor.services import ExcelProcessorService

excel_processor_bp = Blueprint('excel_processor', __name__, 
                            url_prefix='/excel-processor',
                            template_folder='template',
                            static_folder='template')  # Serve static files from template directory

service = ExcelProcessorService()

ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@excel_processor_bp.route('/')
def index():
    """Render the index page for Excel processing."""
    return render_template('index.html')

@excel_processor_bp.route('/upload', methods=['POST'])
def upload_excel():
    """Handle Excel file upload and processing."""
    logging.debug("Received request to upload file.")
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    logging.debug("Checking if a file is selected.")
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    logging.debug(f"File selected: {file.filename}")
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Make sure the upload folder exists
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(file_path)
            logging.debug(f"File saved to {file_path}")
        except Exception as e:
            logging.error(f"Error saving file: {e}")
            return jsonify({'error': 'Failed to save file'}), 500
        
        try:
            logging.debug("Processing file...")
            analysis = service.process_excel(file_path)
            logging.debug(f"File processed successfully. Analysis: {analysis}")
            
            # Only remove the file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)  # Clean up the uploaded file
            
            return jsonify({
                'filename': filename,
                'analysis': analysis
            })
        except Exception as e:
            logging.error(f"Error processing file: {e}")
            
            # Try to clean up the file even if processing failed
            if os.path.exists(file_path):
                os.remove(file_path)
                
            return jsonify({'error': f"Failed to process Excel: {str(e)}"}), 500
    
    logging.debug("Invalid file type.")
    return jsonify({'error': 'Invalid file type'}), 400
