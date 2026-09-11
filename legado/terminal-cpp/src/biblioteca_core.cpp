#include "biblioteca_core.h"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <vector>

using namespace std;

// -----------------------------------------------------------------------------
// Utilitarios de entrada e normalizacao de texto
// -----------------------------------------------------------------------------

void limparEntrada() {
    cin.clear();
    cin.ignore(numeric_limits<streamsize>::max(), '\n');
}

string textoEmMinusculas(string texto) {
    transform(texto.begin(), texto.end(), texto.begin(), [](unsigned char c) {
        return static_cast<char>(tolower(c));
    });
    return texto;
}

void atualizarCamposPesquisa(Livro& livro) {
    livro.tituloPesquisa = textoEmMinusculas(livro.titulo);
    livro.autorPesquisa  = textoEmMinusculas(livro.autor);
    livro.temaPesquisa   = textoEmMinusculas(livro.tema);
}

bool contemTextoNormalizado(const string& textoNormalizado, const string& trecho) {
    return textoNormalizado.find(textoEmMinusculas(trecho)) != string::npos;
}

vector<string> separarCampos(const string& linha) {
    vector<string> campos;
    string campo;
    stringstream fluxo(linha);
    while (getline(fluxo, campo, '\t')) {
        campos.push_back(campo);
    }
    return campos;
}

// -----------------------------------------------------------------------------
// Persistencia em disco (formato TSV)
// -----------------------------------------------------------------------------

vector<Livro> carregarBiblioteca(const string& caminhoArquivo) {
    vector<Livro> biblioteca;
    ifstream arquivo(caminhoArquivo);

    if (!arquivo.is_open()) return biblioteca;

    string linha;
    while (getline(arquivo, linha)) {
        vector<string> campos = separarCampos(linha);

        // Aceita 5 (legado), 6, 7 ou 8 campos.
        if (campos.size() < 5 || campos.size() > 8) continue;

        Livro livro;
        livro.titulo          = campos[0];
        livro.autor           = campos[1];
        livro.tema            = campos[2];
        livro.ano             = stoi(campos[3]);
        livro.emprestado      = campos[4] == "1";
        livro.comentarios     = campos.size() >= 6 ? campos[5] : "";
        livro.local           = campos.size() >= 7 ? campos[6] : "";
        livro.grupoLiteratura = campos.size() >= 8 ? campos[7] == "1" : false;
        atualizarCamposPesquisa(livro);

        biblioteca.push_back(livro);
    }

    return biblioteca;
}

void salvarBiblioteca(const vector<Livro>& biblioteca, const string& caminhoArquivo) {
    ofstream arquivo(caminhoArquivo);

    if (!arquivo.is_open()) {
        cout << "\nNao foi possivel salvar a biblioteca no arquivo.\n";
        return;
    }

    for (const Livro& livro : biblioteca) {
        arquivo << livro.titulo        << '\t'
                << livro.autor         << '\t'
                << livro.tema          << '\t'
                << livro.ano           << '\t'
                << (livro.emprestado      ? "1" : "0") << '\t'
                << livro.comentarios   << '\t'
                << livro.local         << '\t'
                << (livro.grupoLiteratura ? "1" : "0") << '\n';
    }
}

// -----------------------------------------------------------------------------
// Exibicao
// -----------------------------------------------------------------------------

void exibirLivro(const Livro& livro, size_t indice) {
    cout << "\nLivro " << indice + 1 << endl;
    cout << "Titulo:  " << livro.titulo << endl;
    cout << "Autor:   " << livro.autor  << endl;
    cout << "Tema:    " << livro.tema   << endl;
    cout << "Ano:     " << livro.ano    << endl;
    cout << "Status:  " << (livro.emprestado ? "Emprestado" : "Disponivel") << endl;
    if (!livro.local.empty()) {
        cout << "Local:   " << livro.local << endl;
    }
    cout << "Grupo de Literatura: " << (livro.grupoLiteratura ? "[X] Sim" : "[ ] Nao") << endl;
}

