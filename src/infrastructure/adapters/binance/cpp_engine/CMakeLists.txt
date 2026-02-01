cmake_minimum_required(VERSION 3.15)
project(aurca_engine_bin LANGUAGES CXX)

find_package(pybind11 REQUIRED)

# Añadimos flags para enlazado estático (VITAL para Windows/MinGW)
if(WIN32)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -static-libgcc -static-libstdc++ -static")
endif()

include_directories(aurca_engine)

pybind11_add_module(aurca_engine_bin aurca_engine/bindings.cpp)

# Aseguramos que el binario se instale en la raíz del paquete
install(TARGETS aurca_engine_bin DESTINATION .)