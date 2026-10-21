# Set the minimum required version of CMake to be 3.23
cmake_minimum_required(VERSION 3.23)

# Create a project named Tutorial
project(Tutorial)

# Add an executable target called Tutorial to the project
# add_executable(Tutorial)

# # Add the Tutorial/Tutorial.cxx source file to the Tutorial target
# target_sources(
# 	Tutorial
# 	PRIVATE
# 		Tutorial/Tutorial.cxx
# )

# target_link_libraries(
# 	Tutorial
#   	PRIVATE
#     	MathFunctions
# )

# Add the Tutorial subdirectory to the project
add_subdirectory(Tutorial)

# Add a library target called MathFunctions to the project
# add_library(MathFunctions)

# # Add the source and header file located in Step1/MathFunctions to the
# # #        MathFunctions target, note that the intended way to include the
# # #        MathFunctions header is:
# # #          #include <MathFunctions.h>
# target_sources (
# 	MathFunctions
# 	PRIVATE
# 		MathFunctions/MathFunctions.cxx

# 	PUBLIC
# 		FILE_SET HEADERS
# 		BASE_DIRS
# 			MathFunctions
# 		FILES 
# 			MathFunctions/MathFunctions.h
# )

# Add the MathFunctions subdirectory to the project
add_subdirectory(MathFunctions)