# Desembaraça Twine

[Português](#portugues) | [English](#english)

<a id="portugues"></a>

## Português

O Desembaraça Twine melhora grafos do Twine: reduz conflitos entre arestas, separa
nós sobrepostos e evita arestas atravessando outros nós. Recebe um `.twee` e gera
uma cópia reorganizada, preservando o original, os conteúdos e as conexões.
As mensagens da CLI estão em português.

### Instalação e primeiro uso

A matriz oficial é **Windows 11 x64 com CPython 3.12 x64 ou 3.14 x64**.
Instale uma dessas versões do [Python](https://www.python.org/downloads/windows/),
baixe ou clone o projeto completo e abra o PowerShell na pasta do projeto:

```powershell
python --version
python run.py 'C:\Grafos\história.twee'
```

Esse procedimento usa somente a biblioteca padrão Python. O metadado
`requires-python >=3.12` define o mínimo de código, sem ampliar a matriz oficial.

No primeiro arquivo válido, a aplicação baixa o Graphviz 16.1.0 do servidor oficial,
confere seu SHA-256 e prepara o motor no cache do usuário. Não é necessário instalar
Graphviz, configurar caminhos ou variáveis de ambiente. O download tem cerca de
8,3 MB e o runtime ocupa cerca de 18 MB, além de avisos e temporários. Reserve
2 GiB livres para preparação e reparo e permissão de escrita no perfil e na pasta da entrada.

A primeira preparação e o reparo precisam de internet com acesso HTTPS ao GitLab.
Com cache saudável, o processamento funciona offline, sem consultar o servidor.
Para preparar antes de ficar sem conexão:

```powershell
python run.py --prepare-runtime
```

Se a preparação falhar, a mensagem explica a causa e a ação para repetir o comando;
nenhuma cópia é publicada. Cache incompleto ou alterado é detectado e obtido novamente.
Para obter e validar uma nova geração deliberadamente, com internet:

```powershell
python run.py --repair-runtime
```

Um reparo malsucedido preserva a seleção anterior saudável. Gerações anteriores são
mantidas e podem aumentar o espaço usado. O cache fica em
`%LOCALAPPDATA%\DesembaracaTwine\runtimes\graphviz\`, com fallback para
`AppData\Local` no perfil. Os avisos ficam em `third-party-notices/` de cada geração.
O Graphviz global e a antiga variável `TWINE_GRAPHVIZ_DOT` não selecionam mais o motor;
remova essa configuração de scripts antigos e use os comandos acima.

Instalação opcional do pacote, na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\desembaraca-twine.exe 'C:\Grafos\história.twee'
```

A instalação pode baixar ferramentas de build do índice Python. Elas não são
exigidas pelo fluxo via checkout. Invocar a venv diretamente dispensa ativação e
mudanças na política do PowerShell.

### Instalação remota, sem clonar o projeto

Com Python e pip disponíveis, execute de qualquer pasta:

```powershell
python -m pip install --user --upgrade --force-reinstall "https://github.com/Extremois/desembaraca-twine/archive/refs/heads/feat/002-manage-layout-runtime.zip"
```

O pip obtém o ZIP da branch de desenvolvimento diretamente do GitHub; não é
necessário instalar Git nem baixar o projeto manualmente. A instalação requer
internet e pode baixar ferramentas de build do índice Python. A reinstalação
forçada permite atualizar o código mesmo enquanto a versão de desenvolvimento
do pacote continuar igual. Essa branch está em validação; consulte o estado abaixo.

Com a pasta `Scripts` da instalação de usuário do Python no PATH, use:

```powershell
desembaraca-twine 'C:\Grafos\história.twee'
```

Se o terminal não reconhecer o comando, use a chamada pelo Python, que funciona
sem adicionar a pasta `Scripts` ao PATH:

```powershell
python -m twine_edge_overlap.cli 'C:\Grafos\história.twee'
```

As opções `--prepare-runtime` e `--repair-runtime` também estão disponíveis nessas
invocações. O Graphviz continua sendo obtido automaticamente na primeira
preparação e reutilizado offline depois.

### Resultado e limites

#### Linux e macOS: estado da implementação

O pacote Python já tem seleção de plataforma e cache POSIX, mas esta revisão ainda
não distribui um motor Linux/macOS qualificado. Os comandos abaixo descrevem o
percurso de uma candidata com componente compatível; a candidata atual recusa a
execução POSIX enquanto esse componente não estiver no catálogo. A URL remota
anterior não representa uma entrega desta feature em andamento.

Com CPython **3.12 ou 3.14 nativo**, incluindo venv/pip, uma candidata pode ser
instalada sem alterar o Python do sistema ou exigir Git/Graphviz:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install /caminho/para/candidata.whl
.venv/bin/desembaraca-twine --prepare-runtime
.venv/bin/python -m twine_edge_overlap '/caminho/história.twee'
```

Use o caminho absoluto ao Python/console da venv para chamar de outra pasta.
Linux usa XDG_CACHE_HOME absoluto, com fallback `~/.cache`; macOS usa
`~/Library/Caches`, ambos com `DesembaracaTwine/runtimes/graphviz/` abaixo da base.
Python precisa corresponder à arquitetura nativa; Rosetta não qualifica um Mac.
As origens dos dois Pythons ainda precisam ser ensaiadas por célula da matriz.
Há um [procedimento parcial de pré-requisitos Linux](specs/003-add-cross-platform-support/evidence/linux-prerequisites.md), ensaiado com instalações privadas dos dois Pythons no WSL; ele não aprova as células nativas.
Algumas versões da matriz dependem de elegibilidade gratuita, como Ubuntu Pro ou
RHEL Developer; isso não é inferido por parentesco entre distribuições nem exige
enviar credenciais à ferramenta. Consulte as condições na matriz.

Um ambiente sem validação pode funcionar em **melhor esforço**, com aviso em
stderr, quando houver motor tecnicamente compatível. O aviso não muda os códigos
de resultado. ABI/arquitetura incompatível ou motor ausente impede a execução.
Em rolling, atualizar pacotes ou kernel pode retirar a correspondência oficial;
não é preciso reverter atualizações para usar um componente ainda compatível.

Se a execução for negada, confira permissões e se o filesystem permite programas;
no macOS, consulte as políticas normais e a distribuição assinada do projeto.
O erro não atribui automaticamente a causa a Gatekeeper ou `noexec`.
Para filesystem sem hardlinks, use uma pasta que permita a publicação atômica.
Falha/reparo preservam a geração anterior saudável e os arquivos de entrada.
Repita `--repair-runtime` após corrigir a condição; o reparo requer internet.

A cópia fica ao lado da entrada, como `.layout.twee` ou `.layout-N.twee`, sem
sobrescrever arquivos. Importe a cópia no Twine para visualizar o resultado.
São mostradas três contagens antes/depois: conflitos entre arestas, sobreposições
entre nós e travessias de nós alheios. Nenhuma contagem pode aumentar. Alguns
grafos mantêm conflitos; sem melhoria admissível, a cópia conserva o layout inicial.

| Código | Resultado |
| --- | --- |
| 0 | Sucesso completo |
| 2 | Cópia válida com limitações |
| 1 | Falha |
| 130 | Cancelamento |

Perfil: UTF-8, uma história, links `[[destino]]`, `[[texto->destino]]`,
`[[destino<-texto]]` e `[[texto|destino]]`, incluindo setters preservados sem execução.
StoryTitle/StoryData são opcionais. Posições/tamanhos ausentes recebem padrões do
importador Twine na cópia. Nomes escapados, navegação por macros e destinos inexistentes
são recusados. Limites: 10 MiB, 100 nós, 300 links, cabeçalhos de 8 KiB, 60s de
processamento e 30s de motor. Preparação: orçamento separado de 300s, até 30s por
operação de rede e 10s por sondagem. Prazos são cooperativos; I/O pode terminar após
o prazo. Veja o [contrato do formato](specs/001-reduce-edge-overlap/contracts/format-profile.md).

### Estado e documentação

O suporte a Linux e macOS está em implementação na [feature 003](specs/003-add-cross-platform-support/validation.md).
A detecção de plataforma, o cache POSIX e os testes compartilhados já existem;
o catálogo distribuído ainda contém apenas o motor Windows. Builds Linux locais
são experimentais. A [matriz proposta](specs/003-add-cross-platform-support/support-matrix.md)
não representa plataformas já qualificadas. Não há instalador Linux/macOS disponível nesta revisão.

Motor gerenciado e testes de preservação, layout, offline e recuperação implementados.
A validação local usa Windows 11 com CPython 3.12 e 3.14, incluindo primeiro uso
com download real, seis referências offline e recuperação. Por decisão do mantenedor,
a aceitação em Windows limpo está adiada; o trabalho prossegue no sistema atual,
sem criar VM. A reabertura das novas saídas no Twine permanece pendente. Consulte
as [evidências e limitações](specs/002-manage-layout-runtime/validation.md).
O perfil geométrico segue Twine 2.12.1. Graphviz fornece posições; os arcos são
recalculados pelo projeto. ELK.js/Node foram usados apenas na comparação de motores.

- [Guia de validação e recuperação](specs/002-manage-layout-runtime/quickstart.md)
- [Especificação](specs/002-manage-layout-runtime/spec.md), [plano](specs/002-manage-layout-runtime/plan.md) e [tarefas](specs/002-manage-layout-runtime/tasks.md)
- [Pesquisa e comparação de motores](specs/001-reduce-edge-overlap/research.md)
- [Contribuição e testes](CONTRIBUTING.md)
- [Dependências e licenças](docs/third-party.md)
- [Constituição](.specify/memory/constitution.md)

### Licença

Código autoral sob [Apache-2.0](LICENSE), com aviso em [NOTICE](NOTICE).
Wheel/sdist incluem manifesto e avisos. A aplicação obtém os binários do fornecedor
diretamente; esses componentes conservam suas próprias licenças.

<a id="english"></a>

## English

[Voltar ao português / Back to Portuguese](#portugues)

Desembaraça Twine reduces edge conflicts, node overlaps, and edges crossing unrelated
nodes. It reads a `.twee` file and creates a rearranged copy, preserving the original,
contents, and links. CLI messages and most supporting documentation are in Portuguese.

### Installation and first use

The official matrix is **Windows 11 x64 with CPython 3.12 x64 or 3.14 x64**.
Install one of these [Python versions](https://www.python.org/downloads/windows/),
download or clone the complete project, and open PowerShell in its root directory:

```powershell
python --version
python run.py 'C:\Graphs\story.twee'
```

This workflow uses only Python's standard library. The `requires-python >=3.12`
metadata defines the code minimum; it does not extend the official support matrix.

For the first valid input, the application downloads Graphviz 16.1.0 from its official
server, verifies SHA-256, and prepares it in the user cache. No separate Graphviz
installation, executable paths, or environment configuration are required. The download
is about 8.3 MB and the runtime occupies about 18 MB, plus notices and temporary files.
Allow 2 GiB of free space and write access to the user profile and input directory.

Initial preparation and repair need internet access over HTTPS to GitLab.
A healthy cache works offline without contacting the server. To prepare before going offline:

```powershell
python run.py --prepare-runtime
```

Preparation failures explain the cause and recovery step and publish no output copy.
Incomplete or altered caches are detected and downloaded again. To deliberately
download and validate a new generation, while online:

```powershell
python run.py --repair-runtime
```

A failed repair preserves the previous healthy selection. Previous generations are
retained, so disk usage can grow. Cache location:
`%LOCALAPPDATA%\DesembaracaTwine\runtimes\graphviz\`, falling back to
`AppData\Local` in the user profile. Each generation includes `third-party-notices/`.
System Graphviz and the legacy `TWINE_GRAPHVIZ_DOT` setting no longer select the
engine; remove that setting from old scripts and use these commands.

Optional package installation from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\desembaraca-twine.exe 'C:\Graphs\story.twee'
```

Installation may download build tools from the Python package index. Those are not
required for checkout execution. Calling the venv directly avoids activation and
PowerShell policy changes.

### Remote installation without cloning the project

With Python and pip available, run from any directory:

```powershell
python -m pip install --user --upgrade --force-reinstall "https://github.com/Extremois/desembaraca-twine/archive/refs/heads/feat/002-manage-layout-runtime.zip"
```

Pip downloads the development branch ZIP directly from GitHub; Git and a manual
checkout are not required. Installation needs internet access and may download
build tools from the Python package index. Forced reinstallation updates the code
even while the development package version stays the same. This branch is still
under validation; see its status below.

With the Python user installation's `Scripts` directory on PATH, use:

```powershell
desembaraca-twine 'C:\Graphs\story.twee'
```

If the terminal does not recognize the command, invoke the Python module instead;
this works without adding the `Scripts` directory to PATH:

```powershell
python -m twine_edge_overlap.cli 'C:\Graphs\story.twee'
```

Both invocations also accept `--prepare-runtime` and `--repair-runtime`. Graphviz
is still downloaded automatically during initial preparation and reused offline
afterwards.

### Results and limits

#### Linux and macOS: implementation status

The Python package includes platform selection and POSIX caching, but this revision
does not yet distribute a qualified Linux/macOS engine. The commands below describe
a candidate containing a compatible engine; the current candidate refuses POSIX
execution until that engine is in its catalog. The earlier remote URL does not
represent delivery of this feature under development.

With **native CPython 3.12 or 3.14**, including venv/pip, install a candidate without
replacing the system Python or requiring Git/Graphviz:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install /path/to/candidate.whl
.venv/bin/desembaraca-twine --prepare-runtime
.venv/bin/python -m twine_edge_overlap '/path/to/story.twee'
```

Use the absolute path to the venv Python/console from another working directory.
Linux uses absolute XDG_CACHE_HOME with `~/.cache` as fallback; macOS uses
`~/Library/Caches`, each followed by `DesembaracaTwine/runtimes/graphviz/`.
Python must match the native architecture; Rosetta does not qualify a Mac.
Interpreter origins for both Python versions still need testing in each matrix cell.
A [partial Linux prerequisites procedure](specs/003-add-cross-platform-support/evidence/linux-prerequisites.md) was tested with private installations of both Python versions in WSL; it does not qualify native cells.
Some matrix versions depend on free eligibility, such as Ubuntu Pro or RHEL
Developer. Distribution ancestry does not grant this eligibility, and the tool
does not request those credentials. See the matrix for the applicable conditions.

An unvalidated environment can run on a **best effort** basis, with a stderr warning,
when a technically compatible engine exists. The warning does not change result
codes. Incompatible ABI/architecture or a missing engine prevents execution.
On rolling systems, package/kernel updates can remove an official match; reverting
updates is not required to use an engine that remains technically compatible.

If execution is denied, check permissions and whether the filesystem allows programs;
on macOS, consult normal policies and the project's signed distribution. Diagnostics
do not automatically blame Gatekeeper or `noexec`. If hardlinks are unavailable,
use a folder supporting atomic publication. Failed preparation/repair preserves the
previous healthy generation and input files. After correcting the condition, retry
`--repair-runtime`; repair requires internet access.

Output is created next to the input as `.layout.twee` or `.layout-N.twee`, without
overwriting files. Import it into Twine to view it. Three before/after counts describe
edge conflicts, overlapping nodes, and edges crossing unrelated nodes. None may increase.
Some graphs retain conflicts; without acceptable improvement, the initial layout is retained.

| Exit code | Meaning |
| --- | --- |
| 0 | Complete success |
| 2 | Valid copy with limitations |
| 1 | Failure |
| 130 | Cancellation |

Profile: UTF-8, one story, links `[[target]]`, `[[label->target]]`, `[[target<-label]]`,
and `[[label|target]]`, including setters preserved without execution. StoryTitle/StoryData
are optional. Missing positions/sizes receive Twine importer defaults in the copy.
Escaped names, macro navigation, and missing targets are rejected. Limits: 10 MiB,
100 nodes, 300 links, 8 KiB headers, 60s processing, and 30s engine. Preparation has
a separate 300s budget, with 30s network operations and 10s probes. Deadlines are
cooperative; I/O can finish after the deadline. See the
[format contract](specs/001-reduce-edge-overlap/contracts/format-profile.md).

### Status and documentation

Linux and macOS support is being implemented in [feature 003](specs/003-add-cross-platform-support/validation.md).
Platform detection, POSIX caching and shared tests are present; the distributed
catalog still contains only the Windows engine. Local Linux builds are experimental.
The [proposed matrix](specs/003-add-cross-platform-support/support-matrix.md) does not
represent qualified platforms. This revision does not provide a Linux/macOS installer.

The managed engine and preservation, layout, offline, and recovery tests are implemented.
Local validation uses Windows 11 with CPython 3.12 and 3.14, including first use
with a real download, six offline references, and recovery. At the maintainer's
request, clean Windows acceptance is deferred; work continues on the current system
without creating a VM. Reopening newly generated outputs in Twine remains pending.
See the [validation record](specs/002-manage-layout-runtime/validation.md).
Geometry follows Twine 2.12.1. Graphviz supplies positions; the project recalculates arcs.
ELK.js/Node were used only for engine comparisons.

- [Validation and recovery](specs/002-manage-layout-runtime/quickstart.md)
- [Specification](specs/002-manage-layout-runtime/spec.md), [plan](specs/002-manage-layout-runtime/plan.md), and [tasks](specs/002-manage-layout-runtime/tasks.md)
- [Engine comparison](specs/001-reduce-edge-overlap/research.md)
- [Contributing and tests](CONTRIBUTING.md)
- [Dependencies and licenses](docs/third-party.md)
- [Constitution](.specify/memory/constitution.md)

### License

Original code uses [Apache-2.0](LICENSE), with project notices in [NOTICE](NOTICE).
Wheel/sdist include the manifest and notices. The application retrieves engine binaries
directly from the supplier; those components retain their own licenses.
