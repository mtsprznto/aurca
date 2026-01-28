# src\infrastructure\adapters\database\models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Numeric, DateTime, Index
from datetime import datetime
from decimal import Decimal

class Base(DeclarativeBase):
    pass

class CandleModel(Base):
    __tablename__ = "candles"

    # TimescaleDB necesita el timestamp como parte de la llave primaria lógica
    timestamp: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(10), primary_key=True)
    
    open: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    high: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    low: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    close: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    volume: Mapped[Decimal] = mapped_column(Numeric(20, 8))

    # Índice para búsquedas rápidas por símbolo
    __table_args__ = (
        Index("idx_candles_symbol_timeframe", "symbol", "timeframe"),
    )