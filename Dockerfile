# Personal Assistant Demo - Docker Container
# ==========================================

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install uv

# Copy project files
COPY . .

# Create virtual environment and install dependencies
RUN cd personal_assistant_demo && \
    uv venv && \
    uv pip install --python .venv/bin/python -e .

# Expose port for web interface
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH="/app/personal_assistant_demo/src:$PYTHONPATH"
ENV PATH="/app/.venv/bin:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/status || exit 1

# Start the web interface
CMD ["python", "/app/scripts/start_web.py"]
