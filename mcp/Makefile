# DIP Studio MCP Server Makefile

.PHONY: help build run stop clean logs shell test

# Docker image name
IMAGE_NAME = dip-studio-mcp-server
CONTAINER_NAME = dip-studio-mcp-server

help:
	@echo "Available targets:"
	@echo "  build    - Build Docker image"
	@echo "  run      - Run container using docker-compose"
	@echo "  stop     - Stop container"
	@echo "  logs     - Show container logs"
	@echo "  shell    - Open shell in running container"
	@echo "  clean    - Remove container and image"
	@echo "  test     - Test if server is running"

build:
	docker build -t $(IMAGE_NAME) .

run:
	docker-compose up -d

stop:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec mcp-server /bin/bash

test:
	@echo "Testing MCP server..."
	@curl -s http://localhost:8001/mcp > /dev/null && echo "✅ Server is running" || echo "❌ Server is not responding"

clean:
	docker-compose down -v
	docker rmi $(IMAGE_NAME) 2>/dev/null || true
