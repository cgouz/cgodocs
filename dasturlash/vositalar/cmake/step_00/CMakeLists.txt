cmake_minimum_required(VERSION 3.23)

project(step00)

add_executable(hello)

target_sources(
	hello
	PRIVATE
		helloWorld.cxx
)