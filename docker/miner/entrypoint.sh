#!/bin/bash
set -e

# --- AURCA MODULAR ENGINE ---
# Variables con valores por defecto para evitar fallos
USER=${BINANCE_USER:-aurcaV01}
RIG=${RIG_NAME:-rig_generic}
ALGO_VAL=${ALGO:-Etchash}
THREADS=${CPU_THREADS:-0}
W_PORT=${MINER_WEB_PORT:-9090}

T_TARGET=${TARGET_TEMP:-70}
T_CRITICAL=${CRITICAL_TEMP:-82}
LHR_VAL=${LHR_LIMIT:-60}
echo "[DEBUG] --- Aurca Miner Layer: Preparando entorno ---"

# 1. Ajuste del Header de sección dinámico
sed -i "s/\[Etchash\]/\[$ALGO_VAL\]/" config.ini

# 2. Inyección de Credenciales y Red (Basado en .env)
sed -i "s/wallet = .*/wallet = $USER/" config.ini
sed -i "s/rigName = .*/rigName = $RIG/" config.ini
sed -i "s/webPort = .*/webPort = $W_PORT/" config.ini

# 3. Inyección de Pools (Permite cambiar de Pool sin tocar código)
echo "[DEBUG] Validando servidores de pool..."
if [ ! -z "$POOL_1" ]; then sed -i "s|pool1 = .*|pool1 = $POOL_1|" config.ini; fi
if [ ! -z "$POOL_2" ]; then sed -i "s|pool2 = .*|pool2 = $POOL_2|" config.ini; fi
if [ ! -z "$POOL_3" ]; then sed -i "s|pool3 = .*|pool3 = $POOL_3|" config.ini; fi

# 4. Inyección de Parámetros de Hardware
sed -i "s/targetTemp = .*/targetTemp = $T_TARGET/" config.ini
sed -i "s/criticalTemp = .*/criticalTemp = $T_CRITICAL/" config.ini
sed -i "s/lhr = .*/lhr = $LHR_VAL/" config.ini

# 5. Lógica específica CPU vs GPU
if [ "$ALGO_VAL" == "RandomX" ]; then
    echo "[DEBUG] Modo CPU Detectado: Configurando para Binance Pool..."
    sed -i "/lhr =/d" config.ini
    sed -i "/fanSpeed =/d" config.ini
    
    # Aseguramos salto de línea y añadimos parámetros de protocolo
    printf "\ncpuThreads = %s\n" "$THREADS" >> config.ini
    
    # BINANCE FIX: Usamos moneda vacía y forzamos el protocolo de rig
    sed -i "s/coin = .*/coin = /" config.ini
    
    # IMPORTANTE: Binance a veces requiere que el rig vaya pegado a la wallet con un punto
    # incluso si hay una línea de rigName aparte.
    sed -i "s/wallet = .*/wallet = $USER.$RIG/" config.ini
    
    # Añadimos parámetros de compatibilidad al final
    echo "protocol = 1" >> config.ini
else
    echo "[DEBUG] Modo GPU Detectado: Validando bypass de Binance..."
    sed -i "s/coin = .*/coin = ETC/" config.ini
    sed -i "/cpuThreads =/d" config.ini
    sed -i "/protocol =/d" config.ini
fi

# --- AURCA DEBUGGER ---
echo "[DEBUG] --- Configuración final aplicada con éxito ---"
# Ocultamos la wallet en el log por seguridad si el repo es público
cat config.ini | sed "s/wallet = .*/wallet = [REDACTED]/"
echo "[DEBUG] --------------------------------------------"

exec stdbuf -oL -eL ./nanominer config.ini