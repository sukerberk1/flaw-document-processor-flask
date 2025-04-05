import os
import json
import docx
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from langchain_text_splitters import RecursiveCharacterTextSplitter

word_agent_bp = Blueprint('word_agent', __name__, url_prefix='/agents/word')

@word_agent_bp.route('/scan', methods=['POST'])
def scan_word():
    file_path = request.json.get('file_path')
    if not file_path:
        return jsonify({'error': 'No file path provided'}), 400
        
    # Make sure the file exists and is a Word document
    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
    if not os.path.exists(full_path):
        return jsonify({'error': 'File not found'}), 404
        
    if not file_path.lower().endswith(('.docx', '.doc')):
        return jsonify({'error': 'File is not a Word document'}), 400
    
    try:
        # Process the document
        document_data = process_word_document(full_path)
        
        # Convert to JSON string
        json_content = json.dumps(document_data, ensure_ascii=False, indent=2)
        
        # Create a simple summary
        if "error" in document_data:
            summary = document_data["error"]
        else:
            # Create a text-based summary for display
            summary = f"Word Document: {os.path.basename(file_path)}\n"
            summary += f"Paragraphs: {document_data['document_info']['paragraph_count']}\n"
            summary += f"Size: {document_data['document_info']['file_size_kb']:.2f} KB\n\n"
            
            # Add core properties if available
            if document_data["metadata"]:
                summary += "Document Properties:\n"
                for key, value in document_data["metadata"].items():
                    if value and value != "Not available":
                        summary += f"- {key.replace('_', ' ').title()}: {value}\n"
                summary += "\n"
            
            # Add text chunks count
            if "chunks" in document_data:
                summary += f"Text extracted and split into {len(document_data['chunks'])} chunks for processing.\n"
        
        # Format the summary with HTML breaks
        formatted_summary = summary.replace('\n', '<br>')
        
        return jsonify({
            'filename': os.path.basename(file_path),
            'summary': formatted_summary,
            'json_data': document_data
        })
    except Exception as e:
        print(f"Error processing Word document: {str(e)}")
        return jsonify({'error': f"Failed to process Word document: {str(e)}"}), 500

def process_word_document(file_path):
    """Process a Word document and return structured data with text chunks."""
    try:
        # Open the document
        doc = docx.Document(file_path)
        
        # Initialize document structure
        document_data = {
            "metadata": {},
            "document_info": {
                "paragraph_count": len(doc.paragraphs),
                "table_count": len(doc.tables),
                "section_count": len(doc.sections),
                "file_size_kb": os.path.getsize(file_path) / 1024,
                "file_name": os.path.basename(file_path)
            },
            "content": {
                "paragraphs": [],
                "tables": []
            }
        }
        
        # Extract core properties if available
        try:
            if hasattr(doc, 'core_properties'):
                props = doc.core_properties
                document_data["metadata"] = {
                    "title": props.title or "Not available",
                    "author": props.author or "Not available",
                    "subject": props.subject or "Not available",
                    "keywords": props.keywords or "Not available",
                    "category": props.category or "Not available",
                    "comments": props.comments or "Not available",
                    "created": str(props.created) if props.created else "Not available",
                    "modified": str(props.modified) if props.modified else "Not available",
                    "last_modified_by": props.last_modified_by or "Not available"
                }
        except Exception as e:
            document_data["metadata"] = {"error": f"Failed to extract metadata: {str(e)}"}
        
        # Extract paragraphs
        all_text = ""
        for i, para in enumerate(doc.paragraphs):
            text = para.text.strip()
            if text:  # Only add non-empty paragraphs
                document_data["content"]["paragraphs"].append({
                    "index": i,
                    "text": text,
                    "style": para.style.name if para.style else "Normal"
                })
                all_text += text + "\n\n"
        
        # Extract tables
        for i, table in enumerate(doc.tables):
            table_data = {
                "index": i,
                "rows": [],
                "row_count": len(table.rows),
                "column_count": len(table.columns) if table.rows else 0
            }
            
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    row_data.append(cell_text)
                    all_text += cell_text + " "
                table_data["rows"].append(row_data)
                all_text += "\n"
            
            document_data["content"]["tables"].append(table_data)
            all_text += "\n"
        
        # Use LangChain's RecursiveCharacterTextSplitter to chunk the text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Split the text into chunks
        if all_text.strip():
            chunks = text_splitter.split_text(all_text)
            document_data["chunks"] = chunks
        else:
            document_data["chunks"] = ["No text content found in document"]
        
        return document_data
        
    except Exception as e:
        print(f"Error processing Word document: {str(e)}")
        return {"error": f"Error processing Word document: {str(e)}"}