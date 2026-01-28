# Stage 1: Build
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
WORKDIR /app

# 1. Debug de Herramientas: Verificamos que el compilador esté listo
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ninja-build \
    unzip \
    && cmake --version && gcc --version

# 2. Copiamos definiciones
COPY pyproject.toml ./

# 3. Copiamos fuentes (necesario para compilar el motor)
COPY src ./src

# 4. DEBUG PRE-COMPILACIÓN: ¿Está el código donde debe?
RUN echo "--- ESTRUCTURA DE CPP_ENGINE ANTES DE BUILD ---" && \
    ls -R src/infrastructure/adapters/binance/cpp_engine

# 5. Sincronización y Compilación (Forzamos log detallado de CMake)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-editable -v || (ls -R src/infrastructure/adapters/binance/cpp_engine && exit 1)

# 6. DEBUG POST-COMPILACIÓN (En Builder): ¿Se creó el .so y dónde?
RUN echo "--- BUSCANDO BINARIOS EN .VENV (BUILDER) ---" && \
    find /app/.venv -name "aurca_engine*" && \
    echo "--- CONTENIDO DE SITE-PACKAGES (BUILDER) ---" && \
    ls -R /app/.venv/lib/python3.12/site-packages/aurca_engine || echo "Carpeta aurca_engine no encontrada"

# Stage 2: Runtime
FROM python:3.12-slim-bookworm
WORKDIR /app

# Instalamos dependencias de ejecución (libstdc++6 es vital para C++)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

# Traemos el entorno virtual
COPY --from=builder /app/.venv /app/.venv
# Traemos el código (excepto lo ignorado por .dockerignore)
COPY . .

# Limpieza total de rastros de Windows
RUN find . -name "*.pyd" -delete && find . -name "__pycache__" -type d -exec rm -rf {} +

# Variables de Entorno
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/src"
ENV PYTHONUNBUFFERED=1

# 7. DEBUG FINAL DE RUNTIME (La prueba de fuego)
RUN echo "--- INSPECCIÓN FINAL DE SITE-PACKAGES ---" && \
    find /app/.venv/lib/python3.12/site-packages -name "aurca_engine*"

RUN echo "--- PRUEBA DE IMPORTACIÓN DIRECTA ---" && \
    python3 -c "import sys; print('Rutas:', sys.path); import aurca_engine; print('✅ ÉXITO: aurca_engine importado desde:', aurca_engine.__file__)" || \
    (echo "❌ ERROR: No se pudo importar el motor" && exit 1)

CMD ["python", "src/main.py"]