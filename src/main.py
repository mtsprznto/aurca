import asyncio
import structlog
import urllib.parse
from src.application.use_cases.data_management.sync_mining_stats import SyncMiningStats
from src.application.use_cases.trading.evaluate_strategy import EvaluateStrategy
from src.domain.services.feature_engineering.indicators import IndicatorService
from src.infrastructure.adapters.binance.binance_adapter import BinanceAdapter
from src.infrastructure.adapters.binance.websocket_adapter import BinanceWSAdapter
from src.infrastructure.config import settings
from src.infrastructure.adapters.database.repositories.timescale_repository import TimescaleRepository
from src.application.use_cases.data_management.sync_historical_data import SyncHistoricalData

# Configuración única de structlog (evita duplicidad)
if not structlog.is_configured():
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

async def check_performance_context():
    """Verifica si el contenedor tiene acceso a Huge Pages (Ryzen 7 Optim)"""
    try:
        with open("/proc/meminfo", "r") as f:
            if "HugePages_Total" in f.read():
                logger.info("performance_check", status="HugePages_Detected", optimized=True)
            else:
                logger.warning("performance_check", status="StandardPages", optimized=False)
    except Exception:
        logger.info("performance_check", status="Could_not_read_meminfo_WSL2")


async def bootstrap():
    """Inicialización de la aplicación e inyección de dependencias"""
    await check_performance_context()

    # 1. Instanciamos adaptadores
    b_inst = BinanceAdapter()
    db_adapter = TimescaleRepository()
    feature_service = IndicatorService()
    trading_strategy = EvaluateStrategy(
        indicator_service=feature_service, 
        db_repo=db_adapter
    ) 
    mining_service = SyncMiningStats(b_inst, db_adapter)
    ws_tasks = []

    try:
        # 2. Aseguramos que la DB esté lista (Hypertable incluida)
        await db_adapter.initialize_db()
        logger.info("database_ready")

        # --- A. BACKGROUND TASK: MINERÍA ---
        async def mining_worker_loop():
            mining_user = settings.BINANCE_MINING_USER
            logger.info("iniciando_monitor_mineria", user=mining_user)
            while True:
                try:
                    await mining_service.execute(algo="etchash", user=mining_user)
                except Exception as e:
                    logger.error("error_en_loop_mineria", error=str(e))
                await asyncio.sleep(900) # Cada 15 minutos

        # Lanzamos la tarea de minería al fondo
        mining_task = asyncio.create_task(mining_worker_loop())
        ws_tasks.append(mining_task)
        # -----------------------------------

        # 3. Configuramos el Caso de Uso
        sync_service = SyncHistoricalData(
            market_repo=b_inst,
            storage_repo=db_adapter
        )
        # Sincronizamos (Productor)
        symbols_to_sync = (await b_inst.get_trading_symbols())[:3]

        for symbol in symbols_to_sync:
            await sync_service.execute(symbol=symbol, interval="1h", target_days=30)
            
            # Análisis (Consumidor - C++ Engine)
            # Ahora que sabemos que la DB tiene datos, los procesamos
            candles = await db_adapter.get_historical_data(symbol, timeframe="1h")
            if candles:
                closes = [float(c.close) for c in candles]
                returns = feature_service.compute_returns(closes)
                logger.info("analysis_complete", symbol=symbol, first_ret=returns[0] if returns else 0)
            

        # C. Inicio de Tiempo Real (WebSockets)
        logger.info("iniciando_modo_tiempo_real", symbols=symbols_to_sync)
        for symbol in symbols_to_sync:
            # AQUÍ ES DONDE PASAMOS TODO CORRECTAMENTE
            ws_client = BinanceWSAdapter(
                symbol=symbol, 
                indicator_service=feature_service, 
                strategy=trading_strategy
            )
            ws_tasks.append(asyncio.create_task(ws_client.start()))


        # Mantener el loop vivo mientras las tareas de WS funcionen
        await asyncio.gather(*ws_tasks)

    except asyncio.CancelledError:
        logger.info("cancelacion_recibida_deteniendo_tareas")
    except Exception as e:
        logger.error("error_durante_la_ejecucion", error=str(e))
        raise # Re-lanzamos para que el bloque de abajo también lo capture si es necesario

    finally:
        # 5. CIERRE LIMPIO DE RECURSOS
        # Esto se ejecuta SIEMPRE, falle o no el código de arriba
        logger.info("cerrando_conexiones_del_agente...")
        for task in ws_tasks:
            if not task.done():
                task.cancel()
        if ws_tasks:
            await asyncio.gather(*ws_tasks, return_exceptions=True)
            
        if b_inst:
            # Cerramos Binance (evita el error de Unclosed Client Session)
            await b_inst.close()
        if db_adapter and hasattr(db_adapter, 'engine'):
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