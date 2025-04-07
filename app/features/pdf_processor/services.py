import os
from typing import List, Dict, Any
from PyPDF2 import PdfReader
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
from app.features.pdf_processor.models import PDFDocument
from app.domain.models import MinimalDefect
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
The location should be identifiable place on the map and should be as concrete as possible.

Example of report beginning:
<report-beginning-example>
Zamość, dnia 08 kwietnia 2022 r. 
PROTOKÓŁ  
z przeglądu stanu technicznego branży budowlanej w okresie gwarancyjnym 
budynku Sądu Okręgowego i Rejonowego w Zamościu przeprowadzonego w dniach 21
25.03.2022 r. sporządzony w dniu 08.04.2022 r. 
</report-beginning-example>

Desired location output:
<location-output>
Sąd Okręgowy i Rejonowy w Zamościu
</location-output>

Answer with a concrete place, without any introductions or explanations.
"""

DEFECT_LIST_INSTRUCTIONS = """\n
You must provide a list of defects from the following report document.
Document contains various defects in various locations.
Example of defect format in the doument:
<defect-examples>
latarnia doświetleniowa - kiosk I - sala rozpraw nr 30 - zmurszenie blachy (dziura) przy oknie
P.29A - okno do regulacji

</defect-examples>

Your answer should strictly follow a json format:
[
    {
        "name": "Latarnia doświetleniowa - zmurszenie blachy (dziura) przy oknie",
        "location":"Sąd Rejonowy w Zamości Kiosk I - sala rozpraw nr 30"
    },
    {
        "name": "Okno do regulacji",
        "location":"Sąd Rejonowy w Zamości P.29A"
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

    def generate_report_location(self, text) -> str:
        return self.ask_llm(text, [
                    { "role": "system", "content": ASSISTANT_SYSTEM_PROMPT},
                    {"role": "user", "content": DEFECTS_LOCATION_INSTRUCTIONS + get_document_delimited(text)},
                ]) + "\n\n"
    
    async def generate_defect_list(self, text: str, location_prompt: str) -> List[MinimalDefect]:
        lines = text.split("\n")
        chunk_size = 15

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
        defect_lists_results = await asyncio.gather(*tasks)

        all_defects: List[MinimalDefect] = []

        for raw_defect_list in defect_lists_results:
            sanitized_defect_list = raw_defect_list.replace("```", "").replace("json", '').replace("I don't know.", "").replace("I don't know", "")
            try:
                chunk_found_defects: List[MinimalDefect] = json.loads(sanitized_defect_list)
                if isinstance(chunk_found_defects, list):
                    print(f"Found {len(chunk_found_defects)} defects in chunk.")
                    all_defects.extend(chunk_found_defects)
                else:
                    print(f"Unexpected result: {raw_defect_list}")
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")
                print(f"Raw defect list: {raw_defect_list}")

        await asyncio.sleep(2)  #TODO this sleep does not work to avoid rate limits
        print("Cleaning up event loop...")
        # Join results and return
        return all_defects


    async def process_pdf(self, file_path):
        """Process a PDF file and return a PDFDocument with summary."""
        filename = os.path.basename(file_path)
        content = self.read_pdf(file_path)
        
        location = self.generate_report_location(content)

        defects_lists = await self.generate_defect_list(content, location)

        return PDFDocument(
            filename, 
            content, 
            str(defects_lists).replace("'", '"') # format into json string
            )
