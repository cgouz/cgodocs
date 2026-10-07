# Bitwise Operators in C

Bitwise operators in C operate directly on the binary representation of integer values, performing operations bit by bit instead of on whole numbers. These operators are widely used in low-level programming, optimization, and embedded systems.

- Work with integral data types like char, short, int, and long.
- Used in system programming, embedded systems, and bit masking.
- Help perform fast operations such as shifting, toggling, and checking bits.

## Types of Bitwise Operators in C
Bitwise operators in C perform operations directly on the individual bits of integer data, enabling efficient low-level data manipulation and optimization.

### 1. Bitwise AND (&)
Bitwise AND operation compare each bit at the same position in the integer and the resultant bit will be set (1) only and only if both corresponding bits are set (1), otherwise it will be unset (0). The symbol which is used to perform bitwise AND operation is &.

**Example**: Let's perform a bitwise AND operation between two numbers- 7 and 4. In binary, 7 is represented as 111 and 4 is represented as 100.

```txt
  a = 7 = 111
  b = 4 = 100

  Bitwise AND Operation

    1  1  1
  & 1 0 0
    ------
    1 0 0  = 4
```

As we can see, only the last corresponding bits are set in both numbers. Therefore: 7 & 4 = 4

```c
#include <stdio.h>

int main() {
    printf("%d\n", (7 & 4));
    return 0;
}
```
**Output:**
```txt
4
```
### 2. Bitwise OR (|)
The Bitwise OR operation compares each bit at the same position, and the result bit will be set (1) if any of the corresponding bits are set (1). The symbol used to perform the bitwise OR operation is |.

**Example**: We will perform a bitwise OR operation between two numbers, 7 and 4.

```txt
a = 7 = 111
b = 4 = 100

Bitwise OR Operation

  1 1 1
| 1 0 0
  ------
  1 1 1 = 7
```

As we can see in the above example, the bits are set if at least one of the corresponding bits is set. Therefore, 7 | 4 = 7.

```cpp
#include <stdio.h>

int main() {
    printf("%d\n", (7 | 4));
    return 0;
}
```
Output
```
7
```

### 3. Bitwise XOR (^)

The Bitwise XOR operation compares each bit at the same position, and the result bit will be set (1) if the corresponding bits differ, i.e., one should be 1 and the other should be 0. The symbol used to perform the bitwise XOR operation is ^.

**Example:** We will perform a bitwise XOR operation between two numbers, 7 and 4.
```
a = 7 = 111
b = 4 = 100

Bitwise XOR Operation

  1 1 1
^ 1 0 0
------
  0 1 1 = 3   
```
As we can see in the above example, the bits are set where the corresponding bits differ. Therefore, 7 ^ 4 = 3.
```c
#include <stdio.h>

int main() {
    printf("%d\n", (7 ^ 4));
    return 0;
}
```

**Output**
```
3
```

### 4. Bitwise NOT (~)
The Bitwise NOT operation is performed on a single number. It changes the current bit to its complement, i.e., if the current bit is 0, then in the result it will be 1, and if the current bit is 1, it will become 0. It is denoted by the symbol ~.

**Example:** We will perform the Bitwise NOT operation on the number 4.

```
a = 4

Binary representation of 4: 00000000 00000000 00000000 00000100

After applying ~a:  11111111 11111111 11111111 11111011
```

The above representation shows only 3 bits for simplicity, but in reality, bitwise NOT operates on the full bit-width of the integer (typically 32-bit or 64-bit). For example, in a 32-bit system:

```cpp
#include <stdio.h>

int main() {
    printf("%d\n", (~4));
    return 0;
}
```
Output
```
-5
```

### n5. Left Shift (<<)
The leftshift operator shifts the bits of an integer to the left by a specific number of positions (as mentioned). This left shift operation is equivalent to multiplying the integer by 2 raised to the power of the number of positions shifted. The symbol used to represent the left shift operator is <<.

Example: Consider we have an integer 5, and we will left-shift its bits by 2 positions. The operation will be represented as

```
5 << 2
```
The number 5 is represented as 101 in binary. We will add some zeros at the beginning to left-shift the bits. Therefore, it will be represented as 00000101.

```
0 0 0 0 0 1 0 1 << 2
------------
0 0 0 1 0 1 0 0
```
Now, we will move all the bits two positions to the left and fill the empty positions with 0. Therefore, it will become 00010100, which is 20. As mentioned earlier, left-shifting the number by two bits means multiplying it by 2 raised to the power of 2, which is 4. So, 5 * 4 = 20.
```c
#include <stdio.h>

int main() {
    printf("%d\n", (5 << 2));
    return 0;
}
```
**Output**
```
20
```

### 6. Right Shift (>>)
The right shift operator (>>) shifts the bits of an integer to the right by a specified number of positions. For non-negative integers, it is generally equivalent to dividing the number by 2^n, where n is the number of shifted positions. However, for negative signed integers, the behavior may vary depending on the compiler implementation.

Example: Consider we have an integer 16, and we will right-shift its bits by 2 positions. The operation will be represented as

```
16 >> 2;
```

The number 16 is represented as 10000 in binary. We will add some zeros at the beginning to right-shift the bits. Therefore, it will be represented as 00010000.

```
0 0 0 1 0 0 0 0 >> 2
------------
0 0 0 0 0 1 0 0
```

Now, we will move all the bits two positions to the right and fill the empty positions with 0. Therefore, it will become 00000100, which is 4. As mentioned earlier, right-shifting the number by two bits means dividing it by 2 raised to the power of 2, which is 4. So, 16 / 4 = 4.

```c
#include <stdio.h>

int main() {
    printf("%d\n", (16 >> 2));
    return 0;
}
```
Output
```
4
```

### Interesting Facts About Bitwise Operators
- Shift Operators: Left-shift (<<) and right-shift (>>) should not be used with negative numbers. Shifting by a negative number or more than the size of the integer leads to undefined behavior. No shift occurs if the number of shifts is 0.
- Bitwise OR (|): The OR of two numbers is like adding them if no carry occurs. If there is a carry, the sum is calculated as a | b + a & b.
- Bitwise XOR (^): Very useful in programming problems. For example, finding the odd occurring number in a set where all other numbers occur even times can be done efficiently using XOR.

```c
#include <stdio.h>

int main(void)
{

    int arr[] = {12, 12, 14, 90, 14, 14, 14};
    int n = sizeof(arr) / sizeof(arr[0]);
    int res = 0, i;
    for (int i = 0; i < n; i++)
        res ^= arr[i];
    printf("%d", res);
    return 0;
}
```
Output
```
90
```

### Comparison Table of Bitwise Operators

| Operator | Name        | Purpose                                  |
|----------|-------------|------------------------------------------|
| `&`      | Bitwise AND | Returns 1 only if both bits are 1        |
| `\|`     | Bitwise OR  | Returns 1 if at least one bit is 1       |
| `^`      | Bitwise XOR | Returns 1 if bits are different          |
| `~`      | Bitwise NOT | Inverts all bits                         |
| `<<`     | Left Shift  | Shifts bits left (`x << n` = x · 2ⁿ)     |
| `>>`     | Right Shift | Shifts bits right (`x >> n` = x / 2ⁿ)    |