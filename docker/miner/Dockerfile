FROM nvidia/cuda:12.2.0-base-ubuntu22.04

# Instalamos dependencias incluyendo 'coreutils' para stdbuf
RUN apt-get update && apt-get install -y wget tar gettext-base coreutils && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Descarga y extracción de Nanominer
RUN wget https://github.com/nanopool/nanominer/releases/download/v3.9.2/nanominer-linux-3.9.2.tar.gz \
    && tar -xvf nanominer-linux-3.9.2.tar.gz \
    && rm nanominer-linux-3.9.2.tar.gz

# Copiamos la configuración y el script de entrada
COPY docker/miner/config.ini .
COPY docker/miner/entrypoint.sh .

# Aseguramos permisos de ejecución
RUN chmod +x entrypoint.sh

# Forma JSON recomendada (invoca al script que maneja la lógica)
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]