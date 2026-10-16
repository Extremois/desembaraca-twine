# TwineEdgeOverlap

[Português](#portugues) | [English](#english)

<a id="portugues"></a>

## Português

Ferramenta em desenvolvimento para melhorar a legibilidade de grafos do Twine:
reduzir cruzamentos e trechos coincidentes entre arestas, separar nós sobrepostos e
evitar arestas atravessando nós que não fazem parte da conexão.

O fluxo recebe um arquivo `.twee` por comando e produz uma nova cópia `.twee`,
preservando o original, os conteúdos e as conexões. O resultado informa seu
caminho e distingue sucesso completo, limitações e falha.


O português é o idioma principal do projeto, incluindo as mensagens da CLI e a maior
parte da documentação de apoio. Este README está disponível em português e inglês.

### Estado atual

CLI, leitor, patch de posições, avaliação dos arcos e publicação sem sobrescrita
implementados. Há 78 testes automatizados e seis casos de referência com três contagens
zeradas, cuja reabertura no Twine web foi confirmada pelo usuário. As três histórias
estão concluídas; licença Apache-2.0 e inventário em `docs/third-party.md` disponíveis.
O fluxo validado é pelo checkout, sem dependências Python adicionais. Não há garantia
de resolução universal; resultados com conflitos remanescentes informam limitações.

O bloqueio **FMT-01** tem uma amostra real recebida em formato `.twee`, com posições e
tamanhos dos nós. O usuário confirmou `.twee` para entrada e saída. Um ensaio em cópia
local verificou preservação dos bytes fora das posições. O usuário confirmou a reabertura
no Twine, encerrando FMT-01 para o perfil observado. O perfil geométrico foi identificado
no código-fonte oficial Twine 2.12.1 fornecido em ZIP, com arcos elípticos e laços.

Graphviz `dot` 16.1.0 foi selecionado após comparação com ELK.js 0.12.0. Usam-se apenas
posições; os arcos são recalculados pelo perfil do Twine. Candidatos que aumentem qualquer
contagem são rejeitados. Se não houver melhoria admissível, gera-se cópia íntegra com
o layout original e explica-se a limitação. ELK.js/Node não são dependências de produção.

### Preparar o ambiente no Windows

Use Python 3.12 ou posterior e instale o [Graphviz separadamente](https://graphviz.org/download/).
Baixe ou clone o projeto completo e abra o PowerShell na pasta raiz. Para executar
diretamente pelo código-fonte, sem instalar o pacote Python:

```powershell
python --version
python run.py 'C:\Grafos\história.twee'
```

A CLI procura o Graphviz no PATH e nas pastas padrão do Windows. Para outra localização,
informe o caminho completo do executável:

```powershell
$env:TWINE_GRAPHVIZ_DOT = 'C:\outra-pasta\Graphviz\bin\dot.exe'
```

O [quickstart validado](specs/001-reduce-edge-overlap/quickstart.md) usa
`python run.py CAMINHO` e não precisa instalar o pacote. Os comandos de instalação
abaixo são opcionais e exigem acesso ao índice; essa alternativa não foi verificada.
Foram exercitados Python 3.14.6 e Graphviz 16.1.0 no Windows.

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -c "import twine_edge_overlap; print(twine_edge_overlap.__file__)"
```

O caminho impresso deve apontar para `src/twine_edge_overlap/__init__.py` deste checkout.
O uso do executável do ambiente evita precisar ativá-lo ou alterar a política do PowerShell.
A instalação pode precisar de acesso ao índice de pacotes para setuptools, pytest e suas
dependências. O projeto não possui dependências Python de produção nesta etapa.

Sem acesso ao índice de pacotes, execute diretamente pelo checkout:

```powershell
.\.venv\Scripts\python.exe run.py 'C:\Grafos\história.twee'
```

Esse caminho executa a CLI sem instalar o backend. A instalação editável não foi
validada neste ambiente, pois a rede bloqueou a obtenção de setuptools.

Para conferir sintaxe e executar os testes disponíveis sem dependências adicionais:

```powershell
.\.venv\Scripts\python.exe -m compileall -q src
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os experimentos também podem ser executados separadamente:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests/experiments -v
.\.venv\Scripts\python.exe experiments/compare_layouts.py --probe
```

A sondagem retorna 2 quando faltam dependências. Ela não executa layouts nem comprova
a melhoria do grafo. Consulte a [preparação da comparação](specs/001-reduce-edge-overlap/layout-comparison.md).
Há testes de integração com Graphviz real e resultados esperados para o corpus sintético.

### Processamento

Após instalar o pacote, execute:

```powershell
twine-edge-overlap 'C:\Grafos\história.twee'
```

Ou use `python run.py CAMINHO` neste checkout. A cópia fica na pasta da entrada com nome
`.layout.twee` ou `.layout-N.twee`, sem sobrescrever arquivos existentes.
Importe a cópia gerada no Twine para visualizar o resultado.
O resultado mostra o caminho absoluto e as três contagens
antes/depois: conflitos entre arestas, sobreposições entre nós e travessias de nós alheios.
Nenhuma dessas contagens pode aumentar. Códigos: 0 sucesso, 2 limitações com cópia válida,
1 falha, 130 cancelamento. Perfil: UTF-8, uma história, links `[[destino]]`,
`[[texto->destino]]`, `[[destino<-texto]]` e `[[texto|destino]]`, inclusive setters
preservados sem execução. Metadados `position`/`size` ausentes recebem os padrões do
importador Twine somente na cópia. StoryTitle/StoryData são opcionais. Nomes escapados,
navegação por macros e destinos inexistentes são recusados. Limites: 10 MiB, 100 nós, 300 links, 60s globais e
30s de motor e cabeçalhos de até 8 KiB. O prazo é verificado cooperativamente durante
o processamento; uma chamada de I/O do sistema operacional não pode ser interrompida por
esse controle. Com baseline íntegra, o esgotamento permite finalizar uma cópia sem
melhoria e explicar a limitação. Consulte o [contrato completo](specs/001-reduce-edge-overlap/contracts/format-profile.md).

### Documentação e contribuição

- [Especificação e cenários](specs/001-reduce-edge-overlap/spec.md)
- [Plano técnico e bloqueios](specs/001-reduce-edge-overlap/plan.md)
- [Pesquisa e comparação de motores](specs/001-reduce-edge-overlap/research.md)
- [Tarefas de implementação](specs/001-reduce-edge-overlap/tasks.md)
- [Como contribuir](CONTRIBUTING.md)
- [Dependências e licenças de terceiros](docs/third-party.md)
- [Constituição do projeto](.specify/memory/constitution.md)

Graphviz deve ser instalado separadamente, conforme suas
[distribuições oficiais](https://graphviz.org/download/). A instalação Python não inclui
esse executável. Nenhum binário de Graphviz ou ELK.js é distribuído com esta preparação.

### Licença

Apache License, Version 2.0 (`Apache-2.0`), escolhida explicitamente pelo mantenedor.
Texto integral em [LICENSE](LICENSE), aviso do projeto em [NOTICE](NOTICE).
As dependências externas conservam suas próprias licenças; consulte o
[inventário e a avaliação da integração](docs/third-party.md).

<a id="english"></a>

## English

[Voltar ao português / Back to Portuguese](#portugues)

A tool under development to improve the readability of Twine graphs:
reduce edge crossings and coincident segments, separate overlapping nodes, and
prevent edges from passing through nodes that are not part of the connection.

Each command processes one `.twee` file and produces a new `.twee` copy,
preserving the original file, passage contents, and connections. The result reports
the output path and distinguishes complete success, limitations, and failure.

Portuguese is the project's primary language, including CLI messages and most
supporting documentation. This README is available in Portuguese and English.

### Current status

The CLI, parser, position patching, arc evaluation, and output publication without
overwriting existing files are implemented. There are 78 automated tests and six
reference cases with all three conflict counts reduced to zero; the user confirmed
that the outputs reopened correctly in Twine web. All three user stories are
complete. The project uses Apache-2.0, with a dependency inventory in
`docs/third-party.md`.

Running directly from the source checkout is the validated workflow and requires
no additional Python libraries. The tool does not guarantee that every conflict
can be resolved; remaining conflicts are reported as limitations.

The **FMT-01** format investigation used a real `.twee` sample containing node
positions and sizes. The user confirmed `.twee` for both input and output.
A test on a local copy verified that bytes outside position values were preserved.
The user confirmed that the output reopened in Twine, closing FMT-01 for the observed
profile. The geometry profile was identified from the official Twine 2.12.1 source
archive and includes elliptical arcs and self-loops.

Graphviz `dot` 16.1.0 was selected after comparison with ELK.js 0.12.0.
Only node positions are used; arcs are recalculated according to the Twine profile.
Candidates that increase any conflict count are rejected. If no acceptable
improvement is found, the tool produces an intact copy with the initial layout and
explains the limitation. ELK.js and Node.js are not production dependencies.

### Setting up on Windows

Use Python 3.12 or later and install [Graphviz separately](https://graphviz.org/download/).
The Python installation does not include Graphviz. Download or clone the complete
project, then open PowerShell in its root directory.

The [validated quickstart, in Portuguese](specs/001-reduce-edge-overlap/quickstart.md)
uses `python run.py PATH` and does not require installing the Python package:

```powershell
python --version
python run.py 'C:\Graphs\story.twee'
```

The CLI looks for Graphviz on PATH and in standard Windows installation directories.
For another location, set the full executable path:

```powershell
$env:TWINE_GRAPHVIZ_DOT = 'C:\custom-location\Graphviz\bin\dot.exe'
```

Python 3.14.6 and Graphviz 16.1.0 were exercised on Windows.

The editable installation commands below are optional and require access to the
package index. This alternative was not verified in the current environment because
network access prevented downloading setuptools:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -c "import twine_edge_overlap; print(twine_edge_overlap.__file__)"
```

The printed path should point to `src/twine_edge_overlap/__init__.py` in this
checkout. Calling the virtual environment's Python directly avoids activation or
changes to PowerShell execution policy. Package installation may need to download
setuptools, pytest, and their dependencies. The project currently has no Python
production dependencies.

Without access to the package index, you can also use a virtual environment to run
directly from the source checkout:

```powershell
.\.venv\Scripts\python.exe run.py 'C:\Graphs\story.twee'
```

Check syntax and run the tests without additional Python libraries:

```powershell
.\.venv\Scripts\python.exe -m compileall -q src
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The experiments can also be run separately:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests/experiments -v
.\.venv\Scripts\python.exe experiments/compare_layouts.py --probe
```

The probe returns exit code 2 when dependencies are missing. It does not run layouts
or demonstrate graph improvement. See the
[comparison setup, in Portuguese](specs/001-reduce-edge-overlap/layout-comparison.md).
Integration tests use the real Graphviz executable and expected results for the
synthetic corpus.

### Processing

After installing the Python package, run:

```powershell
twine-edge-overlap 'C:\Graphs\story.twee'
```

Alternatively, use `python run.py PATH` from the source checkout. The copy is
created next to the input with a `.layout.twee` or `.layout-N.twee` suffix,
without overwriting existing files. Import the generated copy into Twine to view it.

The result shows the absolute output path and three before/after counts:
edge conflicts, overlapping nodes, and edges passing through unrelated nodes.
None of these counts may increase.

| Exit code | Meaning |
| --- | --- |
| 0 | Complete success |
| 2 | Valid copy with limitations |
| 1 | Failure |
| 130 | Cancellation |

Supported profile: UTF-8, one story, and links using `[[target]]`,
`[[label->target]]`, `[[target<-label]]`, or `[[label|target]]`.
Setters are preserved without execution. Missing `position` and `size`
metadata receive Twine importer defaults only in the copy. StoryTitle and StoryData
are optional. Escaped passage names, macro-based navigation, and nonexistent link
destinations are rejected.

Limits: 10 MiB per file, 100 nodes, 300 link occurrences, 60 seconds overall,
30 seconds for the layout engine, and headers up to 8 KiB. The deadline is checked
cooperatively during processing; operating-system I/O calls cannot be interrupted
by this mechanism. If an intact baseline has already been validated, reaching the
deadline allows publication of a copy without improvement, with the limitation
reported. See the [full profile contract, in Portuguese](specs/001-reduce-edge-overlap/contracts/format-profile.md).

### Documentation and contributing

The following documents are primarily in Portuguese:

- [Specification and scenarios](specs/001-reduce-edge-overlap/spec.md)
- [Technical plan and blockers](specs/001-reduce-edge-overlap/plan.md)
- [Research and engine comparison](specs/001-reduce-edge-overlap/research.md)
- [Implementation tasks](specs/001-reduce-edge-overlap/tasks.md)
- [Contributing](CONTRIBUTING.md)
- [Third-party dependencies and licenses](docs/third-party.md)
- [Project constitution](.specify/memory/constitution.md)

Graphviz must be installed separately using its
[official distributions](https://graphviz.org/download/). No Graphviz or ELK.js
binaries are bundled with this project.

### License

Apache License, Version 2.0 (`Apache-2.0`), explicitly selected by the maintainer.
The complete text is in [LICENSE](LICENSE), with project notices in [NOTICE](NOTICE).
External dependencies retain their own licenses; see the
[dependency inventory and integration assessment](docs/third-party.md).

