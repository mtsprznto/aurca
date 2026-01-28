#include <pybind11/pybind11.h>
#include <pybind11/stl.h> 
#include <vector>

namespace py = pybind11;

// Declaración externa de la función que vive en features.cpp
std::vector<double> calculate_log_returns(const std::vector<double> &prices);

PYBIND11_MODULE(aurca_engine, m)
{
    m.doc() = "Motor C++ de Aurca para cálculos de alta velocidad";
    m.def("calculate_log_returns", &calculate_log_returns, "Calcula retornos logarítmicos de una serie de precios");
}