import os
import json
import time
import fitz  # PyMuPDF
import base64
import re
from io import BytesIO
from PIL import Image
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from langchain_text_splitters import RecursiveCharacterTextSplitter

pdf_agent_bp = Blueprint('pdf_agent', __name__, url_prefix='/agents/pdf')

def extract_text_from_page(page):
    """Extract text from a page with layout preservation."""
    text = page.get_text("text")
    if not text.strip():
        # Try extracting as raw text if structured extraction fails
        text = page.get_text("rawdict")
        if isinstance(text, dict) and "blocks" in text:
            all_text = []
            for block in text["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        if "spans" in line:
                            for span in line["spans"]:
                                if "text" in span:
                                    all_text.append(span["text"])
            text = " ".join(all_text)
    return text

def get_page_dimensions(page):
    """Get page dimensions in points and convert to inches and mm."""
    rect = page.rect
    width_pt, height_pt = rect.width, rect.height
    # Convert to inches (1 pt = 1/72 inch)
    width_in, height_in = width_pt / 72, height_pt / 72
    # Convert to mm (1 inch = 25.4 mm)
    width_mm, height_mm = width_in * 25.4, height_in * 25.4
    
    return {
        "width_pt": round(width_pt, 2),
        "height_pt": round(height_pt, 2),
        "width_in": round(width_in, 2),
        "height_in": round(height_in, 2),
        "width_mm": round(width_mm, 2),
        "height_mm": round(height_mm, 2)
    }

def extract_page_images(page, max_images=5, max_size=800):
    """Extract images from the page, limit count and resize if needed."""
    images = []
    image_count = 0
    
    for img_index, img in enumerate(page.get_images(full=True)):
        if image_count >= max_images:
            break
            
        try:
            xref = img[0]
            base_image = page.parent.extract_image(xref)
            
            if base_image:
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Open the image with PIL
                pil_image = Image.open(BytesIO(image_bytes))
                
                # Resize if image is too large (preserving aspect ratio)
                width, height = pil_image.size
                if width > max_size or height > max_size:
                    if width > height:
                        new_width = max_size
                        new_height = int(height * max_size / width)
                    else:
                        new_height = max_size
                        new_width = int(width * max_size / height)
                    pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)
                
                # Convert to base64 for JSON
                buffered = BytesIO()
                pil_image.save(buffered, format=image_ext.upper())
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                # Add image data
                image_data = {
                    "index": img_index,
                    "width": width,
                    "height": height,
                    "format": image_ext,
                    "size_kb": len(image_bytes) / 1024,
                    "base64": f"data:image/{image_ext};base64,{img_base64}"
                }
                
                images.append(image_data)
                image_count += 1
                
        except Exception as e:
            print(f"Error extracting image {img_index}: {str(e)}")
            continue
            
    return images

def extract_links(page):
    """Extract hyperlinks from the page."""
    links = []
    for link in page.get_links():
        link_data = {"type": link["kind"]}
        
        if "uri" in link and link["uri"]:
            link_data["uri"] = link["uri"]
        elif "page" in link:
            link_data["page"] = link["page"]
            
        if "from" in link:
            # Get rectangle coordinates
            rect = link["from"]
            link_data["rect"] = {
                "x0": rect.x0,
                "y0": rect.y0,
                "x1": rect.x1,
                "y1": rect.y1
            }
            
        links.append(link_data)
    return links

def extract_form_fields(page):
    """Extract form fields from the page."""
    fields = []
    widgets = page.widgets()
    
    if widgets:
        for i, widget in enumerate(widgets):
            field = {
                "index": i,
                "field_type": widget.field_type,
                "field_name": widget.field_name,
                "field_value": widget.field_value,
                "rect": {
                    "x0": widget.rect.x0,
                    "y0": widget.rect.y0,
                    "x1": widget.rect.x1,
                    "y1": widget.rect.y1
                }
            }
            fields.append(field)
            
    return fields

