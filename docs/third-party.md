# Dependências e licenças

Inventário do fluxo por código-fonte e do runtime gerenciado, verificado em 2026-10-16.
O código autoral usa Apache-2.0, escolhido explicitamente pelo mantenedor; texto em
[LICENSE](../LICENSE) e aviso em [NOTICE](../NOTICE). Não há binários ou código de
Graphviz, ELK.js, Node.js, Twine ou Python incorporados ao projeto; textos de licença
e avisos de terceiros acompanham o manifesto do runtime.

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

## Inventário anterior da instalação global (histórico)

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
essas bibliotecas. Esse inventário histórico não qualifica o ZIP gerenciado. A revisão
do artefato obtido automaticamente e os avisos complementares estão descritos adiante.

## Build e desenvolvimento opcionais

`setuptools>=68` é o backend de build; `pytest>=8` é um extra opcional de
desenvolvimento. Ambos indicam MIT nas origens. A suíte usa unittest. Na qualificação
de distribuições foram obtidos em venv isolada build 1.6.1, setuptools 84.0.0, wheel
0.48.0, packaging 26.3, pyproject_hooks 1.3.3 e colorama 0.4.6. Essas ferramentas e
pip não são dependências de execução nem são incorporadas à entrega. A obtenção de
ferramentas pode precisar de acesso ao índice; resultados estão em validation.md.

ELK.js e Node não aparecem em `project.dependencies`. O pacote ELK instalado declara
dependências de desenvolvimento (por exemplo web-worker); o experimento usou o worker
simulado do bundle no mesmo processo. Esses componentes não são exigidos pela CLI.

## Compatibilidade da integração escolhida

O projeto distribui sua implementação independente sob Apache-2.0 e usa Graphviz
gerenciado pela aplicação, trocando apenas IDs sintéticos, dimensões e relações por arquivo
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

## Artefato qualificado para obtenção automática

A feature `002-manage-layout-runtime` obteve e verificou o ZIP oficial win32 16.1.0.
O [inventário do ZIP](graphviz-16.1.0-managed-runtime.json)
contém origem, SHA-256 real, tamanhos e os 302 arquivos, incluindo 97 EXE/DLLs.
Ele é distinto do inventário anterior da instalação global e não contém binários.

SHA-256 verificado: `37906f29ede26cf1952f8cf942c1e7814ab86ef448130136c8607b1b6ffe0870`.
O ZIP não contém arquivos com nomes de licença/aviso identificáveis pelos termos
license/copying/notice/copyright. Os avisos complementares foram recuperados das
fontes do fornecedor e incluídos no projeto, conforme a revisão abaixo.

A [evidência de qualificação](../specs/002-manage-layout-runtime/validation.md)
registra o impedimento inicial de T004 e sua resolução. O manifesto ativo fixa o
artefato e avisos; instalação separada de Graphviz deixou de ser requisito.

### Revisão concluída para o download direto

A revisão seguinte complementa o registro inicial acima: o [inventário de componentes](graphviz-16.1.0-components.json)
mapeia todos os 302 arquivos a 28 componentes, distinguindo licenças de bibliotecas das
licenças dos respectivos projetos/ferramentas. Os 29 arquivos em
`src/twine_edge_overlap/third_party/graphviz-16.1.0/` incluem textos, avisos e SOURCES.json;
o manifesto fixa seus caminhos e SHA-256 para instalação junto ao runtime e uso offline.

Os avisos vcpkg provêm do commit `ff985525b23a1a72ddb1a89482ea12233c3cbe85`
usado pela tag Graphviz; o texto PCRE2 foi complementado com LICENCE da tag 10.43.
ANN 1.1.2 tem aviso LGPL e copyright no cabeçalho do fornecedor, complementado pelo texto
LGPL-2.1; as fontes públicas do autor estão referenciadas. Os termos Microsoft foram
extraídos do documento oficial Visual C++ 2015-2022 Runtime, preservando o texto completo.
NOASSERTION dos metadados de receita não foi convertido em licença presumida: para
libiconv/liblzma/Tcl foram usados os avisos de biblioteca correspondentes.

A composição escolhida mantém o Python autoral independente sob Apache-2.0 e executa
Graphviz como programa separado, sem carregar suas DLLs no Python ou incorporar fontes
dos motores ao código autoral. O usuário obtém o ZIP original diretamente do fornecedor,
sem reempacotamento/espelho de binários pelo projeto; avisos e referências de fontes são
mantidos separadamente. A conclusão de compatibilidade se limita a essa composição e
ao uso local dos componentes obtidos. Não autoriza redistribuir binários Microsoft ou
outros componentes em wheel, sdist ou releases: tal mudança exige revisão própria.

Os [termos oficiais do runtime Microsoft](https://visualstudio.microsoft.com/license-terms/vs2022-cruntime/)
tratam da instalação e do uso; a [documentação de redistribuição](https://learn.microsoft.com/en-us/visualstudio/releases/2022/redistribution)
mantém condições próprias para quem redistribui. O projeto não troca essas condições por
Apache-2.0 nem oferece os binários a partir de sua própria distribuição. Bibliotecas LGPL
continuam com seus avisos/fontes referenciados e binários do fornecedor intactos.
