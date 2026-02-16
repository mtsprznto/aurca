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

class SignalModel(Base):
    __tablename__ = "trading_signals"

    # Time-series primary key para TimescaleDB
    time: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    
    signal_type: Mapped[str] = mapped_column(String(10)) # BUY/SELL
    price: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    rsi: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=True)

class MiningEarningsModel(Base):
    """Para registrar lo que Binance Pool te deposita automáticamente"""
    __tablename__ = "mining_earnings"

    timestamp: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    coin: Mapped[str] = mapped_column(String(10), primary_key=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8))

class MiningStatsModel(Base):
    """Monitoreo del rendimiento de tu RTX 3060"""
    __tablename__ = "mining_stats"

    timestamp: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    worker_name: Mapped[str] = mapped_column(String(50), primary_key=True) # ej: "alan.001"
    
    hashrate: Mapped[Decimal] = mapped_column(Numeric(20, 8)) # MH/s
    coin: Mapped[str] = mapped_column(String(10)) # ETC