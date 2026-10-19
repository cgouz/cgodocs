# Modern CMake — Zero to Advanced

```cmake
# ============================================================
# COMMENTS
# ============================================================

# This is a single-line comment.

#[[
    This is a
    multi-line comment.
]]
```

---

# 1. Basic project structure

Oddiy project:

```text
myproject/
├── CMakeLists.txt
├── include/
│   └── math.h
└── src/
    ├── main.c
    └── math.c
```

Build directory source directory’dan alohida bo‘lishi tavsiya qilinadi:

```bash
cmake -S . -B build
cmake --build build
```

Bu:

```text
source/
├── CMakeLists.txt
├── src/
└── include/

build/
├── CMakeCache.txt
├── Makefile / Ninja files
└── executable
```

ko‘rinishini beradi.

---

# 2. Minimum CMake version

```cmake
cmake_minimum_required(VERSION 3.23)
```

Bu:

> project kamida CMake 3.23 talab qiladi

degani.

Agar installed CMake bundan eski bo‘lsa, configuration to‘xtaydi.

Odatda bu `CMakeLists.txt`ning birinchi command’i bo‘ladi.

---

# 3. Project

```cmake
project(MyProject)
```

Yaxshiroq:

```cmake
project(
    MyProject
    VERSION 1.0.0
    LANGUAGES C
)
```

C++ project:

```cmake
project(
    MyProject
    VERSION 1.0.0
    LANGUAGES CXX
)
```

C va C++:

```cmake
project(
    MyProject
    VERSION 1.0.0
    LANGUAGES C CXX
)
```

Bu avtomatik variables yaratadi:

```cmake
PROJECT_NAME
PROJECT_VERSION

PROJECT_VERSION_MAJOR
PROJECT_VERSION_MINOR
PROJECT_VERSION_PATCH

PROJECT_SOURCE_DIR
PROJECT_BINARY_DIR
```

Masalan:

```cmake
message(STATUS "Project: ${PROJECT_NAME}")
message(STATUS "Version: ${PROJECT_VERSION}")
```

---

# 4. Variables

Variable yaratish:

```cmake
set(MY_VARIABLE "Hello")
```

Ishlatish:

```cmake
message(STATUS "${MY_VARIABLE}")
```

Masalan:

```cmake
set(APP_NAME myapp)

add_executable(${APP_NAME}
    src/main.c
)
```

Bir nechta qiymat:

```cmake
set(SOURCES
    src/main.c
    src/math.c
    src/game.c
)
```

Keyin:

```cmake
add_executable(myapp ${SOURCES})
```

---

# 5. CMake built-in directory variables

Current `CMakeLists.txt` joylashgan directory:

```cmake
${CMAKE_CURRENT_SOURCE_DIR}
```

Current build directory:

```cmake
${CMAKE_CURRENT_BINARY_DIR}
```

Root project source:

```cmake
${PROJECT_SOURCE_DIR}
```

Root project build:

```cmake
${PROJECT_BINARY_DIR}
```

Yana:

```cmake
${CMAKE_SOURCE_DIR}
${CMAKE_BINARY_DIR}
```

---

# 6. message()

Oddiy output:

```cmake
message("Hello CMake")
```

Status:

```cmake
message(STATUS "Configuring project...")
```

Warning:

```cmake
message(WARNING "Something may be wrong")
```

Author warning:

```cmake
message(AUTHOR_WARNING "Developer warning")
```

Error, lekin processing davom etishi mumkin:

```cmake
message(SEND_ERROR "Configuration error")
```

Darhol to‘xtatish:

```cmake
message(FATAL_ERROR "Cannot continue")
```

---

# 7. Executable target

Eng muhim commandlardan biri:

```cmake
add_executable(myapp
    src/main.c
)
```

Bu `myapp` nomli **target** yaratadi.

Bir nechta source:

```cmake
add_executable(myapp
    src/main.c
    src/game.c
    src/player.c
)
```

Mental model:

```text
TARGET: myapp
├── main.c
├── game.c
└── player.c
```

---

# 8. target_sources()

Sources’larni keyin ham qo‘shish mumkin:

```cmake
add_executable(myapp)

target_sources(myapp
    PRIVATE
        src/main.c
        src/game.c
        src/player.c
)
```

Modern CMake’da target atrofida configuration yig‘ish uchun qulay.

---

# 9. Include directories

Eski global style:

