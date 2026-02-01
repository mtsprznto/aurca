import os
from datetime import datetime
from decimal import Decimal
from src.domain.entities.market_data import Candle
from src.domain.services.feature_engineering.indicators import IndicatorService
# Soporte para local
msys_path = r"D:\msys64\ucrt64\bin" 
if os.path.exists(msys_path):
    import ctypes
    os.add_dll_directory(msys_path)

def test_rsi_logic():
    print("🧪 Iniciando Test de Integración RSI...")
    
    # 1. Simulamos 20 velas de subida constante
    mock_candles = [
        Candle(
            symbol="BTCUSDT",
            timestamp=datetime.now(),
            open=Decimal(100 + i),
            high=Decimal(101 + i),
            low=Decimal(99 + i),
            close=Decimal(101 + i),
            volume=Decimal(10),
            timeframe="1h"
        ) for i in range(20)
    ]

    # 2. Pasamos por el servicio que usa el motor C++
    service = IndicatorService()
    processed_candles = service.add_indicators(mock_candles)

    # 3. Validaciones
    last_candle = processed_candles[-1]
    
    print(f"📊 Resultado Final:")
    print(f"   - Símbolo: {last_candle.symbol}")
    print(f"   - Último Cierre: {last_candle.close}")
    print(f"   - RSI Calculado (C++): {last_candle.rsi}")
    print(f"   - Log Return (C++): {last_candle.log_return}")

    if last_candle.rsi is not None and last_candle.rsi > 50:
        print("✅ TEST EXITOSO: El RSI refleja la tendencia alcista.")
    else:
        print("❌ TEST FALLIDO: El RSI no se calculó correctamente.")

if __name__ == "__main__":
    test_rsi_logic()