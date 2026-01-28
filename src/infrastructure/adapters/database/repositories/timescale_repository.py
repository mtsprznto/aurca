# src\infrastructure\adapters\database\repositories\timescale_repository.py
from datetime import datetime
import structlog
from typing import List, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text

from src.domain.entities.market_data import Candle
from src.application.ports.output.market_data_storage import IMarketDataStorage
from src.infrastructure.adapters.database.models import Base, CandleModel
from src.infrastructure.config import settings

logger = structlog.get_logger()

class TimescaleRepository(IMarketDataStorage):
    def __init__(self):
        self.engine = create_async_engine(settings.DATABASE_URL)
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def initialize_db(self):
        """Crea tablas y convierte 'candles' en Hypertable"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # Comando específico de TimescaleDB
            await conn.execute(text(
                "SELECT create_hypertable('candles', 'timestamp', if_not_exists => TRUE);"
            ))
        logger.info("db_initialized_with_timescale")

    async def save_candles(self, candles: List[Candle]):
        async with self.async_session() as session:
            for c in candles:
                # 'Upsert': Si ya existe (mismo timestamp/symbol/tf), actualiza.
                stmt = insert(CandleModel).values(
                    symbol=c.symbol,
                    timestamp=c.timestamp,
                    open=c.open,
                    high=c.high,
                    low=c.low,
                    close=c.close,
                    volume=c.volume,
                    timeframe=c.timeframe
                ).on_conflict_do_nothing() # No duplicamos datos
                await session.execute(stmt)
            await session.commit()
        logger.debug("candles_saved_to_db", count=len(candles))

    async def get_last_candle_timestamp(self, symbol: str, timeframe: str) -> Optional[datetime]:
        async with self.async_session() as session:
            result = await session.execute(
                text("SELECT MAX(timestamp) FROM candles WHERE symbol = :symbol AND timeframe = :timeframe"),
                {"symbol": symbol, "timeframe": timeframe}
            )
            return result.scalar()
    
    async def get_historical_data(self, symbol: str, timeframe: str, limit: int = 10000) -> List[CandleModel]:
        async with self.async_session() as session:
            # Ordenamos por timestamp ASCENDENTE para que el motor C++ procese la serie temporal correctamente
            stmt = text("""
                SELECT timestamp, open, high, low, close, volume 
                FROM candles 
                WHERE symbol = :symbol AND timeframe = :timeframe
                ORDER BY timestamp ASC
                LIMIT :limit
            """)
            result = await session.execute(stmt, {
                "symbol": symbol, 
                "timeframe": timeframe, 
                "limit": limit
            })
            
            # Convertimos las filas en objetos CandleModel para mantener consistencia
            rows = result.fetchall()
            return [
                CandleModel(
                    symbol=symbol,
                    timestamp=row[0],
                    open=row[1],
                    high=row[2],
                    low=row[3],
                    close=row[4],
                    volume=row[5],
                    timeframe=timeframe
                ) for row in rows
            ]