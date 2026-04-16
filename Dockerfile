FROM mcr.microsoft.com/playwright:v1.45.0-jammy

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install Python and pip
RUN apt-get update && apt-get install -y python3 python3-pip

# Copy and install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# CRITICAL: This installs the browser AND the system-level 
# dependencies (libgbm, libasound, etc.) required to run them.
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

EXPOSE 8080

CMD ["python3", "app.py"]
