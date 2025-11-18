#!/bin/bash
set -e

# Deploy Big Node with locally built image
# This rebuilds the image from local files without pushing to GitHub

cd "$(dirname "$0")"

echo "============================================"
echo "Big Node - Local Development Deployment"
echo "============================================"
echo ""

# Check if config.env exists
if [ ! -f config.env ]; then
    echo "⚠️  config.env not found. Creating from template..."
    cp config.env.template config.env
    echo ""
    echo "⚠️  IMPORTANT: Edit config.env and set DELEGATION_AUTH_TOKEN!"
    echo ""
    read -p "Press Enter to continue after editing config.env..."
fi

# Load configuration
source config.env

echo "Building image from local files..."
echo ""

# Build and start services
docker compose \
    -f docker-compose.yml \
    -f docker-compose.mlnode.yml \
    -f docker-compose.mlnode.local.yml \
    build --no-cache

echo ""
echo "Starting services..."
echo ""

docker compose \
    -f docker-compose.yml \
    -f docker-compose.mlnode.yml \
    -f docker-compose.mlnode.local.yml \
    up -d

echo ""
echo "============================================"
echo "✓ Deployment complete!"
echo "============================================"
echo ""
echo "Services running:"
docker compose -f docker-compose.yml -f docker-compose.mlnode.yml -f docker-compose.mlnode.local.yml ps
echo ""
echo "View logs:"
echo "  docker logs -f mlnode-308"
echo ""
echo "Test delegation API:"
echo "  curl http://localhost:${DELEGATION_PORT:-9090}/health"
echo ""
