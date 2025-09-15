# Use the full Python 3.11 image, which includes more build tools
FROM python:3.11

WORKDIR /app

# Install system dependencies (git is still needed)
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the entire project
COPY . .

# Set Python path so imports work
ENV PYTHONPATH=/app

# Expose the port Koyeb expects
EXPOSE 8080

# Run the app with Gunicorn for production (using 1 worker for memory)
CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "web.backend.main:app", "--bind", "0.0.0.0:8080"]