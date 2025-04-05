import os
import json
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
        
        # Parse the JSON content
        try:
            pdf_data = json.loads(document.content)
        except json.JSONDecodeError:
            pdf_data = {"error": "Failed to parse JSON data"}
        
        # Format a simple summary for display
        summary = document.summary.replace('\n', '<br>')
        
        return jsonify({
            'filename': document.filename,
            'summary': summary,
            'json_data': pdf_data  # Return the structured JSON data
        })
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return jsonify({'error': f"Failed to process PDF: {str(e)}"}), 500
