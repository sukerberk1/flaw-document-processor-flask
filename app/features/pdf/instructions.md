# PDF Processing System with Local Vector DB

This guide provides instructions for implementing a PDF processing system with chunking, summarization, and a completely local vector database within a vertical slice architecture.

## Project Structure

```
app/
└── features/
    └── pdf/
        ├── Application/         # Application services
        │   ├── Commands/        # Command handlers
        │   ├── Queries/         # Query handlers
        │   └── DTOs/            # Data transfer objects
        ├── Domain/              # Domain models and interfaces
        │   ├── Models/
        │   └── Interfaces/
        ├── Infrastructure/      # Implementation details
        │   ├── Database/        # Local vector DB setup
        │   ├── PdfExtraction/   # PDF extraction logic
        │   ├── Chunking/        # Text chunking strategies
        │   └── Summarization/   # Summarization services
        └── API/                 # API endpoints/controllers
```

## Step 1: Setup Project Dependencies

Create a `requirements.txt` file in your PdfProcessor folder:

```
# PDF Processing
pymupdf==1.22.3
pdf2image==1.16.3
pytesseract==0.3.10
Pillow==10.0.1

# Vector Database (Local)
faiss-cpu==1.7.4
chromadb==0.4.13

# Embeddings and LLM
langchain==0.0.267
openai==0.28.1

# Utilities
numpy==1.24.3
pydantic==1.10.8
python-dotenv==1.0.0
```

## Step 2: Environment Setup

Create a `.env` file in your PdfProcessor folder:

```
OPENAI_API_KEY=your_openai_api_key_here
VECTOR_DB_PATH=./Features/PdfProcessor/Infrastructure/Database/vector_db
```

## Step 3: Implement Core Components

### 3.1 PDF Extraction Service

Create `Infrastructure/PdfExtraction/PdfExtractor.py`:

```python
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
from ...Domain.Models.PdfPage import PdfPage
from ...Domain.Interfaces.IPdfExtractor import IPdfExtractor

class PdfExtractor(IPdfExtractor):
    def extract(self, pdf_path):
        """Extract text and images from PDF"""
        doc = fitz.open(pdf_path)
        pdf_data = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            # If minimal text found, try OCR
            if len(text.strip()) < 20:
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(img)

            # Extract images (optional)
            images = []
            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                images.append({
                    "index": img_index,
                    "bytes": image_bytes
                })

            pdf_data.append(PdfPage(
                page_number=page_num + 1,
                text=text,
                images=images
            ))

        return pdf_data
```

### 3.2 Text Chunking Service

Create `Infrastructure/Chunking/TextChunker.py`:

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from ...Domain.Models.TextChunk import TextChunk
from ...Domain.Interfaces.ITextChunker import ITextChunker

class TextChunker(ITextChunker):
    def __init__(self, chunk_size=1000, chunk_overlap=100):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def chunk_text(self, pdf_pages):
        """Split text into manageable chunks"""
        chunks = []

        for page in pdf_pages:
            page_chunks = self.text_splitter.split_text(page.text)

            for i, chunk_text in enumerate(page_chunks):
                chunks.append(TextChunk(
                    content=chunk_text,
                    page_number=page.page_number,
                    chunk_index=i,
                    metadata={"page": page.page_number}
                ))

        return chunks
```

### 3.3 Vector Database Setup

For FAISS (fastest setup and completely local):

Create `Infrastructure/Database/VectorDatabase.py`:

```python
import os
import faiss
import numpy as np
import pickle
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from ...Domain.Interfaces.IVectorDatabase import IVectorDatabase

class FaissVectorDatabase(IVectorDatabase):
    def __init__(self, embedding_model=None):
        self.embedding_model = embedding_model or OpenAIEmbeddings()
        self.vector_db_path = os.getenv("VECTOR_DB_PATH")
        os.makedirs(os.path.dirname(self.vector_db_path), exist_ok=True)
        self.vector_db = None

    def store_chunks(self, chunks, document_id):
        """Store text chunks in vector database"""
        texts = [chunk.content for chunk in chunks]
        metadatas = [{"page": chunk.page_number, "chunk_index": chunk.chunk_index, "document_id": document_id} for chunk in chunks]

        db = FAISS.from_texts(
            texts,
            self.embedding_model,
            metadatas=metadatas
        )

        # Save the database to disk
        db_path = f"{self.vector_db_path}/{document_id}"
        db.save_local(db_path)
        return True

    def load_document(self, document_id):
        """Load a specific document's vectors"""
        db_path = f"{self.vector_db_path}/{document_id}"
        self.vector_db = FAISS.load_local(db_path, self.embedding_model)
        return self.vector_db

    def similarity_search(self, query, k=4):
        """Search for similar chunks to the query"""
        if not self.vector_db:
            raise ValueError("No document loaded. Call load_document first.")

        return self.vector_db.similarity_search(query, k=k)
