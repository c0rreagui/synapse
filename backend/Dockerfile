# Use uma imagem leve do Python
FROM python:3.10-slim

# Define diretório de trabalho
WORKDIR /app

# Instala dependências do sistema (FFmpeg é a chave aqui)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala Playwright e navegadores
RUN pip install playwright && playwright install --with-deps chromium

# Expõe a porta 8000
EXPOSE 8000

# Comando padrão (live reload habilitado)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
