# Before You Begin

The CMake tutorial consists of hands-on exercises writing and building a C++ project; solving progressively more complex build requirements such as libraries, code generators, tests, and external dependencies. Before we are ready to even begin the first step of that journey, we need to ensure we have the correct tools at hand and understand how to use them.

> Note The tutorial material assumes the user has a C++20 compiler and toolchain available, and at least a beginner understanding of the C++ language. It is impossible to cover here all the possible ways one might acquire these prerequisites.

This prerequisite step provides recommendations for how to acquire and run CMake itself in order to carry out the rest of the tutorial. If you're already familiar with the basics of how to run CMake, you can feel free to move on to the rest of the tutorial.

# CMake Generators

CMake is a configuration program, sometimes called a "meta" build system. As with other configuration systems, CMake is not ultimately responsible for running the commands which produce the software build. Instead, CMake generates a build system based on project, environment, and user-provided configuration information.

CMake supports multiple build systems as the output of this configuration process. These output backends are called "generators", because they generate the build system. CMake supports many generators, the documentation for which can be found at cmake-generators(7). Information about supported generators for your particular CMake installation can be found via cmake --help under the "Generators" heading.

Using CMake thus requires one of the build programs which consumes this generator output be available. The Unix Makefiles, Ninja, and Visual Studio generators require a compatible make, ninja, and Visual Studio installation respectively.

> Note The default generator on Windows is typically the newest available Visual Studio version on the machine running CMake, everywhere else it is Unix Makefiles.

Which generator is used can be controlled via the CMAKE_GENERATOR environment variable, or the cmake -G option.

# Single and Multi-Configuration Generators¶

In many cases, it is possible to treat the underlying build system as an implementation detail and not differentiate between, for example, ninja and make when using CMake. However, there is one significant property of a given generator which we need to be aware of for even trivial workflows: if the generator supports single configuration builds, or if it supports multi-configuration builds.

Software builds often have several variants which we might be interested in. These variants have names like Debug, Release, RelWithDebInfo, and MinSizeRel, with properties corresponding to the name of the given variant.

A single-configuration build system always builds the software the same way, if it is generated to produce Debug builds it will always produce a Debug build. A multi-configuration build system can produce different outputs depending on the configuration specified at build time.

~~~Note:
The terms build configuration and build type are synonymous. When dealing with single-configuration generators, which only support a single variant, the generated variant is usually called the "build type".
When dealing with multi-configuration generators, the available variants are usually called the "build configurations". Selecting a variant at build time is usually called "selecting a configuration" and referred to by flags and variables as the "config".

However, this convention is not universal. Both technical and colloquial documentation often mix the two terms. Configuration and config are considered the more correct in contexts which generically address both single and multi-configuration generators.
~~~

The commonly used generators are as follows:

---------------------|------------------------------
**Single-Configuration** | 	**Multi-Configuration**
---------------------|------------------------------
Ninja                | Ninja Multi-Config
---------------------|------------------------------
Unix Makefiles       | Visual Studio (all versions)
---------------------|------------------------------
FASTBuild            | Xcode

When using a single-configuration generator, the build type is selected based on the CMAKE_BUILD_TYPE environment variable, or can be specified directly when invoking CMake via cmake -DCMAKE_BUILD_TYPE=<config>.

~~~
Note: For the purpose of the tutorial, it is generally unnecessary to specify a build type when working with single-configuration generators.The platform-specific default behavior will work for all exercises.
~~~

When using a multi-configuration generator, the build configuration is specified at build time using either a build-system specific mechanism, or via the cmake --build --config option.

# Other Usage Basics¶
The rest of the tutorial will cover the remaining usage basics in greater depth, but for the purpose of ensuring we have a working development environment a few more CMake option flags will be enumerated here.

## cmake -S <dir>
Specifies the project root directory, where CMake will find the project to be built. This contains the root CMakeLists.txt file which will be discussed in Step 1 of the tutorial.

When unspecified, defaults to the current working directory.

## cmake -B <dir>
Specifies the build directory, where CMake will output the files for the generated build system, as well as artifacts of the build itself when the build system is run.

When unspecified, defaults to the current working directory.

## cmake --build <dir>
Runs the build system in the specified build directory. This is a generic command for all generators. For multi-configuration generators, the desired configuration can be requested via:

cmake --build <dir> --config <cfg>