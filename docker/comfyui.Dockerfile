FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install ComfyUI requirements
COPY ComfyUI/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ComfyUI/ .

# Expose the port
EXPOSE 8188

# Run ComfyUI
CMD ["python", "main.py", "--listen", "0.0.0.0"] 