# What is CMake
>Building and Managing Complex Software Projects Simplified

## Understanding CMake
CMake is a tool that generates native build system files for a variety of platforms. It is widely used to configure projects, specify build parameters, and streamline the compilation process.

Feature	               |  Description
-----------------------|----------------------------------
Cross-Platform Support | Generates build files for Unix, Windows, macOS, and more.
Customizability	       | Provides flexibility through its scripting language.
Integration	           | Compatible with IDEs like Visual Studio, Xcode, and CLion.
Dependency Management  | Simplifies handling of third-party libraries.
Parallel Builds	       | Supports concurrent build processes for faster compilation.
----------------------------------------------------------

## How CMake Works
CMake separates the configuration of a build system from the actual build process. Developers write CMakeLists.txt files to define the build configuration, which are then used to generate build system files like Makefiles or Visual Studio project files.

The `CMakeLists.txt` file is the heart of a CMake-based project. It defines how the project should be built.

```cmake
cmake_minimum_required(VERSION 3.10)
project(MyProject)

# Add executable target
add_executable(MyExecutable main.cpp utils.cpp)
```
This example specifies the minimum CMake version, the project name, and an executable target with its source files.

