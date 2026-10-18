# Evidência de implementação — feature 003

## Baseline e escopo

- Branch preservada: feat/002-manage-layout-runtime; commit inicial 3ad9b6632140149a65586d2a5519687c93b8b323.
- Alterações anteriores preservadas: README.md, pyproject.toml, src/twine_edge_overlap/cli.py e specs/002-manage-layout-runtime/contracts/cli.md (renomeação do comando/instalação remota).
- Baseline em Windows 11 AMD64, CPython 3.14: `python -m unittest discover -s tests -q`, 122 testes, 41,628 s, OK. Execução com acesso autorizado ao cache do usuário; execução inicial restrita falhou antes de alterações por permissão no cache.
- O pytest não está instalado no Python padrão/ambiente de build; a suíte existente usa unittest e pôde ser executada sem instalar dependências.
- Ubuntu 26.04 LTS x86_64 / CPython 3.14.4 já existente no WSL: disponibilidade constatada; compilador/CMake não encontrados. Não foi criada VM nem instalada distribuição.
- WSL fornece evidência POSIX parcial; não aprova automaticamente Ubuntu 26.04, kernel convencional, outras distribuições ou ARM64.
- Permanecem abertas a aceitação Windows limpo e a revisão visual anteriores em [feature 002](../002-manage-layout-runtime/validation.md).

## Critérios de registro

Tarefas de código/teste só são marcadas após verificação correspondente. Builds sem fonte/hash/toolchain/avisos e plataformas sem ensaio real permanecem pendentes. Metadados de alvo não significam suporte entregue.

Os registros por alvo seguem [evidence/README.md](evidence/README.md). Nenhum ensaio simulado, container ou WSL é convertido em aprovação de outro SO/arquitetura. Não publicar histórias privadas, inventário do usuário, credenciais ou caminhos pessoais.

## Implementação verificada em 2026-10-17

T001–T021 concluídas: registro de 69 SupportTargets/138 slots Python, formato de
evidência, workflow de fundação, detecção local, catálogo empacotado, seleção ABI,
cache Windows/XDG/macOS, lock do SO, contexto privado, schema 2 POSIX e adaptador
Windows schema 1. O provedor continua resolvido uma vez por operação; classificação
local consome o orçamento de processamento, aquisição tem orçamento separado.

O cache POSIX valida propriedade, links, modos 0644/0755 e cria diretórios 0700 e
registros 0600 mesmo com umask 000. Hashes/modos e probe precedem ready/seletor;
seleção atômica e fsync de diretórios preservam a geração anterior em falha. Não
foi introduzida coleta de gerações nem seleção de Graphviz global. Arquivo e
identidade Windows permanecem idênticos ao commit base. Detecção Windows usa
IsWow64Process2; tradução e Windows Server não viram Windows 11 x64 validado.

Rolling usa duas consultas locais limitadas e hash canônico de inventário completo;
pacote/canal/kernel diferentes retiram a correspondência. Falha/desconhecimento
resulta em melhor esforço quando existir artefato ABI compatível. Um gate conhecido
como falho não é apagado pela união com outro registro positivo. Testes dessa
política são sintéticos e não aprovam nenhuma célula.

| Execução | Resultado | Limite da evidência |
|---|---|---|
| Windows 11 AMD64 / CPython 3.14.6, suíte completa | 152 testes, 55,532 s, OK, 3 skips | Skips são POSIX; não qualificam POSIX |
| Windows 11 AMD64 / CPython 3.12.10, suíte completa | 152 testes, 55,723 s, OK, 3 skips | Interpretador embutido usado nos testes; instalação limpa continua pendente |
| Ubuntu 26.04 x86_64 WSL / CPython 3.14.4, fundação antes do caso umask | 79 testes, 51,833 s, OK, 5 skips | Skips Windows; não é aceitação de kernel/distribuição nativa |
| Ubuntu WSL, fundação final após correção de umask | 80 testes, 54,151 s, OK, 5 skips | Inclui crash/concorrência com schema POSIX; mesmos limites WSL |
| Cache POSIX com umask 000, após correção | 4 testes POSIX, 2,272 s, OK | Payload controlado, sem qualificação de motor |
| Wheel/sdist finais e instalação do wheel em venv fora do checkout / Windows 3.14.6 | OK, help por console/módulo e prepare com cache existente | Não é instalação remota/limpa, instalação isolada do sdist ou qualificação POSIX; [hashes e verificações](evidence/package-smoke.json) |
| compileall de src/tests/tools/runtime e git diff --check | OK | Verificação estática local |

Resultados Windows, inventário SHA-256 da revisão de código não commitada,
preservação exata do manifesto/notices e duas resoluções do cache sem abertura
de rede estão em [windows-regression.json](evidence/windows-regression.json).
Testes de aquisição/recuperação incluem transportes controlados e executáveis
Windows reais verificados; não representam nova qualificação do ZIP upstream.
T064 foi concluída com essa regressão; T065 permanece aberta. Nesse checkpoint,
22 das 84 tarefas estavam verificadas e 62 continuavam abertas. O checkpoint
mais recente está registrado abaixo.

O wheel/sdist contém catálogo, matriz e os 29 arquivos de avisos/fontes existentes,
sem executáveis/bibliotecas de todas as plataformas. Artefatos temporários de
empacotamento não foram publicados. O workflow foi criado, mas não executado em CI
remoto nesta sessão. A CLI continua `desembaraca-twine`.

## Build Linux experimental e ABI

Com autorização, foram instaladas ferramentas de desenvolvimento na distribuição
WSL já existente: GCC/G++ 15.2, CMake 4.2.3, pkg-config, Bison e Flex. Não foi
instalado Graphviz global nem criada VM/distribuição. O SDK de desenvolvimento não
é o SDK baseline prometido para distribuição.

Fonte oficial Graphviz 16.1.0: SHA-256
`1e028b2b3e84e946c1d3e8c47590f8f0741bba1041fe6eff36eee87e598ea249`,
41.189.481 bytes; revisão `e41c710710be080ad37af1b51c6e2f8beffa9ee5`.
O arquivo-fonte e COPYING foram conferidos antes de extração/build. Receitas para
as seis variantes e ferramentas estão descritas em [tools/runtime](../../tools/runtime/README.md).

O build glibc x86_64 foi concluído com bibliotecas internas Graphviz estáticas e
sem raster/fontes/bindings opcionais. Descoberta de bindings/PATH interop causou
problemas iniciais de configuração; as receitas agora desabilitam bindings e usam
PATH explícito do SDK. Diretórios em /tmp não sobreviveram ao ciclo da sessão WSL;
o build e o corpus finais usaram /var/tmp. Esses incidentes não foram convertidos
em evidência positiva de qualificação.

O [relatório do corpus WSL](evidence/linux-wsl-smoke.json), produzido por
`tools/runtime/smoke-corpus.py`, registra hashes de 13 entradas/saídas, preservação
e métricas. As seis referências conhecidas terminaram em `(0,0,0)`; nenhuma das
três contagens aumentou nos demais casos. Executável real foi relocado para caminho
com espaços e acento. Consultas DNS/socket Python foram bloqueadas; não houve
traçamento de syscalls do processo nativo, portanto não se afirma observação
completa de rede nativa.

NEEDED observado: `libm.so.6` e `libc.so.6`; maior símbolo observado: **GLIBC_2.38**.
O artefato não satisfaz o baseline Ubuntu 18.04. O build não entra no catálogo e
não concede suporte a Ubuntu 26.04 ou outra célula. Licenças/fontes de dependências
incorporadas, mínimos de kernel/CPU, SDK antigo, assinatura e qualificação completa
permanecem gates próprios. A ferramenta de inspeção vincula aprovação aos bytes da
proveniência/fontes/notices e recusa inventário/dependências não declarados; sua
existência não equivale a uma auditoria aprovada para qualquer bundle POSIX.

