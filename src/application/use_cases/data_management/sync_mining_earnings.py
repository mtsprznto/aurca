# src\application\use_cases\data_management\sync_mining_earnings.py

import structlog
from datetime import datetime
from src.infrastructure.config import settings

logger = structlog.get_logger()

class SyncMiningEarnings:
    def __init__(self, binance_adapter, db_repo, notifier):
        self.binance = binance_adapter
        self.db = db_repo
        self.notifier = notifier

    async def execute(self, user: str):
        try:
            # 1. Obtenemos los pagos desde el adaptador de Binance
            # Nota: Necesitarás implementar 'get_mining_earnings' en tu BinanceAdapter
            earnings = await self.binance.get_mining_earnings(user)
            if not earnings:
                logger.info("mining_sync", detail="No hay nuevos pagos de minería")
                return
            
            coin = earnings[0]['coin']
            symbol = f"{coin}USDT"
            price_usd = await self.binance.get_asset_price(symbol)


            # 2. Guardamos en la DB (TimescaleRepository)
            for record in earnings:
                # El método save_mining_earnings debería devolver True si insertó 
                # o False si hubo conflicto (ya existía).
                is_new = await self.db.save_mining_earnings(record)
                
                if is_new:
                    amount = record['amount']
                    value_usd = amount * price_usd
                    # Enviar mensaje profesional a Telegram
                    msg = (
                        "💰 **Nuevo Pago de Minería**\n"
                        f"• Worker: `{settings.RIG_NAME}`\n"
                        f"• Activo: `{record['coin']}`\n"
                        f"• Cantidad: `{record['amount']:.8f}`\n"
                        f"• Valor: `${value_usd:.2f} USD` (aprox)\n"
                        "--------------------------\n"
                        f"• Fecha: {record['timestamp'].strftime('%d/%m/%Y %H:%M')} UTC"
                    )
                    await self.notifier.send_message(msg)
                    logger.info("mining_payout_notified", amount=record['amount'])

            logger.info("mining_sync_success", count=len(earnings))
        except Exception as e:
            logger.error("mining_sync_error", error=str(e))