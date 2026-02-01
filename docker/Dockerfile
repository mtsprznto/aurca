# Stage 1: Build
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake ninja-build && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
# Copiamos la carpeta del motor (esto es vital para el path en el pyproject)
COPY src/infrastructure/adapters/binance/cpp_engine ./src/infrastructure/adapters/binance/cpp_engine

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

# Stage 2: Runtime
FROM python:3.12-slim-bookworm
WORKDIR /app

# Solo necesitamos la librería estándar de C++ para ejecutar
RUN apt-get update && apt-get install -y --no-install-recommends \
    libstdc++6 && \
    rm -rf /var/lib/apt/lists/*

# Copiamos el entorno virtual y el código
COPY --from=builder /app/.venv /app/.venv
COPY . .

# Configuramos variables de entorno
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/src"
ENV PYTHONUNBUFFERED=1

# Test rápido para asegurar que el binario de Linux (.so) cargue bien
RUN python -c "import aurca_engine; print('✅ MOTOR C++ CARGADO EN LINUX')"

CMD ["python", "-m", "src.main"]