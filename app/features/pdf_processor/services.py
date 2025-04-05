import os
import json
import tempfile
import fitz  # PyMuPDF
from PyPDF2 import PdfReader
from openai import OpenAI
from dotenv import load_dotenv
from app.features.pdf_processor.models import PDFDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

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
    
    def perform_ocr_on_page(self, image):
        """Perform OCR on a single image using Tesseract with enhanced settings."""
        try:
            # Preprocessing the image for better OCR results
            # Convert to grayscale if it's not already
            if image.mode != 'L':
                image = image.convert('L')
                
            # Optional: Apply some image enhancement techniques
            # 1. Increase contrast
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)  # Increase contrast by 50%
            
            # 2. Apply threshold to make text more distinct
            from PIL import ImageFilter
            image = image.filter(ImageFilter.SHARPEN)
            
            # Use pytesseract with optimized configuration
            custom_config = r'--oem 3 --psm 6 -l eng'  # OCR Engine Mode 3 (default) + Page Segmentation Mode 6 (assume single uniform block of text)
            text = pytesseract.image_to_string(image, config=custom_config)
            return text
        except Exception as e:
            print(f"OCR error: {str(e)}")
            return ""

    def extract_text_with_ocr(self, file_path):
        """Extract text from PDF using OCR with enhanced image quality."""
        try:
            # Convert PDF pages to images with higher DPI for better OCR accuracy
            # Higher DPI means more detailed images, which can improve OCR results
            images = convert_from_path(
                file_path,
                dpi=300,  # Higher DPI for better quality
                thread_count=4,  # Use multiple threads for faster processing
                poppler_path=None  # Set this to your poppler path if needed
            )
            
            text_results = []
            total_pages = len(images)
            
            print(f"Processing {total_pages} pages with OCR")
            
            for i, image in enumerate(images):
                print(f"OCR processing page {i+1}/{total_pages}")
                # Perform OCR on each page
                page_text = self.perform_ocr_on_page(image)
                text_results.append((i + 1, page_text))
                
                # Basic quality check - if we got very little text, try with different settings
                if len(page_text.strip()) < 50:
                    print(f"Low text content detected on page {i+1}, trying alternate OCR settings")
                    # Try with alternative settings - sometimes different settings work better
                    # 1. Try with different page segmentation mode
                    custom_config = r'--oem 3 --psm 3 -l eng'  # PSM 3 - Fully automatic page segmentation
                    alt_text = pytesseract.image_to_string(image, config=custom_config)
                    
                    # If the alternative gave better results, use that instead
                    if len(alt_text.strip()) > len(page_text.strip()):
                        print(f"Using alternate OCR text for page {i+1} (got {len(alt_text.strip())} chars vs {len(page_text.strip())})")
                        text_results[-1] = (i + 1, alt_text)
            
            return text_results
        except Exception as e:
            print(f"PDF to image conversion error: {str(e)}")
            return []
            
    def read_pdf_pymupdf(self, file_path):
        """Read a PDF file and extract its text content using PyMuPDF and OCR for images."""
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
                "pages": [],
                "ocr_text": []
            }
            
            # Extract text from each page
            has_sparse_text = False
            total_text_length = 0
            pages_with_little_text = 0
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                total_text_length += len(page_text)
                
                if len(page_text.strip()) < 100:  # Consider a page with less than 100 chars as potentially needing OCR
                    pages_with_little_text += 1
                
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
            
            # Enhanced OCR detection logic
            # Calculate average text per page
            avg_text_per_page = total_text_length / len(doc) if len(doc) > 0 else 0
            
            # Analyze image count and size to determine if document is image-heavy
            total_images = sum(len(page.get("images", [])) for page in document_data["pages"])
            image_heavy = total_images > len(doc) * 2  # More than 2 images per page on average
            
            # Check if we need to perform OCR based on multiple criteria
            needs_ocr = False
            ocr_reason = []
            
            if total_text_length < 1000:
                needs_ocr = True
                ocr_reason.append(f"Very little text detected ({total_text_length} chars)")
            
            if pages_with_little_text / len(doc) > 0.3:
                needs_ocr = True
                ocr_reason.append(f"{pages_with_little_text} out of {len(doc)} pages have little text")
            
            if avg_text_per_page < 200:
                needs_ocr = True
                ocr_reason.append(f"Low average text per page ({avg_text_per_page:.1f} chars)")
            
            if image_heavy:
                needs_ocr = True
                ocr_reason.append(f"Image-heavy document ({total_images} images in {len(doc)} pages)")
            
            # Add whether OCR was used and why to the document data
            document_data["ocr_detection"] = {
                "needs_ocr": needs_ocr,
                "total_text_length": total_text_length,
                "avg_text_per_page": avg_text_per_page,
                "pages_with_little_text": pages_with_little_text,
                "total_pages": len(doc),
                "total_images": total_images,
                "reasons": ocr_reason if needs_ocr else []
            }
            
            if needs_ocr:
                print(f"PDF appears to be image-heavy or scanned: {', '.join(ocr_reason)}. Performing OCR on {file_path}")
                
                # Extract text using OCR
                ocr_results = self.extract_text_with_ocr(file_path)
                document_data["used_ocr"] = True
                
                # Add OCR text to the document data
                document_data["ocr_text"] = []
                for page_num, ocr_text in ocr_results:
                    document_data["ocr_text"].append({
                        "page_number": page_num,
                        "text": ocr_text
                    })
                    
                    # Merge OCR text with existing page text if the page exists
                    for page in document_data["pages"]:
                        if page["page_number"] == page_num:
                            # Compare text quality - not just length, but also content
                            original_text = page["text"].strip()
                            ocr_text = ocr_text.strip()
                            
                            # Count actual words rather than just length
                            original_word_count = len([w for w in original_text.split() if len(w) > 1])
                            ocr_word_count = len([w for w in ocr_text.split() if len(w) > 1])
                            
                            # If OCR produced significantly more words or original text is very short
                            if ocr_word_count > original_word_count * 1.2 or len(original_text) < 100:
                                page["text"] = ocr_text
                                page["text_source"] = "ocr"
                                page["text_comparison"] = {
                                    "original_chars": len(original_text),
                                    "ocr_chars": len(ocr_text),
                                    "original_words": original_word_count,
                                    "ocr_words": ocr_word_count
                                }
                            else:
                                page["text_source"] = "pdf"
                                page["text_comparison"] = {
                                    "original_chars": len(original_text),
                                    "ocr_chars": len(ocr_text),
                                    "original_words": original_word_count,
                                    "ocr_words": ocr_word_count,
                                    "kept_original": True
                                }
            else:
                document_data["used_ocr"] = False
                print(f"PDF has sufficient text content, skipping OCR")
            
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
            
            # Collect all the text from the document with improved handling for OCR results
            all_text = ""
            
            # Intelligently combine text sources based on which is better for each page
            has_ocr = "ocr_text" in document_data and document_data["ocr_text"]
            has_used_ocr = document_data.get("used_ocr", False)
            
            # Set up page tracking to avoid duplication
            page_texts = {}
            
            # Process pages in order, taking the best text source for each
            for page in document_data["pages"]:
                page_num = page["page_number"]
                text = page["text"]
                source = page.get("text_source", "pdf")
                
                # Store the best text version for each page
                page_texts[page_num] = {
                    "text": text,
                    "source": source 
                }
            
            # Now build the combined text in page order
            if has_used_ocr:
                all_text += "# DOCUMENT TEXT (with OCR enhancement)\n\n"
            else:
                all_text += "# DOCUMENT TEXT\n\n"
                
            for page_num in sorted(page_texts.keys()):
                info = page_texts[page_num]
                
                # Add the page text with source information
                source_label = "OCR" if info["source"] == "ocr" else "PDF"
                all_text += f"## Page {page_num} ({source_label}):\n\n{info['text']}\n\n"
                
                # Add comparison info if available (only for diagnostics, will be chunked out)
                for page in document_data["pages"]:
                    if page["page_number"] == page_num and page.get("text_comparison"):
                        comparison = page["text_comparison"]
                        if comparison.get("kept_original", False):
                            all_text += f"[Note: Original PDF text used ({comparison['original_words']} words) instead of OCR ({comparison['ocr_words']} words)]\n\n"
                        elif info["source"] == "ocr":
                            all_text += f"[Note: OCR improved text from {comparison['original_words']} to {comparison['ocr_words']} words]\n\n"
            
            # Add a separate metadata section that will likely be in its own chunk
            all_text += "# DOCUMENT METADATA\n\n"
            
            if document_data["metadata"]:
                for key, value in document_data["metadata"].items():
                    if value and value != "Not available":
                        all_text += f"{key.replace('_', ' ').title()}: {value}\n"
            
            # Use LangChain's RecursiveCharacterTextSplitter to chunk the text with optimized settings
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1200,  # Slightly larger chunks for more context
                chunk_overlap=250,  # More overlap to ensure continuity
                length_function=len,
                separators=["\n\n", "\n", ".", " ", ""]
            )
            
            # Split the text into chunks
            if all_text.strip():
                chunks = text_splitter.split_text(all_text)
                document_data["chunks"] = chunks
            else:
                document_data["chunks"] = ["No text could be extracted from this PDF"]
            
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
            # Create a more detailed text-based summary for display with OCR information
            summary = f"PDF Document: {filename}\n"
            summary += f"Pages: {document_data['document_info']['page_count']}\n"
            summary += f"Size: {document_data['document_info']['file_size_kb']:.2f} KB\n\n"
            
            # Add OCR processing information if available
            if document_data.get("used_ocr", False):
                summary += "OCR Processing:\n"
                summary += "✓ Image-heavy or scanned document detected\n"
                
                # Add reasons for OCR if available
                if document_data.get("ocr_detection", {}).get("reasons"):
                    summary += "OCR was used because:\n"
                    for reason in document_data["ocr_detection"]["reasons"]:
                        summary += f"- {reason}\n"
                
                # Add statistics about OCR text improvement
                total_orig_words = 0
                total_ocr_words = 0
                improved_pages = 0
                
                for page in document_data["pages"]:
                    if page.get("text_comparison"):
                        total_orig_words += page["text_comparison"].get("original_words", 0)
                        total_ocr_words += page["text_comparison"].get("ocr_words", 0)
                        if page.get("text_source") == "ocr":
                            improved_pages += 1
                
                if improved_pages > 0:
                    summary += f"OCR improved text extraction on {improved_pages} out of {document_data['document_info']['page_count']} pages\n"
                    summary += f"Words extracted: {total_ocr_words} (vs. {total_orig_words} from standard extraction)\n"
                
                summary += "\n"
            elif "used_ocr" in document_data:
                summary += "PDF analysis: Document has sufficient text content, OCR not needed\n\n"
            
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
