FROM nvidia/cuda:12.2.0-base-ubuntu22.04

# Instalamos dependencias: añadimos 'sed' para limpiar el entrypoint
RUN apt-get update && apt-get install -y \
    wget \
    tar \
    gettext-base \
    coreutils \
    sed \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Descarga y extracción de Nanominer
RUN wget https://github.com/nanopool/nanominer/releases/download/v3.9.2/nanominer-linux-3.9.2.tar.gz \
    && tar -xvf nanominer-linux-3.9.2.tar.gz \
    && rm nanominer-linux-3.9.2.tar.gz

# 2. Copiamos la configuración y el script
COPY docker/miner/config.ini .
COPY docker/miner/entrypoint.sh .

# --- FIX CRÍTICO ---
# Eliminamos los retornos de carro (\r) de Windows antes de dar permisos
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

# 3. Ejecución
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]