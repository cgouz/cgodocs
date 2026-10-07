#include <iostream>

using namespace std;

int main() {
    
    int a = 2147483647; // Maximum value for a 32-bit signed integer
    
    cout << "Initial value of a: " << a << endl;

    a++; // This will cause an overflow
    cout << "Value of a after incrementing: " << a << endl; // This

    return 0;
}