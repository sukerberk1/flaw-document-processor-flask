import PyPDF2
from typing import List

class PdfExtractor:
    """Extracts text content from PDF files."""
    
    def extract_text(self, pdf_file) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_file: File-like object containing PDF data
            
        Returns:
            str: Extracted text content
        """
        text = ""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
