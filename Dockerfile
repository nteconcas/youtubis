FROM python:3.11-slim

# Instalar FFmpeg (obrigatório para conversão de áudio e merge de vídeo+audio)
RUN apt-get update && apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro para aproveitar cache do Docker
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copiar o restante do código
COPY . .

# Criar diretório de downloads
RUN mkdir -p downloads

# Expor porta 8796
EXPOSE 8796

# Comando para rodar em produção com Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8796", "app:app"]
