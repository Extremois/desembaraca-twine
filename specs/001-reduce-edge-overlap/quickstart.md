# Execução local no Windows

Fluxo validado por código-fonte, sem instalação do pacote nem acesso à rede.
Requer Python e Graphviz instalados separadamente. Ambiente exercitado: Windows,
Python 3.14.6 e Graphviz 16.1.0. O código declara Python >=3.12 como requisito mínimo;
outras versões não foram exercitadas nesta entrega.

## Preparação

Abra PowerShell na raiz deste checkout e confira:

```powershell
python --version
& 'C:\Program Files (x86)\Graphviz\bin\dot.exe' -V
python run.py --version
```

Se Graphviz estiver em outra pasta, coloque dot no PATH ou defina
`TWINE_GRAPHVIZ_DOT` com o caminho completo do executável. Use a
[instalação oficial completa](https://graphviz.org/download/), com bibliotecas e plugins.
Python não inclui Graphviz. A CLI procura PATH e instalações Windows padrão.

## Ensaio com exemplo sintético

Crie uma cópia do fixture em uma pasta local. O bloco conserva uma entrada já existente:

```powershell
New-Item -ItemType Directory -Force '.tmp/quickstart' | Out-Null
if (-not (Test-Path '.tmp/quickstart/exemplo.twee')) {
    Copy-Item -LiteralPath 'tests/fixtures/crossing.twee' -Destination '.tmp/quickstart/exemplo.twee'
}
python run.py '.tmp/quickstart/exemplo.twee'
```

Esperado: estado sucesso, caminho absoluto de `exemplo.layout.twee` e contagens:

```text
Pares de arestas: 1 -> 0
Pares de nós: 0 -> 0
Pares aresta–nó: 0 -> 0
```

Em novas execuções, usa-se outro nome, como `exemplo.layout-2.twee`, sem sobrescrever.
A entrada permanece idêntica byte a byte. Os seis exemplos resolvíveis do corpus
foram reabertos no Twine web e confirmados pelo usuário. Entradas sem posições/tamanhos
recebem os padrões de importação do Twine somente na cópia gerada.

## Seu arquivo e estados

```powershell
python run.py 'C:\Grafos\história.twee'
```

Uma entrada por execução. A saída fica na pasta da entrada com nome distinto; exige
permissão de escrita nessa pasta. Código 0: sucesso completo; 2: cópia íntegra com
limitações, inclusive sem melhoria; 1: falha sem saída válida anunciada; 130: cancelamento.
Toda cópia informa as três contagens antes/depois, sem aumentar nenhuma delas.

Perfil: fonte UTF-8, StoryTitle/StoryData opcionais, links simples e com rótulos
(`->`, `<-`, `|`), coordenadas position/size opcionais. Cabeçalhos escapados,
destinos inexistentes e navegação por macros não são suportados.
Limites: 10 MiB, 8 KiB por cabeçalho, 100 nós, 300 links, 60s cooperativos de processamento,
30s de motor, 8 MiB de saída do processo. I/O do sistema não é interrompido pelo prazo.
Detalhes no [perfil](contracts/format-profile.md) e [contrato CLI](contracts/cli.md).

## Verificações

```powershell
python -m unittest discover -s tests -v
python -m compileall -q src tests run.py
```

Resultado atual: 78 testes aprovados. Nenhuma dependência Python adicional
é necessária para a CLI ou esses testes.

## Instalação editável opcional — não verificada

Para criar o comando `twine-edge-overlap` no ambiente Python, com acesso ao índice:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\twine-edge-overlap.exe 'C:\Grafos\história.twee'
```

Essa alternativa depende de setuptools e pytest e não foi validada no ambiente sem
rede. O fluxo validado acima é pelo checkout. O projeto usa Apache-2.0; consulte
[LICENSE](../../LICENSE), [NOTICE](../../NOTICE) e o [inventário](../../docs/third-party.md).