```cmake
include_directories(include)
```

o‘rniga target-based style:

```cmake
target_include_directories(myapp
    PRIVATE
        ${PROJECT_SOURCE_DIR}/include
)
```

Bu GCC’dagi taxminan:

```bash
-I/path/to/include
```

ga mos keladi.

---

# 10. PRIVATE / PUBLIC / INTERFACE

Modern CMake’ning eng muhim tushunchalaridan biri.

```cmake
target_include_directories(mylib
    PUBLIC
        include
)
```

### PRIVATE

Faqat targetning o‘zi foydalanadi:

```text
target
  ↓
uses dependency

consumer
  ✗ doesn't inherit
```

Misol:

```cmake
target_include_directories(myapp PRIVATE include)
```

---

### PUBLIC

Targetning o‘zi ham ishlatadi, target’dan foydalanuvchilar ham oladi:

```text
library
  ↓
uses setting

consumer
  ↓
inherits setting
```

---

### INTERFACE

Targetning o‘zi ishlatmaydi.

Faqat undan foydalanuvchilarga uzatiladi:

```text
library itself
   ✗

consumer
   ✓
```

---

# 11. Creating a static library

```cmake
add_library(mymath STATIC
    src/add.c
    src/sub.c
)
```

Natijada Linux’da taxminan:

```text
libmymath.a
```

yaratiladi.

---

# 12. Creating a shared library

```cmake
add_library(mymath SHARED
    src/add.c
    src/sub.c
)
```

Linux:

```text
libmymath.so
```

Windows:

```text
mymath.dll
```

macOS:

```text
libmymath.dylib
```

---

# 13. Library without explicitly choosing STATIC/SHARED

```cmake
add_library(mymath
    src/add.c
    src/sub.c
)
```

Bu holatda:

```cmake
BUILD_SHARED_LIBS
```

configuration ta’sir qilishi mumkin.

Masalan:

```bash
cmake -S . -B build -DBUILD_SHARED_LIBS=ON
```

---

# 14. Linking libraries

```cmake
target_link_libraries(myapp
    PRIVATE
        mymath
)
```

Mental model:

```text
myapp
  ↓
depends on
  ↓
mymath
```

System math library:

```cmake
target_link_libraries(myapp
    PRIVATE
        m
)
```

GCC’da bu:

```bash
-lm
```

ga o‘xshaydi.

---

# 15. Complete library example

Structure:

```text
project/
├── CMakeLists.txt
├── include/
│   └── mymath.h
└── src/
    ├── main.c
    ├── add.c
    └── sub.c
```

CMake:

```cmake
cmake_minimum_required(VERSION 3.23)

project(MyMathProject LANGUAGES C)

add_library(mymath
    src/add.c
    src/sub.c
)

target_include_directories(mymath
    PUBLIC
        ${PROJECT_SOURCE_DIR}/include
)

add_executable(app
    src/main.c
)

target_link_libraries(app
    PRIVATE
        mymath
)
```

Dependency:

```text
app
 ↓
mymath
 ↓
include/mymath.h
```

---

# 16. C language standard

Target-based modern approach:

```cmake
target_compile_features(myapp
    PRIVATE
        c_std_11
)
```

C17:

```cmake
target_compile_features(myapp
    PRIVATE
        c_std_17
)
```

C23:

```cmake
target_compile_features(myapp
    PRIVATE
        c_std_23
)
```

C++:

```cmake
target_compile_features(myapp
    PRIVATE
        cxx_std_20
)
```

Bu CMake’ga:

> target kamida shu language feature/standard’ni talab qiladi

deydi.

---

# 17. Compiler options

GCC:

```bash
-Wall -Wextra -Wpedantic
```

CMake:

```cmake
target_compile_options(myapp
    PRIVATE
        -Wall
        -Wextra
        -Wpedantic
)
```

Lekin compiler-specific option bo‘lsa compiler’ni tekshirish yaxshi.

```cmake
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(myapp
        PRIVATE
            -Wall
            -Wextra
            -Wpedantic
    )
endif()
```

---

# 18. Compiler definitions

C:

```c
#ifdef DEBUG
    printf("Debug\n");
#endif
```

CMake:

```cmake
target_compile_definitions(myapp
    PRIVATE
        DEBUG
)
```

Taxminan:

```bash
-DDEBUG
```

ga teng.

Value bilan:

```cmake
target_compile_definitions(myapp
    PRIVATE
        VERSION_MAJOR=1
)
```

