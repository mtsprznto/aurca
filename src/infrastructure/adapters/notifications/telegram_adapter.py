import asyncio
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
        
        self._lock = asyncio.Lock()
        self._last_sent = 0
        self._client = httpx.AsyncClient(timeout=10.0) # Cliente persistente

        if self.enabled:
            self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        else:
            logger.warning("telegram_disabled", reason="Missing token or chat_id in .env")

    async def send_message(self, message: str):
        if not self.enabled:
            return False
        
        async with self._lock:
            try:
                now = asyncio.get_event_loop().time()
                wait = 1.5 - (now - self._last_sent)
                if wait > 0:
                    await asyncio.sleep(wait)
                async with httpx.AsyncClient(timeout=10.0) as client:
                    payload = {
                        "chat_id": self.chat_id,
                        "text": f"**Aurca RIG: {settings.RIG_NAME}: **\n{message}",
                        "parse_mode": "Markdown"
                    }
                    for attempt in range(3):
                        response = await self._client.post(self.base_url, json=payload)
                        
                        if response.status_code == 429:
                            retry_after = response.json().get("parameters", {}).get("retry_after", 5)
                            logger.warning("telegram_rate_limited", retry_after=retry_after)
                            await asyncio.sleep(retry_after + 1)
                            continue
                        
                        response.raise_for_status()
                        self._last_sent = asyncio.get_event_loop().time()
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
    