void listarLivros(const vector<Livro>& biblioteca) {
    if (biblioteca.empty()) {
        cout << "\nNenhum livro cadastrado.\n";
        return;
    }
    cout << "\n--- Lista de Livros ---\n";
    for (size_t i = 0; i < biblioteca.size(); i++) {
        exibirLivro(biblioteca[i], i);
    }
}

void listarPorTema(const vector<Livro>& biblioteca) {
    if (biblioteca.empty()) { cout << "\nNenhum livro cadastrado.\n"; return; }

    string tema;
    bool encontrou = false;

    cout << "\nDigite o tema desejado: ";
    limparEntrada();
    getline(cin, tema);

    cout << "\n--- Livros do tema pesquisado ---\n";
    for (size_t i = 0; i < biblioteca.size(); i++) {
        if (contemTextoNormalizado(biblioteca[i].temaPesquisa, tema)) {
            exibirLivro(biblioteca[i], i);
            encontrou = true;
        }
    }
    if (!encontrou) cout << "\nNenhum livro encontrado para esse tema.\n";
}

void pesquisarPorAutor(const vector<Livro>& biblioteca) {
    if (biblioteca.empty()) { cout << "\nNenhum livro cadastrado.\n"; return; }

    string trechoAutor;
    bool encontrou = false;

    cout << "\nDigite o nome ou parte do nome do autor: ";
    limparEntrada();
    getline(cin, trechoAutor);

    cout << "\n--- Resultado da pesquisa por autor ---\n";
    for (size_t i = 0; i < biblioteca.size(); i++) {
        if (contemTextoNormalizado(biblioteca[i].autorPesquisa, trechoAutor)) {
            exibirLivro(biblioteca[i], i);
            encontrou = true;
        }
    }
    if (!encontrou) cout << "\nNenhum livro encontrado para esse autor.\n";
}

void listarGrupoDeLiteratura(const vector<Livro>& biblioteca) {
    if (biblioteca.empty()) { cout << "\nNenhum livro cadastrado.\n"; return; }

    bool encontrou = false;
    cout << "\n--- Livros discutidos no grupo de literatura ---\n";
    for (size_t i = 0; i < biblioteca.size(); i++) {
        if (biblioteca[i].grupoLiteratura) {
            exibirLivro(biblioteca[i], i);
            encontrou = true;
        }
    }
    if (!encontrou) cout << "\nNenhum livro foi discutido no grupo de literatura ainda.\n";
}

// -----------------------------------------------------------------------------
// Cadastro e edicao
// -----------------------------------------------------------------------------

void cadastrarLivro(vector<Livro>& biblioteca) {
    Livro livro;

    cout << "\nTitulo do livro: ";
    limparEntrada();
    getline(cin, livro.titulo);

    cout << "Autor do livro: ";
    getline(cin, livro.autor);

    cout << "Tema do livro: ";
    getline(cin, livro.tema);

    cout << "Ano de publicacao: ";
    cin >> livro.ano;
    limparEntrada();

    string resposta;
    cout << "Discutido no grupo de literatura? [X] sim  [ ] nao  (s/n): ";
    getline(cin, resposta);
    livro.grupoLiteratura = (!resposta.empty() &&
                             tolower(static_cast<unsigned char>(resposta[0])) == 's');

    livro.emprestado = false;
    atualizarCamposPesquisa(livro);
    biblioteca.push_back(livro);

    cout << "\nLivro cadastrado com sucesso!\n";
}

