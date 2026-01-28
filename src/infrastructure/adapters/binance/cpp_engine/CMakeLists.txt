# src\infrastructure\adapters\binance\cpp_engine\CMakeLists.txt
cmake_minimum_required(VERSION 3.18)
project(aurca_engine)

set(CMAKE_CXX_STANDARD 17)

find_package(pybind11 REQUIRED)

# Definimos el módulo
pybind11_add_module(aurca_engine 
    aurca_engine/src/features.cpp 
    aurca_engine/bindings.cpp
)
# ESTO ES LO QUE DA LA CERTEZA:
# 1. Forzamos que el nombre del archivo sea exactamente aurca_engine.so (sin prefijos lib)
set_target_properties(aurca_engine PROPERTIES 
    OUTPUT_NAME "aurca_engine"
    PREFIX ""
)
# 2. Instrucción de instalación que scikit-build-core usa para el empaquetado
install(TARGETS aurca_engine LIBRARY DESTINATION aurca_engine)