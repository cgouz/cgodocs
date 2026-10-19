# Minimum required CMake version
cmake_minimum_required(VERSION 3.23)

# Define project name, version and languages
project(MyProject VERSION 1.0.0 LANGUAGES C CXX)

# Set a variable
set(APP_NAME myapp)

# Set a list variable
set(SOURCES
    src/main.c
    src/game.c
)

# Print a status message
message(STATUS "Project: ${PROJECT_NAME}")

# Create a boolean option configurable with -D
option(ENABLE_LOGGING "Enable logging" OFF)

# Conditional statement
if(ENABLE_LOGGING)
    message(STATUS "Logging enabled")
elseif(WIN32)
    message(STATUS "Running on Windows")
else()
    message(STATUS "Default case")
endif()

# Logical operators
if(UNIX AND NOT APPLE)
    message(STATUS "Unix, but not Apple")
endif()

# String comparison
if(PROJECT_NAME STREQUAL "MyProject")
    message(STATUS "Project name matched")
endif()

# Numeric comparison
if(MY_NUMBER GREATER 10)
    message(STATUS "Greater than 10")
endif()

# Loop over values
foreach(item one two three)
    message(STATUS "${item}")
endforeach()

# Loop over numeric range
foreach(i RANGE 0 10 2)
    message(STATUS "${i}")
endforeach()

# While loop
while(CONDITION)
    message(STATUS "Looping")
endwhile()

# Evaluate arithmetic expression
math(EXPR RESULT "10 + 20")

# Append item to list
list(APPEND SOURCES src/player.c)

# Remove item from list
list(REMOVE_ITEM SOURCES src/game.c)

# Get list length
list(LENGTH SOURCES SOURCE_COUNT)

# Get item from list
list(GET SOURCES 0 FIRST_SOURCE)

# Create executable target
add_executable(myapp
    src/main.c
    src/game.c
)

# Add sources to an existing target
target_sources(myapp
    PRIVATE
        src/player.c
)

# Create static library
add_library(mymath STATIC
    src/add.c
    src/sub.c
)

# Create shared library
add_library(mymath_shared SHARED
    src/add.c
    src/sub.c
)

# Create library using BUILD_SHARED_LIBS default
add_library(mylib
    src/lib.c
)

# Create interface-only library
add_library(project_options INTERFACE)

# Create alias for another target
add_library(MyProject::Math ALIAS mymath)

# Add include directories to target
target_include_directories(myapp
    PRIVATE
        ${PROJECT_SOURCE_DIR}/include
)

# Public include directory inherited by consumers
target_include_directories(mymath
    PUBLIC
        ${PROJECT_SOURCE_DIR}/include
)

# Link libraries to target
target_link_libraries(myapp
    PRIVATE
        mymath
        m
)

# Set required C language standard
target_compile_features(myapp
    PRIVATE
        c_std_17
)

# Set required C++ language standard
target_compile_features(mycppapp
    PRIVATE
        cxx_std_20
)

# Add compiler options
target_compile_options(myapp
    PRIVATE
        -Wall
        -Wextra
        -Wpedantic
)

# Add preprocessor definitions
target_compile_definitions(myapp
    PRIVATE
        DEBUG
        VERSION_MAJOR=1
)

# Define DEBUG only for Debug builds
target_compile_definitions(myapp
    PRIVATE
        $<$<CONFIG:Debug>:DEBUG>
)

# Add subdirectory containing another CMakeLists.txt
add_subdirectory(src)

# Find external package
find_package(SDL2 REQUIRED)

# Link imported package target
target_link_libraries(myapp
    PRIVATE
        SDL2::SDL2
)

# Find threading library
find_package(Threads REQUIRED)

# Link portable threading target
target_link_libraries(myapp
    PRIVATE
        Threads::Threads
)

# Find pkg-config
find_package(PkgConfig REQUIRED)

# Find library through pkg-config
pkg_check_modules(
    SDL2_TTF
    REQUIRED
    IMPORTED_TARGET
    SDL2_ttf
)

# Link pkg-config imported target
target_link_libraries(myapp
    PRIVATE
        PkgConfig::SDL2_TTF
)

# Generate file from template
configure_file(
    config.h.in
    config.h
    @ONLY
)

# Define custom CMake function
function(print_name NAME)
    message(STATUS "${NAME}")
endfunction()

# Call custom function
print_name("hello")

# Define macro
macro(print_value VALUE)
    message(STATUS "${VALUE}")
