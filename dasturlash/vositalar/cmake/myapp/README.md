# Run
## Linux/macOS:
### build:
```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release

cmake --build build
```
### run:
```sh
./build/myapp
```
### Tests:
```sh
ctest --test-dir build --output-on-failure
```

## Windows Visual Studio build:
```shell
cmake -S . -B build

cmake --build build --config Release
```

result:
```txt
build/Release/myapp.exe
```