## Pendências que impedem a entrega completa

- O catálogo ativo contém somente o artefato Windows legado. Os 69 alvos e seus
  138 slots novos continuam pendentes; nenhum foi promovido por mock/WSL/skip.
- T024–T031: receitas candidatas existem, mas faltam SDK glibc antigo, builds
  ARM64/musl, medições, auditorias e URLs HTTPS imutáveis de bundles qualificados.
- T049–T052/T056: não há host macOS Intel/Apple Silicon, SDK e credenciais de
  assinatura/notarização disponíveis nesta sessão. Não foi usado bypass.
- O checkpoint abaixo acrescenta contratos, workflows, harness, promoção por
  célula e diagnósticos. A execução nativa e a documentação de distribuição
  ainda têm tarefas abertas em [tasks.md](tasks.md); ferramentas implementadas
  não substituem os ensaios de aceitação.
- A matriz inteira exige ambos os Pythons por célula, instalação externa/primeiro
  uso/offline, rastreamento de rede nativa, falhas/crash/concorrência, fontes/notices
  e reabertura real das seis saídas no Twine. Ambientes ausentes permanecem abertos.
- Windows limpo e revisão visual Twine anteriores permanecem pendentes. Esta
  execução usa o sistema atual autorizado, sem criar VM, trocar branch ou publicar.

O README PT/EN distingue implementação em andamento da matriz entregue. Este é
um incremento da fundação, não encerramento da feature ou anúncio de Linux/macOS.

## Continuação: contratos e ferramentas de qualificação (2026-10-18)

O estado atual é **46/84 tarefas concluídas, 38 pendentes**. O
[ledger de suporte](evidence/support-ledger.md) relaciona as 69 células, seus
138 slots Python e os 28 requisitos FR/SC às tarefas e evidências. Todos os
novos alvos continuam pendentes; o catálogo público permanece somente Windows.

Foram implementados contratos Linux/macOS, diagnósticos de execução, publicação
concorrente sem sobrescrita, recuperação/crash e preservação dos resultados.
A classificação distingue a variante AlmaLinux x86-64-v2 por consulta limitada
ao pacote de release; uma variante desconhecida não herda aprovação de outra.
Gates comuns são restritos a licenças/Twine e não substituem os ensaios dos dois
Pythons. A aquisição continua usando o motor privado, sem Graphviz global.

As ferramentas de manutenção agora coletam evidência de um pacote instalado
fora do checkout, conferem integridade de logs e propõem promoção somente com
os gates completos. Foram criados workflows manuais para runners nativos já
configurados, drivers de aceitação opt-in e um procedimento macOS de assinatura/
notarização. Esses workflows não foram executados remotamente. Assinatura e
notarização não foram executadas: somente sintaxe e recusas de ambiente foram
ensaiadas. Nenhuma célula real foi promovida pelas ferramentas ou seus testes.

| Execução | Resultado | Limite da evidência |
|---|---|---|
| Windows atual / CPython 3.14.6 | 182 testes, 32,402 s, OK, 8 skips | Quatro drivers nativos Linux/macOS e quatro casos POSIX não executados |
| Windows atual / CPython 3.12.10 | 182 testes, 32,959 s, OK, 8 skips | Mesmos limites; não equivale a instalação Windows limpa |
| Ubuntu 26.04 WSL existente / CPython 3.14.4 | Fundação: 106 testes, 33,913 s, OK, 5 skips | Não qualifica uma distribuição/kernel nativos |
| Wheel instalado em venv externo / Windows 3.14.6 | Primeiro uso real, aquisição em cache isolado, preparo repetido e corpus de 13 casos: OK | Fonte não commitada; instalação remota/sdist, rastreamento nativo de rede e revisão Twine pendentes |
| Corpus de referência / Windows 3.12 e 3.14 | 13 casos por Python; preservação e métricas verificadas | Comparação semântica e geométrica; não é revisão visual |
| Workflows YAML, wrapper de assinatura e compileall | Parse/sintaxe: OK | Não são execução CI, build macOS ou notarização |

Os resultados e a identificação do código estão em
[continuation-regression.json](evidence/continuation-regression.json).
O [relatório do pacote](evidence/windows-package-harness.json) referencia o log
redigido e seu SHA-256. Os relatórios
[Python 3.12](evidence/windows-reference-python312.json) e
[Python 3.14](evidence/windows-reference-python314.json) registram hashes e métricas
do corpus. Ajustes posteriores de expectativas para caminhos canônicos foram
verificados por testes direcionados; não representam nova execução macOS.

T023/T048 têm drivers implementados, mas continuam abertas sem execução POSIX
nativa. No WSL existente, a checagem encontrou ausência de venv/ensurepip e de
Python 3.12 nos locais padrão; não instalou SDK adicional nem concluiu T033.
T035/T055 permanecem parciais enquanto faltarem bundles e URLs POSIX reais.
T051 permanece aberta sem assinatura/notarização nativas. Builds antigos/ARM64/
musl, auditorias e a matriz completa ainda exigem os ambientes correspondentes.

A tentativa de listar aplicativos para revisão Twine retornou
`Computer Use native pipe is unavailable` (arquivo de pipe ausente). Nenhuma
história foi importada ou revisada visualmente por essa tentativa. T063/T065 e
as pendências anteriores de revisão visual permanecem abertas. Não houve criação
de VM, troca de branch, commit, push ou publicação nesta continuação.

## Retenção das saídas de revisão e auditoria local

O coletor agora aceita `--review-output` para exportar as seis saídas públicas
antes de encerrar o ambiente temporário. Confere cada SHA-256 contra o corpus,
recusa sobrescrita/links/ausência/adulteração e gera manifesto com a identidade do
ensaio. Os workflows guardam esses arquivos junto dos logs. A revisão visual
permanece `pending`; não se copia o cache nem o inventário completo para esse
diretório. O quickstart descreve a revisão em biblioteca de teste isolada.

O percurso real foi repetido no Windows atual com o wheel local em venv externa,
cache inicialmente isolado e Graphviz oficial: 13 casos passaram. As seis saídas
retidas estão em [windows-review-003](evidence/windows-review-003/manifest.json),
com identidade e hashes; o
[registro da coleta](evidence/windows-review-collection.json) referencia o log
redigido e seu SHA-256. São referências públicas, com IFID compartilhado: não
importá-las sobre histórias de uma biblioteca pessoal. Nenhuma foi revisada
visualmente nesta execução, e a fonte não commitada impede promoção de suporte.

A [auditoria local de limites](evidence/security-limits.json) registra a inspeção
do código de download, cache, runner, classificação, parser e publicação, além dos
novos contratos de privacidade. Inclui subprocessos reais para timeout e teto
combinado de 8 MiB, requisição GET fixa sem corpo, orçamento de probe, preparo
expirado sem aquisição, identidade limitada, ambiente filho filtrado e DOT sem
títulos/texto da história. Transportes/probes controlados continuam identificados
como tais. Não equivale a rastreamento de rede do motor nativo.

Após as alterações, `tests/run_foundation.py` passou com **115 testes** em cada
execução: Windows CPython 3.14.6 (20,488 s, 4 skips), Windows CPython 3.12.10
(19,969 s, 4 skips) e Ubuntu WSL CPython 3.14.4 (34,595 s, 5 skips). Essa é a suíte
de fundação, não uma repetição da suíte completa de 182 testes do checkpoint
anterior. Os skips não aprovam os respectivos ambientes. Os novos testes de
exportação falharam pela ausência da função antes de sua implementação e passaram
após a mudança.

T080 tem agora a auditoria local do código, mas continua aberta para fechamento
com os pacotes e percursos finais exigidos pelas dependências. T063/T065/T079 e
os gates nativos permanecem pendentes. O total continua **46/84 tarefas**, com
38 abertas; nenhum alvo foi promovido. Não houve instalação de SDK, criação de
VM, execução remota de CI, commit ou push nesta execução.

