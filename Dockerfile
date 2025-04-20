FROM python:3.11-slim

# 1. Install ALL required system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    tesseract-ocr-eng \
    tesseract-ocr-ara \  # Optional: For Arabic support
    # Add more languages as needed:
    # tesseract-ocr-fra \  # French
    # tesseract-ocr-spa \  # Spanish
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Verify Tesseract installation
RUN tesseract --version

WORKDIR /app

# 3. Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy application
COPY . .

# 5. Explicitly set environment variables
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
