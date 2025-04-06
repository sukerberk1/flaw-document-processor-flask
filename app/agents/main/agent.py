from flask import Blueprint, request, jsonify, current_app
import os
import json
import tiktoken
from openai import OpenAI

# Create blueprint
main_agent_bp = Blueprint('main_agent', __name__, url_prefix='/agents/main')

# Initialize OpenAI client
client = OpenAI()

# Initialize tokenizer for gpt-3.5-turbo
tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")

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
            
        # Function to count tokens accurately using tiktoken
        def count_tokens(text):
            if not text:
                return 0
            # Convert to string if not already
            if not isinstance(text, str):
                text = str(text)
            return len(tokenizer.encode(text))
        
        # Function to chunk text into smaller pieces with a maximum token count
        def chunk_text(text, max_tokens=300):
            if not text or count_tokens(text) <= max_tokens:
                return text
                
            # For lists, process each item
            if isinstance(text, list):
                result = []
                for item in text:
                    if isinstance(item, str):
                        # Process string items
                        chunks = chunk_text(item, max_tokens)
                        if isinstance(chunks, list):
                            result.extend(chunks)
                        else:
                            result.append(chunks)
                    else:
                        # Non-string items just get added
                        result.append(item)
                return result
            
            # If it's a string, split it
            if not isinstance(text, str):
                return text
                
            # Use sentence-aware splitting for better context preservation
            tokens = tokenizer.encode(text)
            if len(tokens) <= max_tokens:
                return text
                
            # Split into sentences and then group them into chunks
            import re
            sentences = re.split(r'(?<=[.!?])\s+', text)
            chunks = []
            current_chunk = ""
            current_tokens = 0
            
            for sentence in sentences:
                sentence_tokens = count_tokens(sentence)
                
                # If a single sentence exceeds token limit, split at word boundaries
                if sentence_tokens > max_tokens:
                    words = sentence.split()
                    temp_chunk = ""
                    temp_tokens = 0
                    
                    for word in words:
                        word_tokens = count_tokens(word + " ")
                        if temp_tokens + word_tokens > max_tokens:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip())
                            temp_chunk = word + " "
                            temp_tokens = word_tokens
                        else:
                            temp_chunk += word + " "
                            temp_tokens += word_tokens
                    
                    if temp_chunk:
                        if current_tokens + temp_tokens <= max_tokens:
                            current_chunk += temp_chunk
                            current_tokens += temp_tokens
                        else:
                            chunks.append(current_chunk.strip())
                            current_chunk = temp_chunk
                            current_tokens = temp_tokens
                    continue
                
                # Try to add the sentence to the current chunk
                if current_tokens + sentence_tokens <= max_tokens:
                    current_chunk += sentence + " "
                    current_tokens += sentence_tokens
                else:
                    # Finish the current chunk and start a new one
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + " "
                    current_tokens = sentence_tokens
            
            # Add the last chunk if there is one
            if current_chunk:
                chunks.append(current_chunk.strip())
                
            return chunks
        
        # Function to optimize a document for LLM processing
        def optimize_for_llm(doc_data, doc_type):
            # Create a optimized structure focused on semantic understanding
            optimized = {
                "document_type": doc_type,
                "metadata": {},
                "content": []
            }
            
            # Extract metadata based on document type
            metadata_keys = ['title', 'author', 'subject', 'creator', 'producer', 'comments', 'category', 'keywords']
            if isinstance(doc_data, dict) and 'metadata' in doc_data:
                optimized['metadata'] = {
                    k: v for k, v in doc_data.get('metadata', {}).items() 
                    if k in metadata_keys and v
                }
            
            # Extract document statistics
            if doc_type == 'pdf':
                if 'page_count' in doc_data:
                    optimized['page_count'] = doc_data['page_count']
                if 'total_image_count' in doc_data:
                    optimized['images'] = doc_data['total_image_count']
                if 'has_toc' in doc_data and doc_data['has_toc']:
                    optimized['has_table_of_contents'] = True
            elif doc_type == 'word':
                if 'document_info' in doc_data:
                    info = doc_data['document_info']
                    if 'paragraph_count' in info:
                        optimized['paragraph_count'] = info['paragraph_count']
                    if 'table_count' in info:
                        optimized['table_count'] = info['table_count']
                    if 'estimated_word_count' in info:
                        optimized['word_count'] = info['estimated_word_count']
            
            # Extract and chunk text content
            text_content = None
            
            # Try different text fields based on document structure
            if 'text' in doc_data:
                text_content = doc_data['text']
            elif 'text_content' in doc_data:
                text_content = doc_data['text_content']
            elif 'chunks' in doc_data and isinstance(doc_data['chunks'], list):
                text_content = "\n\n".join(doc_data['chunks'])
            
            # If we have text content, chunk it and add to the optimized structure
            if text_content:
                # Chunk the text content
                chunked_content = chunk_text(text_content)
                
                # Add the chunked content to the optimized structure
                if isinstance(chunked_content, list):
                    optimized['content'] = chunked_content
                else:
                    optimized['content'] = [chunked_content]
            
            return optimized
        
        # Process all documents and create optimized summaries
        processed_docs = {}
        total_docs = len(combined_data)
        
        for key, doc_data in combined_data.items():
            # Extract document type
            doc_type = key.split('_')[0]  # pdf or word
            doc_name = key.split('_', 1)[1] if '_' in key else key
            
            # Create an optimized representation for the LLM
            optimized_doc = optimize_for_llm(doc_data, doc_type)
            
            # Add the document name
            optimized_doc['name'] = doc_name
            
            # Add to the processed documents
            processed_docs[key] = optimized_doc
        
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