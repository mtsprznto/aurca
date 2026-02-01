#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <iostream>
#include "src/features.cpp"

namespace py = pybind11;

// Declaración externa de la función que vive en features.cpp
std::vector<double> calculate_log_returns(const std::vector<double> &prices);

PYBIND11_MODULE(aurca_engine_bin, m)
{
    m.doc() = "Aurca Engine C++ Core";
    m.def("calculate_log_returns", [](const std::vector<double> &prices)
          {
        // --- DEBUGGER LAYER ---
        std::cout << "[DEBUG C++] Procesando lote de " << prices.size() << " precios." << std::endl;
        // ----------------------
        return calculate_log_returns(prices); }, "Calcula retornos logarítmicos de una serie de precios");

    m.def("calculate_rsi", [](const std::vector<double> &prices, int period)
          {
        // --- DEBUGGER ---
        std::cout << "[DEBUG C++] RSI: Procesando " << prices.size() << " velas con p=" << period << std::endl;
        return calculate_rsi(prices, period); }, "Calcula el RSI de una serie de precios", py::arg("prices"), py::arg("period") = 14);
}