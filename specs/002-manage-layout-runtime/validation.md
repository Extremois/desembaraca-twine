# Validação: runtime de layout gerenciado

**Estado atual (2026-10-16)**: implementação e distribuição validadas localmente.
T004 concluída; o bloqueio descrito no histórico abaixo foi resolvido. A aceitação
em Windows limpo nas duas versões e a reabertura das novas saídas no Twine continuam
pendentes. Os registros históricos não descrevem o estado atual do código.

## Baseline — 2026-10-16

Ambiente observado: Windows build 26200 AMD64, CPython 3.14.6 x64.
Comando: `python -X utf8 -m unittest discover -s tests -v`.
Resultado: 78 testes, 77 aprovados e 1 erro em 2,660s.

Erro preexistente: `integration.test_roundtrip.RoundtripTests.test_bom_crlf_and_tags_survive`
lança `FormatError: Esperada fonte Twee UTF-8 com cabeçalhos ::` durante `parse(raw)`.
Nenhum código de produção havia sido alterado quando essa baseline foi executada.
Os testes de motor usam a instalação Graphviz global existente; não comprovam a feature.

## Matriz de aceitação

| Ambiente | Instalação limpa | Primeiro layout | Seis referências offline | Recuperação |
| --- | --- | --- | --- | --- |
| Windows 11 x64 / CPython 3.12 x64 | Pendente | Pendente | Pendente | Pendente |
| Windows 11 x64 / CPython 3.14 x64 | Pendente | Pendente | Pendente | Pendente |

O ambiente desta sessão não é máquina limpa. O mínimo de código/metadados
`requires-python >=3.12` não amplia a matriz oficial acima.

## Rastreabilidade e evidências exigidas

| Requisito | Evidência | Estado |
| --- | --- | --- |
| FR-001 / SC-001 | Procedimento documentado sem Graphviz global, primeira melhoria | Pacotes externos com PATH isolado aprovados; máquina limpa pendente |
| FR-002 | Preparação automática sem configuração de caminhos | Implementado e validado localmente |
| FR-003 | Aceitação nas duas combinações oficiais | Pendente |
| FR-004 / SC-003 | Original idêntico, dados preservados, sem sobrescrita | Suíte de preservação aprovada |
| FR-005 / SC-002 | Seis referências zeradas e reabertura Twine | Seis zeradas; reabertura nova pendente |
| FR-006 / SC-006 | Estados, códigos e ausência de saída parcial | Contratos e integração aprovados |
| FR-007 / SC-004 | Causa, impacto, recuperação e nova tentativa | Cenários controlados da CLI aprovados |
| FR-008 | Interrupção antes/depois do seletor, geração anterior preservada | Processos Windows reais; testes aprovados |
| FR-009 / SC-005 | README PT/EN, requisitos e percurso completo | Docs atualizados; percurso em VM limpa pendente |
| FR-010 / SC-007 | Corpus com rede bloqueada e cache saudável | Motor real offline aprovado nas duas versões de Python |
| FR-011 | Origem/hash, inventário nativo, compatibilidade e avisos por componente | Qualificação e hashes de 29 avisos nos dois pacotes aprovados |

Para cada ensaio, registrar comando, versões, condições iniciais, código de saída,
resultado esperado/observado e arquivos de evidência. Omitir histórias privadas e credenciais.
Qualificação, avisos e distribuições foram concluídos na retomada documentada abaixo.
Reabertura e matriz limpa continuam pendentes.

## T002 — infraestrutura isolada

Criado `tests/runtime_support.py` com ZIP sintético em memória, transporte controlado,
cache temporário e bloqueio de DNS/conexões. Smoke check: ZIP reaberto com conteúdo
esperado, transporte registra uma chamada e os helpers funcionam sob bloqueio de rede.
Nenhum helper acessa a rede real por padrão.

## T003 — artefato real qualificado quanto à integridade e estrutura

- URL: `https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/16.1.0/windows_10_cmake_Release_Graphviz-16.1.0-win32.zip`.
- SHA-256 calculado e igual ao checksum oficial:
  `37906f29ede26cf1952f8cf942c1e7814ab86ef448130136c8607b1b6ffe0870`.
- ZIP: 8.271.496 bytes; expansão: 17.871.086 bytes; 302 arquivos, incluindo 97 EXE/DLLs.
- Prefixo: `Graphviz-16.1.0-win32/`; executável: `bin/dot.exe` sob esse prefixo.
- `bin/config8` incluído contém nomes relativos de plugins, sem caminho absoluto
  de build detectado. Nenhuma sondagem de execução foi feita nesta etapa.
