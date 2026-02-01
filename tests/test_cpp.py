import os
import aurca_engine

# Mantener soporte para Windows local (MSYS2)
msys_path = r"D:\msys64\ucrt64\bin" 
if os.path.exists(msys_path):
    os.add_dll_directory(msys_path)

print("🚀 Probando Motor Aurca (C++)...")

def test_engine():
    # 1. Probar Retornos Logarítmicos
    if aurca_engine.calculate_log_returns:
        precios = [100.0, 102.5, 101.0, 105.0, 110.0]
        retornos = aurca_engine.calculate_log_returns(precios)
        print(f"✅ Log Returns OK: {retornos}")
    else:
        print("❌ Error: calculate_log_returns no disponible.")

    # 2. Probar RSI
    if hasattr(aurca_engine, 'calculate_rsi') and aurca_engine.calculate_rsi:
        # Generamos una serie de precios que sube constantemente para ver el RSI subir
        precios_subida = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124, 126, 128]
        rsi_vals = aurca_engine.calculate_rsi(precios_subida, 14)
        
        print(f"✅ RSI OK. Último valor calculado: {rsi_vals[-1]:.2f}")
        print(f"Serie completa RSI: {[round(x, 2) for x in rsi_vals]}")
    else:
        print("❌ Error: calculate_rsi no disponible en el motor.")

if __name__ == "__main__":
    test_engine()