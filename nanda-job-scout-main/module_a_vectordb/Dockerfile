# ============================================
# Module A — Vector DB (Resume Tips)
# ============================================
FROM python:3.11-slim

WORKDIR /app

# Install system deps for sentence-transformers
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
RUN pip install --no-cache-dir \
    fastapi uvicorn pydantic \
    langchain langchain-core langchain-community langchain-text-splitters \
    sentence-transformers chromadb

# Copy application code
COPY . .

# Pre-build the vector database during image build
RUN python build_db.py

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
