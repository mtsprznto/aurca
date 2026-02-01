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
    
    @staticmethod
    def add_indicators(candles):
        """
        Toma una lista de entidades MarketData y calcula indicadores 
        usando el motor nativo de alto rendimiento.
        """
        if not candles:
            return candles

        # Extraemos precios de cierre para el motor C++
        close_prices = [float(c.close) for c in candles]

        # DEBUGGER integrado: monitoreamos la salud del motor
        if aurca_engine.calculate_rsi is None:
            logger.error("motor_cpp_no_disponible", detail="RSI no cargado")
            return candles

        try:
            # Cálculo nativo (RSI 14 por defecto)
            rsi_values = aurca_engine.calculate_rsi(close_prices, 14)
            
            # Cálculo de retornos logarítmicos
            log_returns = aurca_engine.calculate_log_returns(close_prices)

            # Inyectamos los valores de vuelta en las entidades
            # Nota: log_returns tiene len-1, el primer elemento queda en 0.0
            for i, candle in enumerate(candles):
                candle.rsi = rsi_values[i] if i < len(rsi_values) else None
                if i > 0 and (i-1) < len(log_returns):
                    candle.log_return = log_returns[i-1]
                else:
                    candle.log_return = 0.0

        except Exception as e:
            logger.exception("error_calculando_indicadores_nativos", error=str(e))
        
        return candles