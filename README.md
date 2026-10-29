# Desembaraça Twine

**Escopo de validação:** GitHub Actions por ABI/arquitetura/Python (glibc/musl, x64/ARM64; macOS Intel/ARM64; Windows x64; Python 3.12/3.14). A lista de distribuições é uma declaração de compatibilidade, sem certificação individual. Assinatura Apple e notarização macOS são opcionais; sem configuração Apple, os componentes não têm atestado Developer ID/notarização. Não é necessário fornecer credenciais Apple para os testes. Os seis runtimes POSIX e seus kits de fontes estão [publicados](https://github.com/Extremois/desembaraca-twine/releases/tag/graphviz-16.1.0-posix-46d111d), com integridade e licenças revisadas.

[Português](#portugues) | [English](#english)

<a id="portugues"></a>

## Português

O Desembaraça Twine melhora grafos do Twine: reduz conflitos entre arestas, separa
nós sobrepostos e evita arestas atravessando outros nós. Recebe um `.twee` e gera
uma cópia reorganizada, preservando o original, os conteúdos e as conexões.
As mensagens da CLI estão em português.

### Instalação e primeiro uso

A matriz qualificada cobre **Linux glibc ≥ 2.27 e musl ≥ 1.2.0 em x64/ARM64, macOS ≥ 15 em Intel/ARM64 e Windows x64 (runtime Win32 legado), com CPython 3.12 ou 3.14 nativo**. A qualificação por ABI foi executada no GitHub Actions; o runner Windows Server não é apresentado como certificação de Windows 11 limpo. Os comandos abaixo mostram o uso no Windows; a instalação Linux/macOS aparece adiante.
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
python -m venv "$HOME\.venvs\desembaraca-twine"
& "$HOME\.venvs\desembaraca-twine\Scripts\python.exe" -m pip install "https://github.com/Extremois/desembaraca-twine/archive/53fb2aba47d78b5cb4a6679cafaaef5fc5e52c29.zip"
```

A URL fixa uma revisão de desenvolvimento já enviada ao repositório. Git e
checkout manual não são necessários. A instalação requer internet e pode baixar
ferramentas de build do índice Python. Reinstalar a mesma URL mantém essa revisão,
sem buscar alterações posteriores.

Essa revisão instala o comando atual `desembaraca-twine`. Use o caminho da venv
para executar de qualquer pasta, sem alterar o PATH:

```powershell
& "$HOME\.venvs\desembaraca-twine\Scripts\desembaraca-twine.exe" 'C:\Grafos\história.twee'
```

A chamada por módulo funciona nessa revisão sem adicionar `Scripts` ao PATH:

```powershell
& "$HOME\.venvs\desembaraca-twine\Scripts\python.exe" -m twine_edge_overlap 'C:\Grafos\história.twee'
```

As opções `--prepare-runtime` e `--repair-runtime` também estão disponíveis.
Graphviz é obtido na primeira preparação e reutilizado offline depois. Essa revisão contém o catálogo completo com os sete artefatos e a matriz ABI qualificada.

### Resultado e limites

#### Linux e macOS: estado da implementação

O pacote seleciona o runtime pela ABI e arquitetura, verifica o download HTTPS e
prepara um cache privado. Com CPython **3.12 ou 3.14 nativo**, incluindo venv/pip,
instale sem alterar o Python do sistema ou exigir Git/Graphviz:

```sh
python3.12 -m venv "$HOME/.venvs/desembaraca-twine"
"$HOME/.venvs/desembaraca-twine/bin/python" -m pip install "https://github.com/Extremois/desembaraca-twine/archive/53fb2aba47d78b5cb4a6679cafaaef5fc5e52c29.zip"
"$HOME/.venvs/desembaraca-twine/bin/desembaraca-twine" --help
"$HOME/.venvs/desembaraca-twine/bin/python" -m twine_edge_overlap --help
```

Troque `python3.12` por `python3.14` para usar essa versão. Confirme a versão com
`python3.12 --version`; o interpretador escolhido precisa oferecer venv e pip.
Use o caminho absoluto ao Python/console da venv para chamar de outra pasta.
Linux usa XDG_CACHE_HOME absoluto, com fallback `~/.cache`; macOS usa
`~/Library/Caches`, ambos com `DesembaracaTwine/runtimes/graphviz/` abaixo da base.
Python precisa corresponder à arquitetura nativa; Rosetta não qualifica um Mac.
No Linux, use CPython x86_64 ou aarch64 da origem indicada para sua distribuição.
No macOS 15, use CPython Intel no Mac Intel e arm64 no Apple Silicon; confira com
`python3.12 -c 'import platform; print(platform.machine())'`. Os instaladores de
[Python para macOS](https://www.python.org/downloads/macos/) são uma origem possível;
a instalação da ferramenta usa apenas a venv. Reserve 2 GiB, escrita no perfil e
na pasta da história, e filesystem que permita execução e publicação por hardlink.
Instalar o pacote requer HTTPS ao GitHub e ao índice Python. Quando houver bundle
qualificado, prepare com `--prepare-runtime` antes de ficar offline; cache saudável
não tenta rede. `--repair-runtime` requer rede e preserva a geração saudável em falha.
No macOS, mantenha as proteções normais e use somente a distribuição assinada e
notarizada quando disponível. Nenhum comando deste guia remove quarentena.
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

Os sete alvos ABI foram qualificados nos dois Pythons: 42 instalações externas
(wheel, sdist e URL remota), corpus de 13 casos, preservação, reutilização offline,
reparo, interrupção, crash e concorrência. A revisão visual do usuário em Twine
2.12.1 permanece vinculada aos hashes idênticos das seis saídas finais.
Os runtimes POSIX e fontes estão publicados em pares; o runtime Windows original
continua vindo diretamente do upstream. Veja a [matriz ABI](specs/003-add-cross-platform-support/support-matrix.md)
e os [recibos de qualificação](specs/003-add-cross-platform-support/evidence/final-paired-review-2026-10-28/qualification/summary.json).
As 69 entradas de distribuições são declarações de compatibilidade.

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

The qualified matrix covers **Linux glibc ≥ 2.27 and musl ≥ 1.2.0 on x64/ARM64, macOS ≥ 15 on Intel/ARM64, and Windows x64 (legacy Win32 runtime), with native CPython 3.12 or 3.14**. ABI qualification ran in GitHub Actions; the actual Windows Server runner is not represented as clean Windows 11 certification. The following commands show Windows usage; Linux/macOS installation is documented below.
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
python -m venv "$HOME\.venvs\desembaraca-twine"
& "$HOME\.venvs\desembaraca-twine\Scripts\python.exe" -m pip install "https://github.com/Extremois/desembaraca-twine/archive/53fb2aba47d78b5cb4a6679cafaaef5fc5e52c29.zip"
```

The URL pins a development revision already pushed to the repository. Git and
a manual checkout are not required. Installation needs internet and may download
tools from the Python package index. Reinstalling this URL keeps that revision
rather than fetching later changes.

This revision installs the current `desembaraca-twine` command. Use the venv path
from any working directory without changing PATH:

```powershell
& "$HOME\.venvs\desembaraca-twine\Scripts\desembaraca-twine.exe" 'C:\Graphs\story.twee'
```

The module invocation works on that revision without adding `Scripts` to PATH:

```powershell
& "$HOME\.venvs\desembaraca-twine\Scripts\python.exe" -m twine_edge_overlap 'C:\Graphs\story.twee'
```

Both invocations accept `--prepare-runtime` and `--repair-runtime`. Graphviz is
downloaded during initial preparation and reused offline afterwards. This remote revision includes all seven runtime artifacts and the qualified ABI matrix.

### Results and limits

#### Linux and macOS: implementation status

The package selects the runtime by ABI and architecture, verifies its HTTPS
download, and prepares a private cache. With native **CPython 3.12 or 3.14**,
including venv/pip, install without changing system Python or requiring Git/Graphviz:

```sh
python3.12 -m venv "$HOME/.venvs/desembaraca-twine"
"$HOME/.venvs/desembaraca-twine/bin/python" -m pip install "https://github.com/Extremois/desembaraca-twine/archive/53fb2aba47d78b5cb4a6679cafaaef5fc5e52c29.zip"
"$HOME/.venvs/desembaraca-twine/bin/desembaraca-twine" --help
"$HOME/.venvs/desembaraca-twine/bin/python" -m twine_edge_overlap --help
```

Replace `python3.12` with `python3.14` to use that version. Check the version with
`python3.12 --version`; the selected interpreter must provide venv and pip.
Use the absolute path to the venv Python/console from another working directory.
Linux uses absolute XDG_CACHE_HOME with `~/.cache` as fallback; macOS uses
`~/Library/Caches`, each followed by `DesembaracaTwine/runtimes/graphviz/`.
Python must match the native architecture; Rosetta does not qualify a Mac.
On Linux, use CPython x86_64 or aarch64 from the origin documented for your distribution.
On macOS 15, use Intel CPython on Intel and arm64 on Apple Silicon; check with
`python3.12 -c 'import platform; print(platform.machine())'`. The
[macOS Python installers](https://www.python.org/downloads/macos/) are one possible
origin; the tool installs only in its venv. Allow 2 GiB, write access to the profile
and story directory, and a filesystem allowing execution and hardlink publication.
Package installation needs HTTPS to GitHub and the Python package index. Once a
qualified bundle is available, use `--prepare-runtime` before going offline; a healthy
cache attempts no network access. Repair needs network access and preserves the
healthy generation on failure. On macOS, keep normal protections and use the signed,
notarized distribution when available. No command here removes quarantine.
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

All seven ABI targets were qualified on both Pythons: 42 external installations
(wheel, sdist, and immutable remote URL), a 13-case corpus, preservation, offline
reuse, repair, interruption, crash, and concurrency. The user's visual review in
Twine 2.12.1 remains bound to the identical six final output hashes.
POSIX runtimes and sources are published in pairs; the original Windows runtime
is still obtained directly from upstream. See the [ABI matrix](specs/003-add-cross-platform-support/support-matrix.md)
and [qualification receipts](specs/003-add-cross-platform-support/evidence/final-paired-review-2026-10-28/qualification/summary.json).
The 69 distribution entries are compatibility declarations.

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

This product includes software developed by the University of California,
Berkeley and its contributors.
