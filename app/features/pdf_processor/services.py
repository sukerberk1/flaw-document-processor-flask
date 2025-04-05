import os
import fitz  # PyMuPDF
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
            print("WARNING: OPENAI_API_KEY environment variable is not set")
            # We'll initialize without the key, but operations will fail
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
    
    def read_pdf_pymupdf(self, file_path):
        """Read a PDF file and extract its text content using PyMuPDF."""
        try:
            doc = fitz.open(file_path)
            text = ""
            
            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
            
            # Extract metadata
            metadata = doc.metadata
            if metadata:
                text = f"--- PDF Metadata ---\n" + \
                       f"Title: {metadata.get('title', 'Not available')}\n" + \
                       f"Author: {metadata.get('author', 'Not available')}\n" + \
                       f"Subject: {metadata.get('subject', 'Not available')}\n" + \
                       f"Keywords: {metadata.get('keywords', 'Not available')}\n" + \
                       f"Creator: {metadata.get('creator', 'Not available')}\n" + \
                       f"Producer: {metadata.get('producer', 'Not available')}\n" + \
                       f"Creation Date: {metadata.get('creationDate', 'Not available')}\n" + \
                       f"Modification Date: {metadata.get('modDate', 'Not available')}\n\n" + text
            
            # Add document info
            text = f"--- Document Information ---\n" + \
                   f"Page Count: {len(doc)}\n" + \
                   f"File Size: {os.path.getsize(file_path) / 1024:.2f} KB\n\n" + text
            
            if not text.strip():
                return "No readable text found in the PDF. The document might be scanned or contain only images."
                
            doc.close()
            return text
            
        except Exception as e:
            print(f"Error reading PDF with PyMuPDF: {str(e)}")
            return f"Error reading PDF: {str(e)}"
    
    def read_pdf(self, file_path):
        """Read a PDF file using PyMuPDF, fallback to PyPDF2 if needed."""
        try:
            # First try with PyMuPDF for better extraction
            return self.read_pdf_pymupdf(file_path)
        except Exception as pymupdf_error:
            print(f"PyMuPDF error, trying PyPDF2: {str(pymupdf_error)}")
            try:
                # Fallback to PyPDF2
                reader = PdfReader(file_path)
                text = ""
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:  # Only add if text was successfully extracted
                        text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                
                if not text.strip():
                    return "No readable text found in the PDF. The document might be scanned or contain only images."
                    
                return text
            except Exception as e:
                print(f"Error reading PDF with PyPDF2: {str(e)}")
                return f"Error reading PDF: {str(e)}"
    
    def generate_summary(self, text, max_length=500):
        """Generate a summary of the text using OpenAI's API."""
        if not self.client:
            return "Error: OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable."
            
        # Limit text length to avoid token limits
        max_text_length = 15000  # Approximately 4000 tokens
        if len(text) > max_text_length:
            text = text[:max_text_length] + "... [text truncated due to length]"
            
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
            print(f"OpenAI API error: {str(e)}")
            return f"Error generating summary: {str(e)}"
    
    def process_pdf(self, file_path):
        """Process a PDF file and return a PDFDocument with extracted text."""
        filename = os.path.basename(file_path)
        content = self.read_pdf(file_path)
        # For the agent, we'll just return the extracted text without summarizing
        return PDFDocument(filename, content, content) 
