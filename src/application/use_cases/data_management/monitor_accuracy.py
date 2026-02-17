import structlog
from datetime import datetime, timedelta, timezone
from src.application.ports.output.market_data_storage import IMarketDataStorage
from src.application.ports.output.notification_port import NotificationPort

logger = structlog.get_logger()

class MonitorAccuracy:
    def __init__(self, db_repo: IMarketDataStorage, notifier: NotificationPort):
        self.db = db_repo
        self.notifier = notifier

    async def execute(self):
        """Calcula el acierto del motor C++ en las últimas 24h"""
        logger.info("iniciando_health_check_predictivo")
        
        # 1. Obtener señales de las últimas 24h desde la DB
        # Asumiendo que implementaste 'get_recent_signals' en tu repo
        signals = await self.db.get_recent_signals(hours=24)
        
        if not signals:
            logger.info("no_hay_señales_para_analizar")
            return

        total_signals = len(signals)
        success_count = 0

        for sig in signals:
            # 2. Consultar el precio actual del símbolo para comparar
            # (En un modelo pro, compararíamos contra el precio N velas después)
            current_price = await self.db.get_last_price(sig.symbol)
            price_entry = sig.price
            is_correct = False
            if sig.signal_type == "BUY" and current_price > price_entry:
                is_correct = True
            elif sig.signal_type == "SELL" and current_price < price_entry:
                is_correct = True
            
            if is_correct:
                success_count += 1

        # 3. Calcular porcentaje
        accuracy = (success_count / total_signals) * 100
        
        # 4. Notificar vía Telegram
        report = (
            "🎯 **Reporte de Precisión (24h)**\n\n"
            f"• **Motor:** C++ Aurca Engine\n"
            f"• **Señales evaluadas:** `{total_signals}`\n"
            f"• **Acierto:** `{accuracy:.2f}%`\n"
            f"• **Estado:** {'✅ Saludable' if accuracy > 50 else '⚠️ Revisar Estrategia'}"
        )
        
        await self.notifier.send_message(report)
        logger.info("accuracy_report_sent", accuracy=accuracy)