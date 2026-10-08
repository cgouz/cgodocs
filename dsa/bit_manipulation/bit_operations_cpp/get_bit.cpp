#include <iostream>
#include <bitset>

bool get_bit(int number, int i) {

    return (number & (1 << i)) != 0;
}

// 5 => 0101
// 1 => 0001
// 1 << 2 => 0100
// 0101 & 0100 => 0100
// 0100 != 0 => true
int main () {

    int number = 5; // Binary: 0101
    int i = 2;

    std::cout << get_bit(number, i) << std::endl; // Output: 1

    return 0;
}
