FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/templates /app/static /data/playlists /data/downloads

# Copy application files
COPY app.py .
COPY templates/ ./templates/

# Create a non-root user
RUN useradd -m -u 1000 musicuser && \
    chown -R musicuser:musicuser /app /data
USER musicuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/library-status || exit 1

# Run the application
CMD ["python", "app.py"]