#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Verify Flask is installed
echo "Verifying Flask installation..."
python -c "import flask; print(f'Flask version: {flask.__version__}')"

# Run the application
echo "Starting the application..."
PYTHONPATH=$(pwd) python app.py