void editarDadosLivro(Livro& livro) {
    string entrada;
    cout << "\nEditando o livro selecionado. Deixe em branco para manter o valor atual.\n";

    cout << "Titulo atual: " << livro.titulo << endl;
    cout << "Novo titulo: ";
    getline(cin, entrada);
    if (!entrada.empty()) livro.titulo = entrada;

    cout << "Autor atual: " << livro.autor << endl;
    cout << "Novo autor: ";
    getline(cin, entrada);
    if (!entrada.empty()) livro.autor = entrada;

    cout << "Tema atual: " << livro.tema << endl;
    cout << "Novo tema: ";
    getline(cin, entrada);
    if (!entrada.empty()) livro.tema = entrada;

    cout << "Ano atual: " << livro.ano << endl;
    cout << "Novo ano: ";
    getline(cin, entrada);
    if (!entrada.empty()) {
        stringstream fluxoAno(entrada);
        int novoAno;
        if (fluxoAno >> novoAno) livro.ano = novoAno;
        else cout << "\nAno invalido. O ano atual foi mantido.\n";
    }

    cout << "Status atual: " << (livro.emprestado ? "Emprestado" : "Disponivel") << endl;
    cout << "O livro esta emprestado? (s/n, deixe em branco para manter): ";
    getline(cin, entrada);
    if (!entrada.empty()) {
        char r = static_cast<char>(tolower(static_cast<unsigned char>(entrada[0])));
        if (r == 's') livro.emprestado = true;
        else if (r == 'n') livro.emprestado = false;
        else cout << "\nStatus invalido. O status atual foi mantido.\n";
    }

    cout << "Grupo de Literatura atual: " << (livro.grupoLiteratura ? "[X] Sim" : "[ ] Nao") << endl;
    cout << "Discutido no grupo de literatura? (s/n, deixe em branco para manter): ";
    getline(cin, entrada);
    if (!entrada.empty()) {
        char r = static_cast<char>(tolower(static_cast<unsigned char>(entrada[0])));
        if (r == 's') livro.grupoLiteratura = true;
        else if (r == 'n') livro.grupoLiteratura = false;
        else cout << "\nResposta invalida. O valor atual foi mantido.\n";
    }

    atualizarCamposPesquisa(livro);
    cout << "\nLivro atualizado com sucesso!\n";
}

bool pesquisarPorTituloIncompleto(vector<Livro>& biblioteca) {
    if (biblioteca.empty()) { cout << "\nNenhum livro cadastrado.\n"; return false; }

    string trechoTitulo;
    vector<size_t> indicesEncontrados;

    cout << "\nDigite parte do titulo do livro: ";
    limparEntrada();
    getline(cin, trechoTitulo);

    cout << "\n--- Resultado da pesquisa por titulo ---\n";
    for (size_t i = 0; i < biblioteca.size(); i++) {
        if (contemTextoNormalizado(biblioteca[i].tituloPesquisa, trechoTitulo)) {
            exibirLivro(biblioteca[i], i);
            indicesEncontrados.push_back(i);
        }
    }

    if (indicesEncontrados.empty()) {
        cout << "\nNenhum livro encontrado com esse trecho no titulo.\n";
        return false;
    }

    string resposta;
    cout << "\nDeseja editar algum livro encontrado? (s/n): ";
    getline(cin, resposta);
    if (resposta.empty() || tolower(static_cast<unsigned char>(resposta[0])) != 's') return false;

    size_t numeroLivro;
    cout << "Digite o numero do livro que deseja editar: ";
    cin >> numeroLivro;
    if (cin.fail()) { limparEntrada(); cout << "\nNumero invalido.\n"; return false; }
    limparEntrada();

    if (numeroLivro < 1 || numeroLivro > biblioteca.size()) {
        cout << "\nNumero de livro invalido.\n";
        return false;
    }

    size_t indiceLivro = numeroLivro - 1;
    bool estaNoResultado = find(indicesEncontrados.begin(),
                                indicesEncontrados.end(),
                                indiceLivro) != indicesEncontrados.end();
    if (!estaNoResultado) { cout << "\nEsse livro nao faz parte do resultado.\n"; return false; }

    editarDadosLivro(biblioteca[indiceLivro]);
    return true;
}

bool editarLivro(vector<Livro>& biblioteca) {
    return pesquisarPorTituloIncompleto(biblioteca);
}

// -----------------------------------------------------------------------------
// Impressao individual
// -----------------------------------------------------------------------------

