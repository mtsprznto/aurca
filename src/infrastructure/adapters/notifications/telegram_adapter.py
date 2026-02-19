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
        self.enabled = all([self.token, self.chat_id])
        
        self._lock = asyncio.Lock()
        self._last_sent = 0
        # Cliente único para evitar fugas de memoria y sockets
        self._client = httpx.AsyncClient(timeout=10.0) 

        if self.enabled:
            self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        else:
            logger.warning("telegram_disabled", reason="Missing token or chat_id in .env")

    async def send_message(self, message: str):
        if not self.enabled:
            return False
        
        async with self._lock:
            try:
                # Rate limiting manual (1.5s entre mensajes)
                now = asyncio.get_event_loop().time()
                wait = 1.5 - (now - self._last_sent)
                if wait > 0:
                    await asyncio.sleep(wait)
                
                # Usamos HTML para evitar errores de escape de Markdown
                payload = {
                    "chat_id": self.chat_id,
                    "text": f"<b>Aurca RIG:</b> <code>{settings.RIG_NAME}</code>\n\n{message}",
                    "parse_mode": "HTML"
                }
                
                for attempt in range(3):
                    response = await self._client.post(self.base_url, json=payload)
                    
                    if response.status_code == 429:
                        retry_after = response.json().get("parameters", {}).get("retry_after", 5)
                        await asyncio.sleep(retry_after + 1)
                        continue
                    
                    if response.status_code != 200:
                        # Esto nos dirá exactamente qué carajo le molesta a Telegram
                        logger.error("telegram_api_error", status=response.status_code, response=response.text)
                    
                    response.raise_for_status()
                    self._last_sent = asyncio.get_event_loop().time()
                    return True
                    
            except Exception as e:
                logger.error("telegram_send_failed", error=str(e))
                return False

    async def send_trade_alert(self, symbol: str, signal: str, price: float, analysis: dict):
        try:
            emoji = "🚀" if signal == "BUY" else "🔻"
            # Formateamos con etiquetas HTML simples
            text = (
                f"{emoji} <b>NUEVA SEÑAL DETECTADA</b> {emoji}\n\n"
                f"<b>Symbol:</b> <code>{symbol}</code>\n"
                f"<b>Signal:</b> <code>{signal}</code>\n"
                f"<b>Price:</b> <code>${price:,.2f}</code>\n\n"
                f"📊 <b>Engine Analysis (C++):</b>\n"
                f"• RSI: <code>{analysis.get('rsi', 0):.2f}</code>\n"
                f"• Returns: <code>{analysis.get('returns', 0):.4f}%</code>"
            )
            return await self.send_message(text)
        except Exception as e:
            logger.error("telegram_send_failed", error=str(e))
            return False