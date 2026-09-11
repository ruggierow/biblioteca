#include "biblioteca_core.h"

#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits.h>
#include <mach-o/dyld.h>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>

using namespace std;

// -----------------------------------------------------------------------------
// Resolucao portatil do caminho do arquivo de dados
// -----------------------------------------------------------------------------

static bool arquivoExiste(const string& caminho) {
    ifstream teste(caminho);
    return teste.good();
}

// Retorna o diretorio absoluto onde o executavel reside.
static string diretorioDoExecutavel() {
    char buf[PATH_MAX];
    uint32_t size = sizeof(buf);
    if (_NSGetExecutablePath(buf, &size) != 0) return "";
    char resolved[PATH_MAX];
    if (!realpath(buf, resolved)) return "";
    string path(resolved);
    size_t pos = path.rfind('/');
    return pos != string::npos ? path.substr(0, pos) : "";
}

// Retorna o diretorio de trabalho atual (absoluto).
static string diretorioAtual() {
    char buf[PATH_MAX];
    return getcwd(buf, sizeof(buf)) ? string(buf) : "";
}

// Resolve o caminho do arquivo de dados de forma portatil.
// Ordem de prioridade:
//   1. Variavel de ambiente BIBLIOTECA_FILE (override para desenvolvedores).
//   2. biblioteca.txt ja existente ao lado do executavel.
//   3. biblioteca.txt ja existente no diretorio de trabalho atual.
//   4. Criar arquivo novo ao lado do executavel (instalacoes limpas).
//   5. Ultimo recurso: diretorio de trabalho atual.
static string definirCaminhoArquivo() {
    // 1. Override explicito
    const char* envOverride = getenv("BIBLIOTECA_FILE");
    if (envOverride && envOverride[0] != '\0') return string(envOverride);

    string dirExe = diretorioDoExecutavel();
    string dirCwd = diretorioAtual();

    // 2. Arquivo ja existe ao lado do executavel
    if (!dirExe.empty()) {
        string c = dirExe + "/biblioteca.txt";
        if (arquivoExiste(c)) return c;
    }

    // 3. Arquivo ja existe no diretorio atual
    if (!dirCwd.empty()) {
        string c = dirCwd + "/biblioteca.txt";
        if (arquivoExiste(c)) return c;
    }

    // 4. Novo arquivo ao lado do executavel
    if (!dirExe.empty()) return dirExe + "/biblioteca.txt";

    // 5. Ultimo recurso
    return dirCwd.empty() ? "/tmp/biblioteca.txt" : dirCwd + "/biblioteca.txt";
}

const string NOME_ARQUIVO           = definirCaminhoArquivo();
const string NOME_ARQUIVO_IMPRESSAO = "/tmp/cadastro_livro_biblioteca.txt";

// -----------------------------------------------------------------------------
// Menu
// -----------------------------------------------------------------------------

void exibirMenu() {
    cout << "\n===== Sistema de Gestao de Biblioteca =====\n";
    cout << " 1. Cadastrar livro\n";
    cout << " 2. Listar todos os livros\n";
    cout << " 3. Pesquisar por tema\n";
    cout << " 4. Pesquisar por titulo incompleto\n";
    cout << " 5. Pesquisar por autor\n";
    cout << " 6. Listar livros do grupo de literatura\n";
    cout << " 7. Editar livro por titulo\n";
    cout << " 8. Imprimir cadastro de livro\n";
    cout << " 9. Emprestar livro\n";
    cout << "10. Devolver livro\n";
    cout << "11. Recarregar biblioteca do disco\n";
    cout << " 0. Sair\n";
    cout << "Escolha uma opcao: ";
}

// -----------------------------------------------------------------------------
// Ponto de entrada
// -----------------------------------------------------------------------------

int main() {
    vector<Livro> biblioteca = carregarBiblioteca(NOME_ARQUIVO);
    int opcao = -1;

    cout << "\nArquivo de dados: " << NOME_ARQUIVO << "\n";
    cout << "Base de dados carregada com " << biblioteca.size() << " livro(s).\n";

    while (true) {
        exibirMenu();
        cin >> opcao;

        if (cin.fail()) {
            limparEntrada();
            cout << "\nOpcao invalida. Digite um numero.\n";
            continue;
        }

        switch (opcao) {
            case 1:
                cadastrarLivro(biblioteca);
                salvarBiblioteca(biblioteca, NOME_ARQUIVO);
                break;
            case 2:
                listarLivros(biblioteca);
                break;
            case 3:
                listarPorTema(biblioteca);
                break;
            case 4:
                if (pesquisarPorTituloIncompleto(biblioteca))
                    salvarBiblioteca(biblioteca, NOME_ARQUIVO);
                break;
            case 5:
                pesquisarPorAutor(biblioteca);
                break;
            case 6:
                listarGrupoDeLiteratura(biblioteca);
                break;
            case 7:
                if (editarLivro(biblioteca))
                    salvarBiblioteca(biblioteca, NOME_ARQUIVO);
                break;
            case 8:
                imprimirCadastroLivro(biblioteca, NOME_ARQUIVO_IMPRESSAO);
                break;
            case 9:
                emprestarLivro(biblioteca);
                salvarBiblioteca(biblioteca, NOME_ARQUIVO);
                break;
            case 10:
                devolverLivro(biblioteca);
                salvarBiblioteca(biblioteca, NOME_ARQUIVO);
                break;
            case 11:
                biblioteca = carregarBiblioteca(NOME_ARQUIVO);
                cout << "\nBiblioteca recarregada: " << biblioteca.size() << " livro(s).\n";
                break;
            case 0:
                salvarBiblioteca(biblioteca, NOME_ARQUIVO);
                cout << "\nBiblioteca salva em " << NOME_ARQUIVO << ".\n";
                cout << "Encerrando o programa...\n";
                return 0;
            default:
                cout << "\nOpcao invalida. Tente novamente.\n";
        }
    }
}
