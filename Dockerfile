FROM python:3.10-slim

# Install system dependencies: git + distutils for build tools
RUN apt-get update && apt-get install -y \
    git \
    python3-distutils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Upgrade pip + install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Expose port
EXPOSE 5000

# Start the app
CMD ["python", "app.py"]