## Inspeção sem URL e correção do RUNPATH experimental

`verify-artifact.py` agora cria e lê inventário local de candidata, separado do
manifesto de distribuição. O inventário vincula os bytes exatos da proveniência,
executável e demais arquivos com SHA/tamanho/modo, sem URL ou entrada de catálogo.
Recusa links, modos inseguros, alteração de identidade/proveniência e limites
excedidos. A inspeção por inventário mantém a auditoria revisada obrigatória e as
verificações de dependências, arquitetura/ABI e assinatura aplicável antes do
probe. O modo por manifesto continua disponível. Ver o
[procedimento do mantenedor](../../tools/runtime/README.md).

O ensaio inicial com o binário WSL existente encontrou RUNPATH com componentes
vazios, antes de alcançar a recusa por glibc antiga. O resultado não foi convertido
em inspeção aprovada. As seis receitas estáticas passaram a usar
`CMAKE_SKIP_RPATH=ON`. Um novo build glibc x86_64, feito offline com fonte e SDK já
existentes em diretório novo, não contém RPATH/RUNPATH. O executável tem SHA-256
`1e9633e9b36e337a5832565a50554bf1b3271e7791deebef6efdae4e073a0a73`.

O [inventário real](evidence/linux-wsl-candidate-inventory.json) registra dois
arquivos. O [relatório do pipeline](evidence/local-inventory-smoke.json) vincula
inventário/proveniência e log redigido, registra `libm.so.6`/`libc.so.6`, ausência de
RPATH e maior símbolo **GLIBC_2.38**. O verificador recusou corretamente o baseline
2.27 e a inspeção sem auditoria. Medição de dependências não é auditoria jurídica
nem qualificação do artefato; nenhum manifesto público foi ativado.

O [novo corpus WSL](evidence/linux-wsl-no-rpath-corpus.json) passou 13 casos, com as
seis referências em `(0,0,0)`, originais/semântica preservados e nenhuma métrica
aumentada. Inclui relocação com espaços/acentos e zero chamadas DNS/socket Python.
Não houve rastreamento de syscalls nativas de rede, instalação do bundle pelo
runtime normal ou revisão Twine. A build antiga foi preservada.

Os três novos testes de inventário falharam por funcionalidade ausente antes da
implementação. Depois, os oito testes da ferramenta passaram no WSL; os dois
casos de filesystem POSIX são skips no Windows. A fundação completa passou com
**118 testes** por execução: Windows/Python 3.14.6 (18,530 s, 6 skips),
Windows/Python 3.12.10 (18,127 s, 6 skips), WSL/Python 3.14.4 (35,733 s, 5 skips).
Testes de inspeção positiva usam bytes/runner/auditoria explicitamente sintéticos;
não foram persistidos como aprovação de um bundle real.

T024–T031/T049–T052 continuam abertas: falta cumprir baseline, demais builds,
auditorias, URLs e os próprios gates nativos. O total permanece **46/84 tarefas**,
com 38 pendentes e todos os novos alvos sem promoção. Não foi instalado novo SDK,
criada VM, alterada branch, executado CI remoto ou publicado artefato.

## Empacotamento do ZIP candidato

Foi implementado `tools/runtime/pack-candidate.py`, que transforma o inventário
local e a árvore exata do build em ZIP candidato, sem URL, execução do motor ou
alteração do catálogo. Reutiliza a verificação da árvore do inspetor, confere
novamente tamanho/hash durante a cópia e inclui os bytes dos notices presentes.
Recusa saída existente, arquivos extras/alterados, links e ZIP acima de 128 MiB
(incluindo metadados). Preserva a cópia exata do inventário e referencia a
proveniência por hash, sem copiar seus caminhos locais para o pacote.

Os quatro testes novos falharam por funcionalidade ausente antes da implementação
e passaram depois. Cobrem bytes repetíveis, conteúdo/modos/timestamp, ausência de
rede e de mutação de ambiente/cwd, recusa de sobrescrita, mudança durante a cópia
e limite incluindo overhead ZIP. O hash da árvore também passou a ter leitura
limitada pelo tamanho inventariado. A inspeção nativa mantém seus gates e a
checagem de modos; o empacotamento de uma cópia no Windows registra explicitamente
a impossibilidade de medir seus modos POSIX.

Dois ZIPs reais do build WSL sem RPATH foram produzidos em diretórios novos e
conferidos arquivo a arquivo. Ambos têm **1.584.834 bytes**, dois arquivos e SHA-256
`423781270cbc8a2237f9893e78b19688aa5945ab6c85f2aca4eb8f93d4bd94c4`.
O teste de saída já existente falhou como esperado, preservando o ZIP anterior.
Os binários/ZIPs ficaram somente no ambiente local; a evidência pública contém
metadados em [candidate-packaging-smoke.json](evidence/candidate-packaging-smoke.json).
O empacotamento não executou o binário nem fez download de componentes.

A suíte `tests/run_foundation.py` passou com **122 testes** em cada execução:
Windows/Python 3.14.6 (21,020 s, 6 skips), Windows/Python 3.12.10 (20,672 s,
6 skips), WSL/Python 3.14.4 (36,897 s, 5 skips). São ensaios da fundação e de
ferramentas; skips, mocks e WSL não aprovam células nativas ausentes.

T028/T031/T052 continuam abertas: o ZIP é candidato não qualificado. O build
continua exigindo símbolos GLIBC_2.38 e faltam auditorias, baseline antigo,
outras arquiteturas/ABIs, assinatura macOS, URL real e aceitação por célula.
O estado permanece **46/84 tarefas**, com 38 pendentes. Não houve criação de VM,
instalação de SDK, mudança de branch, commit, push ou publicação.

## Entradas estáticas do linker e cobertura da auditoria Linux

O build passou a registrar na proveniência os hashes do comando de linkedição,
da regra de dependências GNU ld e das entradas reais do linker. A leitura é
limitada e não executa expressões make/shell. Mantém contagem de referências
repetidas e hashes de entradas distintas; ausência de metadados fica explícita.
Isso complementa `NEEDED`, que não expõe os arquivos estáticos lidos.

O inspetor Linux agora exige que a auditoria identifique cobertura dos arquivos
`.a`/`.o` em `components[].link_input_sha256`, vinculada ao executável e à mesma
proveniência. Sem metadados ou cobertura de fontes/notices, não aprova inspeção.
A validação permanece decisão do revisor: ler um arquivo estático não prova quais
membros foram incorporados nem determina sua licença. A fonte Graphviz continua
fixada; a revisão de seus subcomponentes também permanece pendente.

Um novo build offline no WSL, usando somente fonte e SDK existentes, registrou
**74 entradas**, incluindo nove arquivos estáticos do SDK: `libstdc++.a`,
`libgcc.a`, `libgcc_eh.a`, `libc_nonshared.a` e cinco objetos de inicialização.
O executável desse build tem SHA-256
`b9b16ddaddd87e2b855a259a6d2d6b49c4e7649bd43a6f87d0dc67ddbbc655b1`.
Seu [relatório de linkedição](evidence/linux-linkage-capture.json) contém os hashes
e referencia o log redigido. Os caminhos absolutos do SDK foram retirados da
representação pública. Os builds/relatórios anteriores foram preservados.

Foi criado o [ledger Linux de licenças](../../tools/runtime/licenses/linux.json)
com as quatro variantes explicitamente pendentes, incluindo hashes reais das
nove entradas SDK observadas na variante experimental. Não há auditoria aprovada,
fonte/notice inventados, inclusão desses componentes no pacote público ou nova
qualificação. O executável novo não foi submetido ao corpus/aceitação nativa;
os ensaios de corpus anteriores continuam ligados aos seus próprios hashes.