---

# 19. Generator expressions

Configuration’ga qarab setting berish mumkin:

```cmake
target_compile_definitions(myapp
    PRIVATE
        $<$<CONFIG:Debug>:DEBUG>
)
```

Ma’nosi:

```text
Debug build
   ↓
DEBUG defined

Release build
   ↓
DEBUG yo‘q
```

Yana:

```cmake
target_compile_options(myapp
    PRIVATE
        $<$<C_COMPILER_ID:GNU>:-Wall>
)
```

---

# 20. Conditions

```cmake
if(CONDITION)

endif()
```

Misol:

```cmake
if(UNIX)
    message(STATUS "Unix-like OS")
endif()
```

Windows:

```cmake
if(WIN32)
    message(STATUS "Windows")
endif()
```

Apple:

```cmake
if(APPLE)
    message(STATUS "macOS")
endif()
```

---

# 21. if / elseif / else

```cmake
if(CMAKE_BUILD_TYPE STREQUAL "Debug")

    message(STATUS "Debug")

elseif(CMAKE_BUILD_TYPE STREQUAL "Release")

    message(STATUS "Release")

else()

    message(STATUS "Other configuration")

endif()
```

---

# 22. Comparison

String:

```cmake
if(NAME STREQUAL "cppgo")
endif()
```

Number:

```cmake
if(VERSION_NUMBER GREATER 10)
endif()
```

Useful operators:

```text
EQUAL
LESS
LESS_EQUAL
GREATER
GREATER_EQUAL

STREQUAL

VERSION_LESS
VERSION_GREATER
VERSION_EQUAL

MATCHES
```

---

# 23. Boolean logic

```cmake
if(A AND B)
endif()
```

```cmake
if(A OR B)
endif()
```

```cmake
if(NOT A)
endif()
```

Example:

```cmake
if(UNIX AND NOT APPLE)
    message(STATUS "Probably Linux or another Unix")
endif()
```

---

# 24. foreach

```cmake
foreach(item a b c)
    message(STATUS "${item}")
endforeach()
```

Output:

```text
a
b
c
```

---

# 25. foreach RANGE

```cmake
foreach(i RANGE 5)
    message("${i}")
endforeach()
```

```text
0
1
2
3
4
5
```

Start/stop:

```cmake
foreach(i RANGE 2 10)
endforeach()
```

Step:

```cmake
foreach(i RANGE 0 10 2)
endforeach()
```

---

# 26. Lists

Create list:

```cmake
set(SOURCES
    main.c
    game.c
    player.c
)
```

Append:

```cmake
list(APPEND SOURCES
    enemy.c
)
```

Remove:

```cmake
list(REMOVE_ITEM SOURCES game.c)
```

Length:

```cmake
list(LENGTH SOURCES SOURCE_COUNT)
```

Access:

```cmake
list(GET SOURCES 0 FIRST_SOURCE)
```

---

# 27. while

```cmake
set(i 0)

while(i LESS 5)

    message("${i}")

    math(EXPR i "${i} + 1")

endwhile()
```

---

# 28. math()

```cmake
math(EXPR RESULT "5 + 10")
```

Then:

```cmake
message("${RESULT}")
```

---

# 29. option()

User configurable boolean option:

```cmake
option(
    ENABLE_LOGGING
    "Enable application logging"
    ON
)
```

Build:

```bash
cmake -S . -B build \
    -DENABLE_LOGGING=OFF
```

Use:

```cmake
if(ENABLE_LOGGING)

    target_compile_definitions(myapp
        PRIVATE
            ENABLE_LOGGING
    )

endif()
```

---

# 30. Cache variables

```cmake
set(
    MY_VALUE
    "hello"
    CACHE STRING
    "Example configurable value"
)
```

Command line:

```bash
cmake -S . -B build \
    -DMY_VALUE=world
```

---

# 31. Environment variables

Read:

```cmake
$ENV{HOME}
```

Example:

```cmake
message(STATUS "Home: $ENV{HOME}")
```

Set:

```cmake
set(ENV{MY_VAR} "hello")
```

---

# 32. configure_file()

Input:

```text
config.h.in
```

Example:

```c
#define PROJECT_VERSION_MAJOR @PROJECT_VERSION_MAJOR@
#define PROJECT_VERSION_MINOR @PROJECT_VERSION_MINOR@
```

CMake:

