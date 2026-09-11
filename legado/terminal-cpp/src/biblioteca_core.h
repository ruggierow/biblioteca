#pragma once
// =============================================================================
//  biblioteca_core.h — Declaracoes publicas do nucleo do sistema de biblioteca.
//
//  Separar a logica de negocio do ponto de entrada (main) permite:
//    * Compilar as funcoes como biblioteca estatica (biblioteca_core).
//    * Incluir esse cabecalho nos testes sem arrastar a funcao main().
//    * Reutilizar o codigo em outros contextos futuramente.
//
//  As funcoes de persistencia (carregarBiblioteca / salvarBiblioteca) recebem
//  o caminho do arquivo como parametro em vez de usar uma constante global.
//  Isso permite que os testes usem arquivos temporarios sem tocar no arquivo
//  real de dados do usuario.
// =============================================================================

#include <string>
#include <vector>

// -----------------------------------------------------------------------------
// Struct principal
// -----------------------------------------------------------------------------
struct Livro {
    std::string titulo;
    std::string autor;
    std::string tema;
    int         ano          = 0;
    bool        emprestado   = false;
    std::string comentarios;
    std::string local;
    bool        grupoLiteratura = false;
    std::string tituloPesquisa;   // cache em minusculas
    std::string autorPesquisa;
    std::string temaPesquisa;
};

// -----------------------------------------------------------------------------
// Utilitarios de texto e entrada
// -----------------------------------------------------------------------------
void        limparEntrada();
std::string textoEmMinusculas(std::string texto);
void        atualizarCamposPesquisa(Livro& livro);
bool        contemTextoNormalizado(const std::string& textoNormalizado,
                                   const std::string& trecho);
std::vector<std::string> separarCampos(const std::string& linha);

// -----------------------------------------------------------------------------
// Persistencia em disco
// -----------------------------------------------------------------------------
std::vector<Livro> carregarBiblioteca(const std::string& caminhoArquivo);
void               salvarBiblioteca(const std::vector<Livro>& biblioteca,
                                    const std::string& caminhoArquivo);

// -----------------------------------------------------------------------------
// Operacoes do catalogo
// -----------------------------------------------------------------------------
void exibirLivro(const Livro& livro, std::size_t indice);
void listarLivros(const std::vector<Livro>& biblioteca);
void listarPorTema(const std::vector<Livro>& biblioteca);
void pesquisarPorAutor(const std::vector<Livro>& biblioteca);
void listarGrupoDeLiteratura(const std::vector<Livro>& biblioteca);

void cadastrarLivro(std::vector<Livro>& biblioteca);
void editarDadosLivro(Livro& livro);
bool pesquisarPorTituloIncompleto(std::vector<Livro>& biblioteca);
bool editarLivro(std::vector<Livro>& biblioteca);

void imprimirCadastroLivro(const std::vector<Livro>& biblioteca,
                           const std::string& arquivoImpressao);
void emprestarLivro(std::vector<Livro>& biblioteca);
void devolverLivro(std::vector<Livro>& biblioteca);
