from flask import Blueprint, request, jsonify, current_app
import os
import json
from openai import OpenAI

# Create blueprint
main_agent_bp = Blueprint('main_agent', __name__, url_prefix='/agents/main')

# Initialize OpenAI client
client = OpenAI()

@main_agent_bp.route('/summarize', methods=['GET'])
def summarize_combined_data():
    """
    Reads the combined document data from memory and generates a summary using OpenAI API.
    """
    try:
        # Get the combined data from application variable
        combined_data = current_app.combined_document_data
        
        # Check if there's any data
        if not combined_data:
            return jsonify({
                'error': 'No combined data found. Please scan documents first.'
            }), 404
            
        # Prepare a more compact representation by extracting key information
        document_summary = {}
        total_docs = len(combined_data)
        
        for key, doc_data in combined_data.items():
            # Extract only essential fields to reduce token count
            doc_type = key.split('_')[0]  # pdf or word
            doc_name = key.split('_', 1)[1] if '_' in key else key
            
            # Create a compact summary for each document
            doc_summary = {
                "type": doc_type,
                "name": doc_name,
            }
            
            # Extract basic metadata depending on document type
            if doc_type == 'pdf' and isinstance(doc_data, dict):
                if 'metadata' in doc_data:
                    doc_summary['metadata'] = {
                        k: v for k, v in doc_data.get('metadata', {}).items() 
                        if k in ['title', 'author', 'subject', 'creator', 'producer']
                    }
                # Extract just document length or page count
                if 'page_count' in doc_data:
                    doc_summary['page_count'] = doc_data['page_count']
                
                # Extract just first few text chunks to get context
                if 'text' in doc_data and isinstance(doc_data['text'], str):
                    # Take just first 1000 chars
                    doc_summary['text_sample'] = doc_data['text'][:1000] + "..."
                
            elif doc_type == 'word' and isinstance(doc_data, dict):
                if 'metadata' in doc_data:
                    doc_summary['metadata'] = {
                        k: v for k, v in doc_data.get('metadata', {}).items() 
                        if k in ['title', 'author', 'comments', 'category']
                    }
                # Extract short text sample
                if 'text' in doc_data and isinstance(doc_data['text'], str):
                    # Take just first 1000 chars
                    doc_summary['text_sample'] = doc_data['text'][:1000] + "..."
            
            document_summary[key] = doc_summary
        
        # Create a compact overview of the documents
        compact_data = {
            "document_count": total_docs,
            "document_types": {
                "pdf": sum(1 for k in combined_data.keys() if k.startswith('pdf_')),
                "word": sum(1 for k in combined_data.keys() if k.startswith('word_')),
            },
            "documents": document_summary
        }
        
        # Convert the compact data to JSON
        compact_json = json.dumps(compact_data, indent=2)
        
        # Prepare system message for the API call
        system_message = """
        You are an expert document analyzer. Your task is to summarize the combined data from multiple documents.
        Provide a concise summary that highlights:
        1. How many and what types of documents were processed
        2. Key information found across the documents based on the text samples
        3. Any notable patterns or insights from the available metadata
        
        Keep your summary clear, professional, and under 500 words.
        """
        
        # Call OpenAI API to generate summary with reduced data
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Please summarize this combined document data: {compact_json}"}
            ],
            max_tokens=800,
            temperature=0.5
        )
        
        # Extract the summary from the API response
        summary = response.choices[0].message.content.strip()
        
        return jsonify({
            'summary': summary,
            'document_count': len(combined_data)
        })
        
    except Exception as e:
        # Log the error
        current_app.logger.error(f"Error generating summary: {str(e)}")
        return jsonify({
            'error': f"Error generating summary: {str(e)}"
        }), 500