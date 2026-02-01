import os
import aurca_engine

# Vital en Windows para las DLLs de MSYS2
msys_path = r"D:\msys64\ucrt64\bin" 
if os.path.exists(msys_path):
    os.add_dll_directory(msys_path)

print("🚀 Probando Motor Aurca (C++)...")

if aurca_engine.calculate_log_returns is None:
    print("❌ Error: El motor no cargó la función. Revisa el binario.")
else:
    try:
        precios = [100.0, 102.5, 101.0, 105.0, 110.0]
        retornos = aurca_engine.calculate_log_returns(precios)
        
        print("✅ ¡CÁLCULO EXITOSO!")
        print(f"Entrada: {precios}")
        print(f"Salida (Log Returns): {retornos}")
    except Exception as e:
        print(f"❌ Error durante el cálculo: {e}")