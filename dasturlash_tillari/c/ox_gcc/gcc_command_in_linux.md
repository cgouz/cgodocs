# gcc command in Linux with examples

GCC stands for GNU Compiler Collections which is used to compile mainly C and C++ language. It can also be used to compile Objective C and Objective C++.

- The most important option required while compiling a source code file is the name of the source program, rest every argument is optional like a warning, debugging, linking libraries, object file etc.
- There are different options in gcc command to allow the user to stop the compilation process at different stages.   

```txt
gcc [-c|-S|-E] [-std=standard]
```
---
**Example:** This will compile the source.c file and give the output file as a.out file which is default name of output file given by gcc compiler, which can be executed using ./a.out 
```sh
gcc source.c
```
---
* -o opt: This will compile the source.c file but instead of giving default name hence executed using ./opt, it will give output file as opt. -o is for output file option. 
```sh
gcc source.c -o opt
```
---
* -Werror: This will compile the source and show the warning if any error is there in the program, -W is for giving warnings. 
```sh
gcc source.c -Werror -o opt
```
---
* -Wall: This will check not only for errors but also for all kinds warning like unused variables errors, it is good practice to use this flag while compiling the code. 
```sh
gcc source.c -Wall -o opt
```
---
* -ggdb3: This command give us permissions to debug the program using gdb which will be described later, -g option is for debugging. 
```sh
gcc -ggdb3 source.c -Wall -o opt
```
---
* -lm : This command link math.h library to our source file, -l option is used for linking particular library, for math.h we use -lm. 
```sh
gcc -Wall source.c -o opt -lm
```
---
* -std=c11 :This command will use the c11 version of standards for compiling the source.c program, which allows to define variable under loop initializations also using newer standards version is preferred. 
```sh
gcc -Wall -std=c11 source.c -o opt
```
---
* -c : This command compile the program and give the object file as output, which is used to make libraries. 
---
* -v : This option is used for the verbose purpose. 