```cmake
configure_file(
    config.h.in
    config.h
    @ONLY
)
```

Generated:

```c
#define PROJECT_VERSION_MAJOR 1
#define PROJECT_VERSION_MINOR 0
```

Generated header directory’ni target’ga berish:

```cmake
target_include_directories(myapp
    PRIVATE
        ${PROJECT_BINARY_DIR}
)
```

---

# 33. add_subdirectory()

Large project:

```text
project/
├── CMakeLists.txt
├── app/
│   ├── CMakeLists.txt
│   └── main.c
└── math/
    ├── CMakeLists.txt
    ├── math.c
    └── math.h
```

Root:

```cmake
add_subdirectory(math)
add_subdirectory(app)
```

`math/CMakeLists.txt`:

```cmake
add_library(mymath
    math.c
)

target_include_directories(mymath
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
)
```

`app/CMakeLists.txt`:

```cmake
add_executable(myapp
    main.c
)

target_link_libraries(myapp
    PRIVATE
        mymath
)
```

---

# 34. find_package()

External dependency qidirish:

```cmake
find_package(SDL2 REQUIRED)
```

Keyin:

```cmake
target_link_libraries(myapp
    PRIVATE
        SDL2::SDL2
)
```

Yoki:

```cmake
find_package(OpenSSL REQUIRED)
```

```cmake
target_link_libraries(myapp
    PRIVATE
        OpenSSL::SSL
)
```

Modern CMake’da imkon qadar imported target ishlatish yaxshi:

```text
SDL2::SDL2
OpenSSL::SSL
Threads::Threads
```

---

# 35. Threads

```cmake
find_package(Threads REQUIRED)

target_link_libraries(myapp
    PRIVATE
        Threads::Threads
)
```

---

# 36. pkg-config

Ba’zi Unix libraries uchun:

```cmake
find_package(PkgConfig REQUIRED)
```

Masalan:

```cmake
pkg_check_modules(
    SOME_LIB
    REQUIRED
    IMPORTED_TARGET
    some-library
)
```

Keyin:

```cmake
target_link_libraries(myapp
    PRIVATE
        PkgConfig::SOME_LIB
)
```

---

# 37. SDL example

```cmake
cmake_minimum_required(VERSION 3.23)

project(
    Tetris
    VERSION 1.0.0
    LANGUAGES C
)

find_package(SDL2 REQUIRED)
find_package(SDL2_ttf REQUIRED)

add_executable(tetris
    src/main.c
    src/game.c
)

target_include_directories(tetris
    PRIVATE
        ${PROJECT_SOURCE_DIR}/include
)

target_compile_features(tetris
    PRIVATE
        c_std_17
)

target_compile_options(tetris
    PRIVATE
        -Wall
        -Wextra
)

target_link_libraries(tetris
    PRIVATE
        SDL2::SDL2
        SDL2_ttf::SDL2_ttf
        m
)
```

---

# 38. Debug / Release

Single-config generator:

```bash
cmake -S . -B build \
    -DCMAKE_BUILD_TYPE=Debug
```

Release:

```bash
cmake -S . -B build \
    -DCMAKE_BUILD_TYPE=Release
```

Possible common configurations:

```text
Debug
Release
RelWithDebInfo
MinSizeRel
```

---

# 39. Generator selection

Default generator:

```bash
cmake -S . -B build
```

Ninja:

```bash
cmake -S . -B build -G Ninja
```

Unix Makefiles:

```bash
cmake -S . -B build \
    -G "Unix Makefiles"
```

List generators:

```bash
cmake --help
```

---

# 40. Configure vs build

Configure/generate:

```bash
cmake -S . -B build
```

Build:

```bash
cmake --build build
```

Not necessarily:

```bash
cd build
make
```

`cmake --build` generator-independent.

For example it can internally use:

```text
make
ninja
msbuild
Xcode
```

---

# 41. Parallel build

```bash
cmake --build build --parallel
```

Specific number:

```bash
cmake --build build --parallel 8
```

---

# 42. Build specific target

```bash
cmake --build build \
    --target myapp
```

---

# 43. Clean

```bash
cmake --build build \
    --target clean
```

Yoki full clean:

```bash
rm -rf build
```

Then:

```bash
cmake -S . -B build
```

---

# 44. Testing with CTest

Enable:

```cmake
include(CTest)
```

Then:

