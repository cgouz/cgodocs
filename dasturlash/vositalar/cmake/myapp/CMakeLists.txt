cmake_minimum_required(VERSION 3.23)

project(
    MyApp
    VERSION 1.0.0
    LANGUAGES C
)

option(
    MYAPP_BUILD_TESTS
    "Build tests"
    ON
)

# ------------------------------------------------------------------------------
# Core library
# ------------------------------------------------------------------------------

add_library(myapp_core
    src/math_utils.c
    src/platform.c
)

add_library(
    MyApp::Core
    ALIAS
    myapp_core
)

target_include_directories(myapp_core
    PUBLIC
        ${PROJECT_SOURCE_DIR}/include

    PRIVATE
        ${PROJECT_SOURCE_DIR}/src
)

target_compile_features(myapp_core
    PUBLIC
        c_std_17
)

# ------------------------------------------------------------------------------
# Platform-specific configuration
# ------------------------------------------------------------------------------

if(WIN32)

    target_compile_definitions(myapp_core
        PRIVATE
            MYAPP_WINDOWS
    )

elseif(APPLE)

    target_compile_definitions(myapp_core
        PRIVATE
            MYAPP_MACOS
    )

elseif(UNIX)

    target_compile_definitions(myapp_core
        PRIVATE
            MYAPP_LINUX
    )

endif()

# ------------------------------------------------------------------------------
# Compiler warnings
# ------------------------------------------------------------------------------

if(MSVC)

    target_compile_options(myapp_core
        PRIVATE
            /W4
    )

elseif(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")

    target_compile_options(myapp_core
        PRIVATE
            -Wall
            -Wextra
            -Wpedantic
    )

endif()

# ------------------------------------------------------------------------------
# Application
# ------------------------------------------------------------------------------

add_executable(myapp
    src/main.c
)

target_link_libraries(myapp
    PRIVATE
        MyApp::Core
)

# ------------------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------------------

if(MYAPP_BUILD_TESTS)

    include(CTest)

    add_executable(test_math
        tests/test_math.c
    )

    target_link_libraries(test_math
        PRIVATE
            MyApp::Core
    )

    add_test(
        NAME MathTest
        COMMAND test_math
    )

endif()

# ------------------------------------------------------------------------------
# Install
# ------------------------------------------------------------------------------

install(
    TARGETS myapp
    RUNTIME DESTINATION bin
)