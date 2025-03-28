import os
from PyPDF2 import PdfReader
from openai import OpenAI
from dotenv import load_dotenv
from app.features.pdf_processor.models import PDFDocument

# Load environment variables
load_dotenv(override=True)  # Add override=True to force reload

class PDFProcessorService:
    """Service for processing PDFs and generating summaries."""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        print(f"Loading OpenAI API key: {'Found' if api_key else 'Not found'}")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=api_key)
    
    def read_pdf(self, file_path):
        """Read a PDF file and extract its text content."""
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    def generate_summary(self, text, max_length=500):
        """Generate a summary of the text using OpenAI's API."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise summaries of text."},
                    {"role": "user", "content": f"Please provide a concise summary of the following text (max {max_length} characters):\n\n{text}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def process_pdf(self, file_path):
        """Process a PDF file and return a PDFDocument with summary."""
        filename = os.path.basename(file_path)
        content = self.read_pdf(file_path)
        summary = self.generate_summary(content)
        return PDFDocument(filename, content, summary) 