```cmake
if(BUILD_TESTING)

    add_executable(test_math
        tests/test_math.c
    )

    target_link_libraries(test_math
        PRIVATE
            mymath
    )

    add_test(
        NAME MathTest
        COMMAND test_math
    )

endif()
```

Build:

```bash
cmake --build build
```

Run tests:

```bash
ctest --test-dir build
```

Verbose:

```bash
ctest --test-dir build \
    --output-on-failure
```

---

# 45. install()

Executable:

```cmake
install(
    TARGETS myapp
    RUNTIME DESTINATION bin
)
```

Library:

```cmake
install(
    TARGETS mymath
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)
```

Headers:

```cmake
install(
    DIRECTORY include/
    DESTINATION include
)
```

Install:

```bash
cmake --install build
```

Custom prefix:

```bash
cmake --install build \
    --prefix /tmp/myproject
```

---

# 46. Alias targets

```cmake
add_library(mymath
    src/math.c
)

add_library(
    MyProject::Math
    ALIAS
    mymath
)
```

Then:

```cmake
target_link_libraries(myapp
    PRIVATE
        MyProject::Math
)
```

Bu external package style’ga o‘xshaydi:

```text
SDL2::SDL2
OpenSSL::SSL
MyProject::Math
```

---

# 47. INTERFACE library

Code yaratmaydigan target:

```cmake
add_library(project_options INTERFACE)
```

Masalan requirements:

```cmake
target_compile_features(project_options
    INTERFACE
        c_std_17
)
```

```cmake
target_compile_options(project_options
    INTERFACE
        -Wall
        -Wextra
)
```

Keyin:

```cmake
target_link_libraries(myapp
    PRIVATE
        project_options
)
```

---

# 48. Object library

```cmake
add_library(common_objects OBJECT
    src/a.c
    src/b.c
)
```

Object files boshqa targets’da ishlatilishi mumkin.

---

# 49. File operations

Read file:

```cmake
file(READ file.txt CONTENT)
```

Write:

```cmake
file(WRITE output.txt "Hello")
```

Append:

```cmake
file(APPEND output.txt "World")
```

Create directory:

```cmake
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/generated")
```

---

# 50. glob

Possible:

```cmake
file(GLOB SOURCES
    src/*.c
)
```

Lekin project source list uchun ko‘pincha explicit yozish yaxshiroq:

```cmake
target_sources(myapp
    PRIVATE
        src/main.c
        src/game.c
        src/player.c
)
```

Chunki project structure aniq ko‘rinadi.

---

# 51. String operations

```cmake
set(NAME "hello")
```

Uppercase:

```cmake
string(TOUPPER "${NAME}" NAME_UPPER)
```

Lowercase:

```cmake
string(TOLOWER "${NAME}" NAME_LOWER)
```

Replace:

```cmake
string(
    REPLACE
    "hello"
    "world"
    RESULT
    "${NAME}"
)
```

---

# 52. Functions

Custom CMake function:

```cmake
function(print_name NAME)

    message(
        STATUS
        "Name = ${NAME}"
    )

endfunction()
```

Call:

```cmake
print_name("cppgo")
```

Functions have their own variable scope.

---

# 53. Macros

```cmake
macro(print_name NAME)

    message(
        STATUS
        "Name = ${NAME}"
    )

endmacro()
```

Call:

```cmake
print_name("cppgo")
```

Important:

```text
function()
→ creates scope

macro()
→ mostly works in caller scope
```

---

# 54. return()

```cmake
function(example)

    if(NOT UNIX)
        return()
    endif()

    message("Unix")

endfunction()
```

---

# 55. Compiler information

C compiler:

```cmake
${CMAKE_C_COMPILER}
```

Compiler ID:

```cmake
${CMAKE_C_COMPILER_ID}
```

Examples:

```text
GNU
Clang
AppleClang
MSVC
```

C++:

```cmake
${CMAKE_CXX_COMPILER}
${CMAKE_CXX_COMPILER_ID}
```

---

# 56. Platform information

```cmake
CMAKE_SYSTEM_NAME
CMAKE_SYSTEM_PROCESSOR
```

Host:

```cmake
CMAKE_HOST_SYSTEM_NAME
CMAKE_HOST_SYSTEM_PROCESSOR
```

Useful especially for cross-compilation.

---

# 57. Checking cross-compilation

```cmake
if(CMAKE_CROSSCOMPILING)

    message(
        STATUS
        "Cross compiling"
    )

endif()
```

