include(FetchContent)

# Baixa o Google Test na primeira vez que o projeto e configurado.
# As compilacoes seguintes usam o cache local.
FetchContent_Declare(
    googletest
    URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

add_executable(testes_biblioteca test_biblioteca.cpp)

target_link_libraries(testes_biblioteca
    PRIVATE
        biblioteca_core
        GTest::gtest_main
)

# Registra cada TEST() como um caso de teste CTest separado.
include(GoogleTest)
gtest_discover_tests(testes_biblioteca)
