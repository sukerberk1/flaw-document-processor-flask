from flask import Blueprint, request, jsonify
from .services import ExcelProcessorService

excel_processor_bp = Blueprint('excel_processor', __name__, url_prefix='/excel-processor')

service = ExcelProcessorService()

ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@excel_processor_bp.route('/')
def index():
    """Render the index page for Excel processing."""
    return "Excel Processor Home"

@excel_processor_bp.route('/upload', methods=['POST'])
def upload_excel():
    """Handle Excel file upload and processing."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        summary = service.process_excel(file)
        return jsonify({'summary': summary})

    return jsonify({'error': 'Invalid file type'}), 400
