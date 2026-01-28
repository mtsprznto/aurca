# src/application/ports/output/market_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.market_data import Candle

class IMarketRepository(ABC):
    @abstractmethod
    async def get_historical_candles(self, symbol: str, interval: str, limit: int) -> List[Candle]:
        """Obtiene datos históricos para entrenamiento o análisis"""
        pass

    @abstractmethod
    async def subscribe_to_realtime_quotes(self, symbol: str):
        """Inicia la conexión en tiempo real (Websocket)"""
        pass
    
    @abstractmethod
    async def get_historical_candles(
        self, 
        symbol: str, 
        interval: str, 
        limit: int, 
        start_time: Optional[int] = None  # Añadimos esto
    ) -> List[Candle]:
        pass