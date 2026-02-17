# src\infrastructure\adapters\binance\binance_adapter.py
# El código Python que importa el .so/.pyd

import asyncio
from base64 import b64encode


import time
from binance import AsyncClient
import structlog
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timezone

import urllib

from src.domain.entities.market_data import Candle
from src.application.ports.output.market_repository import IMarketRepository
from src.infrastructure.config import settings

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

logger = structlog.get_logger()

class BinanceAdapter(IMarketRepository):
    def __init__(self):
        self.client = None
        self._lock = asyncio.Lock()

    def _sign_ed25519(self, payload: str) -> str:
        """Firma exacta según el estándar de Binance 2026"""
        with open(settings.BINANCE_PRIVATE_KEY_PATH, "rb") as f:
            private_key_data = f.read()
            
        # Cargar llave privada Ed25519
        private_key = serialization.load_pem_private_key(
            private_key_data,
            password=None
        )
        
        # Firmar el payload (query string)
        signature = private_key.sign(payload.encode("utf-8"))
        
        # Binance requiere la firma en BASE64
        return b64encode(signature).decode("utf-8")

    async def _get_client(self):
        """Inicializa el cliente asíncrono con llaves Ed25519"""
        async with self._lock:
            if self.client is None:
                # Leemos el contenido de la llave privada (debe ser el string del PEM)
                try:
                    with open(settings.BINANCE_PRIVATE_KEY_PATH, "r") as f:
                        private_key_content = f.read()
                    
                    self.client = await AsyncClient.create(
                        api_key=settings.BINANCE_API_KEY,
                        private_key=private_key_content
                    )
                    logger.debug("cliente_creado_con_exito")
                except FileNotFoundError:
                    logger.error("archivo_llave_no_encontrado", path=settings.BINANCE_PRIVATE_KEY_PATH)
                    raise
        return self.client

    async def get_historical_candles(
            self, 
            symbol: str, 
            interval: str, 
            limit: int, 
            start_time: int = None) -> List[Candle]:
        
        client = await self._get_client()

        logger.info("fetching_historical_data", symbol=symbol, interval=interval)
        
        # Throttling preventivo: Binance API Rate Limit protection
        # Un pequeño sleep asegura que no enviamos ráfagas incontrolables
        await asyncio.sleep(0.1) 
        try:
            # Obtenemos Klines (velas)
            klines = await client.get_klines(
                symbol=symbol, 
                interval=interval, 
                limit=limit,
                startTime=start_time
            )
            
            candles = []
            for k in klines:
                candles.append(Candle(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(k[0] / 1000.0),
                    open=Decimal(str(k[1])),
                    high=Decimal(str(k[2])),
                    low=Decimal(str(k[3])),
                    close=Decimal(str(k[4])),
                    volume=Decimal(str(k[5])),
                    timeframe=interval
                ))
            return candles
        except Exception as e:
            if "429" in str(e) or "7002" in str(e):
                logger.critical("RATE_LIMIT_HIT", error=str(e))
                await asyncio.sleep(60) # Pausa de seguridad de un minuto si nos avisan
            raise e

    async def get_asset_price(self, symbol: str) -> float:
        """Obtiene el precio actual de un activo (ej: ETCUSDT)"""
        try:
            client = await self._get_client()
            ticker = await client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception:
            return 0.0

    async def subscribe_to_realtime_quotes(self, symbol: str):
        # Esto lo implementaremos con el motor de C++ para máxima velocidad
        logger.warning("realtime_subscription_pending_cpp_engine", symbol=symbol)
        pass
    
    async def get_trading_symbols(self) -> List[str]:
        client = await self._get_client()
        info = await client.get_exchange_info()
        # Filtramos: Solo pares que se puedan tradear y que terminen en USDT
        symbols = [
            s['symbol'] for s in info['symbols'] 
            if s['status'] == 'TRADING' and s['symbol'].endswith('USDT')
        ]
        logger.info("symbols_retrieved", count=len(symbols))
        return symbols
    
    async def get_mining_status(self, algo: str = "etchash"):
        user_name = settings.BINANCE_MINING_USER
        client = await self._get_client()
        
        params = {
            'algo': algo,
            'userName': user_name,
            'recvWindow': 60000,
            'timestamp': int(time.time() * 1000)
        }
        
        try:
            sorted_params = sorted(params.items())
            query_string = urllib.parse.urlencode(sorted_params)
            signature = self._sign_ed25519(query_string)
            safe_signature = urllib.parse.quote(signature)
            
            url = f"https://api.binance.com/sapi/v1/mining/worker/list?{query_string}&signature={safe_signature}"

            try:
                async with client.session.get(
                    url, 
                    headers=client._get_headers()
                ) as response:
                    result = await response.json()

                    if response.status == 200 and result.get('code') == 0:
                        logger.info("mining_data_success", workers=len(result['data'].get('workerDatas', [])))
                        return result
                    else:
                        logger.error("binance_api_mining_error", status=response.status, detail=result)
                        return result
            finally:
                # Si solo vas a hacer una petición y cerrar (como en un cron), cierra aquí.
                # Si es un loop, el cierre debe ir en el finalmente del bootstrap en main.py
                pass
        except Exception as e:
            logger.error("mining_request_failed", error=str(e))
            return None

    async def get_mining_earnings(self, user_name: str, algo: str = "etchash") -> List[dict]:
        """
        Obtiene el historial de pagos (Earnings) de Binance Pool.
        """
        client = await self._get_client()
        
        # Parámetros para la API de Binance
        params = {
            'algo': algo,
            'userName': user_name,
            'pageSize': 10, # Traemos los últimos 10 pagos
            'recvWindow': 60000,
            'timestamp': int(time.time() * 1000)
        }
        
        try:
            # 1. Preparar Query String y Firma Ed25519
            sorted_params = sorted(params.items())
            query_string = urllib.parse.urlencode(sorted_params)
            signature = self._sign_ed25519(query_string)
            safe_signature = urllib.parse.quote(signature)
            
            url = f"https://api.binance.com/sapi/v1/mining/payment/list?{query_string}&signature={safe_signature}"

            # 2. Ejecución de la petición asíncrona
            async with client.session.get(
                url, 
                headers=client._get_headers()
            ) as response:
                result = await response.json()
                
                if response.status == 200 and result.get('code') == 0:
                    raw_data = result['data'].get('accountProfits', [])
                    logger.info("earnings_retrieved_success", count=len(raw_data))
                    
                    # 3. Mapeo al formato que espera nuestro TimescaleRepository
                    formatted_earnings = []
                    for item in raw_data:
                        raw_ts = item.get('time') or item.get('day')
                        dt_object = datetime.fromtimestamp(float(raw_ts) / 1000.0, tz=timezone.utc)
                        # Binance devuelve el tiempo en milisegundos
                        formatted_earnings.append({
                            "timestamp": dt_object,
                            "coin": item.get('coinName', 'UNKNOWN'),
                            "amount": float(item.get('profitAmount', 0))
                        })
                    return formatted_earnings
                else:
                    logger.error("binance_api_earnings_error", status=response.status, detail=result)
                    return []
                    
        except Exception as e:
            logger.error("earnings_request_failed", error=str(e))
            return []

    async def close(self):
        if self.client:
            logger.info("cerrando_sesion_final_binance...")
            # Cerramos la sesión interna de aiohttp explícitamente
            if self.client.session:
                await self.client.session.close()
            await self.client.close_connection()
            await asyncio.sleep(0.250) 
            self.client = None


    