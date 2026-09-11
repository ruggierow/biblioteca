// =============================================================================
//  test_biblioteca.cpp — Testes unitarios e de integracao do sistema Biblioteca
// =============================================================================
//
//  Organizacao dos testes:
//
//    Suite TextoTest          — funcoes de normalizacao e busca de texto.
//    Suite SepararCamposTest  — parser de linhas TSV.
//    Suite LivroTest          — struct Livro e atualizarCamposPesquisa.
//    Suite PersistenciaTest   — round-trip salvar/carregar em arquivo temporario.
//    Suite CompatibilidadeTest— leitura de arquivos legados (5, 6 e 7 colunas).
//    Suite GrupoLiteraturaTest— campo grupoLiteratura no ciclo completo.
// =============================================================================

#include <gtest/gtest.h>
#include "biblioteca_core.h"

#include <fstream>
#include <string>
#include <vector>

using namespace std;

// -----------------------------------------------------------------------------
// Helpers de teste
// -----------------------------------------------------------------------------

// Escreve conteudo em um arquivo temporario e retorna o caminho.
static string escreverArquivoTemp(const string& nome, const string& conteudo) {
    string caminho = "/tmp/teste_biblioteca_" + nome + ".txt";
    ofstream arq(caminho);
    arq << conteudo;
    return caminho;
}

// Cria um Livro com campos minimos preenchidos para nao depender do stdin.
static Livro novoLivro(const string& titulo,
                        const string& autor,
                        const string& tema,
                        int ano,
                        bool emprestado = false,
                        bool grupo = false) {
    Livro l;
    l.titulo          = titulo;
    l.autor           = autor;
    l.tema            = tema;
    l.ano             = ano;
    l.emprestado      = emprestado;
    l.grupoLiteratura = grupo;
    atualizarCamposPesquisa(l);
    return l;
}

// =============================================================================
// Suite TextoTest — normalizacao e busca
// =============================================================================

TEST(TextoTest, MinusculasBasico) {
    EXPECT_EQ(textoEmMinusculas("Machado de Assis"), "machado de assis");
}

TEST(TextoTest, MinusculasJaMinusculas) {
    EXPECT_EQ(textoEmMinusculas("romance"), "romance");
}

TEST(TextoTest, MinusculasVazio) {
    EXPECT_EQ(textoEmMinusculas(""), "");
}

TEST(TextoTest, MinusculasMaiusculas) {
    EXPECT_EQ(textoEmMinusculas("DOM CASMURRO"), "dom casmurro");
}

TEST(TextoTest, BuscaEncontraSubstring) {
    EXPECT_TRUE(contemTextoNormalizado("dom casmurro", "casmurro"));
}

TEST(TextoTest, BuscaCaseInsensitive) {
    EXPECT_TRUE(contemTextoNormalizado("dom casmurro", "DOM"));
    EXPECT_TRUE(contemTextoNormalizado("dom casmurro", "Casmurro"));
}

TEST(TextoTest, BuscaNaoEncontra) {
    EXPECT_FALSE(contemTextoNormalizado("dom casmurro", "quixote"));
}

TEST(TextoTest, BuscaTextoVazio) {
    // Trecho vazio deve ser encontrado em qualquer texto.
    EXPECT_TRUE(contemTextoNormalizado("qualquer texto", ""));
}

TEST(TextoTest, BuscaEmTextoVazio) {
    EXPECT_FALSE(contemTextoNormalizado("", "algo"));
}

// =============================================================================
// Suite SepararCamposTest — parser TSV
// =============================================================================

TEST(SepararCamposTest, TresCampos) {
    auto campos = separarCampos("a\tb\tc");
    ASSERT_EQ(campos.size(), 3u);
    EXPECT_EQ(campos[0], "a");
    EXPECT_EQ(campos[1], "b");
    EXPECT_EQ(campos[2], "c");
}

TEST(SepararCamposTest, CampoVazioNoMeio) {
    auto campos = separarCampos("titulo\t\ttema");
    ASSERT_EQ(campos.size(), 3u);
    EXPECT_EQ(campos[1], "");
}

TEST(SepararCamposTest, UmCampo) {
    auto campos = separarCampos("solitario");
    ASSERT_EQ(campos.size(), 1u);
    EXPECT_EQ(campos[0], "solitario");
}

