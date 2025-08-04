#!/bin/bash

# Multi-Protocol Agent Orchestrator Deployment Script

set -e

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(cd "$PROJECT_DIR/../.." && pwd)"

echo "🚀 Deploying Multi-Protocol Agent Orchestrator"

# Configuration
ACTION="${1:-start}"
IMAGE_TAG="${2:-latest}"

echo "📋 Deployment Configuration:"
echo "   Action: $ACTION"
echo "   Image Tag: $IMAGE_TAG"
echo "   Project: $PROJECT_DIR"
echo "   Repository: $REPO_ROOT"
echo ""

# Change to repository root for docker-compose
cd "$REPO_ROOT"

case "$ACTION" in
    "build")
        echo "🏗️  Building orchestrator image..."
        cd "$PROJECT_DIR"
        ./scripts/build.sh "$IMAGE_TAG"
        ;;
    
    "start")
        echo "▶️  Starting orchestrator stack..."
        
        # Check if .env file exists
        if [ ! -f ".env" ]; then
            echo "⚠️  No .env file found. Creating from example..."
            if [ -f "$PROJECT_DIR/.env.example" ]; then
                cp "$PROJECT_DIR/.env.example" .env
                echo "📝 .env file created. Please edit it with your API keys:"
                echo "   - OPENAI_API_KEY"
                echo "   - ANTHROPIC_API_KEY"
                echo ""
            else
                echo "❌ No .env.example found!"
                exit 1
            fi
        fi
        
        # Start the orchestrator and dependencies
        docker-compose up -d orchestrator
        
        # Wait for services to be healthy
        echo "⏳ Waiting for services to be healthy..."
        sleep 10
        
        # Check service health
        echo "🔍 Checking service health..."
        docker-compose ps orchestrator
        
        echo ""
        echo "✅ Orchestrator deployed successfully!"
        echo ""
        echo "🌐 Access URLs:"
        echo "   Orchestrator API: http://localhost:8004"
        echo "   API Documentation: http://localhost:8004/docs"
        echo "   Health Check: http://localhost:8004/health"
        echo "   System Status: http://localhost:8004/status"
        echo ""
        echo "📊 Useful Commands:"
        echo "   docker-compose logs -f orchestrator    # View logs"
        echo "   docker-compose ps                      # Check status"
        echo "   docker-compose down                    # Stop services"
        ;;
    
    "stop")
        echo "⏹️  Stopping orchestrator..."
        docker-compose stop orchestrator
        echo "✅ Orchestrator stopped"
        ;;
    
    "restart")
        echo "🔄 Restarting orchestrator..."
        docker-compose restart orchestrator
        echo "✅ Orchestrator restarted"
        ;;
    
    "logs")
        echo "📜 Showing orchestrator logs..."
        docker-compose logs -f orchestrator
        ;;
    
    "status")
        echo "📊 Orchestrator Status:"
        echo ""
        docker-compose ps orchestrator
        echo ""
        echo "🔍 Service Health:"
        curl -s http://localhost:8004/health | python3 -m json.tool 2>/dev/null || echo "Service not responding"
        ;;
    
    "down")
        echo "🛑 Stopping all services..."
        docker-compose down
        echo "✅ All services stopped"
        ;;
    
    "clean")
        echo "🧹 Cleaning up orchestrator resources..."
        docker-compose down -v
        docker rmi agent-orchestrator:latest 2>/dev/null || true
        echo "✅ Cleanup complete"
        ;;
    
    *)
        echo "❌ Unknown action: $ACTION"
        echo ""
        echo "Usage: $0 <action> [image_tag]"
        echo ""
        echo "Actions:"
        echo "   build    Build the orchestrator Docker image"
        echo "   start    Start the orchestrator and dependencies"
        echo "   stop     Stop the orchestrator"
        echo "   restart  Restart the orchestrator"
        echo "   logs     Show orchestrator logs"
        echo "   status   Show orchestrator status"
        echo "   down     Stop all services"
        echo "   clean    Clean up all resources"
        echo ""
        echo "Examples:"
        echo "   $0 build v1.0.0      # Build with specific tag"
        echo "   $0 start             # Start with latest image"
        echo "   $0 logs              # View logs"
        echo "   $0 status            # Check status"
        exit 1
        ;;
esac