```

For ChromaDB (better for persistence and querying):

```python
import os
import chromadb
from chromadb.config import Settings
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from ...Domain.Interfaces.IVectorDatabase import IVectorDatabase

class ChromaVectorDatabase(IVectorDatabase):
    def __init__(self, embedding_model=None):
        self.embedding_model = embedding_model or OpenAIEmbeddings()
        self.vector_db_path = os.getenv("VECTOR_DB_PATH")
        os.makedirs(self.vector_db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.vector_db_path)
        self.vector_db = None

    def store_chunks(self, chunks, document_id):
        """Store text chunks in vector database"""
        texts = [chunk.content for chunk in chunks]
        metadatas = [{"page": chunk.page_number, "chunk_index": chunk.chunk_index, "document_id": document_id} for chunk in chunks]
        ids = [f"{document_id}_{chunk.page_number}_{chunk.chunk_index}" for chunk in chunks]

        db = Chroma.from_texts(
            texts,
            self.embedding_model,
            metadatas=metadatas,
            ids=ids,
            persist_directory=f"{self.vector_db_path}/{document_id}"
        )

        db.persist()
        return True

    def load_document(self, document_id):
        """Load a specific document's vectors"""
        db_path = f"{self.vector_db_path}/{document_id}"
        self.vector_db = Chroma(
            persist_directory=db_path,
            embedding_function=self.embedding_model
        )
        return self.vector_db

    def similarity_search(self, query, k=4):
        """Search for similar chunks to the query"""
        if not self.vector_db:
            raise ValueError("No document loaded. Call load_document first.")

        return self.vector_db.similarity_search(query, k=k)
```

### 3.4 Summarization Service

Create `Infrastructure/Summarization/SummarizationService.py`:

```python
from langchain.chains.summarize import load_summarize_chain
from langchain.llms import OpenAI
from langchain.docstore.document import Document
from ...Domain.Interfaces.ISummarizationService import ISummarizationService

class SummarizationService(ISummarizationService):
    def __init__(self, llm=None):
        self.llm = llm or OpenAI(temperature=0)

    def summarize_chunks(self, chunks, strategy="map_reduce"):
        """Summarize text chunks using the specified strategy"""
        # Convert chunks to Documents for LangChain
        docs = [Document(page_content=chunk.content, metadata={"page": chunk.page_number})
                for chunk in chunks]

        # Load the appropriate chain
        chain = load_summarize_chain(self.llm, chain_type=strategy)

        # Run the summarization
        summary = chain.run(docs)

        return summary

    def query_pdf(self, vector_db, query):
        """Query PDF content using similarity search and LLM"""
        # Get relevant chunks
        docs = vector_db.similarity_search(query)

        # Format prompt with docs and query
        prompt_template = """
        Based on the following extracted portions of a PDF document, please answer the question.

        EXTRACTED CONTENT:
        {docs}

        QUESTION: {query}

        ANSWER:
        """

        formatted_docs = "\n\n".join([f"Document (Page {doc.metadata['page']}): {doc.page_content}" for doc in docs])
        prompt = prompt_template.format(docs=formatted_docs, query=query)

        # Get response from LLM
        response = self.llm.predict(prompt)

        return response
```

## Step 4: Create Application Layer Services

### 4.1 Process PDF Command Handler

Create `Application/Commands/ProcessPdfCommandHandler.py`:

```python
import os
import uuid
from ...Domain.Models.ProcessPdfCommand import ProcessPdfCommand
from ...Infrastructure.PdfExtraction.PdfExtractor import PdfExtractor
from ...Infrastructure.Chunking.TextChunker import TextChunker
from ...Infrastructure.Database.VectorDatabase import FaissVectorDatabase
from ...Infrastructure.Summarization.SummarizationService import SummarizationService

class ProcessPdfCommandHandler:
    def __init__(self):
        self.pdf_extractor = PdfExtractor()
        self.text_chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
        self.vector_db = FaissVectorDatabase()
        self.summarizer = SummarizationService()

    def handle(self, command: ProcessPdfCommand):
        # Generate a unique ID for this document
        document_id = str(uuid.uuid4())

        # Extract content from PDF
        pdf_pages = self.pdf_extractor.extract(command.pdf_path)

        # Chunk the text
        chunks = self.text_chunker.chunk_text(pdf_pages)

        # Store in vector database
        self.vector_db.store_chunks(chunks, document_id)

        # Generate summary if requested
        summary = None
        if command.generate_summary:
            summary = self.summarizer.summarize_chunks(chunks, strategy=command.summary_strategy)

        # Return the document ID for future queries
        return {
            "document_id": document_id,
            "page_count": len(pdf_pages),
            "chunk_count": len(chunks),
            "summary": summary
        }