def extract_annotations(page):
    """Extract annotations from the page."""
    annotations = []
    
    for annot in page.annots():
        annot_data = {
            "type": annot.type[1],
            "rect": {
                "x0": annot.rect.x0,
                "y0": annot.rect.y0,
                "x1": annot.rect.x1,
                "y1": annot.rect.y1
            }
        }
        
        if annot.info:
            if annot.info.get("content"):
                annot_data["content"] = annot.info["content"]
            if annot.info.get("title"):
                annot_data["author"] = annot.info["title"]
            if annot.info.get("creationDate"):
                annot_data["created"] = str(annot.info["creationDate"])
                
        annotations.append(annot_data)
        
    return annotations

def extract_tables(page, min_rows=2, min_cols=2):
    """
    Attempt to detect tables on the page by analyzing the text layout.
    This is a basic implementation and may not work for all PDFs.
    """
    tables = []
    
    # Get blocks that might represent tables
    blocks = page.get_text("dict")["blocks"]
    for block_idx, block in enumerate(blocks):
        if "lines" not in block:
            continue
            
        # Look for consistent line patterns that might indicate a table
        lines = block["lines"]
        if len(lines) < min_rows:
            continue
            
        # Check if lines have similar y-positions and consistent spacing
        potential_table = []
        for line_idx, line in enumerate(lines):
            if "spans" not in line:
                continue
                
            # Extract cells from spans
            row = []
            for span in line["spans"]:
                if "text" in span:
                    row.append(span["text"])
                    
            if len(row) >= min_cols:
                potential_table.append(row)
                
        # If we have enough rows with enough columns, consider it a table
        if len(potential_table) >= min_rows:
            tables.append({
                "block_index": block_idx,
                "rows": potential_table,
                "row_count": len(potential_table),
                "estimated_col_count": max(len(row) for row in potential_table)
            })
            
    return tables

