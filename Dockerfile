# Use the official pre-configured Playwright image with Python & browser binaries
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Prevent Python from buffering outputs (ensures logs show up in Render dashboard instantly)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working directory
WORKDIR /app

# Copy dependency manifest first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies (upgrade pip first)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Set executable permission for startup script
RUN chmod +x start.sh

# Render default fallback port (dynamic port mapping occurs at runtime)
EXPOSE 10000

# Start Streamlit dynamically bound to Render's port
CMD ["sh", "start.sh"]
