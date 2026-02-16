#ifndef FEATURES_HPP
#define FEATURES_HPP
#include <vector>

std::vector<double> calculate_log_returns(const std::vector<double>& prices);
std::vector<double> calculate_rsi(const std::vector<double>& prices, int period);

#endif