Os quatro contratos novos falharam por funcionalidade ausente antes da mudança e
passaram depois, incluindo recusa de auditoria sem cobertura dos runtimes. A
fundação passou com **126 testes** em cada execução: Windows/Python 3.14.6
(22,758 s, 6 skips), Windows/Python 3.12.10 (22,434 s, 6 skips), WSL/Python 3.14.4
(41,243 s, 5 skips). A inspeção positiva em unitários usa dados/runner/auditoria
explicitamente sintéticos, sem promover alvos.

T030 continua parcial, pois fontes correspondentes, notices e compatibilidade
não foram revisados para todas as entradas/variantes. O total permanece
**46/84 tarefas**, com 38 abertas. Não houve instalação de SDK, criação de VM,
troca de branch, commit, push ou publicação.

## CPython privado e experimento de baseline glibc

Foram obtidos e verificados CPython **3.12.15** e **3.14.8** da distribuição
python-build-standalone 20261003, em diretórios privados no WSL existente. As
venvs, pip/ensurepip, SSL e módulos padrão foram executados; o hash do Python do
sistema permaneceu igual. A fundação passou com **126 testes** em cada um:
3.12.15 em 33,171 s e 3.14.8 em 32,901 s, ambos com cinco skips. As origens,
hashes e limites constam em [linux-prerequisites.md](evidence/linux-prerequisites.md).

Wheel e sdist da árvore atual foram construídos e instalados em quatro venvs
externas, dois formatos × dois Pythons. Console/módulo, importação da venv,
caminhos com espaço/acento e presença da licença passaram; os 29 notices do
wheel foram conferidos. O processamento POSIX foi recusado com código 1,
preservando o original e sem aquisição de cache, porque o catálogo continua
somente Windows. Isso verifica instalação e recusa esperada, sem aprovar o
primeiro uso Linux. O ensaio sdist usou cache pip de usuário existente; futuras
repetições devem fixar `PIP_CACHE_DIR` privado. Ver os
[quatro ensaios](evidence/linux-package-installation.json).

Também foi obtida privadamente a toolchain Zig **0.15.2**, com arquivo e SHA
fixados. O experimento usou alvo `x86_64-linux-gnu.2.27`, CPU `baseline` e
wrappers registrados por hash. Eles traduzem somente as opções GCC de CPU da
receita e configuram `MATH_LIB=m`, resolvido pelo linker do alvo. Três tentativas
falharam antes do build completo: duas por sintaxe de CPU e uma por descoberta
de libm. A receita compartilhada permaneceu com suas opções originais.

A quarta tentativa compilou Graphviz 16.1.0, produzindo SHA-256
`97347dcf491874804d063acf48f78d323b28af896a8008f8f8f4cd72de602c4c`.
`readelf` mediu símbolo máximo **GLIBC_2.14**, ausência de RPATH/RUNPATH,
loader `/lib64/ld-linux-x86-64.so.2` e dependências `libm.so.6`,
`libpthread.so.0`, `libc.so.6`, `ld-linux-x86-64.so.2`. O verificador recusou a
última dependência, ausente da lista experimental aprovada; essa lista não foi
relaxada. A nota ELF Linux ABI 2.0.0 não prova kernel mínimo utilizável.

O mesmo binário passou pelos **13 casos públicos e relocação** com Python
3.12.15 e 3.14.8. Os seis casos conhecidos terminaram sem conflitos, com
preservação dos originais e sem regressão das métricas. Ver
[build/inspeção](evidence/linux-zig-baseline.json),
[corpus 3.12](evidence/linux-zig-corpus-3.12.json) e
[corpus 3.14](evidence/linux-zig-corpus-3.14.json). O bloqueio de rede nesses
ensaios é somente Python, sem trace nativo.

São evidências experimentais: faltam captura equivalente das entradas do
linker, fontes/licenças dos runtimes LLVM, inspeção aprovada e execução nos
baselines antigos, kernel/hardware e células nativas. T024/T028/T030/T033/T078
permanecem parciais. O total continua **46/84**, com 38 tarefas abertas.
Não houve VM, substituição de Python do SO, instalação global, alteração de
catálogo, commit, push ou publicação. Os SDKs privados foram obtidos com
autorização; os checkpoints anteriores registram seus próprios estados históricos.

## Captura LLD e alvo explícito de kernel

Um novo build privado fixou `x86_64-linux.4.15-gnu.2.27` e CPU `baseline`.
A saída detalhada do probe anterior revelou Linux 5.10 como alvo padrão do
compilador: os símbolos glibc baixos, isoladamente, não cobriam essa diferença.
O alvo 4.15 é configuração de compilação, sem prova de execução no kernel mínimo.
Nenhuma célula foi aprovada por essa alteração.

Foi adicionada [relink-zig.py](../../tools/runtime/relink-zig.py), ferramenta
explícita do mantenedor para resolver a recusa de `--dependency-file` pelo
driver Zig 0.15.2. Confere hashes do wrapper/SDK e executável original, usa a
linha gerada pelo CMake como argumentos sem shell, cria referência com o driver
e faz a linkedição final com o LLD direto, habilitando o arquivo de dependências.
Exige igualdade de bytes com a referência antes de registrar o novo candidato.
Os builds anteriores permanecem intactos e diretórios existentes são recusados.

O ensaio real registrou **73 entradas** lidas pelo linker, incluindo seis
entradas estáticas do SDK: `crt1.o`, `libcompiler_rt.a`, `libc_nonshared.a`,
`libc++.a`, `libc++abi.a`, `libunwind.a`. A captura em etapa separada preserva o
escopo dos objetos/bibliotecas Graphviz do build pai. Arquivos lidos não provam
os membros incorporados de cada arquivo estático. Foram observados 11 arquivos
de licença no SDK; seus hashes foram registrados sem declarar que todos são
pertinentes ou que constituem auditoria aprovada.

O executável tem SHA-256
`beaa54239cc77d98840aedf73b94e5e14407ab5f32acd893cedd3c37fb2f76f6`,
idêntico à referência do driver e ao build pai com alvo 4.15. Duas saídas
independentes de relink produziram esse mesmo hash; a segunda inclui a separação
correta dos escopos. Mediu-se **GLIBC_2.14**, loader x86_64 padrão e ausência de
RPATH/RUNPATH. O corpus completo e relocação passaram com CPython 3.12.15 e
3.14.8, preservando originais e zerando os seis casos conhecidos. Esses ensaios
foram feitos com a primeira saída; os relatórios vinculam os mesmos bytes à
saída final. Ver [captura e logs](evidence/linux-zig-lld-capture.json),
[corpus 3.12](evidence/linux-zig-lld-corpus-3.12.json) e
[corpus 3.14](evidence/linux-zig-lld-corpus-3.14.json).

Cinco testes novos cobrem validação de argumentos/saída, caminhos com espaços,
recusa fora do Linux, recusa de bytes diferentes sem substituir o original e
escopo do build pai. A fundação passou com **131 testes**: Windows/Python 3.14.6
(22,619 s, 6 skips), Windows/Python 3.12.10 (22,333 s, 6 skips), WSL/Python 3.14.8
(40,860 s, 5 skips). Os testes sintéticos verificam as recusas da ferramenta;
as 73 entradas e o corpus acima provêm da execução real.

O [ledger de licenças](../../tools/runtime/licenses/linux.json) ganhou um
registro experimental independente com hashes reais das entradas SDK e dos
arquivos de licença observados. Continua `approved: false`; não houve expansão
da lista de bibliotecas aprovada ou inspeção final aprovada. T024/T028/T030
continuam parciais até auditoria e ensaios nos ambientes de destino. O total
permanece **46/84 tarefas**, sem VM, instalação global, catálogo novo, commit,
push ou publicação.

### Continuação: avisos independentes do candidato musl x86_64

