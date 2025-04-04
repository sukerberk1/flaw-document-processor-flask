import os
from PyPDF2 import PdfReader
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
from app.features.pdf_processor.models import PDFDocument
import asyncio
import json
import re

# Load environment variables
load_dotenv(override=True)  # Add override=True to force reload

ASSISTANT_SYSTEM_PROMPT = """
                    You are a helpful assistant that searches through documents and finds relevant info for the user. 
                    You will be asked to find an information in a document or to infer an information based from the document content.
                    Document will be delimited using <document> and </document> tags.
                    Your answer should contain only the information that is relevant to the question.
                    If there is no information in the document that can be used to answer the question, you should say "I don't know".
                    Your answer should be in Polish language.
                    """


DEFECTS_LOCATION_INSTRUCTIONS = """\n
You must provide a location of where the defects report is located.
It should be within the document, most likely at the beginning or end of the document.
The location should be identifiable place on the map.

Answer with a concrete place, without any introductions or explanations.
"""

DEFECT_LIST_INSTRUCTIONS = """\n
You must provide a list of defects from the following report document.
Document contains various defects in various locations.
Example of defect format in the doument:
<defect-example>
latarnia doświetleniowa - kiosk I - sala rozpraw nr 30 - zmurszenie blachy (dziura) przy oknie
</defect-example>

Your answer should strictly follow a json format:
[
    {
        "name": "Latarnia doświetleniowa - zmurszenie blachy (dziura) przy oknie",
        "location":"Sąd Rejonowy w Zamości Kiosk I - sala rozpraw nr 30"
    }
]

Destructure the defect in the document as in the example above.

You have to list all of the defects present in the document. Go line by line and extract all the defects from the document. 
"""

def get_defect_list_instructions(location_prompt: str) -> str:
    return f"""
    {DEFECT_LIST_INSTRUCTIONS}

    Each location should mention the concrete defect location e.g. a room number.
    Locations must also mention information about the building in which the defect is located:
    {location_prompt}

    """

def get_document_delimited(text: str) -> str:
    return f"<document>{text}</document>"


class PDFProcessorService:
    """Service for processing PDFs and generating summaries."""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        print(f"Loading OpenAI API key: {'Found' if api_key else 'Not found'}")
        if not api_key:
            print("WARNING: OPENAI_API_KEY environment variable is not set")
            # We'll initialize without the key, but operations will fail
            self.client = None
            self.client_async = None
        else:
            self.client = OpenAI(api_key=api_key)
            self.client_async = AsyncOpenAI(api_key=api_key)
    
    def read_pdf(self, file_path):
        """Read a PDF file and extract its text content."""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:  # Only add if text was successfully extracted
                    text += page_text + "\n"
            
            if not text.strip():
                return "No readable text found in the PDF. The document might be scanned or contain only images."
                
            return text
        except Exception as e:
            print(f"Error reading PDF: {str(e)}")
            return f"Error reading PDF: {str(e)}"
    
    def ask_llm(self, text, messages, max_length=500):
        """Ask llms questions about text using OpenAI's API."""
        if not self.client:
            return "Error: OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable."
            
        # Limit text length to avoid token limits
        max_text_length = 15000  # Approximately 4000 tokens
        if len(text) > max_text_length:
            text = text[:max_text_length] + "... [text truncated due to length]"
            
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            return f"Error asking llm: {str(e)}"
        
    async def ask_llm_async(self, text, messages, max_length=500):
        """Ask llms questions about text using OpenAI's API."""
        if not self.client:
            return "Error: OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable."
            
        # Limit text length to avoid token limits
        max_text_length = 15000  # Approximately 4000 tokens
        if len(text) > max_text_length:
            text = text[:max_text_length] + "... [text truncated due to length]"
            
        try:
            response = await self.client_async.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            return f"Error asking llm: {str(e)}"


    def generate_defect_location(self, text) -> str:
        return self.ask_llm(text, [
                    { "role": "system", "content": ASSISTANT_SYSTEM_PROMPT},
                    {"role": "user", "content": DEFECTS_LOCATION_INSTRUCTIONS + get_document_delimited(text)},
                ]) + "\n\n"
    
    async def generate_defect_list(self, text: str, location_prompt: str) -> str:
        lines = text.split("\n")
        chunk_size = 20

        async def process_chunk(chunk):
            """Asynchronously process a single chunk."""
            return await self.ask_llm_async(chunk, [
                {"role": "system", "content": ASSISTANT_SYSTEM_PROMPT},
                {"role": "user", "content": get_defect_list_instructions(location_prompt) + get_document_delimited(chunk)},
            ])

        # Split text into chunks
        chunks = ["\n".join(lines[i:i + chunk_size]) for i in range(0, len(lines), chunk_size)]

        # Create asyncio tasks for each chunk
        tasks = [process_chunk(chunk) for chunk in chunks]

        # Run tasks concurrently and gather results
        results = await asyncio.gather(*tasks)

        # Join results and return
        return "\n".join(results)
    
    def flatten_json_arrays(json_string: str) -> list:
        """Flatten a string containing multiple JSON arrays into a single list of dictionaries."""
        try:
            # Split the string into individual JSON arrays
            json_arrays = re.split(r"\]\s*\[", json_string)
            
            # Clean up the split strings and parse them as JSON
            flattened_list = []
            for array_str in json_arrays:
                # Add missing brackets after splitting
                array_str = array_str.strip()
                if not array_str.startswith("["):
                    array_str = "[" + array_str
                if not array_str.endswith("]"):
                    array_str = array_str + "]"
                
                print(array_str)  # Debugging line to check the JSON string
                # Parse the JSON array and extend the flattened list
                flattened_list.extend(json.loads(array_str))
            
            return flattened_list
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {str(e)}")
            return []
    

    def process_raw_defect_lists(raw_defect_lists: str) -> str:
        """Process raw defect lists into a structured format."""
        defect_lists = raw_defect_lists.replace("```", "").replace("json", '').replace("I don't know.", "").replace("I don't know", "")
        flattened_defects = PDFProcessorService.flatten_json_arrays(defect_lists)
        return str(flattened_defects).replace("\"", "\\\"").replace("'", '"') #.replace("None", "null").replace("True", "true").replace("False", "false")


    async def process_pdf(self, file_path):
        """Process a PDF file and return a PDFDocument with summary."""
        filename = os.path.basename(file_path)
        content = self.read_pdf(file_path)
        
        location = self.generate_defect_location(content)

        defects_lists_raw = await self.generate_defect_list(content, location)
        summary = PDFProcessorService.process_raw_defect_lists(defects_lists_raw)

        return PDFDocument(filename, content, summary)
