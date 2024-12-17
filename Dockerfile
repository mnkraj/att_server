# Use Python base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:${PATH}"

# Install required dependencies for Selenium and Chromium
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    chromium-browser \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY . /app

# Expose dynamic Railway port
EXPOSE $PORT

# Run Flask app
CMD ["python", "app.py"]