TEST(SepararCamposTest, LinhaVazia) {
    // getline sobre string vazia nao produz nenhum campo.
    auto campos = separarCampos("");
    EXPECT_TRUE(campos.empty());
}

// =============================================================================
// Suite LivroTest — struct e cache de pesquisa
// =============================================================================

TEST(LivroTest, CamposPesquisaEmMinusculas) {
    Livro l = novoLivro("Dom Casmurro", "Machado de Assis", "Romance", 1899);
    EXPECT_EQ(l.tituloPesquisa, "dom casmurro");
    EXPECT_EQ(l.autorPesquisa,  "machado de assis");
    EXPECT_EQ(l.temaPesquisa,   "romance");
}

TEST(LivroTest, CamposAtualizadosAposModificacao) {
    Livro l = novoLivro("Titulo", "Autor", "Tema", 2000);
    l.titulo = "Novo Titulo";
    atualizarCamposPesquisa(l);
    EXPECT_EQ(l.tituloPesquisa, "novo titulo");
}

TEST(LivroTest, GrupoLiteraturaFalsoPorPadrao) {
    Livro l = novoLivro("X", "Y", "Z", 2000);
    EXPECT_FALSE(l.grupoLiteratura);
}

// =============================================================================
// Suite PersistenciaTest — round-trip salvar -> carregar
// =============================================================================

TEST(PersistenciaTest, RoundTripUmLivro) {
    const string caminho = "/tmp/teste_roundtrip.txt";
    vector<Livro> original = {
        novoLivro("Dom Casmurro", "Machado de Assis", "Romance", 1899)
    };

    salvarBiblioteca(original, caminho);
    vector<Livro> carregado = carregarBiblioteca(caminho);

    ASSERT_EQ(carregado.size(), 1u);
    EXPECT_EQ(carregado[0].titulo, "Dom Casmurro");
    EXPECT_EQ(carregado[0].autor,  "Machado de Assis");
    EXPECT_EQ(carregado[0].tema,   "Romance");
    EXPECT_EQ(carregado[0].ano,    1899);
    EXPECT_FALSE(carregado[0].emprestado);
    EXPECT_FALSE(carregado[0].grupoLiteratura);
}

TEST(PersistenciaTest, RoundTripVariosLivros) {
    const string caminho = "/tmp/teste_varios.txt";
    vector<Livro> original = {
        novoLivro("Livro A", "Autor 1", "Tema X", 2001),
        novoLivro("Livro B", "Autor 2", "Tema Y", 2002, true),
        novoLivro("Livro C", "Autor 3", "Tema Z", 2003, false, true),
    };

    salvarBiblioteca(original, caminho);
    vector<Livro> carregado = carregarBiblioteca(caminho);

    ASSERT_EQ(carregado.size(), 3u);
    EXPECT_EQ(carregado[1].titulo, "Livro B");
    EXPECT_TRUE(carregado[1].emprestado);
    EXPECT_TRUE(carregado[2].grupoLiteratura);
}

TEST(PersistenciaTest, StatusEmprestadoPreservado) {
    const string caminho = "/tmp/teste_emprestado.txt";
    vector<Livro> original = { novoLivro("Livro X", "Autor", "Tema", 2000, true) };

    salvarBiblioteca(original, caminho);
    auto carregado = carregarBiblioteca(caminho);

    ASSERT_EQ(carregado.size(), 1u);
    EXPECT_TRUE(carregado[0].emprestado);
}

TEST(PersistenciaTest, ArquivoInexistenteRetornaVazio) {
    auto resultado = carregarBiblioteca("/tmp/arquivo_que_nao_existe_xyz.txt");
    EXPECT_TRUE(resultado.empty());
}

TEST(PersistenciaTest, CachesPesquisaReconstruidosAoCarregar) {
    const string caminho = "/tmp/teste_cache.txt";
    vector<Livro> original = { novoLivro("Quincas Borba", "Machado", "Realismo", 1891) };

    salvarBiblioteca(original, caminho);
    auto carregado = carregarBiblioteca(caminho);

    ASSERT_EQ(carregado.size(), 1u);
    EXPECT_EQ(carregado[0].tituloPesquisa, "quincas borba");
    EXPECT_EQ(carregado[0].autorPesquisa,  "machado");
}

// =============================================================================
// Suite CompatibilidadeTest — leitura de arquivos com formatos antigos
// =============================================================================

