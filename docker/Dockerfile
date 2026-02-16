# ==========================================
# Stage 1: Builder (Compilación)
# =========================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake ninja-build && \
    rm -rf /var/lib/apt/lists/*

ENV CMAKE_GENERATOR=Ninja
ENV UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
# Copiamos la carpeta del motor (esto es vital para el path en el pyproject)
COPY src/infrastructure/adapters/binance/cpp_engine ./src/infrastructure/adapters/binance/cpp_engine

RUN uv cache clean aurca-engine

# PRIMERO: Instalamos las dependencias de construcción en el entorno
RUN uv venv .venv
ENV PATH="/app/.venv/bin:$PATH"
RUN uv pip install scikit-build-core pybind11 setuptools

# SEGUNDO: Ahora sí, el sync funcionará con --no-build-isolation
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --no-build-isolation

# Copiamos el resto del código fuente
COPY . .

# Instalamos el proyecto
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-build-isolation


# --- DEBUG STAGE 1 ---
RUN echo "DEBUG: Listando archivos en site-packages del venv builder:" && \
    find .venv/lib/python3.12/site-packages -name "*aurca_engine*"
# ---------------------


# ==========================================
# Stage 2: Runtime (Producción)
# ==========================================
FROM nvidia/cuda:12.6.3-runtime-ubuntu22.04
WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Santiago

# Solo necesitamos la librería estándar de C++ para ejecutar
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    build-essential cmake ninja-build && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && apt-get install -y --no-install-recommends \
    python3.12 python3.12-venv python3.12-dev libstdc++6 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/uv
ENV PATH="/uv/bin:$PATH"

# Copiamos el entorno virtual y el código
COPY . .

# Configuramos variables de entorno
ENV PATH="/app/.venv/bin:$PATH"
ENV CMAKE_GENERATOR=Ninja
ENV PYTHONPATH="/app:/app/src"
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv .venv --python python3.12 && \
    uv pip install scikit-build-core pybind11 setuptools debugpy && \
    uv sync --frozen --no-dev --no-build-isolation

# 5. Enlace simbólico para comodidad
RUN ln -sf /app/.venv/bin/python /usr/bin/python

# --- DEBUG STAGE 2 ---
RUN echo "DEBUG: Verificando visibilidad del venv en Runtime:" && \
    ls -l /app/.venv/bin/python && \
    /app/.venv/bin/python -m pip list | grep aurca || echo "AURCA NO INSTALADO"
# ---------------------

EXPOSE 5678

# Test rápido para asegurar que el binario de Linux (.so) cargue bien
RUN python -c "import aurca_engine; print('MOTOR C++ CARGADO EN LINUX')"

CMD ["python", "-m","debugpy", "--listen", "0.0.0.0:5678","-m", "src.main"]