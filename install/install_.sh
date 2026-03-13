#!/bin/bash

# Colores para feedback
CYAN='\033[0-36m'
GREEN='\033[0-32m'
YELLOW='\033[1-33m'
RED='\033[0-31m'
NC='\033[0m'

echo -e "${CYAN}==========================================${NC}"
echo -e "${CYAN}      AURCA ENGINE - SMART INSTALLER      ${NC}"
echo -e "${CYAN}==========================================${NC}"

# --- 1. Verificación e Instalación de Docker ---
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}[!] Docker no detectado. Instalando...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Iniciar Docker si está apagado
if ! sudo systemctl is-active --quiet docker; then
    echo -e "${YELLOW}[*] Iniciando servicio Docker...${NC}"
    sudo systemctl start docker
    sudo systemctl enable docker
fi

# --- 2. Validación de Puertos ---
if ! command -v lsof &> /dev/null; then sudo apt-get update && sudo apt-get install -y lsof &> /dev/null; fi

check_port() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null && return 1 || return 0
}

echo -e "${YELLOW}[*] Verificando puertos (3000, 5433, 9090)...${NC}"
for port in 3000 5433 9090; do
    if ! check_port $port; then
        echo -e "${RED}[!] Puerto $port ocupado. Abortando.${NC}"
        exit 1
    fi
done

# --- 3. Limpieza de Formatos (CRLF a LF) ---
echo -e "${YELLOW}[*] Blindando scripts contra formatos de Windows...${NC}"
find . -type f -name "*.sh" -exec sed -i 's/\r$//' {} +
chmod +x docker/miner/entrypoint.sh 2>/dev/null

# --- 4. Configuración de Red y .env ---
docker network create aurca_shared_net 2>/dev/null || true

if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${RED}[!] .env creado. Configúralo y reinicia el script.${NC}"
    exit 1
fi

# Cargar variables del .env para la notificación
export $(grep -v '^#' .env | xargs)

# --- 5. Detección de Hardware ---
GPU_DETECTED=false
if command -v nvidia-smi &> /dev/null && nvidia-smi -L &> /dev/null; then
    GPU_DETECTED=true
    echo -e "${GREEN}[+] Hardware compatible con GPU detectado.${NC}"
fi

# --- 6. Selección y Ejecución ---
echo -e "${CYAN}Selecciona el modo de despliegue:${NC}"
echo "1) Full Stack (GPU/Local)"
echo "2) Modo CPU (Servidor/VPS)"
echo "3) Salir"
read -p "Opción: " OPTION

case $OPTION in
    1) MODE="FULL (GPU)"; docker compose up -d --build ;;
    2) MODE="LIGHT (CPU)"; docker compose -f docker-compose-cpu.yml up -d --build ;;
    *) exit 0 ;;
esac

# --- 7. Notificación a Telegram ---
if [ "$NOTIFY_STARTUP" = "true" ] || [ "$NOTIFY_STARTUP" = "True" ]; then
    echo -e "${YELLOW}[*] Enviando notificación a Telegram...${NC}"
    MSG="🚀 *Aurca Engine Instalado*%0A%0A🖥 *Rig:* \`${RIG_NAME}\`%0A📦 *Modo:* \`${MODE}\`%0A🌍 *IP:* \`$(curl -s ifconfig.me)\`"
    
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d "chat_id=${TELEGRAM_CHAT_ID}" \
        -d "text=${MSG}" \
        -d "parse_mode=MarkdownV2" > /dev/null
fi

echo -e "${GREEN}==========================================${NC}"
echo -e " Instalación finalizada con éxito. "
echo -e "${GREEN}==========================================${NC}"