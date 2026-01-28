#include <vector>
#include <cmath>

// Lógica pura de C++
std::vector<double> calculate_log_returns(const std::vector<double>& prices) {
    std::vector<double> returns;
    if (prices.size() < 2) return returns;
    
    returns.reserve(prices.size() - 1);
    for (size_t i = 1; i < prices.size(); ++i) {
        if (prices[i-1] > 0) { // Seguridad contra división por cero
            returns.push_back(std::log(prices[i] / prices[i-1]));
        }
    }
    return returns;
}