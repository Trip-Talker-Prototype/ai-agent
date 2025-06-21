# Use official Python image
FROM python:3.13

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Install uv (if you're using uv)
RUN pip install uv

# Copy dependency files first for better caching
COPY pyproject.toml .
COPY requirements.txt .
COPY uv.lock .

# Install Python dependencies
RUN uv pip install --system -e .

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]