# Document Defect Analysis - Vertical Slice Architecture

This Flask application analyzes uploaded documents (PDF, Word) to identify and extract defects mentioned within their content. The project demonstrates **Vertical Slice Architecture** principles, organizing the codebase by **features** (agents) rather than by technical layers.

The application processes documents, breaks them into chunks, and uses AI to identify defects mentioned in the document text.

## Features

The application uses a vertical slice architecture with features organized into agent-based components:

- **PDF Agent** - Extracts and processes content from PDF files
- **Word Agent** - Extracts and processes content from Word documents
- **Main Agent** - Analyzes document content to identify and summarize defects mentioned in the documents

## Live Demo

[https://aider-dpna.onrender.com/](https://aider-dpna.onrender.com/)

## Development Process

- Initial development with [Cursor](https://www.cursor.com/) and [Claude API](https://www.anthropic.com/)
- Feature updaets with [Aider](https://aider.chat/docs/install.html) and [Claude API](https://www.anthropic.com/)
- Deployed with [Render](https://render.com/)

## Project Structure

The application follows a vertical slice architecture organized by agents:

```bash
app/
├── agents/                # Agent-based feature organization
│   ├── main/              # Main agent for defect analysis
│   │   ├── __init__.py    # Package initialization
│   │   ├── agent.py       # Agent implementation with routes
│   │   └── form.md        # Documentation for forms
│   ├── pdf/               # PDF processing agent
│   │   ├── __init__.py
│   │   └── agent.py
│   └── word/              # Word document processing agent
│       ├── __init__.py
│       └── agent.py
├── static/                # Static assets
│   └── ...
├── templates/             # HTML templates
│   ├── base.html          # Base template
│   └── home.html          # Home page template
└── uploads/               # Directory for uploaded files
```

Detailed instructions for LLMs can be found in the [**feature_conventions.md**](./feature_conventions.md) file in the root project directory.

## Setup Instructions

### Docker Setup (Recommended)

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/vertical-slice-architecture-flask.git
   cd vertical-slice-architecture-flask
   ```

2. **Set up environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit the `.env` file with the appropriate configuration:

   ```
   # If using OpenAI (optional)
   OPENAI_API_KEY=your_openai_key_here
   
   # Choose LLM engine: 'local' (Ollama) or 'openai'
   LLM_ENGINE=local
   
   # Secret key for Flask (Optional)
   SECRET_KEY=your_secret_key_here  # defaults to dev_key_for_flask_app
   ```

3. **Build and start the Docker container**

   ```bash
   docker compose up
   ```

   The application will be available at http://localhost:5001

4. **To stop the application**

   ```bash
   # Press Ctrl+C if running in the foreground, or
   docker compose down
   ```

5. **To run in detached mode (background)**
   ```bash
   docker compose up -d
   ```

### Option 2: Running Locally

1. **Clone the repository**

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   ```

3. **Activate the environment**

   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

4. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit the `.env` file to add your OpenAI API key.

6. **Run the application**

   ```bash
   ./run.sh
   # or
   flask run
   ```

## Testing

Run all tests using `pytest`:

```bash
pytest
```

## Docker Details

1. **Dockerfile** - Sets up the Python environment with all required dependencies
2. **docker-compose.yml** - Configures the services:
   - **web** - The Flask application
   - **ollama** - Local LLM service running Llama 3 by default
3. **.dockerignore** - Excludes unnecessary files from the Docker image
4. **.env.example** - Template for environment variables

The container includes all necessary dependencies, including Tesseract OCR and Poppler for PDF processing. Your uploads folder is mounted as a volume so files will persist between container restarts.

### Local LLM Support

By default, the application uses Ollama with Llama 3 (8B parameters) as the local LLM. The first startup will take some time as it downloads the model (approximately 4.7GB). You can switch to other models by changing the `OLLAMA_MODEL` environment variable.

Some recommended models:
- `llama3:8b` (default) - Good all-around model with excellent instruction following
- `phi3:mini` - Microsoft's 3.8B parameter model, smaller but still effective for summarization
- `mistral:7b` - Another good option with strong performance

To use OpenAI instead of a local model, set `LLM_ENGINE=openai` in your .env file and ensure you have a valid API key.
