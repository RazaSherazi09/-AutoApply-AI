# ────────────────────────────────────────────────
# AutoApply AI — Dockerfile
# Base: Playwright Python image with Chromium
# ────────────────────────────────────────────────

FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set working directory
WORKDIR /app

# Copy dependency manifest first (for Docker layer caching)
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Pre-download sentence-transformers model (cached in image)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Create directories
RUN mkdir -p uploads logs

# Expose ports: FastAPI (8000) + Streamlit (8501)
EXPOSE 8000 8501

# Default: run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