---

# 58. Toolchain file

Example:

```text
cmake/
└── aarch64-linux.cmake
```

Content:

```cmake
set(
    CMAKE_SYSTEM_NAME
    Linux
)

set(
    CMAKE_SYSTEM_PROCESSOR
    aarch64
)

set(
    CMAKE_C_COMPILER
    aarch64-linux-gnu-gcc
)

set(
    CMAKE_CXX_COMPILER
    aarch64-linux-gnu-g++
)
```

Configure:

```bash
cmake \
    -S . \
    -B build-arm64 \
    --toolchain cmake/aarch64-linux.cmake
```

Build:

```bash
cmake --build build-arm64
```

---

# 59. Sysroot

Toolchain:

```cmake
set(
    CMAKE_SYSROOT
    /path/to/sysroot
)
```

Mental model:

```text
cross compiler
    +
target headers
    +
target libraries
    +
target libc
    ↓
sysroot
```

---

# 60. Compiler selection

Normally choose before initial configure.

GCC:

```bash
CC=gcc \
CXX=g++ \
cmake -S . -B build
```

Clang:

```bash
CC=clang \
CXX=clang++ \
cmake -S . -B build-clang
```

Or:

```bash
cmake \
    -S . \
    -B build \
    -DCMAKE_C_COMPILER=clang \
    -DCMAKE_CXX_COMPILER=clang++
```

---

# 61. CMake Presets

File:

```text
CMakePresets.json
```

Example:

```json
{
  "version": 6,

  "configurePresets": [
    {
      "name": "debug",

      "generator": "Ninja",

      "binaryDir": "${sourceDir}/build/debug",

      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Debug"
      }
    },

    {
      "name": "release",

      "generator": "Ninja",

      "binaryDir": "${sourceDir}/build/release",

      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Release"
      }
    }
  ]
}
```

Configure:

```bash
cmake --preset debug
```

Build:

```bash
cmake --build \
    build/debug
```

---

# 62. Generator-independent commands

Prefer:

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build
cmake --install build
```

Instead of hard-coding:

```bash
mkdir build
cd build
cmake ..
make
make test
make install
```

Sababi birinchi variant:

```text
Make
Ninja
Visual Studio
Xcode
```

bilan ishlashi mumkin.

---

# 63. Useful command line options

Version:

```bash
cmake --version
```

Help:

```bash
cmake --help
```

Configure:

```bash
cmake -S . -B build
```

Generator:

```bash
cmake -G Ninja \
    -S . \
    -B build
```

Build:

```bash
cmake --build build
```

Parallel:

```bash
cmake --build build \
    --parallel
```

Install:

```bash
cmake --install build
```

Presets:

```bash
cmake --list-presets
```

---

# 64. Inspect variables

```bash
cmake \
    -S . \
    -B build \
    -LAH
```

Useful for viewing cache variables.

---

# 65. Trace CMake execution

```bash
cmake \
    --trace \
    -S . \
    -B build
```

More expanded:

```bash
cmake \
    --trace-expand \
    -S . \
    -B build
```

Useful for debugging CMake itself.

---

# 66. Modern CMake mental model

Old approach often looked like:

```text
global variables
global compiler flags
global include paths
global definitions
```

Modern CMake:

```text
TARGET
│
├── sources
│
├── include directories
│
├── linked libraries
│
├── compile features
│
├── compile options
│
└── compile definitions
```

Example:

```cmake
add_executable(app
    src/main.c
)

target_include_directories(app
    PRIVATE
        include
)

target_compile_features(app
    PRIVATE
        c_std_17
)

target_compile_options(app
    PRIVATE
        -Wall
        -Wextra
)

target_compile_definitions(app
    PRIVATE
        APP_VERSION=1
)

target_link_libraries(app
    PRIVATE
        mymath
)
```

Think:

```text
"What does this target need?"
```

rather than:

```text
"What global compiler flags should I change?"
```

---

# 67. Commands generally avoided for modern target configuration

These commands still exist, but for target-specific configuration prefer their `target_*` alternatives.

Instead of:

```cmake
include_directories(...)
```

prefer:

```cmake
target_include_directories(...)
```

Instead of:

```cmake
link_libraries(...)
```

prefer:

```cmake
target_link_libraries(...)
```

Instead of:

```cmake
add_definitions(...)
```

prefer:

```cmake
target_compile_definitions(...)
```

Instead of manually modifying:

```cmake
CMAKE_C_FLAGS
CMAKE_CXX_FLAGS
```

prefer:

```cmake
target_compile_options(...)
```

Instead of globally requiring a language standard when only one target needs it:

```cmake
set(CMAKE_C_STANDARD 17)
```

prefer:

```cmake
target_compile_features(
    target
    PRIVATE
    c_std_17
)
```

---

# 68. Good minimal C project

```cmake
cmake_minimum_required(VERSION 3.23)

