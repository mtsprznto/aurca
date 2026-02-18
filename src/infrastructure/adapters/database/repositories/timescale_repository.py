# src\infrastructure\adapters\database\repositories\timescale_repository.py
from datetime import datetime, timedelta, timezone
import structlog
from typing import List, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text

from src.domain.entities.market_data import Candle
from src.application.ports.output.market_data_storage import IMarketDataStorage
from src.infrastructure.adapters.database.models import Base, CandleModel, MiningStatsModel, SignalModel
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
            
            # Configuración masiva de Hypertables para TimescaleDB
            hypertables = {
                "candles": "timestamp",
                "trading_signals": "time",
                "mining_stats": "timestamp",
                "mining_earnings": "timestamp"
            }
            for table, col in hypertables.items():
                await conn.execute(text(
                    f"SELECT create_hypertable('{table}', '{col}', if_not_exists => TRUE);"
                ))
            
        logger.info("db_initialized_with_mining_and_trading_support")

    async def save_signal(self, symbol: str, signal_type: str, price: float, rsi: float, timestamp: Optional[datetime] = None):
        """Persistencia con timestamp real del evento"""
        # Si no viene timestamp (fallback), usamos UTC actual
        ts = timestamp or datetime.now(timezone.utc)
        symbol = symbol.upper()

        async with self.async_session() as session:
            
            stmt = insert(SignalModel).values(
                time=ts,
                symbol=symbol,
                signal_type=signal_type,
                price=price,
                rsi=rsi
            )
            stmt = stmt.on_conflict_do_nothing(index_elements=['time', 'symbol'])

            try:
                await session.execute(stmt)
                await session.commit()
                logger.debug("signal_processed", symbol=symbol, type=signal_type, ts=ts)
            except Exception as e:
                await session.rollback()
                logger.error("error_persisting_signal", error=str(e), symbol=symbol)

    async def save_candles(self, candles: List[Candle]):
        async with self.async_session() as session:
            for c in candles:
                # 'Upsert': Si ya existe (mismo timestamp/symbol/tf), actualiza.
                stmt = insert(CandleModel).values(
                    symbol=c.symbol.upper(),
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

    async def save_mining_stats(self, worker: str, hashrate: float, coin: str, timestamp: datetime = None):
        """Registro de rendimiento individual por worker"""
        async with self.async_session() as session:
            db_time = timestamp or datetime.now(timezone.utc)
            
            # Corrección Pylance:
            new_stat = MiningStatsModel(
                timestamp=db_time, 
                worker_name=worker, 
                hashrate=hashrate, 
                coin=coin
            )
            session.add(new_stat)
            try:
                await session.commit()
                # Log con el nombre del worker para saber quién está minando
                logger.info("mining_stat_recorded", worker=worker, hashrate=hashrate)
            except Exception as e:
                await session.rollback()
                logger.error("error_saving_mining_stats", error=str(e), worker=worker)

    async def get_recent_signals(self, hours: int):
        """FIX: Se reemplaza utcnow() por now(timezone.utc)"""
        async with self.async_session() as session: # Corregido de self.Session a self.async_session
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            # Nota: Asegúrate de que SignalModel esté importado de tus modelos
            # result = await session.execute(select(SignalModel).where(SignalModel.time >= cutoff))
            # return result.scalars().all()
            
            # Si prefieres seguir con text() por consistencia:
            query = text("SELECT * FROM trading_signals WHERE time >= :cutoff")
            result = await session.execute(query, {"cutoff": cutoff})
            return result.fetchall()

    async def get_last_price(self, symbol: str):
        async with self.async_session() as session:
            query = text("SELECT close FROM candles WHERE symbol = :symbol ORDER BY timestamp DESC LIMIT 1")
            result = await session.execute(query, {"symbol": symbol})
            return result.scalar()

    async def save_mining_earnings(self, data: dict):
        """
        Guarda las ganancias de minería usando la sesión asíncrona.
        'data' esperado: {"timestamp": datetime, "coin": str, "amount": float}
        """
        async with self.async_session() as session:
            # Aseguramos que el timestamp sea consciente de la zona horaria si no lo es
            ts = data.get("timestamp")
            if ts and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            query = text("""
                INSERT INTO mining_earnings (timestamp, coin, amount)
                VALUES (:timestamp, :coin, :amount)
                ON CONFLICT (timestamp, coin) DO NOTHING
                RETURNING timestamp;
            """)
            
            try:
                result = await session.execute(query, {
                    "timestamp": ts,
                    "coin": data.get("coin"),
                    "amount": data.get("amount")
                })
                await session.commit()
                
                # Si scalar() devuelve algo, es que se insertó. Si es None, es que hubo conflicto (DO NOTHING).
                is_new = result.scalar() is not None
                if is_new:
                    logger.debug("mining_earnings_new_record", coin=data.get("coin"), amount=data.get("amount"))
                return is_new
            
            except Exception as e:
                await session.rollback()
                logger.error("error_saving_mining_earnings", error=str(e))
                raise

