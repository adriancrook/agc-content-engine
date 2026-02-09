FROM python:3.11-slim

# Cache bust: v2
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Run the web app
CMD ["python", "web/app.py"]
