#include <vector>
#include <cmath>
#include <iostream>

// Lógica pura de C++
std::vector<double> calculate_log_returns(const std::vector<double> &prices)
{
    if (prices.size() < 2)
    {
        std::cerr << "[DEBUG C++] Advertencia: Datos insuficientes para calcular retornos." << std::endl;
        return std::vector<double>();
    }

    std::vector<double> returns;
    returns.reserve(prices.size() - 1);

    for (size_t i = 1; i < prices.size(); ++i)
    {
        if (prices[i - 1] > 0)
        {
            returns.push_back(std::log(prices[i] / prices[i - 1]));
        }
        else
        {
            // Debugger para detectar anomalías en los datos de Binance
            std::cerr << "[DEBUG C++] Error en datos: Precio <= 0 detectado en índice " << i - 1 << std::endl;
        }
    }
    return returns;
}

// Lógica RSI (Wilder's Smoothing)
std::vector<double> calculate_rsi(const std::vector<double>& prices, int period) {
    if (prices.size() <= (size_t)period) {
        std::cerr << "[DEBUG C++] RSI Error: Insuficientes datos para periodo " << period << std::endl;
        return {};
    }

    std::vector<double> rsi_values;
    rsi_values.reserve(prices.size());

    double gain = 0.0;
    double loss = 0.0;

    // Primer promedio (Simple)
    for (int i = 1; i <= period; ++i) {
        double diff = prices[i] - prices[i-1];
        if (diff > 0) gain += diff;
        else loss -= diff;
    }

    double avg_gain = gain / period;
    double avg_loss = loss / period;

    // Llenar con NaN o 0 los primeros índices donde no hay RSI
    for (int i = 0; i < period; ++i) rsi_values.push_back(0.0);

    auto compute_rsi_val = [](double g, double l) {
        if (l == 0) return 100.0;
        double rs = g / l;
        return 100.0 - (100.0 / (1.0 + rs));
    };

    rsi_values.push_back(compute_rsi_val(avg_gain, avg_loss));

    // Suavizado de Wilder
    for (size_t i = period + 1; i < prices.size(); ++i) {
        double diff = prices[i] - prices[i-1];
        double current_gain = diff > 0 ? diff : 0.0;
        double current_loss = diff < 0 ? -diff : 0.0;

        avg_gain = (avg_gain * (period - 1) + current_gain) / period;
        avg_loss = (avg_loss * (period - 1) + current_loss) / period;

        rsi_values.push_back(compute_rsi_val(avg_gain, avg_loss));
    }

    return rsi_values;
}