import psutil 
import subprocess
import structlog
import os

from src.application.ports.output.notification_port import NotificationPort

logger = structlog.get_logger()

class ThermalAdapter:
    def __init__(
            self,
            notification_service: NotificationPort, 
            limit_temp=80.0, 
            safe_temp=50.0
        ):
        self.limit_temp = limit_temp
        self.safe_temp = safe_temp
        self.is_miner_running = True # Asumimos que inicia encendido
        self.notifier = notification_service

    async def check_and_protect(self):
        try:
            # 1. Intentamos GPU (Lo más fiable en tu setup con la 3060)
            current_temp = self._get_gpu_temp()
            
            # 1. EMERGENCIA: Apagar minería
            if current_temp >= self.limit_temp and self.is_miner_running:
                logger.critical("TEMPERATURA_CRITICA_APAGANDO_MINERO", temp=current_temp, limit=self.limit_temp)
                #--------------------------------------------------------
                msg = f"🔥 ¡EMERGENCIA TÉRMICA! GPU a {current_temp}°C. Deteniendo minero..."
                await self.notifier.send_message(msg)
                #--------------------------------------------------------
                # Ejecutamos el stop del contenedor específico
                result = subprocess.run(["docker", "stop", "aurca_miner"], capture_output=True, text=True)
                if result.returncode == 0:
                    self.is_miner_running = False
                    logger.warning("minero_detenido_exitosamente")
                return True, current_temp
            if current_temp <= self.safe_temp and not self.is_miner_running:
                logger.info("TEMPERATURA_SEGURA_REINICIANDO_MINERO", temp=current_temp, target=self.safe_temp)
                #--------------------------------------------------------
                msg = f"❄️ Temperatura normalizada ({current_temp}°C). Reiniciando minero."
                await self.notifier.send_message(msg)
                #--------------------------------------------------------
                result = subprocess.run(["docker", "start", "aurca_miner"], capture_output=True, text=True)
                if result.returncode == 0:
                    self.is_miner_running = True
                    logger.info("minero_reiniciado_exitosamente")
                return False, current_temp
            

            return (current_temp >= self.limit_temp), current_temp
        

        except Exception as e:
            logger.error("thermal_check_failed", error=str(e))
            return False, 0.0

    def _get_gpu_temp(self) -> float:
        """Lee la temperatura de la NVIDIA RTX 3060 usando nvidia-smi"""
        try:
            output = subprocess.check_output([
                "nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"
            ]).decode("utf-8").strip()
            return float(output)
        except:
            return 0.0

    def _get_max_cpu_temp(self) -> float:
        """Escaneo de sensores estándar"""
        temps = psutil.sensors_temperatures()
        if not temps: return 0.0
        
        max_t = 0.0
        for entries in temps.values():
            for entry in entries:
                if entry.current > max_t:
                    max_t = entry.current
        return max_t