import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.features.pdf_processor.services import PDFProcessorService

pdf_agent_bp = Blueprint('pdf_agent', __name__, url_prefix='/agents/pdf')

service = PDFProcessorService()

@pdf_agent_bp.route('/scan', methods=['POST'])
def scan_pdf():
    file_path = request.json.get('file_path')
    if not file_path:
        return jsonify({'error': 'No file path provided'}), 400
        
    # Make sure the file exists and is a PDF
    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
    if not os.path.exists(full_path):
        return jsonify({'error': 'File not found'}), 404
        
    if not file_path.lower().endswith('.pdf'):
        return jsonify({'error': 'File is not a PDF'}), 400
    
    try:
        document = service.process_pdf(full_path)
        
        # Format the extracted text with HTML line breaks for display
        formatted_text = document.content.replace('\n', '<br>')
        
        return jsonify({
            'filename': document.filename,
            'summary': formatted_text,
            'extracted_text': document.content  # Include raw text for potential other uses
        })
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return jsonify({'error': f"Failed to process PDF: {str(e)}"}), 500
