# src\infrastructure\adapters\binance\binance_adapter.py
# El código Python que importa el .so/.pyd

import asyncio
from binance import AsyncClient
import structlog
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from src.domain.entities.market_data import Candle
from src.application.ports.output.market_repository import IMarketRepository
from src.infrastructure.config import settings


logger = structlog.get_logger()

class BinanceAdapter(IMarketRepository):
    def __init__(self):
        self.client = None

    async def _get_client(self):
        """Inicializa el cliente asíncrono con llaves Ed25519"""
        if self.client is None:
            # Leemos el contenido de la llave privada (debe ser el string del PEM)
            try:
                with open(settings.BINANCE_PRIVATE_KEY_PATH, "r") as f:
                    private_key_content = f.read()
                
                # La librería espera 'private_key', NO 'private_key_path'
                self.client = await AsyncClient.create(
                    api_key=settings.BINANCE_API_KEY,
                    private_key=private_key_content
                )
                logger.debug("cliente_creado_con_exito")
            except FileNotFoundError:
                logger.error("archivo_llave_no_encontrado", path=settings.BINANCE_PRIVATE_KEY_PATH)
                raise
        return self.client

    async def get_historical_candles(
            self, 
            symbol: str, 
            interval: str, 
            limit: int, 
            start_time: int = None) -> List[Candle]:
        
        client = await self._get_client()

        logger.info("fetching_historical_data", symbol=symbol, interval=interval)
        
        # Throttling preventivo: Binance API Rate Limit protection
        # Un pequeño sleep asegura que no enviamos ráfagas incontrolables
        await asyncio.sleep(0.1) 
        try:
            # Obtenemos Klines (velas)
            klines = await client.get_klines(
                symbol=symbol, 
                interval=interval, 
                limit=limit,
                startTime=start_time
            )
            
            candles = []
            for k in klines:
                candles.append(Candle(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(k[0] / 1000.0),
                    open=Decimal(str(k[1])),
                    high=Decimal(str(k[2])),
                    low=Decimal(str(k[3])),
                    close=Decimal(str(k[4])),
                    volume=Decimal(str(k[5])),
                    timeframe=interval
                ))
            return candles
        except Exception as e:
            if "429" in str(e) or "7002" in str(e):
                logger.critical("RATE_LIMIT_HIT", error=str(e))
                await asyncio.sleep(60) # Pausa de seguridad de un minuto si nos avisan
            raise e

    async def subscribe_to_realtime_quotes(self, symbol: str):
        # Esto lo implementaremos con el motor de C++ para máxima velocidad
        logger.warning("realtime_subscription_pending_cpp_engine", symbol=symbol)
        pass
    
    async def get_trading_symbols(self) -> List[str]:
        client = await self._get_client()
        info = await client.get_exchange_info()
        # Filtramos: Solo pares que se puedan tradear y que terminen en USDT
        symbols = [
            s['symbol'] for s in info['symbols'] 
            if s['status'] == 'TRADING' and s['symbol'].endswith('USDT')
        ]
        logger.info("symbols_retrieved", count=len(symbols))
        return symbols

    
    async def close(self):
        if self.client:
            await self.client.close_connection()
            logger.info("binance_client_closed")