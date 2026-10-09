#include <iostream>
#include <bitset>

// Function to set the ith bit of the
// given number num
int setBit(int num, int i) {
    // Sets the ith bit and return
    // the updated value
    return num | (1 << i);
}

int main () {
    int number = 5; // Binary: 0101
    int i = 1;

    std::cout << "Before setting bit: " << std::bitset<4>(number) << std::endl; // Output: 0101

    number = setBit(number, i);

    std::cout << "After setting bit: " << std::bitset<4>(number) << std::endl; // Output: 0111 = 7

    return 0;
}

/*

5, 1

1: 0001 << 1 => 0010
2: 0101 | 0010 => 0111

*/