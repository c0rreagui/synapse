# Use uma imagem leve do Python
FROM python:3.11-slim

# Define diretorio de trabalho
WORKDIR /app

# Instala dependencias do sistema (FFmpeg + curl + Chromium + VNC tools)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    curl \
    chromium \
    chromium-driver \
    fonts-liberation \
    fonts-croscore \
    fonts-crosextra-carlito \
    fonts-crosextra-caladea \
    fonts-noto-core \
    fonts-freefont-ttf \
    fonts-dejavu-core \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgbm1 \
    libasound2 \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    && rm -rf /var/lib/apt/lists/*

# Instala fonte Inter (Black/ExtraBold) do Google Fonts para legendas
RUN mkdir -p /usr/share/fonts/inter /tmp/inter && \
    curl -sL "https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip" -o /tmp/inter.zip && \
    apt-get update && apt-get install -y --no-install-recommends unzip fontconfig && \
    unzip -q /tmp/inter.zip -d /tmp/inter && \
    find /tmp/inter -name "*.otf" -exec mv {} /usr/share/fonts/inter/ \; && \
    find /tmp/inter -name "*.ttf" -exec mv {} /usr/share/fonts/inter/ \; && \
    fc-cache -f -v && \
    rm -rf /tmp/inter /tmp/inter.zip && \
    apt-get purge -y unzip && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala Playwright + browser Chromium
RUN pip install playwright && playwright install chromium

# Expõe portas: 8000 (API) + 6080 (noVNC)
EXPOSE 8000 6080

# Comando padrão (live reload habilitado)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
