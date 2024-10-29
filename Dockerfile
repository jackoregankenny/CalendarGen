# Use slim Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy only necessary files
COPY requirements.txt .
COPY src/ ./src/
COPY setup.py .

# Install dependencies and clean up in one layer
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn && \
    rm -rf /root/.cache/pip

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Command to run the application
CMD gunicorn --bind 0.0.0.0:$PORT src.webapp.app:app --log-file -