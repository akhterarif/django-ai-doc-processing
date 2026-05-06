#!/bin/bash
# Script to initialize Ollama with required models

echo "Starting Ollama service..."
docker compose up -d ollama

echo "Waiting for Ollama to be ready..."
sleep 10

echo "Pulling gemma2:9b model..."
docker compose exec ollama ollama pull gemma2:9b

echo "Verifying model installation..."
docker compose exec ollama ollama list

echo "Ollama initialization complete!"
echo "You can now run: docker compose up"