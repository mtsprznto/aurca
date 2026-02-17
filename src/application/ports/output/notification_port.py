# src\application\ports\output\notification_port.py

from abc import ABC, abstractmethod

class NotificationPort(ABC):
    @abstractmethod
    async def send_message(self, message: str):
        pass