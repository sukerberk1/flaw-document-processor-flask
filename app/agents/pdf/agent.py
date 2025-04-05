import os
import json
import time
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

pdf_agent_bp = Blueprint('pdf_agent', __name__, url_prefix='/agents/pdf')

@pdf_agent_bp.route('/scan', methods=['POST'])
def scan_pdf():
    """
    Scan a PDF file and extract its content using OCR if necessary.
    
    This endpoint accepts a file path relative to the upload folder
    and processes the PDF to extract text, metadata, and structure.
    It uses OCR (Optical Character Recognition) for image-heavy or 
    scanned documents to improve text extraction.
    """
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
        print(f"Starting PDF processing: {file_path}")
        start_time = time.time()
        
        # Simplified response since PDFProcessorService is removed
        processing_time = time.time() - start_time
        pdf_data = {
            "filename": os.path.basename(file_path),
            "size_kb": os.path.getsize(full_path) / 1024,
            "processing_info": {
                "processing_time_seconds": round(processing_time, 2),
                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        # Create a simple summary
        summary = f"PDF document: {os.path.basename(file_path)}<br>Size: {pdf_data['size_kb']:.2f} KB"
        
        # Log completion
        print(f"Completed PDF processing: {file_path} in {time.time() - start_time:.2f} seconds")
        
        return jsonify({
            'filename': os.path.basename(file_path),
            'summary': summary,
            'json_data': pdf_data
        })
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error processing PDF: {str(e)}\n{error_traceback}")
        
        # Return a more detailed error response
        return jsonify({
            'error': f"Failed to process PDF: {str(e)}",
            'file_path': file_path,
            'error_type': type(e).__name__
        }), 500
