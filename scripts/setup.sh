#!/bin/bash
set -e

echo "🚀 SkyWing Airlines - Multi-Agent RAG Setup"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Install: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose not found. Install: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Prerequisites satisfied"
echo ""

# Copy .env if not exists
if [ ! -f .env ]; then
    echo "📄 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env created. Edit this file to configure your environment."
else
    echo "⚠️  .env already exists. Skipping copy."
fi
echo ""

# Prompt for Azure (optional)
echo "🔑 Azure OpenAI Configuration (optional, press Enter to skip)"
read -p "Azure OpenAI Endpoint: " azure_endpoint
read -p "Azure OpenAI API Key: " azure_key

if [ -n "$azure_endpoint" ]; then
    sed -i.bak "s|AZURE_OPENAI_ENDPOINT=.*|AZURE_OPENAI_ENDPOINT=$azure_endpoint|" .env
    rm -f .env.bak
fi
if [ -n "$azure_key" ]; then
    sed -i.bak "s|AZURE_OPENAI_API_KEY=.*|AZURE_OPENAI_API_KEY=$azure_key|" .env
    rm -f .env.bak
fi
echo ""

# Build
echo "🏗️  Building Docker images..."
docker compose build
echo ""

# Start
echo "🚀 Starting services..."
docker compose up -d
echo ""

# Wait for health
echo "⏳ Waiting for services to be healthy..."
for i in {1..30}; do
    health_check=$(docker compose ps --format "{{.Names}}\t{{.Status}}" 2>/dev/null | grep -c "healthy" || true)
    if [ "$health_check" -lt 6 ]; then
        echo "   Waiting for services... ($i/30)"
        sleep 2
    else
        break
    fi
done

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next Steps:"
echo "   - Check service status: docker compose ps"
echo "   - View logs: make logs"
echo "   - Test chat API:"
echo "     curl -X POST http://localhost:8000/api/v1/chat \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -H 'X-API-Key: your-secret-api-key-change-in-production' \\"
echo "       -d '{\"message\": \"How do I reset VPN?\", \"session_id\": \"demo-001\", \"department\": \"it_support\"}'"
echo ""
echo "🎉 Happy hacking!"
