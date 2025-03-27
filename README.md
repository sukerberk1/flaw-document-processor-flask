# PDF Summarizer

A web application that summarizes PDF documents using natural language processing techniques.

## Features

- Upload PDF files
- Extract text content from PDFs
- Generate concise summaries using NLP
- Adjustable summary length
- Display word count statistics

## Project Structure

The application follows a vertical slice architecture for modularity:

```
app/
├── features/
│   ├── pdf_processing/  # PDF extraction and summarization
│   └── web/             # Web controllers and routes
├── static/              # CSS and JavaScript
└── templates/           # HTML templates
```

## Setup

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
```

2. Activate the virtual environment:
```bash
# On macOS/Linux
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

Start the Flask development server:
```bash
python app.py
```

The application will be available at http://127.0.0.1:5000/

## Usage

1. Open the application in your web browser
2. Upload a PDF file
3. Adjust the summary length using the slider
4. Click "Summarize" to process the PDF
5. View the generated summary and statistics
