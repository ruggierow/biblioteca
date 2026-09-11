cmake_minimum_required(VERSION 3.14)
project(Biblioteca CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Diretorio das fontes
set(SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src")

# Biblioteca estatica com toda a logica de negocio (sem main).
# Tanto o executavel quanto os testes linkam contra ela.
add_library(biblioteca_core STATIC
    ${SRC_DIR}/biblioteca_core.cpp
)
target_include_directories(biblioteca_core PUBLIC ${SRC_DIR})

# Executavel principal
add_executable(Biblioteca ${SRC_DIR}/main.cpp)
target_link_libraries(Biblioteca PRIVATE biblioteca_core)

# Testes
enable_testing()
add_subdirectory(tests)
