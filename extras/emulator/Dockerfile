# Usa uma imagem oficial do Python como base
FROM python:3.10

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos de requirements para o container
COPY requirements.txt .

# Instala os pacotes necessários
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante dos arquivos
COPY sensor_emulator.py .
