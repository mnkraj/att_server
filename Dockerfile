# Use the Python 3.9 slim image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:${PATH}"

# Install dependencies (without libssl1.1)
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    libssl3 \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libatk1.0-0 \
    libcups2 \
    libatk-bridge2.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libasound2 \
    libxss1 \
    libxtst6 \
    libdbus-glib-1-2 \
    fonts-liberation \
    libfontconfig1 \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+' | cut -d. -f1) && \
    wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}.0.0/linux64/chromedriver-linux64.zip" -O /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /usr/bin/ && \
    rm /tmp/chromedriver.zip && \
    mv /usr/bin/chromedriver-linux64/chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY . /app

# Expose port
EXPOSE $PORT

# Run the app
CMD ["python", "app.py"]