void imprimirCadastroLivro(const vector<Livro>& biblioteca, const string& arquivoImpressao) {
    if (biblioteca.empty()) { cout << "\nNenhum livro cadastrado.\n"; return; }

    string trechoTitulo;
    vector<size_t> indicesEncontrados;

    cout << "\nDigite o titulo ou parte do titulo do livro para impressao: ";
    limparEntrada();
    getline(cin, trechoTitulo);

    cout << "\n--- Livros encontrados para impressao ---\n";
    for (size_t i = 0; i < biblioteca.size(); i++) {
        if (contemTextoNormalizado(biblioteca[i].tituloPesquisa, trechoTitulo)) {
            exibirLivro(biblioteca[i], i);
            indicesEncontrados.push_back(i);
        }
    }

    if (indicesEncontrados.empty()) { cout << "\nNenhum livro encontrado.\n"; return; }

    size_t numeroLivro;
    cout << "\nDigite o numero do livro que deseja imprimir: ";
    cin >> numeroLivro;
    if (cin.fail()) { limparEntrada(); cout << "\nNumero invalido.\n"; return; }
    limparEntrada();

    if (numeroLivro < 1 || numeroLivro > biblioteca.size()) {
        cout << "\nNumero de livro invalido.\n";
        return;
    }

    size_t indiceLivro = numeroLivro - 1;
    bool estaNoResultado = find(indicesEncontrados.begin(),
                                indicesEncontrados.end(),
                                indiceLivro) != indicesEncontrados.end();
    if (!estaNoResultado) { cout << "\nEsse livro nao faz parte do resultado.\n"; return; }

    const Livro& livro = biblioteca[indiceLivro];
    ofstream arq(arquivoImpressao);
    if (!arq.is_open()) { cout << "\nNao foi possivel preparar o arquivo para impressao.\n"; return; }

    arq << "Cadastro do Livro\n=================\n\n";
    arq << "Titulo: "  << livro.titulo << '\n';
    arq << "Autor: "   << livro.autor  << '\n';
    arq << "Tema: "    << livro.tema   << '\n';
    arq << "Ano: "     << livro.ano    << '\n';
    arq << "Status: "  << (livro.emprestado ? "Emprestado" : "Disponivel") << '\n';
    if (!livro.local.empty()) arq << "Local: " << livro.local << '\n';
    arq << "Grupo de Literatura: " << (livro.grupoLiteratura ? "[X] Sim" : "[ ] Nao") << '\n';
    arq.close();

    string comando = "lpr " + arquivoImpressao;
    int resultado = system(comando.c_str());
    if (resultado == 0) cout << "\nCadastro enviado para a impressora padrao.\n";
    else cout << "\nNao foi possivel enviar para a impressora.\n";
}

// -----------------------------------------------------------------------------
// Emprestimo e devolucao
// -----------------------------------------------------------------------------

void emprestarLivro(vector<Livro>& biblioteca) {
    if (biblioteca.empty()) { cout << "\nNenhum livro cadastrado.\n"; return; }

    string trechoTitulo;
    bool encontrou = false;

    cout << "\nDigite o titulo ou parte do titulo para emprestimo: ";
    limparEntrada();
    getline(cin, trechoTitulo);

    for (Livro& livro : biblioteca) {
        if (contemTextoNormalizado(livro.tituloPesquisa, trechoTitulo)) {
            encontrou = true;
            if (livro.emprestado) cout << "\nO livro \"" << livro.titulo << "\" ja esta emprestado.\n";
            else { livro.emprestado = true; cout << "\nLivro \"" << livro.titulo << "\" emprestado com sucesso!\n"; }
            break;
        }
    }
    if (!encontrou) cout << "\nLivro nao encontrado.\n";
}

void devolverLivro(vector<Livro>& biblioteca) {
    if (biblioteca.empty()) { cout << "\nNenhum livro cadastrado.\n"; return; }

    string trechoTitulo;
    bool encontrou = false;

    cout << "\nDigite o titulo ou parte do titulo para devolucao: ";
    limparEntrada();
    getline(cin, trechoTitulo);

    for (Livro& livro : biblioteca) {
        if (contemTextoNormalizado(livro.tituloPesquisa, trechoTitulo)) {
            encontrou = true;
            if (!livro.emprestado) cout << "\nO livro \"" << livro.titulo << "\" ja esta disponivel.\n";
            else { livro.emprestado = false; cout << "\nLivro \"" << livro.titulo << "\" devolvido com sucesso!\n"; }
            break;
        }
    }
    if (!encontrou) cout << "\nLivro nao encontrado.\n";
}
