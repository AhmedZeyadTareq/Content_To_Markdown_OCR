FROM python:3.11-slim
# Streamlit Cloud-specific Dockerfile
FROM python:3.11-slim

# 1. Install Tesseract with English language data ONLY
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    tesseract-ocr-eng && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 2. Verify installation (this will fail the build if missing)
RUN tesseract --version

WORKDIR /app

# 3. Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy application files
COPY . .

# 5. Streamlit Cloud specific settings
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
