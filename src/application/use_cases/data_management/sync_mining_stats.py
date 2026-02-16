# src\application\use_cases\data_management\sync_mining_stats.py
import structlog
from src.application.ports.output.market_repository import IMarketRepository
from src.application.ports.output.market_data_storage import IMarketDataStorage

logger = structlog.get_logger()

class SyncMiningStats:
    def __init__(self, binance_repo: IMarketRepository, db_storage: IMarketDataStorage):
        self.binance = binance_repo
        self.db = db_storage

    async def execute(self, algo: str = "etchash", user: str = None):
        """Consulta Binance Pool y persiste el estado de la GPU"""
        data = await self.binance.get_mining_status(algo)
        logger.debug("raw_mining_response", payload=data)

        if data and isinstance(data, dict) and data.get('code') == 0:
            # Usamos .get() en cascada para total seguridad
            inner_data = data.get('data') or {}
            workers = inner_data.get('workerDatas') or []
            
            if not workers:
                logger.info("no_workers_found", user=user, algo=algo)
                return

            for worker in workers:
                # Aquí también usamos .get() por si acaso workerName o hashrate faltan
                w_name = worker.get('workerName', 'unknown')
                w_hash = worker.get('hashrate', 0)
                
                await self.db.save_mining_stats(
                    worker=w_name,
                    hashrate=float(w_hash),
                    coin=algo.upper()
                )
                logger.info("mining_stats_synced", worker=w_name, hr=w_hash)
        else:
            logger.warning("mining_data_invalid_format", detail=data)