### Builder stage ###
FROM python:3.10-slim as builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install ComfyUI requirements
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ComfyUI/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


### Runtime stage ###
FROM python:3.10-slim as runtime

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ComfyUI/ .

# Set Volumes
VOLUME ["/app/input", "/app/output", "/app/models"]

# Set Port
EXPOSE 8188

# Run ComfyUI
CMD ["python", "main.py", "--listen", "0.0.0.0"] 