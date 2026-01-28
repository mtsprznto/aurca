import asyncio
import structlog
from src.domain.services.feature_engineering.indicators import IndicatorService
from src.infrastructure.adapters.binance import binance_adapter
from src.infrastructure.adapters.binance.binance_adapter import BinanceAdapter
from src.infrastructure.config import settings
from src.infrastructure.adapters.database.repositories.timescale_repository import TimescaleRepository
from src.application.use_cases.data_management.sync_historical_data import SyncHistoricalData

# Configuración única de structlog (evita duplicidad)
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
    cache_logger_on_first_use=True,
)

# Configuración de logs para ver qué pasa
logger = structlog.get_logger()


async def bootstrap():
    """Inicialización de la aplicación e inyección de dependencias"""
    
    # 1. Instanciamos adaptadores
    binance_adapter = BinanceAdapter()
    db_adapter = TimescaleRepository()
    feature_service = IndicatorService()

    try:
        # 2. Aseguramos que la DB esté lista (Hypertable incluida)
        await db_adapter.initialize_db()
        logger.info("database_ready")

        # 3. Configuramos el Caso de Uso
        sync_service = SyncHistoricalData(
            market_repo=binance_adapter,
            storage_repo=db_adapter
        )

        # Sincronizamos (Productor)
        symbols_to_sync = (await binance_adapter.get_trading_symbols())[:5] 
        for symbol in symbols_to_sync:
            await sync_service.execute(symbol=symbol, interval="1h", target_days=30)
            
            # Análisis (Consumidor - C++ Engine)
            # Ahora que sabemos que la DB tiene datos, los procesamos
            candles = await db_adapter.get_historical_data(symbol, timeframe="1h")
            if candles:
                closes = [float(c.close) for c in candles]
                returns = feature_service.compute_returns(closes)
                logger.info("analysis_complete", symbol=symbol, first_ret=returns[0] if returns else 0)

    except Exception as e:
        logger.error("error_durante_la_ejecucion", error=str(e))
        raise # Re-lanzamos para que el bloque de abajo también lo capture si es necesario

    finally:
        # 5. CIERRE LIMPIO DE RECURSOS
        # Esto se ejecuta SIEMPRE, falle o no el código de arriba
        logger.info("cerrando_conexiones_del_agente...")
        # Cerramos Binance (evita el error de Unclosed Client Session)
        await binance_adapter.close()
        if hasattr(db_adapter, 'engine'):
            await db_adapter.engine.dispose()
        logger.info("conexiones_cerradas_correctamente")


if __name__ == "__main__":
    try:
        asyncio.run(bootstrap())
    except KeyboardInterrupt:
        logger.info("agente_detenido_por_usuario")
    except Exception as e:
        # Este es el último nivel de captura de errores fatales
        logger.critical("agente_colapsado", error=str(e))