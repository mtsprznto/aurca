# src\application\ports\output\market_data_storage.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from src.domain.entities.market_data import Candle

class IMarketDataStorage(ABC):
    @abstractmethod
    async def save_candles(self, candles: List[Candle]):
        """Guarda una lista de velas en la base de datos"""
        pass

    @abstractmethod
    async def get_last_candle_timestamp(self, symbol: str, timeframe: str)-> Optional[datetime]:
        """Busca la fecha de la última vela guardada para no duplicar"""
        pass