`prepare-draft-notices.py` passou a aceitar o build musl x86_64 medido como
estático. Antes da cópia exige fatos coerentes do SDK, os quatro resultados da
inspeção ELF, hash do relatório e conteúdo sem interpreter/seção dinâmica/NEEDED/
símbolos GLIBC. Preserva o relatório na saída. Seleciona COPYRIGHT musl integral
do arquivo SDK fixado, sem incorporar automaticamente LICENSES glibc.

Dois testes novos demonstraram a ausência inicial do percurso e passaram após
a implementação. Cobrem seleção por variante, recusa de variante não prevista,
SDK incompatível, medição ausente, relatório alterado e conteúdo dinâmico mesmo
com hash atualizado. A chamada inicial de descoberta com raiz `tests/unit`
falhou por não localizar `common`; a execução correta usa a raiz `tests`.

O ensaio real criou uma saída nova e conferiu novamente 58 headers do SDK e
nove arquivos gerados. Os 14 avisos/referências preservam bytes originais,
prefixos completos ColorBrewer/Bison e modo 0644. O dot manteve modo 0755 e SHA
`a58b2f30b70a0393ff0cec93d40e7b039015d1ad2bbdc8a9c60634334519942f`,
idêntico ao build e relink originais. A nova proveniência tem SHA
`daba2f9a893a98f746a101cd3de7d07261b3af51e076690bdbb60891c5055a03`.
Os avisos públicos e recibos privados têm seus hashes conferidos. Ver
[relatório do rascunho musl](evidence/linux-musl-notice-draft.json).

O COPYRIGHT musl também aponta termos específicos por arquivo. Libzigc e
compiler_rt aparecem nas extrações observadas; não foram presumidos ausentes.
A preparação não conclui aplicabilidade por arquivo, fontes correspondentes,
geradores/dados, auditoria revisada ou aceitação Alpine. Não foi criado ZIP ou
inventário com versão musl inferida ou baseline ainda não qualificada. O ledger
registra esse candidato separadamente, com approved/qualified false.

Fundação: **147 testes**, Windows/Python 3.14.6 (21,009 s, 6 skips),
Windows/Python 3.12.10 (19,599 s, 6 skips) e WSL/Python 3.14.8 (42,271 s,
5 skips). Skips não qualificam ambiente nativo. T026/T029/T030 permanecem
parciais e o total continua **46/84**, sem VM, instalação global ou publicação.

## Candidata local com avisos próprios do build

Foi adicionada `tools/runtime/prepare-draft-notices.py` para preparar um novo
diretório de candidata a partir do relink e de sua evidência privada de fontes.
Confere proveniências, executável e arquivos originais fixados antes de copiar.
Os **162 headers externos** foram comparados com seus bytes no arquivo SDK
original, além da conferência dos **nove arquivos gerados** contra a evidência.
Isso completa a conferência de integridade desses headers específicos, sem
substituir a revisão de suas licenças e includes transitivos.

A revisão dos gerados identificou licença/atribuição ColorBrewer no início de
`lib/common/brewer_colors`, fora dos arquivos nomeados LICENSE/COPYING. Esse
prefixo foi preservado integralmente. Os quatro arquivos Bison contêm GPL e
uma exceção no próprio prefixo gerado; ambos foram preservados como bytes dos
arquivos conferidos. A declaração de versão observada é Bison 3.8.2; o scanner
registra Flex 2.6.4. As receitas registradas também mostram origens W3C dos
dados HTML/SVG, cuja aplicabilidade dos avisos segue em revisão. Não se deduz
compatibilidade final apenas por encontrar esses textos.

A candidata nova tem **14 arquivos de avisos/referências** mais `bin/dot`.
Inclui textos Graphviz/SDK selecionados de seus arquivos originais e referências
de fonte explicitamente identificadas como rascunho. O executável mantém SHA-256
`beaa54239cc77d98840aedf73b94e5e14407ab5f32acd893cedd3c37fb2f76f6`;
avisos têm modo 0644 e o executável 0755 no filesystem POSIX.

O inventário foi conferido e um ZIP local de **6.155.410 bytes/15 arquivos** foi
produzido, com SHA-256
`b9e889f911663ffb68d03b2f787684f8c2431ab3ce3f3ecb61f240e0dab6c249`.
Cada payload do ZIP foi comparado ao inventário. O inspetor recusou `review.json`
como auditoria revisada, retornando código 1 com `Reviewed audit must bind the
exact build provenance`. O rascunho não possui aprovação/revisor nem o vínculo
exigido para uma auditoria admissível; inventariar ou empacotar não o aprova.
Ver [avisos, hashes e log](evidence/linux-notice-draft.json).

Uma cópia idêntica para revisão local no Windows foi colocada em
`tools/runtime/artifacts/linux-glibc/linux-glibc-x86_64-notice-draft/`, pasta
ignorada pelo Git. Contém ZIP, inventário, resumo, proveniência e revisão. Os
originais privados WSL foram preservados; não houve extração como runtime Windows.

Três contratos cobrem preservação dos prefixos completos, recusa de exceção
Bison incompleta e recusa de arquivo-fonte alterado antes de criar candidata.
Os dois contratos iniciais falharam antes da implementação e passaram depois.
A fundação passou com **140 testes**: Windows/Python 3.14.6 (19,452 s, 6 skips),
Windows/Python 3.12.10 (19,188 s, 6 skips), WSL/Python 3.12.15 (35,649 s,
5 skips). Não foi necessário repetir o corpus para o executável inalterado.

O ledger registra a candidata com `approved: false`. Faltam decisões de
aplicabilidade dos avisos, origem/termos dos dados, oferta completa das fontes,
auditoria final e aceitação nativa dos ambientes de destino. T030 continua
parcial e o total permanece **46/84 tarefas**. Não houve VM, instalação global,
catálogo novo, commit, push ou publicação.

## Primeiro build musl x86_64 estático

As receitas musl passaram a declarar `-static`. O mantenedor pode executar um
experimento Linux glibc → musl na mesma arquitetura somente com
`--cross-libc-experiment --execute`. O padrão continua recusando famílias libc
diferentes. A opção exige fatos explícitos de alvo estático no SDK e hash do
inspetor ELF, mantendo as recusas de OS/arquitetura divergentes e tradução.
A proveniência identifica o modo experimental, a família/versão libc do host,
o alvo e o kernel; nenhuma máquina ou distro nova foi criada.

Antes de concluir o build, são verificados arquitetura ELF, ausência de
interpreter, seção dinâmica, NEEDED e símbolos GLIBC. O inspetor de candidatas
também exige essa medição quando a receita musl declara `-static`; uma lista
vazia de bibliotecas só é aceita sob a política estática explícita. A auditoria
revisada continua obrigatória. Isso não converte o ensaio em aceite Alpine.

Foi construída uma variante real com alvo `x86_64-linux.4.15-musl`, CPU
`baseline` e a toolchain privada Zig 0.15.2 já existente. O probe C++ estático
executou, e Graphviz 16.1.0 compilou com SHA-256
`a58b2f30b70a0393ff0cec93d40e7b039015d1ad2bbdc8a9c60634334519942f`.
O relink registrou **66 entradas**, **324 extrações** e produziu bytes idênticos
à referência do driver e ao build pai. A nova inspeção confirmou o ELF
totalmente estático. Os limites configurados de kernel/CPU continuam sem
execução no hardware/kernel mínimos.

O corpus completo e relocação passaram com **CPython 3.12.15 e 3.14.8**:
13 casos em cada, preservação dos originais, métricas sem regressão e os seis
casos conhecidos zerados. Não houve GLIBC observada ou bibliotecas dinâmicas
NEEDED. Os Pythons desses ensaios pertencem ao host glibc; não são instalações
Python musl ou ensaios normais de aquisição em Alpine. O bloqueio de rede é
somente Python, sem trace nativo. Ver [build/SDK/inspeção](evidence/linux-musl-static.json),
[corpus 3.12](evidence/linux-musl-corpus-3.12.json) e
[corpus 3.14](evidence/linux-musl-corpus-3.14.json).

