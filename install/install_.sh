#!/bin/bash
#---------------
# antes de correr este escript 
# chmod +x install/install_.sh
#---------------
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

if [ "$OPTION" == "1" ]; then # <--- Cambiado a 1 para Full Stack
    INSTALL_MODE="fullstack"
    echo -e "${GREEN}[INFO] Modo Full Stack seleccionado.${NC}"
    
    # --- LÓGICA DE PUERTOS SOLO PARA FULL STACK ---
    read -p "Configurar puerto para la interfaz Web (por defecto 3000): " WEB_PORT
    WEB_PORT=${WEB_PORT:-3000}
    
    read -p "Configurar puerto para la Base de Datos (por defecto 5432): " DB_PORT
    DB_PORT=${DB_PORT:-5432}
    
    # Inyectar en el .env para que docker-compose los vea
    sed -i "s/^WEB_PORT=.*/WEB_PORT=$WEB_PORT/" .env 2>/dev/null || echo "WEB_PORT=$WEB_PORT" >> .env
    sed -i "s/^DB_PORT=.*/DB_PORT=$DB_PORT/" .env 2>/dev/null || echo "DB_PORT=$DB_PORT" >> .env
    
else
    INSTALL_MODE="cpu"
    echo -e "${YELLOW}[INFO] Modo CPU seleccionado. Omitiendo configuración de puertos web/db.${NC}"
    WEB_PORT=3000
    DB_PORT=5432
fi

# Pregunta común: Puerto del Minero (Añadido para que sea útil en ambos)
read -p "Configurar puerto del monitor del Minero (por defecto 9090): " MINER_PORT
MINER_PORT=${MINER_PORT:-9090}
sed -i "s/^MINER_WEB_PORT=.*/MINER_WEB_PORT=$MINER_PORT/" .env 2>/dev/null || echo "MINER_WEB_PORT=$MINER_PORT" >> .env

case $OPTION in
    1) 
        MODE="FULL (GPU)"
        docker compose up -d --build 
        ;;
    2) 
        MODE="LIGHT (CPU)"
        # Forzamos la variable en el .env para que el docker-compose-cpu sepa qué dockerfile usar
        sed -i "s|^MINER_DOCKERFILE=.*|MINER_DOCKERFILE=docker/miner/Dockerfile.cpu|" .env
        docker compose -f docker-compose-cpu.yml up -d --build 
        ;;
    *) 
        echo "Saliendo..."
        exit 0 
        ;;
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