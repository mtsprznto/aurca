from datetime import datetime
import json
import time
import websockets
import asyncio
import structlog
from src.application.use_cases.trading.evaluate_strategy import EvaluateStrategy
from src.domain.services.feature_engineering.indicators import IndicatorService

logger = structlog.get_logger()

class BinanceWSAdapter:
    def __init__(self, symbol: str, indicator_service: IndicatorService, strategy: EvaluateStrategy):
        self.symbol = symbol.lower()
        self.url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@kline_1h"
        self.indicators = indicator_service
        self.strategy = strategy
        self._is_running = True

    async def start(self):
        while self._is_running:
            try:
                async with websockets.connect(self.url) as ws:
                    logger.info("ws_connected", symbol=self.symbol)
                    print(f"--------- WebSocket conectado para {self.url} -----------")
                    while self._is_running:
                        message = await ws.recv()
                        data = json.loads(message)

                        # Extraemos info de la vela (kline)
                        k = data['k']
                        is_candle_closed = k['x']
                        current_price = float(k['c'])
                        # Calculamos latencia de red (opcional para debug)
                        event_ts = datetime.fromtimestamp(data['E'] / 1000.0)
                        latency = time.time() - (data['E'] / 1000.0)
                        # CALCULAMOS SIEMPRE (para ver el RSI en vivo)
                        start_cpp = time.perf_counter()
                        # Delegamos la evaluación a la estrategia (ella usa el motor C++)
                        # Esto ya actualiza los buffers internos del IndicatorService
                        signal = await self.strategy.execute(self.symbol.upper(), current_price, event_ts)
                        duration_cpp = (time.perf_counter() - start_cpp) * 1000

                        if is_candle_closed:
                            # Recuperamos el último rsi calculado para el log
                            rsi = self.indicators.update_and_calculate_rsi(self.symbol.upper(), current_price)
                            logger.info("CANDLE_CLOSED_SAVING", 
                                        symbol=self.symbol.upper(), 
                                        price=current_price,
                                        rsi=f"{rsi:.2f}" if rsi else "N/A",
                                        cpp_speed=f"{duration_cpp:.4f}ms",
                                        latency=f"{latency:.3f}s")
                        elif signal:
                            logger.info("STRATEGY_ALERT", symbol=self.symbol.upper(), signal=signal)    

            except (websockets.ConnectionClosed, Exception) as e:
                logger.warning("ws_connection_lost", symbol=self.symbol, error=str(e))
                await asyncio.sleep(5) # Espera antes de reintentar (Backoff)
    
    def stop(self):
        self._is_running = False