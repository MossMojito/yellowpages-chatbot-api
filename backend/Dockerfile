# ─────────────────────────────────────────────────────────────────────────────
# Stage: production image
# Base: python:3.11-slim keeps the image small while staying official/stable
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Prevents Python from writing .pyc files and enables unbuffered stdout/stderr
# so gunicorn logs appear immediately in container log streams (e.g. Cloud Logging)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# ── 1. Install dependencies ───────────────────────────────────────────────────
# Copy requirements first so Docker can cache this layer.
# Rebuilds only when requirements.txt changes, not on every code change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── 2. Copy application source ────────────────────────────────────────────────
# Copies the Flask app module, entry-point, and the FAISS/data files
COPY . .

# ── 3. Expose port ────────────────────────────────────────────────────────────
EXPOSE 5000

# ── 4. Run with gunicorn ──────────────────────────────────────────────────────
# --workers 2  : 2 worker processes (tune for available CPUs in production)
# --bind       : listen on all interfaces at port 5000
# run:app      : module `run.py`, Flask application object `app`
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "run:app"]
