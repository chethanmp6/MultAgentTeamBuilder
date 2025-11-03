# Multi-stage Dockerfile for Hierarchical Agent System API
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY api/ ./api/
COPY src/ ./src/
COPY configs/ ./configs/

# Create .env file with placeholder values
COPY env.example .env

# Set environment variables
ENV PYTHONPATH=/app
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV PYTHONUNBUFFERED=1

# Add local packages to PATH
ENV PATH=/root/.local/bin:$PATH

# Expose the API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run the API server
CMD ["python", "-m", "uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]