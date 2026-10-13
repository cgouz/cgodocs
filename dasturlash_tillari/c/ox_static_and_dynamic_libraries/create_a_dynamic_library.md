# How to Create a Dynamic Library in C?

In C, a dynamic library is a library that is loaded at runtime rather than compile time. We can create our own dynamic libraries and use them in our programs. In this article, we will learn how to create a dynamic library in C.

## Creating a Dynamic Library in C
To create a dynamic library in C, we first need to write our C code and then compile it into a shared library using the -shared option of the gcc compiler. Below is the step by step process for creating the dynamic libraries:

### Create Header File
We first create a header file that declares all the methods and properties.
**mathlib.h**
```C
#include pragma once
#ifndef MATHLIB_H

void printHello();
int add(int a, int );


#endl
```

### Create Library Source Code
The below example demonstrates the creation of a dynamic library in C.
```C
// C program to create a dynamic library

// File: mathlib.c

#include <stdio.h>

void print_hello() { printf("Hello, geeksforgeeks!\n"); }

int add(int a, int b) { return a + b; }
```
To compile this code into a shared library, we use the following command:

```sh
gcc -shared -o libmathlib.so mathlib.c -Iinclude/
```
This command creates a dynamic library named libmathlib.so. We can then link this library in our program

Time Complexity: The time complexity of creating a dynamic library depends on the size and complexity of the code being compiled. Auxiliary Space: The space required is the space needed to store the dynamic library, which also depends on the size of the original code.


