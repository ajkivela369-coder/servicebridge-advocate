#include <cmath>
#include <iostream>
#include <stdexcept>
#include <vector>

double cosine_similarity(const std::vector<double>& a, const std::vector<double>& b) {
    if (a.size() != b.size() || a.empty()) {
        throw std::invalid_argument("vectors must be non-empty and have the same length");
    }

    double dot = 0.0;
    double norm_a = 0.0;
    double norm_b = 0.0;

    for (std::size_t i = 0; i < a.size(); ++i) {
        dot += a[i] * b[i];
        norm_a += a[i] * a[i];
        norm_b += b[i] * b[i];
    }

    if (norm_a == 0.0 || norm_b == 0.0) return 0.0;
    return dot / (std::sqrt(norm_a) * std::sqrt(norm_b));
}

int main() {
    std::vector<double> query{0.8, 0.1, 0.4};
    std::vector<double> document{0.7, 0.2, 0.5};
    std::cout << "cosine_similarity=" << cosine_similarity(query, document) << "\n";
}
