#!/bin/bash

# Socratic AI Tutor Launch Script
# This script handles launching the Socratic AI Tutor application

# Check for .env file and create it if needed
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp env.example .env
    echo "Please edit .env file with your OpenAI API key"
    exit 1
fi

# Check if OpenAI API key is set
if grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "OPENAI API key found in .env"
else
    echo "Error: OPENAI_API_KEY not properly set in .env file"
    echo "Please edit .env and set your OpenAI API key"
    exit 1
fi

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "Error: Docker is not running or not installed"
        echo "Please start Docker and try again"
        exit 1
    fi
}

# Function to clean and rebuild frontend
rebuild_frontend() {
    echo "Rebuilding frontend..."
    cd frontend
    npm install
    npm run build
    cd ..
}

# Build and start services with docker-compose
start_services() {
    echo "Starting Socratic AI Tutor services..."
    docker-compose down
    docker-compose up --build -d
    
    echo "Services started! Socratic AI Tutor is now running."
    echo "Backend API: http://localhost:8000"
    echo "Frontend: http://localhost:3001"
}

# Command line arguments
case "$1" in
    rebuild)
        check_docker
        rebuild_frontend
        start_services
        ;;
    stop)
        echo "Stopping Socratic AI Tutor services..."
        docker-compose down
        echo "Services stopped"
        ;;
    *)
        check_docker
        start_services
        ;;
esac 