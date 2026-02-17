# src\application\ports\output\notification_port.py

from abc import ABC, abstractmethod

class NotificationPort(ABC):
    @abstractmethod
    async def send_message(self, message: str):
        pass

    @abstractmethod
    async def send_trade_alert(self, symbol: str, signal: str, price: float, analysis: dict):
        """Envía una alerta profesional de trading con datos del motor C++"""
        pass