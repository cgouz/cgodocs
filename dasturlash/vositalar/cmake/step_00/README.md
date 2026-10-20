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

1. cmake_minimum_required(VERSION 3.23)
this tells CMake:
> This project need at least CMake version 2.23

if you installed CMake older than 2.23, configuration will stop with an error.

So this line is mainly about compatibility.