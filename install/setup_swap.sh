#!/bin/bash

# chmod +x setup_swap.sh

# --- CONFIGURACIÓN ---
SWAP_PATH="/swapfile"
SWAP_SIZE="4G"

# Colores para mensajes profesionales
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}[INFO] Iniciando optimización de memoria para Minería...${NC}"

# 1. Verificar si somos ROOT
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}[ERROR] Este script debe ejecutarse con sudo.${NC}" 
   exit 1
fi

# 2. Verificar si el Swap ya existe para no romper nada
if grep -q "$SWAP_PATH" /proc/swaps; then
    echo -e "${GREEN}[OK] El Swap ya está activo. No es necesario hacer nada.${NC}"
    free -h
    exit 0
fi

# 3. Crear el archivo de Swap
echo -e "${BLUE}[1/5] Creando archivo de Swap de $SWAP_SIZE...${NC}"
fallocate -l $SWAP_SIZE $SWAP_PATH || dd if=/dev/zero of=$SWAP_PATH bs=1M count=4096

# 4. Permisos de seguridad
echo -e "${BLUE}[2/5] Ajustando permisos (chmod 600)...${NC}"
chmod 600 $SWAP_PATH

# 5. Formatear como Swap
echo -e "${BLUE}[3/5] Formateando archivo...${NC}"
mkswap $SWAP_PATH > /dev/null

# 6. Activar Swap
echo -e "${BLUE}[4/5] Activando Swap inmediatamente...${NC}"
swapon $SWAP_PATH

# 7. Hacerlo permanente en /etc/fstab
echo -e "${BLUE}[5/5] Configurando persistencia en /etc/fstab...${NC}"
if ! grep -q "$SWAP_PATH" /etc/fstab; then
    echo "$SWAP_PATH none swap sw 0 0" >> /etc/fstab
fi

echo -e "${GREEN}--------------------------------------------------${NC}"
echo -e "${GREEN}[ÉXITO] Memoria virtual configurada correctamente.${NC}"
echo -e "${GREEN}--------------------------------------------------${NC}"

# 8. Mostrar resultado final
free -h