- Nenhum redirecionamento foi observado; origem final HTTPS em `gitlab.com`.
- Os limites planejados de tamanho e quantidade comportam o pacote.
- Inventário completo: [metadados do ZIP](../../docs/graphviz-16.1.0-managed-runtime.json).
- Não há arquivo cujo nome contenha license, copying, notice ou copyright no ZIP.
  Essa constatação não equivale a concluir que todos os textos internos carecem de avisos.

O primeiro download foi bloqueado pelo sandbox com WinError 10013; a repetição com
permissão de rede concluiu e verificou o checksum. Binários permanecem somente em `.tmp/`
ignorada pelo Git; nenhum manifesto de produção foi criado ou ativado.

## Histórico de T004 — impedimento inicial, depois resolvido

O submódulo de dependências da tag Graphviz 16.1.0 aponta para o commit
`ff985525b23a1a72ddb1a89482ea12233c3cbe85` de graphviz-windows-dependencies.
Foram consultados esse commit, os avisos e metadados SPDX disponíveis no seu diretório
`vcpkg/installed/x86-windows/share/` e as árvores de binários x86.
33 das 62 DLLs do ZIP correspondem exatamente a blobs das árvores de dependências
inspecionadas, usando hash Git calculado a partir dos bytes, sem executar as DLLs.
As demais incluem bibliotecas compiladas pelo próprio Graphviz, arquivos do runtime
Microsoft e `zlib1.dll`; ausência de correspondência nessas duas árvores não demonstra
origem indevida ou incompatibilidade.

Os recursos binários de `msvcp140.dll` e `vcruntime140.dll` identificam 14.44.35211.0.
A documentação oficial de redistribuição Microsoft remete a condições de licença próprias;
a qualificação desta composição ainda não demonstrou seu atendimento. Os metadados SPDX
recuperados também contêm NOASSERTION em alguns componentes e URLs de fontes com variáveis;
não foram tratados como prova automática de compatibilidade ou de fontes correspondentes.

Resultado: T004 permanece aberta. A revisão por componente, os textos complementares
completos e as referências de fontes correspondentes precisam ser concluídos antes de T006.
Não se afirma incompatibilidade jurídica comprovada; falta a evidência exigida pelo projeto.
Etapas posteriores da fundação e histórias não foram executadas, respeitando o gate de T004.
O código de produção, o procedimento de uso e a checklist de requisitos permanecem inalterados.

Fontes consultadas:

- [Submódulos da tag 16.1.0](https://gitlab.com/api/v4/projects/4207231/repository/tree?path=windows/dependencies&ref=16.1.0).
- [Dependências no commit usado](https://gitlab.com/graphviz/graphviz-windows-dependencies/-/tree/ff985525b23a1a72ddb1a89482ea12233c3cbe85).
- [Compilação Windows da tag](https://gitlab.com/graphviz/graphviz/-/blob/16.1.0/ci/windows_build.py).
- [Redistribuição Visual Studio 2022](https://learn.microsoft.com/en-us/visualstudio/releases/2022/redistribution).

## Retomada de T004 — avisos consolidados

Obtidos o LICENSE Graphviz, o aviso ANN do commit usado, LICENCE PCRE2 10.43 e o
documento oficial Microsoft Visual C++ 2015-2022 Runtime. O download Microsoft inicial
retornou 403; requisição com cabeçalhos usuais de navegador e parâmetro de download
concluiu. O texto foi extraído dos parágrafos do DOCX, sem executar instaladores.
As consultas GNU diretas sofreram timeout; o texto LGPL completo já presente nos avisos
do fornecedor foi preservado como complemento ANN, cuja licença foi confirmada na página
oficial do autor. Os avisos adicionais não alteram os binários ou a licença autoral.

Consolidação: 28 componentes mapeiam os 302 arquivos; 29 arquivos de avisos/fontes
incluídos no pacote, com origens/destinos/hashes fixados no manifesto. A revisão em
`docs/third-party.md` delimita a compatibilidade ao download direto original e processo
separado, sem redistribuição de binários pelo projeto. T004 pode prosseguir nessa composição.

T005: teste de importação pela descoberta completa do diretório tests demonstrou ausência
do módulo runtime antes de implementação. A primeira descoberta restrita a tests/unit não
incluía common no caminho; foi corrigido o comando para descobrir a partir de tests.
T006: manifesto gerado com hash real do ZIP, 302 entradas e 29 avisos complementares.

## Implementação local — T007–T021, T023–T027 e T029–T036

O runtime usa exclusivamente o manifesto local fixado, confere bytes/hashes antes
de executar o pacote, valida inventário e avisos em cada resolução e sonda versão e
`json0` no caminho definitivo. A seleção é atômica e os handles fixam a geração.
Não há descoberta de Graphviz global nem alteração persistente do ambiente.

Evidências automatizadas:

- `tests/unit/test_runtime.py`: esquema, identidade, inventário, plataforma,
  primeira preparação controlada, integridade dos avisos e reutilização offline.
- `test_runtime_archives.py`: caminhos Windows inseguros, colisões, links/reparse
  no ZIP, pacote truncado, limites e origens/redirecionamentos não autorizados.
- `test_runtime_repair.py`: publicação/reparo interrompidos, seleção anterior
  preservada, corrupção, falta de espaço/permissão e sondagem inválida.
- `tests/integration/test_runtime_concurrency.py`: processos Windows reais,
  preparações simultâneas, espera limitada a 10s com dono preservado, lock liberado
  após `os._exit(77)` e retomada offline antes/depois de `active.json`.
  O payload desses processos é controlado; não é evidência de portabilidade nativa.
- `tests/integration/test_runtime.py`: Graphviz real, nomes/identidades, corpus
  sem rede, ambiente legado sem efeito e cache com espaços/acentos/caminhos longos.
  Recuperação determinística usa arquivos nativos verificados, recompactados apenas
  para o transporte local de teste; não substitui a qualificação do ZIP original.
- `test_runtime_budget.py`: preparação excluída dos 60s, tempo de leitura mantido
  e DependencyError sem fallback. Os contratos anteriores preservam estados,
  códigos, ausência de saída parcial, bytes e métricas.

O ensaio de distribuição revelou WinError 267 no cwd longo e WinError 206 ao
inferir o executável da linha de comando. Correção: namespace estendido para
arquivos, cwd na raiz comum do cache e argumento `executable` explícito no Popen
Windows. Não depende de editar registro, PATH ou habilitar nomes 8.3. O teste nativo
agora exige caminho do diretório do executável maior que 260 caracteres.
Referências: [CreateProcessW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw)
e [SetCurrentDirectory](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setcurrentdirectory).

### Preservação e seis referências

O corpus de 13 casos passou com nenhuma regressão simultânea das três métricas.
Os seis `known_resolvable` — crossing, coincident, isolated_overlap,
connected_overlap, through_isolated e through_connected — terminaram em `(0,0,0)`.
Os verificadores comparam original byte a byte e invariantes de dados/conexões.
A reabertura nova no Twine não foi executada; a confirmação antiga não é reutilizada.
As seis cópias para revisão estão em `.tmp/managed-review-9cdeab09/`. Seus caminhos,
hashes de entrada/saída, métricas e identidade da geração estão em
[layout-results.json](layout-results.json), com `twine_reopened: false` explícito.

O teste BOM/CRLF da baseline foi corrigido para normalizar CRLF antes de acrescentar
CRLF, evitando produzir CRCRLF quando o Git já converteu o checkout. Nenhuma fixture,
regra de leitura, geometria ou algoritmo foi alterado para acomodar esse erro do teste.

## T037 — cenários locais de recuperação do quickstart

Executada a CLI real, incluindo parser, motor nativo e publicação, com cache exclusivo,
ZIP oficial de T003 novamente conferido e transporte controlado sem rede. Falha de
conexão foi injetada como URLError; restabelecimento disponibilizou os bytes originais
do ZIP, com o manifesto de produção intacto. Não foi alterada a rede do computador.

| Cenário | Código | Resultado observado |
| --- | --- | --- |
| Cache vazio, obtenção indisponível | 1 | Sem cópia; causa, impacto e orientação |
| Repetir o mesmo comando após correção | 0 | Crossing melhorado de `(1,0,0)` para `(0,0,0)` |
| `--prepare-runtime` com cache saudável offline | 0 | Sem transferência e sem história gerada |
| `--repair-runtime` sem conexão | 1 | `active.json` idêntico e geração anterior existente |
| Processar offline após reparo malsucedido | 0 | Nova cópia íntegra, sem rede |
| Plugin alterado e obtenção indisponível | 1 | Corrupção detectada; saídas existentes idênticas |
| Repetir após restabelecer obtenção | 0 | Nova geração válida; métricas finais zeradas |

Mensagem observada: “Não foi possível obter o pacote pela internet. Componente de
processamento indisponível; nenhuma cópia gerada. Restabeleça a conexão/acesso HTTPS
e repita o comando.” Original e cópias prévias permaneceram idênticos em todos os casos.
Interrupções e retomada do seletor foram exercitadas em processos reais nos testes
acima. O procedimento com VM/rede fisicamente desconectada continua em T043.

## T038–T041 — documentação e distribuições

README PT/EN descreve requisitos, download, internet inicial/reparo e uso offline.
CONTRIBUTING e quickstart distinguem testes controlados, motor real e máquina limpa.
Wheel/sdist incluem manifesto, os 29 avisos e LICENSE/NOTICE; inspeção confirmou
ausência de EXE, DLL, cache e temporários. O carregador usa recursos relativos ao
pacote, independentemente do cwd. Nenhuma dependência Python de produção foi adicionada.

Comandos de build:

```powershell
python -m venv .tmp/build-env
.\.tmp\build-env\Scripts\python.exe -m pip install build setuptools wheel
.\.tmp\build-env\Scripts\python.exe -m build --no-isolation --outdir .tmp/release-dist
```

Build concluído com build 1.6.1, setuptools 84.0.0 e wheel 0.48.0. O backend emitiu
aviso de depreciação do metadado `license = {file = "LICENSE"}` preexistente, com
prazo em 2027-02-18; não impediu build/instalação. Avisos de exclusão de EXE/DLL
indicam que tais arquivos não estavam nas fontes. Ferramentas foram obtidas do índice
em venv isolada; o sandbox exigiu permissão de rede e de acesso aos processos externos.
Não se confundem esses limites da automação com pré-requisitos do produto.

Cada distribuição foi instalada com `pip install --no-index --no-deps
--no-build-isolation ARTEFATO` em venv própria fora do checkout, sob
`%TEMP%/twine-distribution-ohxrx6ka/`. Para construir o sdist, as ferramentas da venv
de build foram disponibilizadas apenas ao backend via PYTHONPATH, removido antes de
executar a CLI. Os módulos importados apontaram para os respectivos `site-packages`.

Nos dois ensaios, cwd externo, PATH limitado ao Scripts da venv e variável legada
inválida. `twine-edge-overlap --prepare-runtime` obteve realmente o ZIP oficial em
cache exclusivo. Depois, com DNS/conexões interceptados para falhar, crossing foi
processado com código 0, métricas `(1,0,0) -> (0,0,0)` e original inalterado.
Todos os 29 destinos de avisos foram lidos offline e seus hashes conferidos.

| Distribuição | SHA-256 do artefato testado | Resultado |
| --- | --- | --- |
| `twine_edge_overlap-0.1.0.dev0-py3-none-any.whl` | `04b02d0af2e25b574803c849aa7ef110b455380938a7158f547b8298e1b2d17d` | Instalação, preparação e layout offline aprovados |
| `twine_edge_overlap-0.1.0.dev0.tar.gz` | `978bfe0cab63d98f3922f0a326435c611965ad64e01ce297e204c9ad139f10e4` | Instalação, preparação e layout offline aprovados |

Os artefatos ficam em `.tmp/release-dist/`, ignorados pelo Git; nenhum pacote foi publicado.

## T042 — verificações finais

Ambiente: Windows 11 build 26200 AMD64. Comando de sintaxe:
`python -m compileall -q src`, código 0.

| Python | Comando | Resultado |
| --- | --- | --- |
| CPython 3.14.6 x64 instalado | `python -X utf8 -m unittest discover -s tests -v` | 108/108 aprovados em 35,030s, sem skips |
| CPython 3.12.10 x64 embutido oficial | Descoberta unittest abaixo | 108/108 aprovados em 35,710s, sem skips |

```powershell
.\.tmp\python312\python.exe -X utf8 -c "import sys; sys.path[:0]=['src','tests']; import unittest; unittest.main(module=None,argv=['unittest','discover','-s','tests','-v'])"
```

O ZIP embutido 3.12.10 foi obtido de python.org e o MD5 comparado ao informado na
[página oficial da versão](https://www.python.org/downloads/release/python-31210/).
É um ensaio de compatibilidade local, sem instalar outro Python no sistema e sem
equivaler ao procedimento completo de instalação em VM limpa. Não é recomendação
de usar um patch antigo em produção. O runtime gerenciado já estava pronto; os testes
do corpus e de recuperação bloquearam a rede conforme descrito acima.

## Pendências de aceitação e revisão constitucional

- **T022 e T043**: nenhuma conta/VM Windows limpa foi provisionada nesta sessão.
  A máquina tem Graphviz global e outros runtimes; PATH isolado comprova seleção
  independente, mas não ausência de uma dependência nativa global desconhecida.
  Executar o quickstart completo em Windows limpo com cada Python continua obrigatório.
- **T028**: reabertura das seis novas cópias no Twine ainda sem evidência visual.
  Parser/roundtrip e contagens não substituem essa verificação.
- **T044**: rastreabilidade atualizada, porém fechamento final depende dessas evidências.

Revisão local dos princípios: documentação e fontes acessíveis; responsabilidades de
runtime/CLI/motor/domínio separadas; invariantes preservadas; testes e lacunas
registrados; escolha do download direto e limites justificados em research.md;
licença autoral e avisos de terceiros conservados. Nenhum princípio foi alterado e
nenhuma incompatibilidade foi contornada por mudar silenciosamente o artefato.
O status da especificação permanece de aceitação pendente, não de entrega validada.

## Retomada — disponibilidade das evidências de aceitação

Em 2026-10-16, os SHA-256 das seis entradas em `tests/fixtures/` e das seis
cópias em `.tmp/managed-review-9cdeab09/` foram recalculados e comparados com
`layout-results.json`: todas as 12 comparações passaram. As cópias existentes
continuam disponíveis para revisão; o relatório registra `(0,0,0)` nos seis casos
e mantém `twine_reopened: false`. Essa conferência não executa um novo layout nem
substitui a reabertura no Twine.

O inventário da ferramenta de interação nesta retomada retornou `apps: []` e
`browsers: []`; nenhum Twine ou navegador está acessível para realizar T028.
Nenhuma VM limpa foi disponibilizada ou validada nesta retomada. T022, T028,
T043 e T044 permanecem abertas. Para prosseguir, executar o quickstart nas duas
combinações limpas e disponibilizar o Twine para revisar as seis cópias, registrando
os resultados efetivamente observados. Não há hooks de extensão configurados em
`.specify/extensions.yml`.

### Consulta do Hyper-V solicitada pelo mantenedor

`Get-VM` inicialmente retornou acesso negado no sandbox. Reexecutado com
permissão fora do sandbox, concluiu com código 0. A consulta explícita
`@(Get-VM -ErrorAction Stop).Count` confirmou **0 VMs** no host `GENYSON`.
`Get-VMHost` informou as raízes `C:\ProgramData\Microsoft\Windows\Hyper-V`
e `C:\ProgramData\Microsoft\Windows\Virtual Hard Disks`; a raiz de discos não
listou arquivos. A busca não recursiva por ISO/VHD/VHDX/VMCX nos diretórios
padrão consultados e em Downloads não encontrou imagens. O volume C: informou
252,9 GiB livres. Nenhuma VM foi criada, iniciada ou modificada. É necessário
disponibilizar uma imagem Windows 11 ou indicar uma VM em outro host para
executar a aceitação; essa consulta não altera o estado das tarefas pendentes.

## T045 — percurso adicional no sistema atual, sem VM

O mantenedor instruiu explicitamente prosseguir sem criar VM. T022 e T043 ficam
adiadas; não são condição para continuar o trabalho local e não foram marcadas
como executadas. A especificação e o quickstart registram essa decisão.

Executado em Windows 11 build 26200 AMD64, com CPython 3.14.6 x64 e CPython
3.12.10 x64 embutido já disponível. Cada processo recebeu `LOCALAPPDATA` apontando
para seu próprio diretório de ensaio sob `.tmp/`, sem alterar o cache real ou as
variáveis persistentes do usuário. `TWINE_GRAPHVIZ_DOT` inválida não afetou o
resultado, e descoberta via `shutil.which` foi interceptada para falhar.
As chamadas passam pelo parser e fluxo real da CLI, com captura de stdout/stderr;
não houve substituição do provedor de runtime, do transporte de download ou do motor.

| Cenário | Python 3.12.10 | Python 3.14.6 |
| --- | --- | --- |
| Primeiro arquivo com cache ausente e download HTTPS real do ZIP fixado | Código 0; crossing melhorado | Código 0; crossing melhorado |
| `--prepare-runtime` com DNS/conexões bloqueados | Código 0 | Código 0 |
| Seis referências conhecidas com rede bloqueada | Seis códigos 0; todas `(0,0,0)` | Seis códigos 0; todas `(0,0,0)` |
| Avisos complementares lidos e hashes conferidos offline | 29/29 | 29/29 |
| `--repair-runtime` com obtenção indisponível | Código 1 esperado; seletor idêntico | Código 1 esperado; seletor idêntico |
| Processamento após reparo malsucedido, ainda offline | Código 0; geração anterior reutilizada | Código 0; geração anterior reutilizada |
| Originais, invariantes das cópias e saídas anteriores | Preservados | Preservados |

Hash do ZIP: `37906f29ede26cf1952f8cf942c1e7814ab86ef448130136c8607b1b6ffe0870`.
As conexões foram bloqueadas somente dentro do processo de teste, sem mudar
configurações de rede do computador. A indisponibilidade durante reparo foi
injetada como OSError na resolução de endereço para conferir o diagnóstico
normal de dependência. Cópias, hashes, códigos, mensagens e identidade de geração
estão preservados em [current-host-results.json](current-host-results.json).
São oito saídas conferidas por Python: primeiro uso, seis referências e repetição
após reparo falho. Os diretórios de revisão são `.tmp/current-host-312/` e
`.tmp/current-host-314-network/`.

Comandos usados, com o coletor temporário `.tmp/accept_current_host.py`:

```powershell
python -X utf8 .tmp/accept_current_host.py .tmp/current-host-314-network online
python -X utf8 .tmp/accept_current_host.py .tmp/current-host-314-network offline
.\.tmp\python312\python.exe -X utf8 .tmp/accept_current_host.py .tmp/current-host-312 online
.\.tmp\python312\python.exe -X utf8 .tmp/accept_current_host.py .tmp/current-host-312 offline
```

A primeira obtenção restrita ao sandbox falhou antes de download. As fases online
foram executadas com permissão fora dele. A primeira tentativa offline 3.14 no
sandbox também não conseguiu reutilizar o runtime preparado fora dele; o bloqueio
de rede do teste tornou visível a tentativa de preparação. Essa falha permanece
no relatório, seguida da execução offline aprovada fora do sandbox. Não é evidência
de falha offline do produto fora da restrição da automação.

A tentativa de revisão visual consultou os dois acessos disponíveis: o inventário
integrado continuou vazio e a skill Computer Use nativa retornou
`Computer Use native pipe is unavailable: failed to connect native pipe:
O sistema não pode encontrar o arquivo especificado. (os error 2)`.
Nenhuma reabertura no Twine foi realizada nem inferida dos testes automatizados.
T028 continua pendente; T044 não foi fechada como aceitação completa. Nenhuma VM,
configuração global, algoritmo de layout ou código de produção foi alterado.

## Convergência implementada — T046–T052

Estado: T046, T047, T049, T050, T051 e T052 concluídas. T048 permanece
pendente, assim como a reabertura de T028. T022/T043 continuam adiadas por
instrução do mantenedor de seguir no sistema atual sem criar VM. T044 não foi
fechada como aceitação integral. O registro de T045 acima descreve o ensaio
anterior; as correções de produção desta fase estão discriminadas abaixo.

### Correções e evidências novas

- **T046**: TLS/HTTP indisponível, cinco redirecionamentos permitidos/sexto
  rejeitado, Content-Length incorreto, bytes extraídos acima do inventário e
  prazo cooperativo controlados sem rede real. Sondagens rejeitam versão, JSON,
  identidades, posições e retorno inválidos; limites de tempo/saída são exercitados
  pelo runner controlado, junto da conferência de 10s/1 MiB e do orçamento restante.
  O runner real conserva os testes de encerramento por tempo/saída/interrupção.
  Um teste novo falhou antes da correção: expirar os 300s durante a transferência
  era apresentado como falha de internet. `download()` agora reavalia o prazo
  antes de classificar a falha de conexão; a mensagem correta informa o prazo
  esgotado. O seletor e a geração anterior permanecem íntegros.
- **T047**: junctions Windows reais, criadas pela API `_winapi.CreateJunction`,
  foram detectadas na raiz, seletor e árvore do cache. Junctions para diretórios
  externos também foram introduzidas no staging e no seletor temporário antes
  de falha controlada. Sentinelas externas e arquivos da geração anterior
  permaneceram idênticos; a seleção anterior continuou utilizável sem rede.
  Os cenários passaram nas duas versões de Python, sem skips nem permissões
  adicionais para criar os links. Nenhum binário externo foi executado nesses
  cenários; o runner de preparação era controlado.
- **T049**: os novos testes reproduziram a aceitação indevida do inventário com
  arquivo ancestral, destino de aviso igual à pasta e fontes em formato inválido.
  O carregador agora rejeita colisões hierárquicas sem distinguir caixa, exige
  avisos descendentes de `third-party-notices/` e lista não vazia de URLs HTTP(S)
  de fontes sem credenciais. Os testes também cobrem colisões entre avisos.
  Validação continua anterior a transferência/execução; o manifesto e os 29
  avisos qualificados não foram alterados.
- **T050**: um novo teste demonstrou a preparação implícita em `layout()` antes
  da correção. O adaptador agora exige o handle recebido; a aplicação continua
  resolvendo uma única vez. Testes com motor/runner falso usam provedor explícito
  e falham se houver aquisição inesperada. Testes nativos continuam executando
  o Graphviz gerenciado real, incluindo corpus, offline e caminhos longos.
- **T051**: README PT/EN atualizado para os ensaios locais em CPython 3.12 e
  3.14, com aceitação limpa adiada e revisão visual pendente. Os dois idiomas
  conservam requisitos, comandos, resultado e conexão equivalentes.
- **T048**: inventário integrado novamente retornou `apps: []`, `browsers: []`.
  O acesso nativo retornou `Computer Use native pipe is unavailable` com erro
  Windows 2. Não foi possível abrir o Twine; nenhum relatório foi marcado como
  reaberto. As seis cópias existentes continuam sendo o material para revisão.

O trecho da fase 7 em `tasks.md` continha acentos substituídos por `?` durante a
gravação da convergência via pipe PowerShell. A codificação UTF-8 foi restaurada
nessa seção, mantendo IDs, escopo e rastreabilidade; só tarefas com evidência foram
marcadas concluídas. Nenhuma checklist foi modificada. Não há arquivo de hooks
`.specify/extensions.yml`, portanto nenhum hook de implementação foi executado.

### Verificação final do código corrigido

Comandos executados na raiz do checkout:

```powershell
python -m compileall -q src tests
python -X utf8 -m unittest discover -s tests -v
.\.tmp\python312\python.exe -X utf8 -c "import sys; sys.path[:0]=['src','tests']; import unittest; unittest.main(module=None,argv=['unittest','discover','-s','tests','-v'])"
git diff --check
```

| Ambiente local | Resultado |
| --- | --- |
| Windows 11 AMD64 / CPython 3.14.6 x64 | 122/122 aprovados em 39,003s; sem skips |
| Mesmo Windows / CPython 3.12.10 x64 embutido | 122/122 aprovados em 37,277s; sem skips |
| Compilação de sintaxe e whitespace | Código 0 |

Os novos testes foram executados antes das respectivas correções; falhas esperadas
do diagnóstico de prazo, manifesto e preparação implícita foram observadas.
Uma descoberta restrita por nome `test_runtime.py` incluiu também integração
nativa e encontrou a limitação já conhecida do sandbox. A suíte final acima foi
executada fora dele para permitir o runtime preparado e seus processos.
Essas permissões de automação não são exigência de administrador do produto.
Logs locais: `.tmp/convergence-tests-314.log` e `.tmp/convergence-tests-312.log`.
Contagens, tempos e hashes dos logs estão em
[convergence-results.json](convergence-results.json).

### Distribuições reconstruídas após as correções

Build com as ferramentas já disponíveis, sem obter novas dependências:

```powershell
.\.tmp\build-env\Scripts\python.exe -m build --no-isolation --outdir .tmp/convergence-dist
python -X utf8 .tmp/check_distributions.py .tmp/convergence-dist .tmp/convergence-distribution-results.json
```

Uma tentativa inicial restrita de build no diretório antigo recebeu acesso negado.
O build final usou permissão fora do sandbox e um diretório novo, preservando os
artefatos anteriores. O aviso preexistente de depreciação de `license` permanece,
sem impedir build/instalação. Nenhuma dependência de produção foi adicionada.

| Artefato novo | SHA-256 | Validação |
| --- | --- | --- |
| `twine_edge_overlap-0.1.0.dev0-py3-none-any.whl` | `00e86d7d3e31270ee9a4dc3cb17650a3bf1dd2f85364a4d8cf5c2a05c8afb16d` | Instalação externa, preparação real e layout offline aprovados |
| `twine_edge_overlap-0.1.0.dev0.tar.gz` | `4f85b4833bb39215021eea3129e3849a20bc193319f2cd98815dc8e6b11eb89a` | Instalação externa, preparação real e layout offline aprovados |

Instalados com `--no-index --no-deps --no-build-isolation` em venvs distintas sob
`%TEMP%/twine-distribution-f0anhb3n/`. Cwd externo, PATH limitado aos Scripts da
venv e variável legada inválida. Cada distribuição baixou realmente o ZIP fixado
em cache próprio; depois processou crossing com DNS/conexões bloqueados, código
0, métricas `(1,0,0) -> (0,0,0)` e original idêntico. Manifesto, LICENSE/NOTICE
e os 29 avisos foram inspecionados, sem EXE/DLL/cache nos artefatos. Os avisos
instalados foram lidos e seus hashes conferidos offline. Os bytes de `runtime.py`
e `engines/graphviz.py` em ambos os artefatos foram comparados aos fontes atuais.
Resultados e hashes estão em `convergence-results.json`. Nenhum pacote foi publicado.

### Rastreabilidade consolidada — T052

| Requisito | Critério / aceitação relacionada | Evidência atual | Limite restante |
| --- | --- | --- | --- |
| FR-001 | SC-001; US1/AC1 | Primeiro uso real T045 e duas distribuições novas | Ambiente limpo adiado; reabertura pendente |
| FR-002 | US1/AC2–3 | Runtime gerenciado, PATH/variável legada sem efeito, handle explícito T050 | Nenhuma lacuna local identificada |
| FR-003 | SC-001/SC-005/SC-007 | Suíte completa em 3.12/3.14 no Windows atual | Matriz limpa T022/T043 adiada |
| FR-004 | SC-003; US2/AC2/4 | Preservação, roundtrip, colisões, falhas e corpus aprovados | Reabertura visual de US2/AC1 pendente |
| FR-005 | SC-002; US2/AC1/3 | Corpus sem regressão; seis referências `(0,0,0)` com motor gerenciado | Reabertura Twine T028/T048 pendente |
| FR-006 | SC-006; US2/AC3–4 | Contratos CLI e fallback, aquisição única e erros tipados aprovados | Nenhuma lacuna local identificada |
| FR-007 | SC-004; US3/AC1–4 | Diagnósticos, nova tentativa, TLS/HTTP, prazo e sondagens T046 | Nenhuma lacuna local identificada |
| FR-008 | SC-003/SC-004; US3/AC3–4 | Reparo, seleção atômica, processos reais e junctions/sentinelas T047 | Aceitação completa em ambiente limpo adiada |
| FR-009 | SC-005 | README PT/EN equivalente e quickstart com limites explícitos | Percurso limpo adiado; revisão visual pendente |
| FR-010 | SC-004/SC-007; US1/AC3, US3/AC2–4 | Seis referências offline em ambas as versões; preparo/reparo com conexão explícita | Ensaio em ambiente limpo adiado |
| FR-011 | Aceitação documental | Qualificação/302 arquivos/29 avisos, manifesto reforçado T049 e novos wheel/sdist | Não se estende a redistribuição de binários |

Revisão constitucional: I, documentação/fontes e licença permanecem acessíveis;
II, correções locais sem framework ou dependência nova; III, aplicação prepara e
adaptador recebe handle, domínio permanece independente; IV, originais/saídas e
gerações preservados com verificação; V, cobertura proporcional adicionada com
falhas prévias observadas e limitações explícitas; VI, solução fixada e comparação
anteriores mantidas, sem novo algoritmo. Avisos e fontes de terceiros permanecem
com hashes fixados na distribuição e no runtime. Não se altera a constituição,
não se cria VM e não se declara aceitação integral sem as evidências pendentes.

### Preparação dos commits — integridade dos avisos no Git

Foi observado `core.autocrlf=true` sem regra específica para os avisos de terceiros.
Como os hashes do manifesto se referem aos bytes originais, foi acrescentada
`.gitattributes` com `-text` para `src/twine_edge_overlap/third_party/graphviz-16.1.0/*`.
Essa regra preserva os bytes ao adicionar e restaurar os arquivos, independentemente
da conversão de finais de linha do usuário. Os 29 avisos foram conferidos contra
o conteúdo do índice Git antes do commit do runtime. O manifesto e os avisos não
foram modificados.