def process_pdf(file_path):
    """
    Process a PDF file to extract comprehensive information including:
    - Document metadata
    - Page count and dimensions
    - Full text content with layout preservation
    - Images (limited count with resizing)
    - Links and annotations
    - Form fields
    - Detected tables
    - Text chunks for further processing
    """
    document_data = {
        "filename": os.path.basename(file_path),
        "file_size_kb": os.path.getsize(file_path) / 1024,
        "metadata": {},
        "pages": [],
        "text_content": "",
        "has_form": False,
        "has_images": False,
        "has_links": False
    }
    
    try:
        # Open the PDF
        pdf = fitz.open(file_path)
        
        # Extract document metadata
        metadata = pdf.metadata
        if metadata:
            document_data["metadata"] = {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "keywords": metadata.get("keywords", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", "")
            }
            
        # Check if it's a PDF form
        form_fields = []
        for page in pdf:
            if page.widgets():
                document_data["has_form"] = True
                form_fields.extend(page.widgets())
        
        document_data["form_field_count"] = len(form_fields)
            
        # Extract page information
        all_text = []
        total_images = 0
        total_links = 0
        total_annotations = 0
        
        for page_idx, page in enumerate(pdf):
            page_text = extract_text_from_page(page)
            all_text.append(page_text)
            
            # Extract page images
            page_images = extract_page_images(page)
            has_images = len(page_images) > 0
            if has_images:
                document_data["has_images"] = True
                total_images += len(page_images)
                
            # Extract links
            page_links = extract_links(page)
            has_links = len(page_links) > 0
            if has_links:
                document_data["has_links"] = True
                total_links += len(page_links)
                
            # Extract form fields
            page_fields = extract_form_fields(page)
                
            # Extract annotations
            page_annotations = extract_annotations(page)
            total_annotations += len(page_annotations)
                
            # Try to detect tables
            page_tables = extract_tables(page)
                
            # Add page data
            page_data = {
                "page_number": page_idx + 1,
                "dimensions": get_page_dimensions(page),
                "rotation": page.rotation,
                "text_length": len(page_text),
                "has_images": has_images,
                "image_count": len(page_images),
                "has_links": has_links,
                "link_count": len(page_links),
                "has_form_fields": len(page_fields) > 0,
                "form_field_count": len(page_fields),
                "has_annotations": len(page_annotations) > 0,
                "annotation_count": len(page_annotations),
                "has_tables": len(page_tables) > 0,
                "detected_table_count": len(page_tables)
            }
            
            # Add detailed data (can be large)
            if len(page_text) > 0:
                page_data["text"] = page_text
                
            if has_images:
                page_data["images"] = page_images
                
            if has_links:
                page_data["links"] = page_links
                
            if len(page_fields) > 0:
                page_data["form_fields"] = page_fields
                
            if len(page_annotations) > 0:
                page_data["annotations"] = page_annotations
                
            if len(page_tables) > 0:
                page_data["tables"] = page_tables
                
            document_data["pages"].append(page_data)
            
        # Add document summary
        document_data["page_count"] = len(pdf)
        document_data["text_content"] = "\n\n".join(all_text)
        document_data["total_image_count"] = total_images
        document_data["total_link_count"] = total_links
        document_data["total_annotation_count"] = total_annotations
        
        # Extract TOC/bookmarks if available
        toc = pdf.get_toc()
        if toc:
            document_data["has_toc"] = True
            document_data["toc"] = []
            for item in toc:
                document_data["toc"].append({
                    "level": item[0],
                    "title": item[1],
                    "page": item[2]
                })
        else:
            document_data["has_toc"] = False
            
        # Split text into chunks for further processing
        if document_data["text_content"]:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1200,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            chunks = text_splitter.split_text(document_data["text_content"])
            document_data["chunks"] = chunks
            document_data["chunk_count"] = len(chunks)
            
        # Create a summary of the document
        summary_lines = [
            f"PDF Document: {document_data['filename']}",
            f"Pages: {document_data['page_count']}",
            f"Size: {document_data['file_size_kb']:.2f} KB"
        ]
        
        if document_data["metadata"].get("title"):
            summary_lines.append(f"Title: {document_data['metadata']['title']}")
            
        if document_data["metadata"].get("author"):
            summary_lines.append(f"Author: {document_data['metadata']['author']}")
            
        if document_data["has_toc"]:
            summary_lines.append(f"Table of Contents: Yes ({len(document_data['toc'])} entries)")
            
        if document_data["has_images"]:
            summary_lines.append(f"Images: {document_data['total_image_count']}")
            
        if document_data["has_form"]:
            summary_lines.append(f"Form Fields: {document_data['form_field_count']}")
            
        if document_data["has_links"]:
            summary_lines.append(f"Hyperlinks: {document_data['total_link_count']}")
            
        word_count = len(re.findall(r'\w+', document_data["text_content"]))
        summary_lines.append(f"Word Count: ~{word_count}")
        
        document_data["summary"] = "\n".join(summary_lines)
            
        return document_data
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error in PDF processing: {str(e)}\n{error_traceback}")
        raise

@pdf_agent_bp.route('/scan', methods=['POST'])
def scan_pdf():
    """
    Scan a PDF file and extract its content using PyMuPDF.
    
    This endpoint accepts a file path relative to the upload folder
    and processes the PDF to extract comprehensive information:
    - Document metadata and structure
    - Page content including text, images, links
    - Form fields and annotations
    - Tables (basic detection)
    - Text chunking for further processing
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
        
        # Process the PDF with PyMuPDF
        pdf_data = process_pdf(full_path)
        
        # Add processing metadata
        processing_time = time.time() - start_time
        pdf_data["processing_info"] = {
            "processing_time_seconds": round(processing_time, 2),
            "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "extraction_method": "PyMuPDF"
        }
        
        # Format the summary for display with HTML line breaks
        formatted_summary = pdf_data["summary"].replace('\n', '<br>')
        
        # Log completion
        print(f"Completed PDF processing: {file_path} in {time.time() - start_time:.2f} seconds")
        
        return jsonify({
            'filename': os.path.basename(file_path),
            'summary': formatted_summary,
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
            'error_type': type(e).__name__,
            'traceback': error_traceback
        }), 500
