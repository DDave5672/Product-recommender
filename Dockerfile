FROM python:3.10-slim

# Install required system dependencies
RUN apt-get update && apt-get install -y python3-distutils

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Expose port (Railway uses $PORT)
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
