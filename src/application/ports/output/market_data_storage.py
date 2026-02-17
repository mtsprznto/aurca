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

    @abstractmethod
    async def save_signal(self, symbol: str, signal_type: str, price: float, rsi: float, timestamp: datetime):
        """Guarda una señal de trading generada por la estrategia"""
        pass

    @abstractmethod
    async def save_mining_stats(self, worker: str, hashrate: float, coin: str , timestamp: datetime = None):
        """Guarda el rendimiento de la RTX 3060"""
        pass