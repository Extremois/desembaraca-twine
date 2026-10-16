# Dependências e licenças

Inventário final do fluxo por código-fonte, verificado em 2026-10-16.
O código autoral usa Apache-2.0, escolhido explicitamente pelo mantenedor; texto em
[LICENSE](../LICENSE) e aviso em [NOTICE](../NOTICE). Não há binários ou código de
Graphviz, ELK.js, Node.js, Twine ou Python incorporados ao projeto.

## Componentes do fluxo validado

| Componente | Versão observada | Uso | Licença / condição |
|---|---|---|---|
| Código autoral | 0.1.0.dev0 | CLI, adaptador, geometria e testes | Apache-2.0 |
| Python | 3.14.6 | Interpretador e biblioteca padrão, externos | PSF License e avisos do fornecedor |
| Bibliotecas Python de produção | Nenhuma | Somente biblioteca padrão | Inventário transitivo Python vazio |
| Graphviz | 16.1.0, executável Windows win32 | Processo externo dot, plugins dot_layout/core, saída json0 | EPL-2.0 verificada no LICENSE da tag 16.1.0 |
| Node.js | v24.18.0 | Somente experimento ELK | MIT e avisos de componentes do fornecedor |
| ELK.js | 0.12.0 | Somente experimento comparativo | EPL-2.0 OR GPL-3.0-or-later nos metadados instalados |
| Twine | 2.12.1 | Fonte consultada para comportamento de arcos e importação | GPL-3.0; não copiado nem executado pelo produto |

O fluxo validado é `python run.py` e testes `unittest`: nenhum instalador de pacotes é
necessário. Não há bibliotecas transitivas Python incorporadas. A licença autoral não
substitui as licenças dos pré-requisitos externos.

## Inventário nativo observado

[graphviz-16.1.0-windows-files.json](graphviz-16.1.0-windows-files.json) registra os 97
executáveis e DLLs encontrados na instalação usada, com nomes, tamanhos, SHA-256 e
metadados de versão quando disponíveis. Muitos arquivos não trazem versão em recursos
Windows; o número 16.1.0 vem de `dot -V`, não de uma versão presumida de cada biblioteca.
Esse manifesto contém metadados, não os binários.

A distribuição externa inclui Graphviz/cdt/cgraph/gvc/pathplan/xdot e plugins, além de
DLLs de renderização, fontes e suporte: Cairo, Pango/GLib, Fontconfig, FreeType, HarfBuzz,
FriBidi, libgd, JPEG, TIFF, libpng, WebP, Brotli, bzip2, Expat, libffi, libiconv/gettext,
liblzma, PCRE2, Pixman, Tcl, GTS, zlib e runtime Microsoft. A lista não afirma que todos
esses plugins foram carregados por cada chamada de dot/json0, nem aplica EPL-2.0 a todas
essas bibliotecas. Nenhuma delas é incorporada à entrega deste projeto; seus avisos
permanecem na distribuição instalada do fornecedor. Empacotar essa instalação exigiria
um inventário de licenças próprio por componente; isso não faz parte desta entrega.

## Build e desenvolvimento opcionais

`setuptools>=68` é o backend de build opcional para instalação editável; `pytest>=8`
é um extra opcional de desenvolvimento. Ambos indicam MIT nas origens. Não estavam
instalados no ambiente de validação: não se atribui versão ou árvore transitiva fictícia
a eles, e a instalação editável não é anunciada como verificada. As 69 verificações
foram executadas com unittest. Pip 26.1.2 já existia na venv, mas não é dependência de
execução nem é incorporado à entrega. Instalar os extras requer acesso ao índice.

ELK.js e Node não aparecem em `project.dependencies`. O pacote ELK instalado declara
dependências de desenvolvimento (por exemplo web-worker); o experimento usou o worker
simulado do bundle no mesmo processo. Esses componentes não são exigidos pela CLI.

## Compatibilidade da integração escolhida

O projeto distribui sua implementação independente sob Apache-2.0 e usa Graphviz
instalado separadamente, trocando apenas IDs sintéticos, dimensões e relações por arquivo
DOT/JSON. Não incorpora fontes ou binários EPL/GPL. O avaliador usa matemática SVG
implementada no projeto; as fontes GPL do Twine foram consultadas para identificar o
comportamento e não copiadas ou transpiladas. Nesta composição não foi identificado
componente incorporado que exija relicenciar o código autoral sob a licença dos motores
externos. Essa conclusão se limita a esta
composição de fontes e pré-requisitos; não autoriza redistribuir os motores com seus
avisos omitidos.

## Fontes e avisos

- [Apache License 2.0: texto oficial](https://www.apache.org/licenses/LICENSE-2.0.txt).
  O LICENSE local inclui as nove seções e o apêndice; os termos também foram comparados
  com uma segunda cópia canônica local (licença Apache do packaging distribuída com pip).
- [Python: licenças e componentes](https://docs.python.org/3/license.html).
- [Graphviz 16.1.0: LICENSE da tag](https://gitlab.com/graphviz/graphviz/-/raw/16.1.0/LICENSE).
- [Graphviz: instalação completa](https://graphviz.org/download/).
- [Node.js: licenças e avisos](https://github.com/nodejs/node/blob/v24.18.0/LICENSE).
- [ELK.js: metadados oficiais](https://github.com/kieler/elkjs/blob/master/package.json).
  Versão e licença de 0.12.0 conferidas no package.json instalado localmente.
- [Twine 2.12.1: fonte oficial](https://github.com/klembot/twinejs/releases/tag/2.12.1).
- [setuptools: licença](https://github.com/pypa/setuptools/blob/main/LICENSE).
- [pytest: licença](https://github.com/pytest-dev/pytest/blob/main/LICENSE).
- [SVG: parametrização matemática dos arcos](https://www.w3.org/TR/SVG/implnote.html).

O NOTICE identifica o projeto e remete a este inventário. Os arquivos de amostra
privados e os downloads do editor permanecem fora das fontes versionadas; os fixtures
incluídos são sintéticos. NetworkX foi avaliado documentalmente e não é dependência.
