# src\domain\services\feature_engineering\indicators.py

import os
import sys
import aurca_engine # Python ya lo encontrará si configuramos bien el entrypoint
from typing import List
import structlog

logger = structlog.get_logger()

try:
    import aurca_engine
except ImportError as e:
    logger.error("engine_not_found", error=str(e))
    raise

logger = structlog.get_logger()
logger.info("inspeccionando_motor", metodos=dir(aurca_engine))


print(f"DEBUG: aurca_engine cargado desde {aurca_engine.__file__}")
print(f"DEBUG: contenido de la carpeta del motor: {os.listdir(os.path.dirname(aurca_engine.__file__))}")
print(f"DEBUG: atributos del motor: {dir(aurca_engine)}")

class IndicatorService:
    @staticmethod
    def compute_returns(closing_prices: List[float]) -> List[float]:
        """Calcula retornos logarítmicos usando el motor C++."""
        if len(closing_prices) < 2:
            logger.warning("insufficient_data", count=len(closing_prices))
            return []
        
        return aurca_engine.calculate_log_returns(closing_prices)