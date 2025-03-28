import os
from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.features.pdf_processor.services import PDFProcessorService

pdf_processor_bp = Blueprint('pdf_processor', __name__, 
                          url_prefix='/pdf-processor',
                          template_folder='.')  # Look for templates in the current directory

service = PDFProcessorService()

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@pdf_processor_bp.route('/')
def index():
    return render_template('./template/index.html')

@pdf_processor_bp.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            document = service.process_pdf(file_path)
            os.remove(file_path)  # Clean up the uploaded file
            
            return jsonify({
                'filename': document.filename,
                'summary': document.summary
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400