project(
    MyApp
    VERSION 1.0.0
    LANGUAGES C
)

add_executable(myapp
    src/main.c
)

target_compile_features(myapp
    PRIVATE
        c_std_17
)

target_compile_options(myapp
    PRIVATE
        -Wall
        -Wextra
        -Wpedantic
)
```

Build:

```bash
cmake -S . -B build

cmake --build build
```

---

# 69. Good medium-sized project

```cmake
cmake_minimum_required(VERSION 3.23)

project(
    MyProject
    VERSION 1.0.0
    LANGUAGES C
)

option(
    BUILD_TESTING
    "Build tests"
    ON
)

add_subdirectory(src)

if(BUILD_TESTING)

    include(CTest)

    add_subdirectory(tests)

endif()
```

`src/CMakeLists.txt`:

```cmake
add_library(core
    math.c
    game.c
)

add_library(
    MyProject::Core
    ALIAS
    core
)

target_include_directories(core
    PUBLIC
        ${PROJECT_SOURCE_DIR}/include
)

target_compile_features(core
    PUBLIC
        c_std_17
)

add_executable(myapp
    main.c
)

target_link_libraries(myapp
    PRIVATE
        MyProject::Core
)
```

---

# 70. CMake's place in compilation

CMake itself is not the compiler.

Pipeline:

```text
CMakeLists.txt
      ↓
     CMake
      ↓
configure project
      ↓
generate build system
      ↓
Ninja / Make / Visual Studio
      ↓
gcc / clang / MSVC
      ↓
compiler
      ↓
.o / .obj
      ↓
linker
      ↓
executable / library
```

For example:

```bash
cmake -S . -B build -G Ninja
```

means:

```text
CMake
 ↓
generates Ninja build description
```

Then:

```bash
cmake --build build
```

causes approximately:

```text
CMake
 ↓
Ninja
 ↓
gcc
 ↓
assembler
 ↓
linker
 ↓
binary
```

---

# 71. Core commands to master first

Beginner:

```text
cmake_minimum_required()
project()

add_executable()
add_library()

target_sources()

target_include_directories()
target_link_libraries()

target_compile_features()
target_compile_options()
target_compile_definitions()

set()
option()

message()

if()
foreach()

add_subdirectory()
```

Intermediate:

```text
find_package()
configure_file()

install()

include(CTest)
add_test()

add_library(... INTERFACE)
add_library(... ALIAS)

list()
string()
file()

function()
```

Advanced:

```text
generator expressions

CMakePresets.json

toolchain files
CMAKE_SYSROOT

install/export package configuration

FetchContent

custom commands
custom targets

package creation
cross compilation
```

---

# 72. Learning order

Recommended order:

```text
CMakeLists.txt
      ↓
cmake_minimum_required
      ↓
project
      ↓
add_executable
      ↓
configure vs generate vs build
      ↓
targets
      ↓
multiple sources
      ↓
headers
      ↓
target_include_directories
      ↓
add_library
      ↓
STATIC / SHARED
      ↓
target_link_libraries
      ↓
PRIVATE / PUBLIC / INTERFACE
      ↓
compile features
      ↓
compile options
      ↓
compile definitions
      ↓
subdirectories
      ↓
find_package
      ↓
testing
      ↓
install
      ↓
presets
      ↓
toolchain files
      ↓
cross compilation
```

---

# Golden rule

Modern CMake’da imkon qadar:

```text
configure TARGETS,
not the whole directory globally.
```

Ya’ni:

```cmake
target_include_directories()
target_link_libraries()
target_compile_options()
target_compile_features()
target_compile_definitions()
target_sources()
```

atrofida fikrlash kerak.

Asosiy mental model:

```text
TARGET
 ↓
"What does this target require?"
 ↓
sources
headers
libraries
compiler features
compiler options
definitions
```

Bu modern CMake’ning eng muhim konsepsiyalaridan biridir.