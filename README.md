# Vertical Slice Architecture (Flask)

This project demonstrates how to apply **Vertical Slice Architecture** to a Flask web application, where the application is organized by **features**, not technical layers.

[YouTube Demo – Vertical Slice Architecture](https://www.youtube.com/watch?v=dabeidyv5dg&t=1656s)

## Features

Located in the `/app/features` directory. Each feature encapsulates its own logic and dependencies:

- `pdf_processor` – Summarizes content from PDF files using the ChatGPT API.
- `excel_processor` – Processes Excel files and summarizes them using the ChatGPT API.

## Live Demo

[https://aider-dpna.onrender.com/](https://aider-dpna.onrender.com/)

## Development Process

- Initial development with [Cursor](https://www.cursor.com/) and [Claude API](https://www.anthropic.com/)
- Feature updaets with [Aider](https://aider.chat/docs/install.html) and [Claude API](https://www.anthropic.com/)
- Deployed with [Render](https://render.com/)

## Project Structure

Each feature is self-contained with:

```bash
app/features/<feature_name>/
├── __init__.py         # Package initialization and registration
├── models.py           # Data models and database interactions
├── services.py         # Business logic and core functionality
├── views.py            # Route handlers and request processing
└── template/           # Frontend assets
    ├── index.html      # Main template for the feature
    └── js/
        └── new_feature.js  # Feature-specific JavaScript
```

Detailed instructions for LLMs can be found in the [**feature_conventions.md**](./feature_conventions.md) file in the root project directory.

## Setup Instructions

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

5. **Run the application**

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
