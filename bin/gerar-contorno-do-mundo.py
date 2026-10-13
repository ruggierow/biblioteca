#!/usr/bin/env python3
"""Gera o contorno do mundo que o mapa do motor-web usa.

    ./bin/gerar-contorno-do-mundo.py

Baixa o Natural Earth 1:110m (DOMINIO PUBLICO, naturalearthdata.com) pelo
empacotamento `world-atlas` (ISC), converte para caminhos SVG na projecao do
mapa e REESCREVE o bloco `<script id="contorno-do-mundo">` do biblioteca.html.

So e preciso rodar se um dia quisermos outra escala, outra projecao ou um pais
novo na tabela. O dado gerado fica versionado dentro do HTML, para o aplicativo
nao depender de rede nenhuma.

POR QUE DADO EMBUTIDO, E NAO DESENHO A MAO: contorno de litoral e feito de
milhares de coordenadas. Desenhar de memoria daria um mapa errado com cara de
certo — e mapa errado com cara de certo e pior que mapa nenhum.

PROJECAO: equirretangular, a mesma das bolhas. x = lon + 180, y = 95 - lat, com
uma casa decimal (~11 km, menos de um terco de pixel neste mapa).

DUAS COISAS QUE SO APARECEM DESENHANDO:

  ANTIMERIDIANO — a Russia tem pontos saltando de +179 para -179 graus. Ligados
  num mapa plano, riscam uma faixa atravessando o mundo inteiro. O caminho e
  quebrado onde o salto passa de 180 graus.

  ANTARTIDA — achatada, vira uma barra cinzenta no rodape que nao diz nada
  sobre livros. Fica de fora, e o viewBox encurta junto.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGINA = RAIZ / "motor-web/biblioteca.html"
FONTE = "https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json"

# nome em ingles no Natural Earth -> codigo ISO que a coluna 9 guarda
MEUS = {
 "Brazil":"BR","Argentina":"AR","Chile":"CL","Colombia":"CO","Peru":"PE","Uruguay":"UY",
 "United States of America":"US","Canada":"CA","Mexico":"MX","Cuba":"CU",
 "Portugal":"PT","Spain":"ES","France":"FR","United Kingdom":"GB","Ireland":"IE",
 "Germany":"DE","Italy":"IT","Switzerland":"CH","Austria":"AT","Belgium":"BE",
 "Netherlands":"NL","Denmark":"DK","Sweden":"SE","Norway":"NO","Poland":"PL",
 "Czechia":"CZ","Hungary":"HU","Greece":"GR","Belarus":"BY","Russia":"RU",
 "Turkey":"TR","Israel":"IL","Palestine":"PS","Lebanon":"LB","Iran":"IR",
 "India":"IN","China":"CN","South Korea":"KR","Japan":"JP",
 "Egypt":"EG","Senegal":"SN","Nigeria":"NG","Angola":"AO","Rwanda":"RW",
 "Mozambique":"MZ","South Africa":"ZA","Australia":"AU",
}


def main():
    print(f"baixando {FONTE}")
    d = json.loads(urllib.request.urlopen(FONTE, timeout=60).read())
    sc, tr = d["transform"]["scale"], d["transform"]["translate"]

    def arco(i):
        rev = i < 0
        if rev: i = ~i
        pts, x, y = [], 0, 0
        for dx, dy in d["arcs"][i]:
            x += dx; y += dy
            pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
        return pts[::-1] if rev else pts

    def anel(indices):
        pts = []
        for i in indices:
            a = arco(i)
            pts.extend(a[1:] if pts else a)
        return pts

    def caminho(geom):
        pols = geom["arcs"] if geom["type"] == "MultiPolygon" else [geom["arcs"]]
        partes = []
        for pol in pols:
            for indices in pol:
                pts = anel(indices)
                if len(pts) < 3: continue
                trecho = []
                for k, (lon, lat) in enumerate(pts):
                    if k and abs(lon - pts[k - 1][0]) > 180:   # antimeridiano
                        if len(trecho) > 2: partes.append("M" + "L".join(trecho) + "Z")
                        trecho = []
                    trecho.append(f"{lon + 180:.1f},{95 - lat:.1f}")
                if len(trecho) > 2: partes.append("M" + "L".join(trecho) + "Z")
        return "".join(partes)

    meus, fundo = {}, []
    for g in d["objects"]["countries"]["geometries"]:
        nome = g["properties"]["name"]
        if nome == "Antarctica": continue
        c = caminho(g)
        if not c: continue
        (meus.__setitem__(MEUS[nome], c) if nome in MEUS else fundo.append(c))

    faltam = sorted(set(MEUS.values()) - set(meus))
    if faltam:
        sys.exit(f"ABORTADO: nao achei no Natural Earth: {faltam}")
    print(f"paises com contorno proprio: {len(meus)}   fundo: {len(fundo)} outros")

    bloco = ('        const MAPA_FUNDO = ' + json.dumps("".join(fundo)) + ';\n'
             '        const MAPA_PAISES = ' + json.dumps(meus, separators=(",", ":")) + ';\n')
    pagina = PAGINA.read_text(encoding="utf-8")
    novo, n = re.subn(r'(<script id="contorno-do-mundo">\n).*?(    </script>)',
                      lambda m: m.group(1) + bloco + m.group(2), pagina, flags=re.S)
    if n != 1:
        sys.exit("ABORTADO: nao achei o bloco <script id=\"contorno-do-mundo\"> no HTML.")
    PAGINA.write_text(novo, encoding="utf-8")
    print(f"biblioteca.html reescrito: {len(novo)//1024} KB")


if __name__ == "__main__":
    main()
