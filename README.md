# Flask Vertical Slice Architecture

This project demonstrates a Flask web application structured using the vertical slice architecture pattern, where code is organized by feature rather than by technical layer.

## Project Structure

Each feature has its own directory containing all the components it needs:
- API endpoints (api.py)
- Data models (models.py)
- Business logic (services.py)
- UI views (views.py)
- Tests for each component

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the application: `./run.sh` or `flask run`

## Testing
Run tests with pytest:
```
pytest
```
