#include <iostream>
#include <bitset>
#include <X11/X.h>

// Function to clear the ith bit of
// the given number num
int clearBit(int num, int i)
{

    // Create the mask for the ith
    // bit unset
    int mask = ~(1 << i);

    // Return the updated value
    return num & mask;
}

int main () {
    int num = 4; // Binary: 0100
    int i = 2;    // Clear the 2nd bit

    std::cout << "Original number: " << num << std::endl; // Output: 4
    std::cout << "Number after clearing " << i << "th bit: " << clearBit(num, i) << std::endl; // Output: 0

    return 0;
}

/**
 * num = 4 (Binary: 0100)
 * i = 2 (We want to clear the 2nd bit)
 * step 1: Create a mask to clear the ith bit
 * mask = ~(1 << i) = ~(1 << 2) = ~(00000100) = 11111011
 * step 2: Perform bitwise AND operation with the original number
 * result = num & mask = 0100 & 11111011 = 0000
 */

