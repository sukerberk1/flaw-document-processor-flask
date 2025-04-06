#!/bin/bash
set -e

# Wait for Ollama to be ready
echo "Waiting for Ollama service to be ready..."
until $(curl --output /dev/null --silent --head --fail http://ollama:11434/api/tags); do
    printf '.'
    sleep 2
done
echo "Ollama service is up"

# Get model from environment or use default
MODEL=${OLLAMA_MODEL:-llama3:8b}

# Pull model if not already downloaded
echo "Ensuring model $MODEL is available..."
if ! curl -s http://ollama:11434/api/tags | grep -q "$MODEL"; then
    echo "Pulling model $MODEL (this may take a while)..."
    curl -X POST http://ollama:11434/api/pull -d "{\"name\":\"$MODEL\"}"
else
    echo "Model $MODEL is already available"
fi

# Start the Flask application
echo "Starting Flask application..."
gunicorn --bind 0.0.0.0:$PORT wsgi:app