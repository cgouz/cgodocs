# explain:
```cmake
cmake_minimum_required(VERSION 3.23)

project(step00)

add_executable(hello)

target_sources(
    hello
    PRIVATE
        helloWorld.cxx
)
```

## 1. cmake_minimum_required(VERSION 3.23)
this tells CMake:
> This project need at least CMake version 2.23

if you installed CMake older than 2.23, configuration will stop with an error.

So this line is mainly about compatibility.

## 2. project(step00)

This creates a CMake project named:
```text
step00
```
CMake also uses this command to initialize project-related things.

Because you did not explicitly specify a language, CMake will normally enable both C and C++.

You could also write:
```cmake
project(step00 LANGUAGES CXX)
```
which means:
> “This project only uses C++.”

For your current example, that is a little cleaner.

## 3. add_executable(hello)
This tells CMake:
> “I want to create an executable target named hello.”

The important word here is target.

A target is something CMake builds.

For example:
```text
hello
```
as the executable file on Linux.

At this point, however, you have not yet told CMake which `.cxx` file belongs to `hello`.

That comes next.

## 4. target_sources(
This command adds source files to an existing target.
You already created this target:
```cmake
add_executable(hello)
```

Now you are saying:
> “Here are the source files that belong to hello.”

Inside it:
```txt
hello
```
This is the target you are modifying.

So:
```cmake
target_sources(
    hello
```

means:
> “Add sources to the target named hello.”

Then:
```cmake
PRIVATE
```
This specifies the scope of the source file.
For now, the simplest meaning is:
> “This source file belongs specifically to hello.”

So:
```cmake
PRIVATE
    helloWorld.cxx
```

means:
> "helloWorld.cxx is a source file used by hello."

`PRIVATE`, `PUBLIC`, and `INTERFACE` become much more important later when you work with libraries and dependencies.

For step00, just remember:
```txt
PRIVATE = this target uses it internally
```

# RUN

```sh
cmake -S . -B build
cmake --build build
```

## These two commands do different jobs.

### cmake -S . -B build
```bash
cmake -S . -B build
```
This is the configure/generate step.

Breakdown:

```txt
cmake      → run the CMake program
-S         → source directory option
.          → argument for -S
-B         → build directory option
build      → argument for -B
```

So:
```
-S .
```
means:
> Use the current directory . as the source directory.

CMake expects to find your:

```txt
CMakeLists.txt
```
there.

And:
```
-B build
```
means:
> Put all generated build files inside the build/ directory.

So if you have:
```txt
step00/
├── CMakeLists.txt
└── helloWorld.cxx
```

after:

```sh
cmake -S . -B build
```

you may get:
```
step00/
├── CMakeLists.txt
├── helloWorld.cxx
└── build/
    ├── CMakeCache.txt
    ├── CMakeFiles/
    ├── Makefile
    └── ...
```

Important: this command usually does not compile your C++ source yet.

It mainly reads:

```txt
CMakeLists.txt
```

and generates a build system.

Now the second command:

### cmake --build build

This is the actual build/compile step.

Breakdown:

```txt
cmake        → run CMake
--build      → tell CMake to build an already configured project
build        → path to the build directory
```

So:
```bash
cmake --build build
```
means:
> Go into the build configuration stored in build/ and build the targets.