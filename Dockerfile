# Dockerfile

FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Create a non-root user
RUN useradd --create-home --shell /bin/bash app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies using uv
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Remove any existing Celery beat schedule file to avoid permission issues
RUN rm -f /app/celerybeat-schedule

# Change ownership of the app directory to the app user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

# Expose the port FastAPI is running on
EXPOSE 8000

# Command to run the application with Uvicorn
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]