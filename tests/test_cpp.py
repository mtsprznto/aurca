import os
import sys

# 1. Agrega la ruta de los binarios de MSYS2 (ajusta si tu ruta es diferente)
msys_path = r"D:\msys64\ucrt64\bin" 
if os.path.exists(msys_path):
    os.add_dll_directory(msys_path)

# 2. Tu código anterior para el path del engine
sys.path.append(os.path.abspath("src/infrastructure/adapters/binance/cpp_engine"))


try:
    import aurca_engine
    print("✅ Motor C++ cargado exitosamente!")
    
    precios = [100.0, 102.5, 101.0, 105.0, 110.0]
    retornos = aurca_engine.calculate_log_returns(precios)
    
    print(f"Precios: {precios}")
    print(f"Retornos Logarítmicos: {retornos}")
    
except ImportError as e:
    print(f"❌ Error al importar el motor: {e}")
except Exception as e:
    print(f"❌ Error inesperado: {e}")