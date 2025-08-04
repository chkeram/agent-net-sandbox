#!/bin/bash

# Multi-Protocol Agent Orchestrator Docker Build Script

set -e

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🏗️  Building Multi-Protocol Agent Orchestrator Docker Image"

# Configuration
IMAGE_NAME="agent-orchestrator"
IMAGE_TAG="${1:-latest}"
BUILD_ENV="${BUILD_ENV:-production}"

echo "📋 Build Configuration:"
echo "   Project: $PROJECT_DIR"
echo "   Image: $IMAGE_NAME:$IMAGE_TAG"
echo "   Build Environment: $BUILD_ENV"
echo ""

# Change to project directory
cd "$PROJECT_DIR"

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found in $PROJECT_DIR"
    exit 1
fi

# Build the Docker image
echo "🔨 Building Docker image..."
docker build \
    --build-arg BUILD_ENV="$BUILD_ENV" \
    --tag "$IMAGE_NAME:$IMAGE_TAG" \
    --tag "$IMAGE_NAME:latest" \
    .

# Verify the build
if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    echo ""
    echo "📊 Image Details:"
    docker images "$IMAGE_NAME:$IMAGE_TAG" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    echo ""
    echo "🚀 Usage:"
    echo "   docker run -p 8004:8004 $IMAGE_NAME:$IMAGE_TAG"
    echo ""
    echo "   Or with environment variables:"
    echo "   docker run -p 8004:8004 \\"
    echo "     -e OPENAI_API_KEY=your-key \\"
    echo "     -e ORCHESTRATOR_LLM_PROVIDER=openai \\"
    echo "     $IMAGE_NAME:$IMAGE_TAG"
else
    echo "❌ Docker build failed!"
    exit 1
fi