import os
import json
import fitz  # PyMuPDF
from PyPDF2 import PdfReader
from openai import OpenAI
from dotenv import load_dotenv
from app.features.pdf_processor.models import PDFDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

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
        """Read a PDF file and extract its text content using PyMuPDF and return structured data."""
        try:
            doc = fitz.open(file_path)
            
            # Initialize structure for the document
            document_data = {
                "metadata": {},
                "document_info": {
                    "page_count": len(doc),
                    "file_size_kb": os.path.getsize(file_path) / 1024,
                    "file_name": os.path.basename(file_path)
                },
                "pages": []
            }
            
            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                
                # Extract images if available
                image_list = page.get_images(full=True)
                images = []
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    if base_image:
                        images.append({
                            "index": img_index,
                            "width": base_image["width"],
                            "height": base_image["height"],
                            "type": base_image["ext"]
                        })
                
                # Add page data
                document_data["pages"].append({
                    "page_number": page_num + 1,
                    "text": page_text,
                    "images": images
                })
            
            # Extract metadata
            metadata = doc.metadata
            if metadata:
                document_data["metadata"] = {
                    "title": metadata.get("title", "Not available"),
                    "author": metadata.get("author", "Not available"),
                    "subject": metadata.get("subject", "Not available"),
                    "keywords": metadata.get("keywords", "Not available"),
                    "creator": metadata.get("creator", "Not available"),
                    "producer": metadata.get("producer", "Not available"),
                    "creation_date": metadata.get("creationDate", "Not available"),
                    "modification_date": metadata.get("modDate", "Not available")
                }
                
            doc.close()
            return document_data
            
        except Exception as e:
            print(f"Error reading PDF with PyMuPDF: {str(e)}")
            return {"error": f"Error reading PDF: {str(e)}"}
    
    def read_pdf_with_chunking(self, file_path):
        """Read a PDF file, using LangChain's RecursiveCharacterTextSplitter for chunking."""
        try:
            # First get the structured data
            document_data = self.read_pdf_pymupdf(file_path)
            
            # If there was an error, fall back to PyPDF2
            if "error" in document_data:
                try:
                    # Fallback to PyPDF2
                    reader = PdfReader(file_path)
                    document_data = {
                        "metadata": {},
                        "document_info": {
                            "page_count": len(reader.pages),
                            "file_size_kb": os.path.getsize(file_path) / 1024,
                            "file_name": os.path.basename(file_path)
                        },
                        "pages": []
                    }
                    
                    for page_num, page in enumerate(reader.pages):
                        page_text = page.extract_text() or "No text could be extracted from this page."
                        document_data["pages"].append({
                            "page_number": page_num + 1,
                            "text": page_text,
                            "images": []
                        })
                    
                    # Extract metadata if available
                    if reader.metadata:
                        document_data["metadata"] = {
                            "title": reader.metadata.get("/Title", "Not available"),
                            "author": reader.metadata.get("/Author", "Not available"),
                            "subject": reader.metadata.get("/Subject", "Not available"),
                            "keywords": reader.metadata.get("/Keywords", "Not available"),
                            "creator": reader.metadata.get("/Creator", "Not available"),
                            "producer": reader.metadata.get("/Producer", "Not available")
                        }
                except Exception as e:
                    print(f"Error reading PDF with PyPDF2: {str(e)}")
                    return {"error": f"Failed to read PDF with both methods: {str(e)}"}
            
            # Collect all the text from the document
            all_text = ""
            for page in document_data["pages"]:
                all_text += f"Page {page['page_number']}:\n{page['text']}\n\n"
            
            # Use LangChain's RecursiveCharacterTextSplitter to chunk the text
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            # Split the text into chunks
            chunks = text_splitter.split_text(all_text)
            
            # Add chunks to the document data
            document_data["chunks"] = chunks
            
            return document_data
            
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            return {"error": f"Error processing PDF: {str(e)}"}
    
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
        """Process a PDF file and return a PDFDocument with extracted text as JSON."""
        filename = os.path.basename(file_path)
        document_data = self.read_pdf_with_chunking(file_path)
        
        # Convert to JSON string for storage
        json_content = json.dumps(document_data, ensure_ascii=False, indent=2)
        
        # Create a formatted summary for display
        if "error" in document_data:
            summary = document_data["error"]
        else:
            # Create a simple text-based summary for display
            summary = f"PDF Document: {filename}\n"
            summary += f"Pages: {document_data['document_info']['page_count']}\n"
            summary += f"Size: {document_data['document_info']['file_size_kb']:.2f} KB\n\n"
            
            # Add metadata
            if document_data["metadata"]:
                summary += "Metadata:\n"
                for key, value in document_data["metadata"].items():
                    if value and value != "Not available":
                        summary += f"- {key.replace('_', ' ').title()}: {value}\n"
                summary += "\n"
            
            # Add text chunks count
            if "chunks" in document_data:
                summary += f"Text extracted and split into {len(document_data['chunks'])} chunks for processing.\n"
        
        return PDFDocument(filename, json_content, summary) 
