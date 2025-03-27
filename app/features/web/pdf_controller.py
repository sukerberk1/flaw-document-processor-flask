import os
from flask import Blueprint, request, jsonify, render_template, current_app
from werkzeug.utils import secure_filename
from app.features.pdf_processing import PdfExtractor, PdfSummarizer

pdf_blueprint = Blueprint('pdf', __name__)

@pdf_blueprint.route('/upload', methods=['POST'])
def upload_pdf():
    """Handle PDF upload and summarization."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if file and file.filename.endswith('.pdf'):
        # Process the PDF
        try:
            # Extract text
            extractor = PdfExtractor()
            text = extractor.extract_text(file)
            
            # Summarize text
            summarizer = PdfSummarizer()
            summary_ratio = float(request.form.get('ratio', 0.3))
            summary_data = summarizer.summarize(text, ratio=summary_ratio)
            
            return jsonify({
                "success": True,
                "summary": summary_data["summary"],
                "word_count": summary_data["word_count"],
                "original_word_count": summary_data["original_word_count"],
                "reduction_percentage": round((1 - (summary_data["word_count"] / max(1, summary_data["original_word_count"]))) * 100, 1)
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Only PDF files are allowed"}), 400
