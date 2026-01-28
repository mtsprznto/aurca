# src/domain/entities/market_data.py
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

@dataclass(frozen=True) # Inmutable para evitar errores en el aprendizaje
class Candle:
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    timeframe: str  # Ej: '1h', '1m'

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open