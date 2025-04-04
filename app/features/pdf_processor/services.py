import os
from PyPDF2 import PdfReader
from openai import OpenAI
from dotenv import load_dotenv
from app.features.pdf_processor.models import PDFDocument

# Load environment variables
load_dotenv(override=True)  # Add override=True to force reload

ASSISTANT_SYSTEM_PROMPT = """
                    You are a helpful assistant that searches through documents and finds relevant info for the user. 
                    You will be asked to find an information in a document or to infer an information based from the document content.
                    Document will be delimited using <document> and </document> tags.
                    Your answer should contain only the information that is relevant to the question.
                    If there is no information in the document that can be used to answer the question, you should say "I don't know" or "I can't help with that".
                    Your answer should be in Polish language.
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

The location should be as concrete as possible, including the name of the building, room number, and any other relevant information.
The addres of the building is included in the document.

Destructure the defect in the document as in the example above.

You have to list all of the defects present in the document. Go line by line and extract all the defects from the document. 
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
        else:
            self.client = OpenAI(api_key=api_key)
    
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

    
    def generate_defect_list(self, text) -> str:
        return self.ask_llm(text, [
                    { "role": "system", "content": ASSISTANT_SYSTEM_PROMPT},
                    {"role": "user", "content": DEFECT_LIST_INSTRUCTIONS + get_document_delimited(text)},
                ]) + "\n\n"
    
    def process_pdf(self, file_path):
        """Process a PDF file and return a PDFDocument with summary."""
        filename = os.path.basename(file_path)
        content = self.read_pdf(file_path)
        summary = self.generate_defect_list(content)
        return PDFDocument(filename, content, summary) 
