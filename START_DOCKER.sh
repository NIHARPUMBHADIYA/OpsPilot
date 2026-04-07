#!/bin/bash

echo ""
echo "========================================"
echo "  OpsPilot++ - Docker Startup Helper"
echo "========================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    echo ""
    echo "Please install Docker:"
    echo "  macOS: https://www.docker.com/products/docker-desktop"
    echo "  Linux: https://docs.docker.com/engine/install/"
    echo ""
    exit 1
fi

echo "✅ Docker is installed"
echo ""

# Check if Docker daemon is running
echo "Checking if Docker daemon is running..."
if ! docker ps &> /dev/null; then
    echo "❌ Docker daemon is not running!"
    echo ""
    
    # Try to start Docker on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Starting Docker Desktop on macOS..."
        open -a Docker
        echo ""
        echo "Waiting for Docker to start (this may take 30-60 seconds)..."
        sleep 10
        
        # Check again
        if ! docker ps &> /dev/null; then
            echo ""
            echo "⏳ Docker is still starting..."
            echo "Please wait a bit longer and try again"
            exit 1
        fi
    else
        echo "Please start Docker daemon manually"
        echo "  Linux: sudo systemctl start docker"
        echo "  Or use: sudo dockerd"
        exit 1
    fi
fi

echo "✅ Docker daemon is running!"
echo ""
echo "========================================"
echo "  Docker is ready!"
echo "========================================"
echo ""
echo "You can now run: python main.py"
echo ""