A correspondência de objetos/fontes foi refeita para a variante: **181 objetos,
322 fontes Graphviz, nove arquivos gerados e 58 headers externos**. Os 58
headers e **2.467 arquivos** da árvore musl distribuída pelo SDK foram comparados
ao arquivo original verificado. O manifesto completo permanece privado, com
algoritmo/digest registrados; `COPYRIGHT` musl foi copiado como evidência.
O SDK não inclui arquivo VERSION; a versão upstream foi mantida desconhecida
(`musl_version: null`), sem inventar requisito mínimo de libc do host.

Sete entradas estáticas SDK foram observadas: `crt1.o`, `libc.a`, `libzigc.a`,
`libcompiler_rt.a`, `libc++.a`, `libc++abi.a`, `libunwind.a`. Exigem auditoria
própria; avisos e auditorias glibc não foram considerados aprovação musl.
As entradas correspondentes no ledger Linux continuam pendentes.

Cinco contratos novos cobrem opção explícita e perfil estático, manutenção das
recusas de OS/arquitetura/tradução, recusa de ELF dinâmico e de relink musl sem
medição estática. Falharam antes das mudanças e passaram depois. A fundação
passou com **145 testes**: Windows/Python 3.14.6 (22,053 s, 6 skips),
Windows/Python 3.12.10 (21,579 s, 6 skips), WSL/Python 3.14.8 (40,200 s,
5 skips). O ELF positivo e o corpus vieram de execução real; os unitários não
concedem qualificação nativa.

T026/T027/T029/T030 continuam parciais: faltam ARM64, auditoria, mínimos reais
e os ambientes Alpine nativos com ambos os Pythons. O total permanece
**46/84 tarefas**. Não houve VM, instalação global, catálogo novo, commit,
push ou publicação.

## Correspondência de objetos e fontes Graphviz

Foi adicionada [audit-graphviz-sources.py](../../tools/runtime/audit-graphviz-sources.py),
ferramenta offline do mantenedor para ler os arquivos estáticos regulares como
dados, com suporte a nomes GNU/BSD e recusa de arquivos thin, truncados ou
ambíguos. Verifica metadados de linkedição/extração contra seus hashes e relê o
TSV para conferir sua correspondência com a proveniência. O vínculo de relink
com o build pai e o executável real também é verificado.

Cada membro Graphviz observado foi comparado por hash a um único objeto do
build; o coletor não deduz a fonte somente por nome. Arquivos `.o.d` são lidos
com alvo exato e sem expansão make/shell. As dependências são separadas entre
fontes do arquivo Graphviz fixado, arquivos gerados e headers externos, com
limites por arquivo e agregados. O arquivo-fonte é lido sem extração no disco.

A execução real vinculou **181 objetos**, verificou **322 fontes/headers
Graphviz** contra os bytes do arquivo-fonte e identificou **nove arquivos
gerados** e **162 headers externos**. O executável permanece com SHA-256
`beaa54239cc77d98840aedf73b94e5e14407ab5f32acd893cedd3c37fb2f76f6`,
cujos bytes já passaram no corpus/relocação com ambos os Pythons.

Os gerados incluem `grammar.c/.h`, `scan.c`, `htmlparse.c/.h`, tabelas e headers
de configuração/data. Quatro têm indicadores Bison. Headers externos incluem
identificadores SPDX próprios, como LLVM-exception e Linux-syscall-note; esses
dados demonstram por que zero extrações de uma biblioteca SDK não dispensa
revisão dos headers. Indicadores são registrados para revisão, sem conclusão
automática de aplicabilidade ou compatibilidade de licenças.

O [relatório público](evidence/linux-graphviz-source-audit.json) preserva hashes
do relatório privado e de todos os objetos/fontes/metadados. Os caminhos
privados estão redigidos; índices de dependências evitam repetições no JSON.
Três avisos candidatos foram copiados integralmente do arquivo original e
conferidos por hash: `AUTHORS`, `COPYING` e `lib/rbtree/LICENSE`. Oito nomes de
avisos foram encontrados no arquivo completo; presença no arquivo, por si só,
não decide quais devem integrar o bundle.

Quatro testes cobrem ar simples/GNU/BSD, rejeição de arquivos malformados/thin/
ambíguos, leitura de dependências sem expansão e correspondência única por bytes.
Os três contratos iniciais falharam por ausência da ferramenta antes da
implementação e passaram depois. A fundação passou com **137 testes** no
Windows/Python 3.14.6 (20,758 s, 6 skips), Windows/Python 3.12.10 (20,552 s,
6 skips), e WSL/Python 3.14.8 (35,275 s, 5 skips).

O ledger Linux referencia essa etapa com `approved: false`; a revisão dos
gerados, headers externos, avisos aplicáveis e oferta completa das fontes
continua pendente. T030 permanece parcial, assim como as demais variantes.
Total: **46/84 tarefas**, sem VM, instalação global, catálogo novo, commit,
push ou publicação.

## Fontes SDK verificadas e membros extraídos pelo LLD

O relink passou a registrar também `--why-extract`, vinculando cada linha a um
arquivo estático já identificado por hash. A leitura é somente de dados, com
limites de 8 MiB/100.000 linhas, cabeçalho TSV exato e recusa de arquivos
desconhecidos ou registros malformados. Dois testes novos falharam antes da
implementação e passaram depois. O verificador de auditorias não passou a
dispensar cobertura de arquivos estáticos por terem zero linhas.

Uma execução real em diretório novo gerou **147 linhas de extração** e manteve
o SHA do executável já ensaiado nos dois Pythons:
`beaa54239cc77d98840aedf73b94e5e14407ab5f32acd893cedd3c37fb2f76f6`.
Entre os arquivos estáticos SDK, houve duas extrações de `libc_nonshared.a`:
`fstat-2.32.o` e `elf-init-2.33.o`. Para `libc++.a`, `libc++abi.a`, `libunwind.a`
e `libcompiler_rt.a`, não houve linhas de extração nesse comando. `crt1.o` é
entrada direta. Essa medição distingue arquivos lidos e membros extraídos, sem
provar retenção de todas as seções ou ausência de código dos componentes que
tiveram zero linhas. Templates, código inline e headers transitivos continuam
exigindo revisão própria.

O arquivo original do SDK foi novamente conferido contra seu SHA-256 fixado.
Foram comparados **1.947 arquivos** distribuídos em seus diretórios glibc (297),
libc++ (1.283), libc++abi (34), libunwind (33) e compiler_rt (300), verificando
tamanho e hash dos arquivos instalados contra os bytes do arquivo verificado.
Esses recortes incluem fontes, headers e avisos; não são cópias completas dos
projetos upstream. Manifestos canônicos privados têm algoritmo e digest
registrados para reprodução a partir do arquivo SDK fixado.

As fontes selecionadas para revisão incluem os três arquivos declarados pelo
SDK para startup (`start-2.33.S`, `abi-note.S`, `init.c`), as fontes correspondentes
aos dois membros glibc observados e a raiz `compiler_rt.zig`. Cinco arquivos de
aviso foram copiados integralmente para a pasta de evidência e conferidos por
hash: licença raiz Zig, `glibc/LICENSES` e os três `LICENSE.TXT` LLVM. Isso
prepara a revisão sem aprovar correspondência completa fonte/binário, exceções
por arquivo ou obrigações de distribuição. A origem das receitas está vinculada
à versão 0.15.2 do repositório Zig.

Ver [fontes, hashes e extrações](evidence/linux-zig-sdk-source-audit.json).
O ledger Linux referencia esse registro separadamente, preservando os ensaios
anteriores. `approved: false`, `qualified: false` e
`source_to_binary_complete: false` permanecem explícitos. Nenhuma auditoria foi
admitida pelo runtime e nenhum aviso foi incluído no candidato como aprovado.

