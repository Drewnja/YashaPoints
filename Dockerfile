# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire context
COPY . .

# Debug: List contents of the current directory
RUN ls -la

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make sure scripts in .local are usable:
ENV PATH=/root/.local/bin:$PATH

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]