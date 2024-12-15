#include <iostream>
#include "crow_all.h"
#include <vector>
#include "json.hpp"
#include <cmath>
#include <sstream>
#include <chrono>

std::vector<int> matrix1_demo;
std::vector<int> matrix2_demo;
int got_data = 0;

void printMatrix(const std::vector<int>& matrix, int size) {
    std::stringstream ss;
    for (int i = 0; i < size; ++i) {
        for (int j = 0; j < size; ++j) {
            ss << matrix[i * size + j] << " ";
        }
        ss << std::endl;
    }

    std::cout << ss.str();
}

std::vector<int> matrixMultiply(const std::vector<int>& matrix1, const std::vector<int>& matrix2, int size) {
    std::vector<int> result(size * size, 0);

    for (int i = 0; i < size; ++i) {
        for (int j = 0; j < size; ++j) {
            for (int k = 0; k < size; ++k) {
                result[i * size + j] += matrix1[i * size + k] * matrix2[k * size + j];
            }
        }
    }

    return result;
}

bool isPerfectSquare(int num) {
    int squareRoot = std::sqrt(num);
    return squareRoot * squareRoot == num;
}

void handleProducerMessage(int prod_type, int prod_data) {
    if (prod_type == 1) {
        if (prod_data == -1) {
            got_data++;
        } else {
            matrix1_demo.push_back(prod_data);
        }
    } else if (prod_type == 2) {
        if (prod_data == -1) {
            got_data++;
        } else {
            matrix2_demo.push_back(prod_data);
        }
    }
}

std::pair<int, int> getData(const std::string& requestContent) {
    nlohmann::json json = nlohmann::json::parse(requestContent);
    return {json["message_type"], json["message_content"]};
}

int main() {
    crow::SimpleApp app;
    crow::logger::setLogLevel(crow::LogLevel::Warning);

    auto serverStartTime = std::chrono::high_resolution_clock::now(); // Время начала работы сервера

    CROW_ROUTE(app, "/data")
            .methods("POST"_method)([&](const crow::request& req, crow::response& res) {
                auto [prod_type, prod_data] = getData(req.body);

                handleProducerMessage(prod_type, prod_data);

                res.code = 200;
                res.set_header("Content-Type", "text/plain");
                res.body = std::to_string(prod_data);
                res.end();
            });

    CROW_ROUTE(app, "/end").methods("POST"_method)([&](const crow::request& req, crow::response& res) {
        got_data++;

        if (got_data == 2) {
            auto processingStartTime = std::chrono::high_resolution_clock::now();

            int size = std::sqrt(matrix1_demo.size());
            if (isPerfectSquare(matrix1_demo.size()) && isPerfectSquare(matrix2_demo.size())) {
                std::cout << "Matrix 1:" << std::endl;
                printMatrix(matrix1_demo, size);

                std::cout << "Matrix 2:" << std::endl;
                printMatrix(matrix2_demo, size);

                auto result = matrixMultiply(matrix1_demo, matrix2_demo, size);

                std::cout << "Resultant Matrix:" << std::endl;
                printMatrix(result, size);
            }

            auto processingEndTime = std::chrono::high_resolution_clock::now();
            std::chrono::duration<double, std::milli> processingDuration = processingEndTime - processingStartTime;
            std::cout << "Processing time: " << processingDuration.count() << " ms" << std::endl;

            // Завершаем сервер после обработки данных
            auto serverEndTime = std::chrono::high_resolution_clock::now();
            std::chrono::duration<double, std::milli> serverDuration = serverEndTime - serverStartTime;
            std::cout << "Total server runtime: " << serverDuration.count() << " ms" << std::endl;

            // Завершаем сервер
            exit(0);

            res.code = 200;
            res.set_header("Content-Type", "application/json");
            res.body = "{\"status\": \"OK\", \"message\": \"Matrices processed and multiplied successfully\"}";
        } else {
            res.code = 202;
            res.set_header("Content-Type", "application/json");
            res.body = "{\"status\": \"Processing\", \"message\": \"Waiting for all data\"}";
        }

        res.end();
    });

    std::cout << "Starting server..." << std::endl;
    app.port(8080).multithreaded().run();
}

