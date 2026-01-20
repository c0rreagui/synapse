# Synapse Unified Container
# Runs both Backend (FastAPI) and Frontend (Next.js) in a single container

FROM python:3.11-slim

# Install Node.js and system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    build-essential \
    supervisor \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ===== Backend Setup =====
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Install Playwright and browsers
RUN pip install playwright && playwright install --with-deps chromium

# ===== Frontend Setup =====
COPY frontend/package.json frontend/package-lock.json* /app/frontend/
WORKDIR /app/frontend
RUN npm install
WORKDIR /app

# ===== Copy Source Code =====
COPY backend /app/backend
COPY frontend /app/frontend

# ===== Build Frontend (Production) =====
WORKDIR /app/frontend
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build
WORKDIR /app

# ===== Supervisor Config =====
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports
EXPOSE 3000 8000

# Start via Supervisor (manages both processes)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
