@echo off
title AURCA - Pre-flight Hardware Control
setlocal

:: 1. VERIFICACIÓN DE PERMISOS
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Debes ejecutar este .bat como ADMINISTRADOR.
    echo Haz clic derecho sobre el archivo y selecciona "Ejecutar como administrador".
    pause
    exit /b
)

:: 2. RESET Y PREPARACIÓN
echo [DEBUG] Reseteando frecuencias previas...
nvidia-smi -rgc >nul 2>&1

:: 3. BLOQUEO DE FRECUENCIA (LGC)
:: 1100MHz es un punto dulce para la 3060 Laptop: consume poco y rinde bien en ETC.
echo [INFO] Bloqueando frecuencia del nucleo a 1100MHz...
nvidia-smi -lgc 1100,1100
if %errorLevel% neq 0 (
    echo [ALERTA] No se pudo bloquear la frecuencia. Verificando drivers...
)

:: 4. VERIFICACIÓN DE TEMPERATURA
for /f "tokens=*" %%a in ('nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits') do set TEMP=%%a
echo [DEBUG] Temperatura actual: %TEMP% grados Celsius.

:: 5. LEVANTAR DOCKER STACK
echo [INFO] Iniciando contenedores Aurca...
docker compose up -d --build

echo ---------------------------------------------------
echo [SUCCESS] Sistema Aurca en linea.
echo Monitorea el panel en: http://localhost:9090
echo ---------------------------------------------------
pause