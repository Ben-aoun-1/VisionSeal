# VisionSeal Production Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    chromium \
    chromium-driver \
    libmagic1 \
    libmagic-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright and browsers
RUN pip install playwright
RUN playwright install chromium
RUN playwright install-deps

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p logs screenshots uploads

# Set secure file permissions
RUN chmod 600 .env 2>/dev/null || true
RUN chmod +x *.py

# Create non-root user for security
RUN useradd -m -u 1000 visionseal && \
    chown -R visionseal:visionseal /app
USER visionseal

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start command
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]