TEST(CompatibilidadeTest, CincoColunasLegado) {
    // Formato mais antigo: titulo, autor, tema, ano, emprestado
    string conteudo = "Dom Casmurro\tMachado de Assis\tRomance\t1899\t0\n";
    auto caminho = escreverArquivoTemp("legado5", conteudo);
    auto livros = carregarBiblioteca(caminho);

    ASSERT_EQ(livros.size(), 1u);
    EXPECT_EQ(livros[0].titulo, "Dom Casmurro");
    EXPECT_EQ(livros[0].comentarios, "");
    EXPECT_EQ(livros[0].local, "");
    EXPECT_FALSE(livros[0].grupoLiteratura);
}

TEST(CompatibilidadeTest, SeisColunasComComentarios) {
    string conteudo = "Livro\tAutor\tTema\t2000\t0\tOtimo livro\n";
    auto caminho = escreverArquivoTemp("legado6", conteudo);
    auto livros = carregarBiblioteca(caminho);

    ASSERT_EQ(livros.size(), 1u);
    EXPECT_EQ(livros[0].comentarios, "Otimo livro");
    EXPECT_EQ(livros[0].local, "");
}

TEST(CompatibilidadeTest, SeteColunasComLocal) {
    string conteudo = "Livro\tAutor\tTema\t2000\t0\tComentario\tEstante 3\n";
    auto caminho = escreverArquivoTemp("legado7", conteudo);
    auto livros = carregarBiblioteca(caminho);

    ASSERT_EQ(livros.size(), 1u);
    EXPECT_EQ(livros[0].local, "Estante 3");
    EXPECT_FALSE(livros[0].grupoLiteratura);
}

TEST(CompatibilidadeTest, LinhasInvalidasIgnoradas) {
    // Linha com 3 campos (invalida) deve ser ignorada.
    string conteudo =
        "Dom Casmurro\tMachado\tRomance\t1899\t0\n"
        "linha invalida com poucos campos\n"
        "Livro Dois\tAutor Dois\tTema\t2000\t0\n";
    auto caminho = escreverArquivoTemp("invalidas", conteudo);
    auto livros = carregarBiblioteca(caminho);

    ASSERT_EQ(livros.size(), 2u);
    EXPECT_EQ(livros[0].titulo, "Dom Casmurro");
    EXPECT_EQ(livros[1].titulo, "Livro Dois");
}

// =============================================================================
// Suite GrupoLiteraturaTest — campo grupoLiteratura
// =============================================================================

TEST(GrupoLiteraturaTest, SalvarECarregarMarcado) {
    const string caminho = "/tmp/teste_grupo.txt";
    vector<Livro> original = { novoLivro("X", "Y", "Z", 2000, false, true) };

    salvarBiblioteca(original, caminho);
    auto carregado = carregarBiblioteca(caminho);

    ASSERT_EQ(carregado.size(), 1u);
    EXPECT_TRUE(carregado[0].grupoLiteratura);
}

TEST(GrupoLiteraturaTest, SalvarECarregarNaoMarcado) {
    const string caminho = "/tmp/teste_grupo_nao.txt";
    vector<Livro> original = { novoLivro("X", "Y", "Z", 2000, false, false) };

    salvarBiblioteca(original, caminho);
    auto carregado = carregarBiblioteca(caminho);

    ASSERT_EQ(carregado.size(), 1u);
    EXPECT_FALSE(carregado[0].grupoLiteratura);
}

TEST(GrupoLiteraturaTest, FiltrarPorGrupo) {
    // Simula a logica de listarGrupoDeLiteratura: filtragem manual.
    vector<Livro> biblioteca = {
        novoLivro("Livro do Grupo",  "Autor A", "Tema", 2000, false, true),
        novoLivro("Livro Normal",    "Autor B", "Tema", 2001, false, false),
        novoLivro("Outro do Grupo",  "Autor C", "Tema", 2002, false, true),
    };

    vector<Livro> doGrupo;
    for (const auto& l : biblioteca) {
        if (l.grupoLiteratura) doGrupo.push_back(l);
    }

    ASSERT_EQ(doGrupo.size(), 2u);
    EXPECT_EQ(doGrupo[0].titulo, "Livro do Grupo");
    EXPECT_EQ(doGrupo[1].titulo, "Outro do Grupo");
}
