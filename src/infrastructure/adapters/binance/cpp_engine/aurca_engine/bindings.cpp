#include <pybind11/pybind11.h>
#include <pybind11/stl.h> 
#include <vector>
#include "src/features.cpp"

namespace py = pybind11;

// Declaración externa de la función que vive en features.cpp
std::vector<double> calculate_log_returns(const std::vector<double> &prices);

PYBIND11_MODULE(aurca_engine_bin, m)
{
    m.doc() = "Aurca Engine C++ Core";
    m.def("calculate_log_returns", &calculate_log_returns, "Calcula retornos logarítmicos de una serie de precios");
}