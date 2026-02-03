# DIP Studio MCP Server Dockerfile
# Multi-stage build for optimized image size

# Stage 1: Build stage
FROM python:3.10-slim as builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies for PDF and document processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    # For PDF processing
    libmagic1 \
    # For image processing (PIL/Pillow)
    libjpeg-dev \
    zlib1g-dev \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src/ ./src/
COPY config.yaml ./
COPY requirements.txt ./

# Create data directories
RUN mkdir -p requirements api-specs

# Copy data files (will be empty if directories don't exist)
COPY requirements/ ./requirements/
COPY api-specs/ ./api-specs/

# Expose the MCP server port (default: 8001)
EXPOSE 8001

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/mcp')" || exit 1

# Run the MCP server
CMD ["python", "-m", "src.server"]
