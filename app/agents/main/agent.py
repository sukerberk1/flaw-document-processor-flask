from flask import Blueprint, request, jsonify, current_app
import os
import json
import tiktoken
from app.llm_client import LLMClientFactory

# Create blueprint with the ORIGINAL name to maintain compatibility
main_agent_bp = Blueprint('main_agent', __name__, url_prefix='/agents/main')

# Initialize LLM client using the factory
llm_client = LLMClientFactory.get_client()

# Initialize tokenizer for gpt-3.5-turbo
tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")

@main_agent_bp.route('/summarize', methods=['GET'])
def summarize_combined_data():
    """
    Reads the combined document data from memory and extracts defects mentioned in the documents.
    Returns a comprehensive list of all potential defects mentioned in the document content.
    """
    try:
        # Get the combined data from application variable
        combined_data = current_app.combined_document_data
        
        # Check if there's any data
        if not combined_data:
            return jsonify({
                'error': 'No combined data found. Please scan documents first.'
            }), 404
        
        # Configuration for processing
        MAX_CHUNKS_TO_PROCESS = 25  # Increased to process more chunks per document for better coverage
        
        # Initialize defect list - this will store all detected defects
        defect_list = []
        
        # Function to count tokens accurately using tiktoken
        def count_tokens(text):
            if not text:
                return 0
            # Convert to string if not already
            if not isinstance(text, str):
                text = str(text)
            return len(tokenizer.encode(text))
        
        # Function to chunk text into smaller pieces with a maximum token count
        def chunk_text(text, max_tokens=200):  # Reduced default max tokens
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
            
            # Simple chunking approach to reduce complexity
            # This will create smaller chunks to avoid rate limits
            import re
            sentences = re.split(r'(?<=[.!?])\s+', text)
            chunks = []
            current_chunk = ""
            current_tokens = 0
            
            for sentence in sentences:
                sentence_tokens = count_tokens(sentence)
                
                # Handle very long sentences by simple truncation
                if sentence_tokens > max_tokens:
                    # Split into words and create smaller chunks
                    words = sentence.split()
                    temp_chunk = ""
                    
                    for word in words:
                        if count_tokens(temp_chunk + " " + word) <= max_tokens:
                            temp_chunk += " " + word
                        else:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip())
                            temp_chunk = word
                    
                    if temp_chunk:
                        chunks.append(temp_chunk.strip())
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
        
        # Function to analyze a single document chunk for defects
        def analyze_chunk_for_defects(doc_name, chunk_index, chunk_text, chunk_location=""):
            # Ensure chunk is not too large - limit to ~500 tokens max to avoid rate limiting
            if count_tokens(chunk_text) > 500:
                truncated_chunk = chunk_text[:500]  # Simple truncation
                current_app.logger.warning(f"Chunk too large ({count_tokens(chunk_text)} tokens), truncating to 500 characters")
                chunk_text = truncated_chunk
            
            # Enhanced prompt with stronger emphasis on finding ALL possible defects
            system_message = """
            IMPORTANT: Your PRIMARY task is to extract EVERY SINGLE defect that is mentioned, implied, or referenced in this document chunk. Be EXTREMELY thorough and err on the side of over-identification rather than missing defects.
            
            Aggressively look for ANY mentions of:
            - Product defects, issues, bugs, or quality concerns
            - Equipment failures, breakdowns, malfunctions, or performance degradation
            - Material problems, component failures, or physical defects
            - System errors, exceptions, crashes, or unexpected behaviors
            - Reported failures, incidents, non-conformities, or quality escapes
            - Customer complaints, returns, or dissatisfaction related to quality
            - Non-compliance with standards, specifications, or regulations
            - Even MINOR issues, warnings, or risks that COULD become defects
            - Troubleshooting discussions, repair procedures, or workarounds that imply defects
            
            CRITICALLY IMPORTANT GUIDELINES:
            1. DO NOT miss ANY potential defect, even if mentioned only briefly or indirectly
            2. Include defects even if they seem minor, non-critical, or already resolved
            3. Extract defects from both explicit statements AND implicit references
            4. Consider industry-specific language that might indicate defects
            5. DO NOT analyze the document itself for errors - only extract defects mentioned IN the content
            
            Format each mentioned defect as:
            DEFECT #[number]:
            - TYPE: [type of defect mentioned]
            - DESCRIPTION: [what is the defect/issue, be specific and detailed]
            - EVIDENCE: [exact text mentioning the defect]
            - CONFIDENCE: [low/medium/high]
            
            If truly NO defects are mentioned, respond with: "NO DEFECTS FOUND"
            """
            
            # Call LLM client with the prompts
            user_message = f"Analyze document '{doc_name}' at {chunk_location}:\n\n{chunk_text}"
            response_text = llm_client.chat_completion(
                system_prompt=system_message,
                user_prompt=user_message,
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse the response using a more structured text-based approach
            try:
                current_app.logger.debug(f"Raw LLM response: {response_text[:200]}...")
                
                # Check if there are no defects found
                if "NO DEFECTS FOUND" in response_text:
                    return []
                    
                defects_list = []
                
                # Parse the response text using regex patterns to extract structured defect data
                import re
                
                # Look for defect blocks in the format "DEFECT #X:"
                defect_blocks = re.split(r'DEFECT\s+#\d+:', response_text)
                
                # The first element will be empty or contain text before the first defect
                if defect_blocks and len(defect_blocks) > 1:
                    # Skip first element which is before the first "DEFECT #X:"
                    for block in defect_blocks[1:]:
                        # Create a new defect record
                        defect = {
                            'document': doc_name,
                            'location': chunk_location,
                            'chunk_index': chunk_index,
                            'defect_type': 'Unknown',
                            'description': '',
                            'evidence': '',
                            'severity': 3,
                            'confidence': 'medium'
                        }
                        
                        # Extract defect type
                        type_match = re.search(r'TYPE:\s*(.*?)(?:\n|$|-\s*DESCRIPTION)', block)
                        if type_match:
                            defect['defect_type'] = type_match.group(1).strip()
                            
                        # Extract description
                        desc_match = re.search(r'DESCRIPTION:\s*(.*?)(?:\n|$|-\s*EVIDENCE)', block)
                        if desc_match:
                            defect['description'] = desc_match.group(1).strip()
                            
                        # Extract evidence
                        evidence_match = re.search(r'EVIDENCE:\s*(.*?)(?:\n|$|-\s*SEVERITY)', block)
                        if evidence_match:
                            defect['evidence'] = evidence_match.group(1).strip()
                            
                        # Extract severity
                        severity_match = re.search(r'SEVERITY:\s*(\d+)', block)
                        if severity_match:
                            try:
                                defect['severity'] = int(severity_match.group(1).strip())
                            except ValueError:
                                pass  # Keep default severity if not a valid integer
                                
                        # Extract confidence
                        confidence_match = re.search(r'CONFIDENCE:\s*(high|medium|low)', block, re.IGNORECASE)
                        if confidence_match:
                            defect['confidence'] = confidence_match.group(1).lower().strip()
                            
                        # Only add if we have at least description or evidence
                        if defect['description'] or defect['evidence']:
                            defects_list.append(defect)
                else:
                    # If no structured blocks were found, create a single defect with the entire response
                    current_app.logger.warning("Could not extract structured defects, creating generic entry")
                    defects_list.append({
                        'document': doc_name,
                        'location': chunk_location,
                        'chunk_index': chunk_index,
                        'defect_type': 'Unstructured',
                        'description': 'LLM response not properly structured',
                        'evidence': response_text[:500],  # Limit to first 500 chars
                        'severity': 3,
                        'confidence': 'low'
                    })
                
                return defects_list
                
            except Exception as e:
                current_app.logger.error(f"Error processing LLM response: {str(e)}. Raw response: {response.choices[0].message.content[:200]}")
                return []
        
        # Process each document and its chunks
        for doc_key, doc_data in combined_data.items():
            # Extract document type and name
            doc_type = doc_key.split('_')[0] if '_' in doc_key else 'unknown'
            doc_name = doc_key.split('_', 1)[1] if '_' in doc_key else doc_key
            
            current_app.logger.info(f"Processing document: {doc_name} (Type: {doc_type})")
            
            # Extract text content based on document structure
            text_content = None
            
            if 'text' in doc_data:
                text_content = doc_data['text']
            elif 'text_content' in doc_data:
                text_content = doc_data['text_content']
            elif 'chunks' in doc_data and isinstance(doc_data['chunks'], list):
                text_content = "\n\n".join(doc_data['chunks'])
            
            # If we have text content, chunk it and analyze each chunk
            if text_content:
                # Split content into smaller manageable chunks (reduced from 1000 to 200 tokens)
                chunked_content = chunk_text(text_content, max_tokens=200)
                
                # If chunked_content is not a list, make it one
                if not isinstance(chunked_content, list):
                    chunked_content = [chunked_content]
                
                current_app.logger.info(f"Document {doc_name} split into {len(chunked_content)} chunks")
                
                # Process chunks according to MAX_CHUNKS_TO_PROCESS setting
                if chunked_content:
                    # Get number of chunks to process (up to MAX_CHUNKS_TO_PROCESS)
                    chunks_to_process = min(MAX_CHUNKS_TO_PROCESS, len(chunked_content))
                    
                    for i in range(chunks_to_process):
                        chunk = chunked_content[i]
                        
                        # Limit chunk size to avoid rate limiting (max 500 tokens)
                        if count_tokens(chunk) > 500:
                            chunk = chunk[:500]  # Simple truncation as a fallback
                        
                        # For PDFs, try to provide page information if available
                        chunk_location = ""
                        if doc_type == 'pdf' and 'pages' in doc_data and i < len(doc_data['pages']):
                            page_number = doc_data['pages'][i].get('page_number', i + 1)
                            chunk_location = f"Page {page_number}"
                        else:
                            chunk_location = f"Chunk {i+1}/{len(chunked_content)}"
                        
                        current_app.logger.info(f"Analyzing {doc_name} {chunk_location} ({i+1} of {chunks_to_process})")
                        
                        # Analyze this chunk for defects
                        chunk_defects = analyze_chunk_for_defects(doc_name, i, chunk, chunk_location)
                        
                        # Add any defects found to our master list
                        if chunk_defects:
                            defect_list.extend(chunk_defects)
                            current_app.logger.info(f"Found {len(chunk_defects)} defects in {doc_name} {chunk_location}")
                    
                    # Log how many chunks remain unprocessed
                    if len(chunked_content) > chunks_to_process:
                        current_app.logger.info(f"Skipping {len(chunked_content) - chunks_to_process} remaining chunks to avoid rate limiting")
        
        # More conservative deduplication to preserve unique defects
        unique_defects = []
        seen_descriptions = set()
        
        for defect in defect_list:
            # Create a more specific key for deduplication - only exact matches will be considered duplicates
            defect_type = defect.get('defect_type', '').strip().lower()
            description = defect.get('description', '').strip().lower()
            evidence = defect.get('evidence', '')[:50].strip().lower()
            document = defect.get('document', '').strip().lower()
            
            # Combine type, description, and evidence for a more precise deduplication key
            # This ensures we only deduplicate extremely similar defects
            defect_key = (defect_type, description, evidence, document)
            
            # If key not seen before, add it to our unique list
            if defect_key not in seen_descriptions:
                seen_descriptions.add(defect_key)
                unique_defects.append(defect)
            else:
                # Even for "duplicates", check if there's any additional evidence
                # that might indicate a slightly different defect
                for existing_defect in unique_defects:
                    existing_type = existing_defect.get('defect_type', '').strip().lower()
                    existing_desc = existing_defect.get('description', '').strip().lower()
                    existing_doc = existing_defect.get('document', '').strip().lower()
                    
                    # If it's a match to an existing defect but has different evidence, keep it too
                    if (existing_type == defect_type and 
                        existing_desc == description and
                        existing_doc == document and
                        defect.get('evidence', '') != existing_defect.get('evidence', '')):
                        unique_defects.append(defect)
                        break
        
        current_app.logger.info(f"After deduplication: {len(unique_defects)} unique defects from {len(defect_list)} total defects")
        
        # Final review to ensure nothing is missed
        if unique_defects:
            # Prepare a summary for the LLM to do a final check
            defect_summary = json.dumps(unique_defects)
            
            # Enhanced final check message to ensure maximum defect coverage
            final_check_message = """
            CRITICALLY IMPORTANT: Your task is to review these extracted defects and ENSURE that NO potential defects have been missed. You are the FINAL check to guarantee maximum defect identification.
            
            Follow these steps with extreme thoroughness:
            
            1. Carefully review all defects already identified
            2. Identify ANY ADDITIONAL defects that might have been missed in the initial analysis
            3. Consolidate similar defects but NEVER remove unique defects even if they seem minor
            4. Standardize defect types and descriptions for clarity
            5. Apply domain expertise to identify industry-specific defects that might have been overlooked
            
            It is ABSOLUTELY CRITICAL that your review captures ALL possible defects mentioned in the documents.
            
            First, provide a comprehensive SUMMARY of the main defect categories found, organized by type/severity.
            
            Then list EVERY defect using this format:
            
            DEFECT #[number]:
            - TYPE: [precise categorization of the defect type]
            - DESCRIPTION: [detailed, specific description of what is defective]
            - EVIDENCE: [exact text mentioning the defect]
            - CONFIDENCE: [low/medium/high]
            - DOCUMENT: [source document name]
            - LOCATION: [where in the document]
            
            Remember: It is better to over-identify potential defects than to miss any. Include everything that could reasonably be considered a defect.
            """
            
            # Use a simpler version of the defect list for the final review to reduce token usage
            simplified_defects = []
            for defect in unique_defects:
                # Create a simplified version with shorter evidence text
                simple_defect = {
                    'defect_type': defect.get('defect_type', 'Unknown'),
                    'description': defect.get('description', '')[:100],  # Limit description length
                    'evidence': defect.get('evidence', '')[:50],  # Limit evidence length
                    'severity': defect.get('severity', 3),
                    'confidence': defect.get('confidence', 'medium'),
                    'document': defect.get('document', ''),
                    'location': defect.get('location', '')
                }
                simplified_defects.append(simple_defect)
            
            # Convert to JSON with the simplified list
            simple_defect_summary = json.dumps(simplified_defects)
            
            response_text = llm_client.chat_completion(
                system_prompt=final_check_message,
                user_prompt=f"Review these defects:\n\n{simple_defect_summary}",
                max_tokens=800,
                temperature=0.2
            )
            
            # Parse final review response using a text-based approach
            try:
                current_app.logger.debug(f"Raw final review response: {response_text[:200]}...")
                
                # Extract the summary section (everything before the first DEFECT)
                import re
                parts = re.split(r'DEFECT\s+#\d+:', response_text, 1)
                
                summary = parts[0].strip() if len(parts) > 0 else ""
                current_app.logger.info(f"Final review summary: {summary[:100]}...")
                
                # Extract defects using the same pattern as before
                final_defects = []
                
                # Look for defect blocks
                defect_blocks = re.split(r'DEFECT\s+#\d+:', response_text)
                
                if defect_blocks and len(defect_blocks) > 1:
                    # Skip first element which is before the first "DEFECT #X:"
                    for block in defect_blocks[1:]:
                        # Create a new defect record
                        defect = {
                            'defect_type': 'Unknown',
                            'description': '',
                            'evidence': '',
                            'severity': 3,
                            'confidence': 'medium',
                            'document': '',
                            'location': ''
                        }
                        
                        # Extract all fields
                        field_patterns = {
                            'defect_type': r'TYPE:\s*(.*?)(?:\n|$|-\s*[A-Z]+:)',
                            'description': r'DESCRIPTION:\s*(.*?)(?:\n|$|-\s*[A-Z]+:)',
                            'evidence': r'EVIDENCE:\s*(.*?)(?:\n|$|-\s*[A-Z]+:)',
                            'severity': r'SEVERITY:\s*(\d+)',
                            'confidence': r'CONFIDENCE:\s*(high|medium|low)',
                            'document': r'DOCUMENT:\s*(.*?)(?:\n|$|-\s*[A-Z]+:)',
                            'location': r'LOCATION:\s*(.*?)(?:\n|$|-\s*[A-Z]+:)'
                        }
                        
                        for field, pattern in field_patterns.items():
                            match = re.search(pattern, block, re.IGNORECASE)
                            if match:
                                value = match.group(1).strip()
                                if field == 'severity':
                                    try:
                                        defect[field] = int(value)
                                    except ValueError:
                                        pass
                                else:
                                    defect[field] = value
                                    
                        # Only add if we have at least description or evidence
                        if defect['description'] or defect['evidence']:
                            final_defects.append(defect)
                
                if final_defects:
                    # Use the newly parsed defects
                    unique_defects = final_defects
                    current_app.logger.info(f"Final review complete: now have {len(unique_defects)} defects")
                # If no defects were parsed, keep the original list (don't update unique_defects)
                
                # Add the summary to the app context for later retrieval
                current_app.defect_summary = summary
                
            except Exception as e:
                current_app.logger.warning(f"Error processing final review: {str(e)}. Using original defect list.")
        
        # Get the summary if it exists, or create a default one
        summary = getattr(current_app, 'defect_summary', None)
        if not summary:
            summary = f"Detected {len(unique_defects)} unique defects across {len(combined_data)} documents."
        
        # Create a numbered list of defects mentioned in the documents
        defect_names = []
        for i, defect in enumerate(unique_defects, 1):
            defect_type = defect.get('defect_type', 'Unknown')
            description = defect.get('description', '')[:100]  # Truncate long descriptions
            document = defect.get('document', '')
            location = defect.get('location', '')
            severity = defect.get('severity', 0)
            evidence = defect.get('evidence', '')[:50] + "..." if defect.get('evidence', '') else ""
            
            # Format: "#X: Type: Description - 'Evidence'"
            defect_name = f"#{i}: {defect_type}: {description}\n   Evidence: '{evidence}'\n   Found in: {document} ({location})"
            defect_names.append(defect_name)
        
        # Create a formatted string list for the browser display
        formatted_list = "\n\n".join(defect_names)
        list_title = "# DEFECTS MENTIONED IN DOCUMENTS"
        list_subtitle = f"Found {len(unique_defects)} defects mentioned across {len(combined_data)} documents:"
        list_display = f"{list_title}\n{list_subtitle}\n\n{formatted_list}"
        
        # Return the comprehensive defect list with list display as the main summary
        return jsonify({
            'summary': list_display,  # Use the list as the main summary display
            'original_summary': summary,  # Keep original summary as a secondary field
            'defect_count': len(unique_defects),
            'defect_names': defect_names,
            'defects': unique_defects,
            'document_count': len(combined_data)
        })
        
    except Exception as e:
        # Log the error
        current_app.logger.error(f"Error detecting defects: {str(e)}")
        return jsonify({
            'error': f"Error detecting defects: {str(e)}"
        }), 500