FROM mcr.microsoft.com/playwright:v1.41.0-jammy

WORKDIR /app

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Run the app
CMD ["python3", "app.py"]
