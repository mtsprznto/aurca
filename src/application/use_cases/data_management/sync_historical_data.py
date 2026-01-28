# src\application\use_cases\data_management\sync_historical_data.py

import asyncio
from datetime import datetime, timedelta
import structlog
from src.application.ports.output.market_repository import IMarketRepository
from src.application.ports.output.market_data_storage import IMarketDataStorage

logger = structlog.get_logger()

class SyncHistoricalData:
    def __init__(
        self, 
        market_repo: IMarketRepository, 
        storage_repo: IMarketDataStorage
    ):
        self.market_repo = market_repo
        self.storage_repo = storage_repo

    async def execute(self, symbol: str, interval: str, target_days: int = 365):
        logger.info("iniciando_sincronizacion_historical", symbol=symbol, interval=interval, target_days=target_days)

        # 1. Calcular desde cuándo queremos datos (milisegundos)
        now = datetime.now()
        start_date = now - timedelta(days=target_days)
        current_start_ts = int(start_date.timestamp() * 1000)
        
        # 1. ¿Donde nos quedamos?
        last_stored_ts = await self.storage_repo.get_last_candle_timestamp(symbol, interval)
        
        if last_stored_ts:
            # Si ya tenemos datos, empezamos desde la última vela guardada
            current_start_ts = int(last_stored_ts.timestamp() * 1000)
            logger.info("reanudando_backfill", symbol=symbol, desde=last_stored_ts)
        
        total_saved = 0
        
        while True:
            # Pedimos lotes de 1000 (máximo de Binance)
            candles = await self.market_repo.get_historical_candles(
                symbol=symbol, 
                interval=interval, 
                limit=1000, 
                start_time=current_start_ts
            )

            if not candles or len(candles) <= 1:
                break # Ya no hay más datos o llegamos al presente

            await self.storage_repo.save_candles(candles)
            
            # Actualizamos el puntero para la siguiente petición:
            # Empezamos 1ms después del cierre de la última vela recibida
            current_start_ts = int(candles[-1].timestamp.timestamp() * 1000) + 1
            
            total_saved += len(candles)
            logger.info("lote_procesado", symbol=symbol, acumulado=total_saved, ultimo=candles[-1].timestamp)

            # Respetar Rate Limit
            await asyncio.sleep(0.2)

        logger.info("backfill_profundo_completado", symbol=symbol, total=total_saved)