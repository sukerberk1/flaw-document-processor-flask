import os
import json
import time
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.features.pdf_processor.services import PDFProcessorService

pdf_agent_bp = Blueprint('pdf_agent', __name__, url_prefix='/agents/pdf')

service = PDFProcessorService()

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
        
        # Process the PDF document
        document = service.process_pdf(full_path)
        
        # Parse the JSON content
        try:
            pdf_data = json.loads(document.content)
            
            # Add processing metadata
            processing_time = time.time() - start_time
            pdf_data["processing_info"] = {
                "processing_time_seconds": round(processing_time, 2),
                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "ocr_used": pdf_data.get("used_ocr", False)
            }
            
        except json.JSONDecodeError as json_err:
            print(f"JSON parsing error: {str(json_err)}")
            pdf_data = {
                "error": "Failed to parse JSON data",
                "error_details": str(json_err)
            }
        
        # Format the summary for display with HTML line breaks
        summary = document.summary.replace('\n', '<br>')
        
        # Log completion
        print(f"Completed PDF processing: {file_path} in {time.time() - start_time:.2f} seconds")
        
        return jsonify({
            'filename': document.filename,
            'summary': summary,
            'json_data': pdf_data  # Return the structured JSON data
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
