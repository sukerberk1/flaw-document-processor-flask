FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Tesseract for OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p app/uploads && chmod 777 app/uploads

# Set environment variables
ENV FLASK_APP=app
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Expose port
EXPOSE 5000

# Make script executable
COPY run_with_ollama.sh /app/run_with_ollama.sh
RUN chmod +x /app/run_with_ollama.sh

# Run with the Ollama initialization script
CMD ["/app/run_with_ollama.sh"]