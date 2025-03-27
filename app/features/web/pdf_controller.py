import os
from flask import Blueprint, request, jsonify, render_template, current_app
from werkzeug.utils import secure_filename
from app.features.pdf_processing import PdfExtractor, PdfSummarizer
from app.features.excel_processing import ExcelExtractor

pdf_blueprint = Blueprint('pdf', __name__)

@pdf_blueprint.route('/upload', methods=['POST'])
def upload_pdf():
    """Handle file upload and summarization."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    file_extension = os.path.splitext(file.filename)[1].lower()
        
    if file and file_extension == '.pdf':
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
                "file_type": "pdf",
                "summary": summary_data["summary"],
                "word_count": summary_data["word_count"],
                "original_word_count": summary_data["original_word_count"],
                "reduction_percentage": round((1 - (summary_data["word_count"] / max(1, summary_data["original_word_count"]))) * 100, 1)
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    elif file and file_extension in ['.xlsx', '.xls']:
        # Process the Excel file
        try:
            # Extract text
            extractor = ExcelExtractor()
            text = extractor.extract_text(file)
            metadata = extractor.get_metadata(file)
            
            # Reset file pointer for reading again
            file.seek(0)
            
            # Summarize text
            summarizer = PdfSummarizer()  # Reusing the same summarizer
            summary_ratio = float(request.form.get('ratio', 0.3))
            summary_data = summarizer.summarize(text, ratio=summary_ratio)
            
            return jsonify({
                "success": True,
                "file_type": "excel",
                "summary": summary_data["summary"],
                "word_count": summary_data["word_count"],
                "original_word_count": summary_data["original_word_count"],
                "reduction_percentage": round((1 - (summary_data["word_count"] / max(1, summary_data["original_word_count"]))) * 100, 1),
                "excel_metadata": {
                    "sheet_count": metadata["sheet_count"],
                    "total_rows": metadata["total_rows"],
                    "sheet_names": metadata["sheet_names"]
                }
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Only PDF and Excel files are allowed"}), 400
