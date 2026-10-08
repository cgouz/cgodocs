# Bit Manipulation

Bit Manipulation is a technique used in a variety of problems to get the solution in an optimized way. This technique is very effective from a Competitive Programming point of view. It is all about Bitwise Operators which directly works upon binary numbers or bits of numbers that help the implementation fast. Below are the Bitwise Operators that are used:

- Bitwise AND (&)
- Bitwise OR (|)
- Bitwise XOR (^)
- Bitwise NOT (!)

All data in computer programs are internally stored as bits, i.e., as numbers 0 and 1.

## Bit representation
In programming, an n-bit integer is internally stored as a binary number that consists of n bits. For example, the C++ type int is a 32-bit type, which means that every int number consists of 32 bits.

The int number 43 = 00000000000000000000000000101011

The bits in the representation are indexed from right to left. To convert a bit representation bk ···b2 b1 b0 into a number, we can use the formula 

$$
b_k 2^k + \dots + b_2 2^2 + b_1 2^1 + b_0 2^0
$$

E.g., $1 \cdot 2^5 + 1 \cdot 2^3 + 1 \cdot 2^1 + 1 \cdot 2^0 = 43$.

The bit representation of a number is either signed or unsigned.
Usually, a signed representation is used, which means that both negative and positive numbers can be represented.
A signed variable of n bits can contain any integer between
$-2^{n-1}$ and $2^{n-1} - 1$

The int type in C++ is a signed type, so an int variable can contain any integer between $-2^{31}$ and $2^{31} - 1$.

The first bit in a signed representation is the sign of the number, 0 for non-negative numbers and 1 for negative numbers and the remaining n−1 bits contain the magnitude of the number.

Two’s complement is used, which means that the opposite number of a number is calculated by first inverting all the bits in the number, and then increasing the number by one.
The bit representation of the int number −43 is 11111111111111111111111111010101
In an unsigned representation, only non-negative numbers can be used, but the upper bound for the values is larger.
An unsigned variable of n bits can contain any integer between 0 and $2^n −1$.

In C++, an unsigned int variable can contain any integer between 0 and $2^32 −1$.
There is a connection between the representations:
A signed number −x equals an unsigned number $2^n − x$.
For example, the following pseudo-code snippet shows that the signed number 
x = −43 equals the unsigned number y = $2^32 −43$: 

```cpp
    int x;
    unsigned int y = x;

    cout << x << endl; // -43
    cout << y << endl; // 4294967253sub
```

If a number is larger than the upper bound of the bit representation, the number will overflow. In a signed representation, the next number after  $2^{n-1} - 1$ is $-2^{n-1}$, and in an unsigned representation, the next number after  $2^{n -1}$ is 0. For example, consider the following pseudo-code snippet:

```cpp
    int a = 2147483647; // Maximum value for a 32-bit signed integer
    
    cout << "Initial value of a: " << a << endl;

    a++; // This will cause an overflow
    cout << "Value of a after incrementing: " << a << endl; // This
```
Initially, the value of x is $2^31 −1$. This is the largest value that can be stored in an int variable, so the next number after $2^{31} −1$ is −$2^{31}$.

# Bitwise Operations:
Below is the table to illustrate the result when the operation is performed using Bitwise Operators. Here 0s or 1s mean a sequence of 0 or 1 respectively.



| Operator | Amal     | Natija |
|----------|----------|--------|
| XOR      | `X ^ 0s` | `X`    |
| XOR      | `X ^ 1s` | `~X`   |
| XOR      | `X ^ X`  | `0`    |
| AND      | `X & 0s` | `0`    |
| AND      | `X & 1s` | `X`    |
| AND      | `X & X`  | `X`    |
| OR       | `X \| 0s` | `X`   |
| OR       | `X \| 1s` | `1s`  |
| OR       | `X \| X`  | `X`   |

## Get Bit:
This method is used to find the bit at a particular position(say i) of the given number N. The idea is to find the Bitwise AND of the given number and 2i that can be represented as (1 << i). If the value return is 1 then the bit at the ith position is set. Otherwise, it is unset.

Below is the pseudo-code for the same:
```cpp
// Function to get the bit at the
// ith position
bool getBit(int num, int i) {
    // Return true if the bit is
    // set. Otherwise return false
    return ((num & (1 << i)) != 0);
}
```