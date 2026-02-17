import httpx
import structlog
from src.application.ports.output.notification_port import NotificationPort
from src.infrastructure.config import settings

logger = structlog.get_logger()

class TelegramAdapter(NotificationPort):
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        #self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        self.enabled = all([self.token, self.chat_id])
        
        if self.enabled:
            self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        else:
            logger.warning("telegram_disabled", reason="Missing token or chat_id in .env")

    async def send_message(self, message: str):
        if not self.enabled:
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                payload = {
                    "chat_id": self.chat_id,
                    "text": f"**Aurca Node:**\n{message}",
                    "parse_mode": "Markdown"
                }
                response = await client.post(self.base_url, json=payload)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error("telegram_send_failed", error=str(e))
            return False
        
    async def send_trade_alert(self, symbol: str, signal: str, price: float, analysis: dict):
        try:
            emoji = "🚀" if signal == "BUY" else "🔻"
            text = (
                f"{emoji} **NUEVA SEÑAL DETECTADA** {emoji}\n\n"
                f"**Symbol:** `{symbol}`\n"
                f"**Signal:** `{signal}`\n"
                f"**Price:** `${price:,.2f}`\n\n"
                f"📊 **Engine Analysis (C++):**\n"
                f"• RSI: `{analysis.get('rsi', 0):.2f}`\n"
                f"• Returns: `{analysis.get('returns', 0):.4f}%`"
            )
            return await self.send_message(text)
        except Exception as e:
            logger.error("telegram_send_failed", error=str(e))
            return False
    
