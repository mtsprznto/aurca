# src\application\use_cases\trading\evaluate_strategy.py
from datetime import datetime, timezone
import time
import structlog
from typing import Optional
from src.application.ports.output.market_data_storage import IMarketDataStorage
from src.application.ports.output.notification_port import NotificationPort
from src.domain.services.feature_engineering.indicators import IndicatorService

logger = structlog.get_logger()

class EvaluateStrategy:
    def __init__(
            self, 
            indicator_service: IndicatorService, 
            db_repo: IMarketDataStorage,
            notifier: NotificationPort
        ):
        self.indicators = indicator_service
        self.db = db_repo
        self.notifier = notifier
        # Umbrales configurables (Modificable para escalar a modelos de IA después)
        self.rsi_overbought = 70.0
        self.rsi_oversold = 30.0

    async def execute(self, symbol: str, current_price: float, timestamp: datetime) -> Optional[str]:
        """
        Evalúa las condiciones de mercado en tiempo real.
        Retorna: 'BUY', 'SELL' o None
        """
        start_perf = time.perf_counter()
        
        # 1. Obtenemos el RSI actualizado del buffer del motor C++
        rsi = self.indicators.update_and_calculate_rsi(symbol, current_price)
        
        engine_latency_ms = (time.perf_counter() - start_perf) * 1000

        if rsi is None:
            return None

        # 2. Lógica de Decisión (Estrategia de Reversión a la Media)
        signal = None
        if rsi < self.rsi_oversold:
            logger.warning("STRATEGY_SIGNAL", symbol=symbol, type="BUY_SIGNAL", rsi=f"{rsi:.2f}", price=current_price)
            signal = "BUY"
            
        elif rsi > self.rsi_overbought:
            logger.warning("STRATEGY_SIGNAL", symbol=symbol, type="SELL_SIGNAL", rsi=f"{rsi:.2f}", price=current_price)
            signal = "SELL"

        # 3. Aquí es donde en el futuro llamaremos a la RTX 3060 
        # para validar la señal con un modelo de Deep Learning antes de retornar.
        if signal:
            logger.warning("STRATEGY_SIGNAL", 
                           symbol=symbol, 
                           type=signal, 
                           rsi=f"{rsi:.2f}", 
                           latency_ms=f"{engine_latency_ms:.4f}")
            # Guardamos en TimescaleDB de forma asíncrona
            await self.db.save_signal(symbol, signal, current_price, rsi, timestamp)

            await self.notifier.send_trade_alert(
                symbol=symbol,
                signal=signal,
                price=current_price,
                analysis={"rsi": rsi, "engine_latency": engine_latency_ms}
            )

        return signal