```

### 4.2 Query PDF Command Handler

Create `Application/Commands/QueryPdfCommandHandler.py`:

```python
from ...Domain.Models.QueryPdfCommand import QueryPdfCommand
from ...Infrastructure.Database.VectorDatabase import FaissVectorDatabase
from ...Infrastructure.Summarization.SummarizationService import SummarizationService

class QueryPdfCommandHandler:
    def __init__(self):
        self.vector_db = FaissVectorDatabase()
        self.summarizer = SummarizationService()

    def handle(self, command: QueryPdfCommand):
        # Load the document vectors
        db = self.vector_db.load_document(command.document_id)

        # Query the PDF
        response = self.summarizer.query_pdf(db, command.query)

        return {
            "query": command.query,
            "response": response
        }
```

## Step 5: Create Domain Models and Interfaces

Create necessary domain models in the Domain folder:

### 5.1 Interfaces

Create `Domain/Interfaces/IPdfExtractor.py`:

```python
from abc import ABC, abstractmethod

class IPdfExtractor(ABC):
    @abstractmethod
    def extract(self, pdf_path):
        pass
```

Create similar interface files for `ITextChunker`, `IVectorDatabase`, and `ISummarizationService`.

### 5.2 Models

Create `Domain/Models/PdfPage.py`:

```python
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class PdfPage:
    page_number: int
    text: str
    images: List[Dict[str, Any]] = None
```

Create similar model files for `TextChunk`, `ProcessPdfCommand`, and `QueryPdfCommand`.

## Step 6: Create API Endpoints

Create `API/PdfProcessorController.py`:

```python
from fastapi import APIRouter, UploadFile, File, Form
import os
import tempfile
from ..Application.Commands.ProcessPdfCommandHandler import ProcessPdfCommandHandler
from ..Application.Commands.QueryPdfCommandHandler import QueryPdfCommandHandler
from ..Domain.Models.ProcessPdfCommand import ProcessPdfCommand
from ..Domain.Models.QueryPdfCommand import QueryPdfCommand

router = APIRouter(prefix="/pdf", tags=["PDF Processor"])

@router.post("/process")
async def process_pdf(
    file: UploadFile = File(...),
    generate_summary: bool = Form(True),
    summary_strategy: str = Form("map_reduce")
):
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        # Write the uploaded file content
        temp_file.write(await file.read())
        temp_file_path = temp_file.name

    try:
        # Process the PDF
        handler = ProcessPdfCommandHandler()
        result = handler.handle(ProcessPdfCommand(
            pdf_path=temp_file_path,
            generate_summary=generate_summary,
            summary_strategy=summary_strategy
        ))

        return result
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

@router.post("/query")
async def query_pdf(document_id: str, query: str):
    handler = QueryPdfCommandHandler()
    result = handler.handle(QueryPdfCommand(
        document_id=document_id,
        query=query
    ))

    return result
```

## Step 7: Usage Example

Create a simple script to demonstrate the full process:

```python
import os
from dotenv import load_dotenv
from Features.PdfProcessor.Application.Commands.ProcessPdfCommandHandler import ProcessPdfCommandHandler
from Features.PdfProcessor.Application.Commands.QueryPdfCommandHandler import QueryPdfCommandHandler
from Features.PdfProcessor.Domain.Models.ProcessPdfCommand import ProcessPdfCommand
from Features.PdfProcessor.Domain.Models.QueryPdfCommand import QueryPdfCommand

# Load environment variables
load_dotenv()

def main():
    # Path to your PDF
    pdf_path = "path/to/your/document.pdf"

    # Process the PDF
    process_handler = ProcessPdfCommandHandler()
    process_result = process_handler.handle(ProcessPdfCommand(
        pdf_path=pdf_path,
        generate_summary=True,
        summary_strategy="map_reduce"
    ))

    print(f"Document processed with ID: {process_result['document_id']}")
    print(f"Summary: {process_result['summary']}")

    # Query the processed PDF
    document_id = process_result['document_id']
    query = "What are the main findings in this document?"

    query_handler = QueryPdfCommandHandler()
    query_result = query_handler.handle(QueryPdfCommand(
        document_id=document_id,
        query=query
    ))

    print(f"Query: {query_result['query']}")
    print(f"Response: {query_result['response']}")

if __name__ == "__main__":
    main()
```

## Additional Notes

1. **Data Persistence**: The vector database files are stored locally in the directory specified by `VECTOR_DB_PATH`.

2. **Error Handling**: Add proper error handling and logging in a production environment.

3. **Performance**: For larger PDFs, consider adding background processing using Celery or similar.

4. **Concurrency**: The current implementation is not thread-safe. For multi-user environments, add proper locking mechanisms.

5. **Alternative Local Vector DBs**: Both FAISS and ChromaDB are solid options:
   - FAISS: Faster for similarity search but requires more manual management
   - ChromaDB: Better persistence and querying capabilities with more features