endmacro()

# Call macro
print_value("hello")

# Return from function/file
return()

# Read file content into variable
file(READ input.txt CONTENT)

# Write file
file(WRITE output.txt "Hello")

# Append to file
file(APPEND output.txt " World")

# Create directory
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/generated")

# Find files matching pattern
file(GLOB SOURCES "src/*.c")

# Convert string to uppercase
string(TOUPPER "${PROJECT_NAME}" PROJECT_NAME_UPPER)

# Convert string to lowercase
string(TOLOWER "${PROJECT_NAME}" PROJECT_NAME_LOWER)

# Replace text inside string
string(REPLACE "old" "new" RESULT "${INPUT}")

# Read environment variable
message(STATUS "$ENV{HOME}")

# Set environment variable
set(ENV{MY_VAR} "value")

# Define cache variable
set(MY_VALUE "default" CACHE STRING "User configurable value")

# Install executable
install(
    TARGETS myapp
    RUNTIME DESTINATION bin
)

# Install library
install(
    TARGETS mymath
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

# Install headers
install(
    DIRECTORY include/
    DESTINATION include
)

# Enable CTest support
include(CTest)

# Add test executable
add_executable(test_math
    tests/test_math.c
)

# Register test
add_test(
    NAME MathTest
    COMMAND test_math
)

# Check operating system
if(WIN32)
endif()

if(UNIX)
endif()

if(APPLE)
endif()

# Check compiler
if(CMAKE_C_COMPILER_ID STREQUAL "GNU")
endif()

if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
endif()

# Check whether cross-compiling
if(CMAKE_CROSSCOMPILING)
endif()

# Target operating system name
message(STATUS "${CMAKE_SYSTEM_NAME}")

# Target CPU architecture
message(STATUS "${CMAKE_SYSTEM_PROCESSOR}")

# Host operating system
message(STATUS "${CMAKE_HOST_SYSTEM_NAME}")

# Host CPU architecture
message(STATUS "${CMAKE_HOST_SYSTEM_PROCESSOR}")

# C compiler path
message(STATUS "${CMAKE_C_COMPILER}")

# C++ compiler path
message(STATUS "${CMAKE_CXX_COMPILER}")

# Root project source directory
message(STATUS "${PROJECT_SOURCE_DIR}")

# Root project build directory
message(STATUS "${PROJECT_BINARY_DIR}")

# Current source directory
message(STATUS "${CMAKE_CURRENT_SOURCE_DIR}")

# Current build directory
message(STATUS "${CMAKE_CURRENT_BINARY_DIR}")

# Project name
message(STATUS "${PROJECT_NAME}")

# Project version
message(STATUS "${PROJECT_VERSION}")

# Project version parts
message(STATUS "${PROJECT_VERSION_MAJOR}")
message(STATUS "${PROJECT_VERSION_MINOR}")
message(STATUS "${PROJECT_VERSION_PATCH}")

# Set sysroot for cross-compilation
set(CMAKE_SYSROOT "/path/to/sysroot")

# Set target system in toolchain file
set(CMAKE_SYSTEM_NAME Linux)

# Set target architecture in toolchain file
set(CMAKE_SYSTEM_PROCESSOR aarch64)

# Set cross C compiler
set(CMAKE_C_COMPILER aarch64-linux-gnu-gcc)

# Set cross C++ compiler
set(CMAKE_CXX_COMPILER aarch64-linux-gnu-g++)

# Add custom command that generates a file
add_custom_command(
    OUTPUT generated.c
    COMMAND generator_tool > generated.c
    DEPENDS generator_tool
)

# Add custom build target
add_custom_target(generate_files
    COMMAND generator_tool
)

# Declare dependency between targets
add_dependencies(myapp generate_files)

# Set properties on target
set_target_properties(myapp PROPERTIES
    OUTPUT_NAME "application"
)

# Get target property
get_target_property(
    TARGET_TYPE
    myapp
    TYPE
)

# Include another CMake script
include(cmake/helpers.cmake)

# Include module only if available
include(CheckIncludeFile)

# Check whether C header exists
check_include_file(
    "unistd.h"
    HAVE_UNISTD_H
)

# Print fatal error and stop configuration
message(FATAL_ERROR "Configuration failed")

# Print warning
message(WARNING "Something may be wrong")

# Print developer warning
message(AUTHOR_WARNING "Developer warning")

# Configuration error, generation will fail
message(SEND_ERROR "Invalid configuration")