A fundação passou com **133 testes**: Windows/Python 3.14.6 (28,038 s, 6 skips),
Windows/Python 3.12.10 (25,597 s, 6 skips) e WSL/Python 3.12.15 (37,494 s,
5 skips). Não foi necessário repetir o corpus para bytes idênticos aos já
verificados nos dois Pythons. T030 continua parcial e o total permanece
**46/84 tarefas**, sem VM, instalação global, mudança de catálogo, commit,
push ou publicação.

### Continua??o: invent?rio e ZIP locais do musl est?tico

O invent?rio local passou a separar medi??o est?tica de baseline de compatibilidade.
O novo flag expl?cito `--static-elf` aceita somente receita Linux musl com `-static`,
fatos coerentes do SDK e quatro resultados est?ticos cujo relat?rio tem hash
vinculado ? proveni?ncia. Registra `native_linkage: static-elf` e
`minimum_libc: null`. O caminho convencional continua exigindo vers?o m?nima;
combinar os dois modos ou usar o flag fora da cria??o do invent?rio ? recusado.
N?o h? mudan?a no schema do manifesto distribu?do, sele??o de runtime ou cat?logo.
A decis?o e seus limites est?o registrados em research.md.

Tr?s testes novos cobrem empacotamento sem vers?o inventada, preserva??o do gate
de auditoria antes de executar processos, receita/SDK/medi??o incompat?veis,
relat?rio alterado e cria??o expl?cita com modos POSIX reais no WSL. O caso
positivo falhou inicialmente no contrato anterior de vers?o obrigat?ria; passou
ap?s a implementa??o. A cobertura de cria??o POSIX ? skip no Windows. Na verifica??o
sint?tica da barreira de auditoria, o Windows confere conte?do sem simular modos
POSIX; no WSL os modos reais s?o conferidos.

O candidato com avisos de proveni?ncia
`daba2f9a893a98f746a101cd3de7d07261b3af51e076690bdbb60891c5055a03`
foi inventariado em 15 arquivos. Dois empacotamentos independentes produziram ZIPs
byte a byte id?nticos, com **7.355.837 bytes** e SHA-256
`dfcd0bf5641e28cb6986bbcefe41f77a348016345c824b9c388032dc908b3562`.
Conte?do, hashes, tamanhos, modos e timestamps foram conferidos. O invent?rio tem SHA
`f07f0b66e2a997384bcc9041e65c841fdf195747d3c54acf265caf094c02ea5f`.
H? c?pia exata do ZIP/invent?rio/resumo na pasta local ignorada de revis?o musl,
junto dos recibos anteriores. O motor mant?m os bytes dos ensaios de corpus
anteriores; n?o se atribuiu nova execu??o do corpus a esta etapa.

O inspetor real recusou o review.json incompleto com
`Reviewed audit must bind the exact build provenance`, antes do probe. N?o foram
criadas auditoria aprovada, baseline nativa, URL remota ou entrada de cat?logo.
A auditoria de fontes/licen?as e a qualifica??o Alpine/ARM64/kernel/CPU permanecem
pendentes. Ver [recibo e invent?rio resumido](evidence/linux-musl-candidate-package.json).

Funda??o: **150 testes** em Windows/Python 3.14.6 (21,872 s; 7 skips),
Windows/Python 3.12.10 (21,372 s; 7 skips) e WSL/Python 3.14.8 (43,146 s;
5 skips). Os skips n?o qualificam ambiente nativo. T029/T030 continuam parciais;
o total permanece **46/84**, sem VM, instala??o global, commit, push ou publica??o.

### Continua??o: fontes dos objetos musl e avisos por arquivo

Novo coletor `tools/runtime/audit-musl-objects.py`: valida hashes do execut?vel,
SDK/inspector, archive musl e TSV de extra??es contra a proveni?ncia do relink.
Compara os bytes de cada membro observado com seu objeto real e executa somente
readelf fixado, com profundidade DWARF limitada. Interpreta atributos apenas das
unidades de compila??o de n?vel zero, recusa fontes externas ao SDK e compara
os fontes identificados com os bytes do arquivo SDK fixado. N?o compila nem
executa o candidato; limites de 120 s agregados, 5.000 objetos/fontes, 64 MiB de
fontes e 8 MiB por sa?da de inspe??o. Um primeiro script explorat?rio tentou usar
um campo archive inexistente nas linhas; foi corrigido para archive_sha256 antes
da coleta final. Nenhum resultado dessa tentativa foi usado como evid?ncia.

Os **177 membros** libc.a observados foram associados a **177 fontes**,
237.720 bytes, todas conferidas contra o SDK. **16 fontes** t?m coment?rios
iniciais, incluindo atribui??es/termos de arquivos matem?ticos, qsort e c?digo
x86_64. O relat?rio preserva esses prefixos integralmente e registra o hash das
sa?das DWARF privadas, sem publicar seus caminhos pessoais. Isso documenta
correspond?ncia de metadados, n?o prova compila??o reproduz?vel ou reten??o de
se??es. Ver [fontes observadas](evidence/linux-musl-object-sources.json).

`prepare-draft-notices.py --musl-object-evidence` exige evid?ncia do build/SDK
exatos. Recalcula hashes das fontes e coment?rios diretamente no SDK fixado,
antes de gerar uma sa?da nova. O candidato agora tem **30 avisos/refer?ncias**
e 31 arquivos no invent?rio; os candidatos anteriores foram preservados.
Motor inalterado, SHA
`a58b2f30b70a0393ff0cec93d40e7b039015d1ad2bbdc8a9c60634334519942f`.
Nova proveni?ncia SHA
`658e51e830b80642cf2915d1fc7b4cae81c0cc8c1fa12ba3fb71695760d0caf4`.
Dois ZIPs byte a byte id?nticos: **7.368.435 bytes**, SHA
`471263cf178713d22502141bda44ef3d3e6c7446f8fb9ec08d219cc1eb5d5ace`.
Conte?do/modos/hashes foram conferidos e o inspetor real continuou recusando a
auditoria incompleta antes do probe. N?o houve nova execu??o do corpus, pois os
bytes do motor s?o os mesmos dos ensaios anteriores. Ver
[recibo do pacote com avisos por fonte](evidence/linux-musl-source-notice-package.json).

Quatro testes novos cobrem leitura de unidades de compila??o sem confundir
nomes de fun??es, campos amb?guos, caminhos com espa?os, fontes fora do SDK,
raiz relativa desconhecida, preserva??o de coment?rios e v?nculo exato da
evid?ncia, inclusive duplicatas/travessias. Os tr?s primeiros falharam por falta
do coletor antes da implementa??o; o contrato adicional da prepara??o passou.
Funda??o: **154 testes**, Windows/Python 3.14.6 (21,811 s; 7 skips),
Windows/Python 3.12.10 (21,159 s; 7 skips), WSL/Python 3.14.8 (44,186 s;
5 skips). Skips continuam sem valor de qualifica??o nativa.

T030 avan?ou na coleta por arquivo, mas headers transitivos, demais trechos de
fontes, startup direto, libzigc/compiler_rt/LLVM, geradores/dados e oferta completa
de fontes ainda exigem revis?o. Nenhum audit aprovado foi produzido. Total
**46/84 tarefas**; Alpine/ARM64/macOS e baselines nativas permanecem pendentes,
sem VM, instala??o global, mudan?a de cat?logo, commit, push ou publica??o.

### Continua??o: startup e runtimes Zig do candidato musl

