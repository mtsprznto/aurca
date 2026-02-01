import os
import sys

# Intentamos cargar el binario
try:
    # Importación relativa: busca el .pyd en la misma carpeta que este __init__
    from . import aurca_engine_bin
    calculate_log_returns = aurca_engine_bin.calculate_log_returns
    calculate_rsi = aurca_engine_bin.calculate_rsi
except ImportError as e:
    # Si falla, definimos la función como None para que el sistema sepa que no está disponible
    calculate_log_returns = None
    calculate_rsi = None
    # Esto es útil para debug, pero en producción podrías usar un logger
    print(f"DEBUG: Error cargando binario nativo: {e}")

__all__ = ["calculate_log_returns", "calculate_rsi"]