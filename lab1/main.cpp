#include <iostream>
#include <vector>
#include <fstream>
#include <random>
#include <omp.h>

constexpr int NUM_RUNS = 1;
constexpr int MAX_THREADS = 16;
constexpr int SIZE = 10000000;

void generate_array(std::vector<int>& array, int seed, int threads);

int sedgewick(std::vector<int>& gap_arr, int size) {
    int multiplier1 = 1, multiplier2 = 1, multiplier3 = 1, counter = -1;
    do {
        if (++counter % 2) {  // << нечетный проход
            multiplier2 *= 2;
            gap_arr[counter] = 8 * multiplier1 - 6 * multiplier2 + 1;
        } else {  // << четный проход
            gap_arr[counter] = 9 * multiplier1 - 9 * multiplier3 + 1;
            multiplier3 *= 2;
        }
        multiplier1 *= 2;
    } while (3 * gap_arr[counter] < size);
    return (counter > 0 ? --counter : 0);
}

double shell_sort(std::vector<int>& array, int size, int threads) {
    auto start = omp_get_wtime();
    int gap, j, counter;
    std::vector<int> gap_arr(50);
    counter = sedgewick(gap_arr, size);
    while (counter >= 0) {
        gap = gap_arr[counter--];
#pragma omp parallel for num_threads(threads) shared(array, size, gap) private(j) default(none)
        for (int i = 0; i < gap; i++) {
            for (j = gap + i; j < size; j += gap) {
                int k = j;
                while (k > i && array[k - gap] > array[k]) {
                    int temp = array[k];
                    array[k] = array[k-gap];
                    array[k-=gap] = temp;
                }
            }
        }
    }
    auto end = omp_get_wtime();
    auto duration = end - start;
    std::cout << "Threads: " << threads << ", Time: " << duration << ", First element: " << array[0] << '\n';
    return duration;
}

int main() {
    double start = omp_get_wtime();
    std::ofstream file("results.txt");
    if (!file.is_open()) {
        std::cerr << "Failed to open file\n";
        return 1;
    }

    std::cout << "\tACCURACY == " << omp_get_wtick() << '\n';
    std::vector<std::vector<int>> arrays(NUM_RUNS, std::vector<int>(SIZE));

    for (int threads = 1; threads <= MAX_THREADS; threads++) {
        double time_spent = 0;
        for (int i = 0; i < NUM_RUNS; i++) {
            generate_array(arrays[i], i + 920215, threads);
        }
        for (int run = 0; run < NUM_RUNS; run++) {
            time_spent += shell_sort(arrays[run], SIZE, threads);
        }
        time_spent /= NUM_RUNS;
        file << threads << ' ' << time_spent << '\n';
    }
    start = omp_get_wtime() - start;
    std::cout << "TOTAL TIME " << start <<'\n';
    file << "TOTAL TIME" << ' ' << start << '\n';
    return 0;
}

void generate_array(std::vector<int>& array, int seed, int threads) {
    std::mt19937 gen(seed);
    std::uniform_int_distribution<int> dist(1, RAND_MAX);

#pragma omp parallel for num_threads(threads)
    for (int i = 0; i < array.size(); i++) {
        array[i] = dist(gen);
    }
}