`tools/runtime/audit-zig-runtime.py` complementa o coletor musl com crt1.o direto
e os membros observados de libzigc.a/libcompiler_rt.a. Confere proveni?ncia,
execut?vel, SDK/inspector, extra??es e bytes de archives/membros/objetos. Executa
somente readelf fixado, com limites de 120 s, 8 MiB por sa?da, 1 MiB por fonte,
5.000 refer?ncias por tabela e 64 MiB agregados de fontes. Interpreta exatamente
uma tabela DWARF4 por objeto e recusa vers?es/?ndices amb?guos ou travessias.

O startup aponta a `lib/libc/musl/crt/crt1.c`. Os dois runtimes usam nomes de CU
virtuais zigc/compiler_rt; n?o foram tratados como caminhos de arquivos existentes.
As tabelas identificam 1, 20 e 245 refer?ncias, respectivamente. Junto dos dois
entrypoints explicitamente coletados, foram conferidos **260 arquivos SDK**,
**1.753.358 bytes**, contra o arquivo original fixado. Fonte de entrypoint tem
r?tulo pr?prio e n?o ? apresentada como observa??o DWARF. Ver
[fontes startup/Zig](evidence/linux-musl-zig-runtime-sources.json).

Um builtin.zig gerado foi observado nos dois runtimes, com hash atual
`0795924d103f617454ad0b2eef7c93ee285efe20d2445b4cb00eba519933bd04`.
Foi copiado sem altera??o para a pasta ignorada de revis?o, junto do relat?rio.
Esse hash descreve os bytes atuais e n?o comprova os bytes durante o build.
Fontes geradas n?o foram misturadas com arquivos do SDK fixado.

Os **49 prefixos de coment?rios** completos foram preservados em JSON e arquivos
p?blicos de evid?ncia com hashes conferidos. Um scanner limitado sinaliza linhas
com refer?ncias a licen?a/origem em todo o conte?do: 17 arquivos t?m indicadores,
todos dentro dos prefixos neste recorte. Existem refer?ncias a fontes portadas de
musl e Go; a coleta n?o decide suas obriga??es. Tabelas podem superestimar fontes
com c?digo retido, e busca textual n?o equivale a revis?o sem?ntica exaustiva.
Nenhum aviso foi incorporado automaticamente a um novo candidato ou aprovado.

Quatro testes novos cobrem tabelas com espa?os/diret?rio zero, vers?o n?o prevista,
m?ltiplas tabelas, ?ndices/entradas duplicados ou desconhecidos, travessias,
confinamento de builtin gerado e detec??o de indicadores depois do prefixo.
Os tr?s testes iniciais falharam por aus?ncia do coletor antes da implementa??o;
o quarto validou o scanner adicionado. Funda??o: **158 testes** em
Windows/Python 3.14.6 (21,755 s; 7 skips), Windows/Python 3.12.10 (21,232 s;
7 skips) e WSL/Python 3.14.8 (44,242 s; 5 skips). Skips n?o qualificam SO nativo.

Hashes dos ZIPs anteriores foram novamente conferidos e permanecem id?nticos.
Motor e cat?logos n?o foram alterados. T030 segue parcial: faltam revis?o de
aplicabilidade por arquivo, fontes transitivas/geradores/dados e auditoria final,
al?m da qualifica??o nativa dos bundles. Total **46/84 tarefas**. Sem VM,
instala??o global, execu??o nova do motor/corpus, commit, push ou publica??o.

### Continua??o: integrar coment?rios dos runtimes ao candidato musl

`prepare-draft-notices.py` agora aceita `--zig-runtime-evidence`, combin?vel com
`--musl-object-evidence`. A valida??o compartilhada exige tipo de relat?rio,
proveni?ncia, execut?vel e SDK exatos, caminhos can?nicos/?nicos e fontes dentro
do SDK permitido. Os arquivos gerados s?o separados e n?o aceitos como fontes
SDK. Antes da c?pia, a prepara??o recalcula hash/tamanho de cada fonte e de seu
prefixo diretamente nos bytes do arquivo SDK fixado. A leitura dos coment?rios
presentes no JSON n?o ? usada como fonte dos textos empacotados.

Dois testes novos falharam por aus?ncia das fun??es antes da implementa??o e
passaram depois. Cobrem identidade exata do runtime/SDK, recusa de builtin gerado
como fonte SDK e detec??o de recibos de fonte/prefixo adulterados. A extra??o do
validador comum preservou os testes e comportamento anteriores de avisos musl.

A execu??o real conferiu novamente 58 headers, nove arquivos gerados Graphviz,
177 fontes musl e 260 fontes do startup/runtime Zig. Nova sa?da independente:
**79 arquivos de coment?rios/avisos/refer?ncias**, somando os 49 prefixos Zig aos
30 anteriores, e 80 arquivos no invent?rio. N?o inclui builtin.zig gerado. Sua
c?pia local anterior para revis?o permanece separada. O dot mant?m SHA
`a58b2f30b70a0393ff0cec93d40e7b039015d1ad2bbdc8a9c60634334519942f`.
Nova proveni?ncia SHA
`63bc32568e16a91385f3eba2f818896ab01fcc390388a98db7d28283dbe146ad`.

Dois ZIPs byte a byte id?nticos: **7.393.576 bytes**, SHA-256
`10b37b433a85216f17c65b6e09b58b3c8c26422ea302763efd10a8a11c610410`.
Conte?do, tamanhos, hashes e modos foram conferidos. H? c?pia local ignorada
com ZIP/invent?rio/proveni?ncia/review/relat?rio est?tico; avisos e recibos
p?blicos de evid?ncia est?o vinculados por hash. Ver
[pacote com coment?rios runtime](evidence/linux-musl-runtime-notice-package.json).
O inspetor real recusou o rascunho de auditoria antes do probe. N?o se repetiu
o corpus para o motor inalterado nem se alteraram os candidatos anteriores.

Funda??o: **160 testes** em Windows/Python 3.14.6 (22,157 s; 7 skips),
Windows/Python 3.12.10 (21,651 s; 7 skips), WSL/Python 3.14.8 (44,668 s;
5 skips). Skips n?o qualificam ambientes nativos. Esses coment?rios preservam
material de revis?o, incluindo documenta??o/origem; n?o aprovam aplicabilidade,
textos can?nicos ou oferta completa de fontes. T030 continua parcial e o total
permanece **46/84**, sem VM, instala??o global, novo motor, promo??o de suporte,
commit, push ou publica??o remota.

### Organiza??o dos commits e branch da implementa??o parcial

Por solicita??o do mantenedor, a implementa??o parcial foi organizada em
`feat/003-add-cross-platform-support`, criada de `dev`. A dev local avan?ou por
fast-forward at? origin/dev j? conhecido, commit
`50105db` (merge da spec 002). O conte?do dessa base ? id?ntico ao HEAD anterior
`3ad9b66`; a branch feat/002-manage-layout-runtime foi preservada. N?o houve
merge da feature 003 em dev/main nem push.

Separa??o por assunto: renomea??o da CLI; especifica??o/matriz; runtime POSIX e
testes compartilhados; ferramentas/workflows/testes de qualifica??o; documenta??o,
ledger e evid?ncias. Uma ?nica branch da spec mant?m essas partes dependentes.
Os ZIPs/bin?rios/SDKs e scratch continuam ignorados e fora dos commits.

Os bytes de c?digo/receitas/evid?ncias existentes foram preservados. Atributos
Git passaram a preservar tamb?m arquivos de evid?ncia sem extens?o (por exemplo,
AUTHORS/COPYING), evitando normaliza??o CRLF que invalidaria hashes. O cabe?alho
de tasks.md foi atualizado para a branch atual e sua linha vazia final foi
removida. As valida??es anteriores continuam com seus commits/source_state
originais: gravar commits agora n?o converte ensaios dirty/WSL em qualifica??o
nativa. A feature permanece parcial, **46/84 tarefas**, com **160 testes** na
?ltima regress?o dos dois Pythons Windows e do Python privado WSL.
