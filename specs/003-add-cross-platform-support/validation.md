# Evidência de implementação — feature 003

**Viabilidade de kernels próprios no CI em 2026-10-20**: preparado `native-kernel-preflight.yml` para observar KVM nos runners GitHub Linux x64/ARM64, como usuário padrão e com elevação no runner efêmero. O coletor consulta somente versão da API e extensão de memória de usuário; não cria VM, não inicia guest nem altera permissões/configuração global. Ausência/permissão/API divergente ficam explícitas em JSON, sem fallback para emulação ou aprovação de célula. O ensaio busca viabilizar testes do kernel real de cada distribuição, que os containers Alpine não cobrem. Confirmação no CI pendente; escopo integral mantido, **54/84**.

**Alpine 3.21–3.24 ensaiado em 2026-10-20**: [16 slots de userland](evidence/alpine-userland-compatibility-2026-10-20/summary.json) passaram no CI `b13cd6f`: quatro versões × x64/ARM64 × CPython 3.12/3.14. Imagens/identidade/patch/CPU conferidos; venv/pip Unicode, gerenciador real, preparo automático/explícito, corpus de 13 casos, cache offline e strace com controle positivo aprovados. Dois pacotes musl conferidos por bytes/modos/ELF estático/proveniência após download; cada slot está vinculado ao pacote da arquitetura e os motores mantêm os hashes anteriores. Oito artefatos e 16 pares de rastros de corpus/controle foram reanalisados; nenhuma syscall de rede no corpus, 49 execuções dot por slot. Cinco workflows e seis jobs de fundação com 224 testes passaram. Isso cobre os userlands antes limitados a 3.22; kernel é o do runner, aquisição permanece controlada e não há qualificação nativa ou promoção. T026/T027/T033/T044 continuam parciais para os critérios restantes; **54/84**. Recibos finais locais, sem commit apenas documental.

**Cobertura Alpine preparada em 2026-10-20**: workflow musl passa a reutilizar os mesmos bundles privados em Alpine 3.21/3.22/3.23/3.24, x64/ARM64 e CPython 3.12/3.14 (16 slots). Imagens oficiais consultadas e fixadas por digest; driver exige identidade/Python/CPU/imagem correspondentes, ausência de Graphviz global, venv/pip em caminho Unicode e runtime/corpus offline com strace. Dois testes recusam troca de ambiente/imagem e fallback; 224 testes de fundação passaram em cada Python, oito skips. Execução real do novo percurso aguarda checkpoint CI; T026/T027/T033/T044 permanecem parciais e não há qualificação por container. Total **54/84**.

**Avisos matemáticos confirmados no CI em 2026-10-20**: checkpoint `29ce912` enviado e [cinco workflows aprovados](evidence/runtime-math-notices-ci-2026-10-20/summary.json). Os quatro ZIPs Linux foram baixados e conferidos por inventário/hash/modo/proveniência; glibc ARM64 e musl x64/ARM64 preservam os 28 materiais históricos exatos, sem inclusão por associação em glibc x64. Os quatro motores mantêm seus hashes. Oito relatórios de runtime/rede passaram com 13 casos e 49 execuções dot por Python, sem syscalls de rede no corpus; rastros de controle/corpus preservados. Seis jobs de fundação passaram com 222 testes cada, e macOS passou novamente. T030 parcial para ancestralidade/aplicabilidade, ISO, demais componentes e oferta/retenção de fontes; **54/84**. Recibos finais locais aguardam o próximo commit necessário; nenhuma redução da matriz ou promoção POSIX.

## Referências matemáticas históricas — 2026-10-20

**Avisos matemáticos preparados em 2026-10-20**: [recibo local](evidence/runtime-math-notices-2026-10-20/summary.json) confere 42 fontes C e COPYRIGHT contra o tarball oficial musl 1.1.18 e 19 fontes Zig contra ambos os SDKs fixados. Preparo inclui 27 prefixos individuais mais COPYRIGHT nas três variantes com fontes observadas; glibc x64 permanece sem inclusão por associação. Quinze referências sem prefixo permanecem explícitas. Teste recusa alteração de fonte/referência e caminho inseguro; fundação passou com 222 testes por Python, oito skips. Confirmação dos novos pacotes nativos e ancestralidade/aplicabilidade ainda pendentes; T030 parcial, total **54/84**. Checkpoint necessário ao CI será usado para validar a mudança nos avisos.

Os arquivos originais permanecem comprimidos em `tools/runtime/licenses/data-references/musl-math/`, com hashes de fonte completa e prefixo. O preparo mantém separadamente os termos Sun/FreeBSD e o COPYRIGHT histórico. As referências `ln.c`/`lnf.c`/`__tand.c` são mapeadas explicitamente; `fmod`/`sqrt` recebem material conservador. Não se afirma uma revisão ancestral exata nem presença de todas as fontes observadas nas seções finais. Pacotes CI anteriores permanecem vinculados aos seus hashes e não são descritos como contendo os novos avisos.


## Mapa de alocações Linux confirmado — 2026-10-20

O [recibo das quatro variantes](evidence/linux-allocated-sections-ci-2026-10-20/summary.json)
vincula a revisão `dfc93c8`, cinco workflows aprovados e seis jobs de fundação
com 221 testes cada. O leitor foi reexecutado localmente sobre os mapas e ELF
baixados, conferindo inputs, membros e intervalos das seções alocadas. Glibc
x64/ARM64 e musl x64/ARM64 têm respectivamente 625/648/964/968 contribuições;
os quatro motores mantêm seus hashes anteriores. Oito ensaios de runtime/rede
passaram, e os termos Go foram incorporados onde a fonte revisada foi observada.

O mapa não sustenta descartar as rotinas matemáticas como apenas debug/imports:
compiler_rt contribui código trigonométrico em glibc ARM64 e nas duas musl,
além de exponenciais/logaritmos em glibc ARM64. Atribuições por fonte continuam
na revisão T030. Contêineres musl não qualificam células Alpine; mapas não
concedem aprovação de fontes/licenças, entrega ou matriz. **54/84** tarefas;
recibos finais locais aguardam outro checkpoint necessário ao CI.

## Integração macOS e prioridade de fechamento — 2026-10-20

Os commits `32fa383` e `b1f608e` implementaram e corrigiram o percurso privado
do gerenciador real no macOS. O [recibo consolidado](evidence/macos-runtime-integration-2026-10-20/summary.json)
confere quatro slots nativos Intel/Apple Silicon × Python 3.12/3.14: aquisição
controlada do ZIP, primeiro uso/preparo, Library/Caches, probe final, modos,
13 casos, preservação e seis referências `(0,0,0)`. Os dois ZIPs, inventários
e proveniências foram reconferidos após download. Seis jobs de fundação com
217 testes passaram; regressão do driver Linux compartilhado passou nas quatro
variantes. A falha inicial do driver por `os.listxattr` foi preservada antes da
correção com `/usr/bin/xattr` somente para leitura.

Gatekeeper estava habilitado; SIP já estava desabilitado nos runners e permaneceu
assim. Não se alteraram proteções ou quarentena. A aquisição fixture e a ausência
de assinatura/quarentena não demonstram aceitação da distribuição. T048 permanece
parcial para esse critério final; T051/T056 continuam independentes. **54/84**.

O usuário priorizou encerrar tarefas antes de iniciar novas implementações.
O próximo avanço deve resolver critérios finais, priorizando a auditoria que
desbloqueia a entrega Linux, em vez de repetir coleta de avisos já conferidos.
A matriz completa continua vigente: o mantenedor confirmou explicitamente em
2026-10-20 que todos os alvos permanecem nesta spec. Não transferir distros ou
macOS para specs futuras como atalho de fechamento. Os 30 IDs restantes se agrupam assim:

| Tarefas | Critério que ainda impede fechamento |
| --- | --- |
| T024–T027 | Baselines e cobertura de versões reais; build em host recente/container não os comprova |
| T030/T031/T066 | Decisões de aplicabilidade/terceiros, oferta/retenção de fontes e pacote/manifesto final com origem real |
| T033/T036–T045/T076/T078/T083 | Pré-requisitos, instalação, corpus, recuperação e pacotes finais em cada célula/Python da matriz |
| T048/T051/T052/T056 | Candidata macOS assinada/notarizada, auditoria e percurso distribuído sob proteções normais; credenciais Apple ausentes |
| T063/T065 | Revisão visual real no Twine por célula e aceitação Windows limpa em ambiente existente autorizado |
| T080/T082/T084 | Auditoria final, promoção e revisão integral dependentes das evidências anteriores |

As evidências novas são mantidas locais até outro commit necessário; não houve
release, publicação de runtime ou promoção de catálogo. `debug.log`, preexistente
à consolidação, não foi incluído nos commits.

## Construção glibc consolidada e reconstrução musl — 2026-10-19

**T028 concluída; 54/84 tarefas, 30 pendentes.** O [recibo glibc](evidence/glibc-build-completion-2026-10-19/summary.json)
consolida os dois bundles nativos x64/ARM64, fontes/objetos observados, inventários
e ZIPs conferidos, relocação Unicode/json0, corpus e integração do gerenciador
em ambos os Pythons. A etapa usa os mesmos critérios de construção de candidatas
da T029; auditoria T030 e distribuição T031 são etapas separadas. Os pacotes
verificados estão em `tools/runtime/artifacts/linux-glibc/`, ignorados pelo Git.

Uma reinspeção somente de leitura dos ELF no WSL confirmou CPU, loader,
dependências de sistema e ausência de RPATH/RUNPATH; não executou o binário ARM64
nem substituiu a evidência nativa vinculada. Maiores símbolos glibc observados:
2.14 x64 e 2.17 ARM64, abaixo do alvo de compilação 2.27. Isso não aprova kernel,
CPU ou execução Ubuntu 18.04. T024/T025/T037 mantêm esses gates abertos.

A exportação de fontes agora também atende musl nas duas arquiteturas, com SDK
próprio autenticado, receita correspondente e evidência de alvo estático. O teste
novo falhou antes da implementação e passou depois, incluindo rejeição de alvo
divergente e inspeção dinâmica. O material reúne o tarball Graphviz original,
árvore `lib/` completa do SDK e LICENSE, receitas, referências e módulos auxiliares
com Apache; não coleta executável do compilador, caches, credenciais ou checkout
inteiro. Instruções estão em [REBUILD-SOURCES.md](../../tools/runtime/REBUILD-SOURCES.md).

| Pacote | Arquivos conferidos | Arquivos SDK reconferidos | Bytes do tar.gz |
|---|---|---|---|
| [musl x64](evidence/musl-source-rebuild-2026-10-19/x86_64/summary.json) | 18.164 | 18.102 | 68.348.021 |
| [musl ARM64](evidence/musl-source-rebuild-2026-10-19/aarch64/summary.json) | 18.164 | 18.102 | 68.347.856 |

Após download, cada arquivo do pacote foi conferido contra seu manifesto:
hash/tamanho/modo 0644/data zero, caminhos sem travessia/duplicatas/links,
limites e identidade da candidata. Cada entrada SDK foi reconferida contra o
tarball original específico da CPU, fixado por hash. Os tarballs/ZIPs completos
ficam somente em área ignorada; recibos, manifestos compactados e rastros são
versionados. A árvore SDK também contém código de outras plataformas; sua
presença não afirma ligação de todos esses arquivos ao motor.

Os dois motores foram recompilados fora do checkout, usando as receitas/módulos
exportados, árvore SDK exportada, compilador autenticado novamente e cache vazio.
Original e reconstruído passaram nos 13 casos/relocação em CPython 3.12.13 e
3.14.5, com zero chamadas de rede observadas e controles positivos. Ambos são
estáticos e **não byte-idênticos** aos originais: a evidência é reconstrução
funcional, sem promessa geral de reprodução em bytes. São containers musl de
CPU correspondente sobre kernel Ubuntu, sem qualificação de células Alpine.

A [rodada inicial](evidence/musl-source-rebuild-2026-10-19/initial-failure/summary.json)
falhou nas duas CPUs: o motor compilou, mas faltavam módulos Python importados
pelo verificador ELF no pacote exportado. Os dois logs de erro foram preservados.
Um teste passou a executar o verificador da extração isolada: reproduziu o erro
antes da correção e passou após incluir runtime/catalog/snapshot/errors. Essa
falha inicial continua registrada como failure.

A revisão corrigida `6f225eb6c6ece00e912d67bff9b461e008be4aca` passou no
[CI musl](https://github.com/Extremois/desembaraca-twine/actions/runs/39352379048),
nas regressões [glibc x64](https://github.com/Extremois/desembaraca-twine/actions/runs/39352378883),
[glibc ARM64](https://github.com/Extremois/desembaraca-twine/actions/runs/39352378858)
e [macOS](https://github.com/Extremois/desembaraca-twine/actions/runs/39352379133).
A [fundação corrigida de seis slots](evidence/github-actions-foundation-musl-sources-fixed-2026-10-19.json)
passou com 208 testes por slot; a [fundação inicial](evidence/github-actions-foundation-musl-sources-2026-10-19.json)
é mantida separadamente. Localmente, 208 testes/oito skips em cada Python
passaram após a correção (27,695 s em 3.12; 28,247 s em 3.14).

T030/T066 permanecem parciais: revisão de aplicabilidade/obrigações por arquivo,
fechamento transitivo e oferta permanente das fontes ainda precisam ser concluídos.
Um artifact de sete dias não é oferta permanente. Catálogo e matriz oficiais
continuam preservados, sem publicação de release ou criação de VM local.

## Bundles e avisos musl verificados — 2026-10-19

**T029 concluída; 53/84 tarefas, 31 pendentes.** O [recibo de construção](evidence/musl-build-completion-2026-10-19.json)
consolida os dois bundles privados e sua verificação: ELF64 da CPU correspondente,
sem interpretador/seção dinâmica/NEEDED/glibc, inventários/ZIPs por hash/tamanho/modo,
relocação Unicode, json0, corpus e integração do gerenciador em ambos os Pythons.
ZIP, inventário, proveniência e relatório ELF estão em
`tools/runtime/artifacts/linux-musl/linux-musl-{x86_64,aarch64}/`, ignorados pelo Git.
Somente metadados, rastros e avisos são versionados. T029 é construção/verificação
das candidatas; não aprova licenças, distribuição ou células Alpine.

O pipeline agora usa os coletores de fontes musl e Zig também em ARM64, com
verificação de receita/arquitetura e identidade exata dos relatórios. Três testes
novos falharam antes da implementação e passaram após a alteração. Relatórios
de outra arquitetura não podem fornecer avisos para ARM64 mesmo quando os demais
hashes coincidirem. O coletor musl aceita a identidade SDK moderna aninhada,
preservando a identidade legada e recusando conflitos.

Os recibos de [x64](evidence/alpine-musl-sdk-notices-2026-10-19/x86_64/summary.json)
e [ARM64](evidence/alpine-musl-sdk-notices-2026-10-19/aarch64/summary.json) registram:

| Medida | x64 | ARM64 |
|---|---|---|
| Membros libc.a observados/fontes conferidas | 177/177 | 173/173 |
| Objetos startup/runtime Zig | 3 | 3 |
| Fontes runtime SDK conferidas | 260 | 261 |
| Total de fontes SDK conferidas | 437 | 434 |
| Headers SDK conferidos/prefixos preservados | 58/23 | 58/22 |
| Avisos / demais itens no índice offline | 107/106 | 107/106 |
| Arquivos / bytes do ZIP | 108 / 7.461.934 | 108 / 7.470.068 |

Após download, as fontes e os prefixos foram reconferidos nos tarballs fixados de
cada arquitetura, incluindo os textos SDK integrais copiados e todos os headers
observados. O índice offline confere hashes/tamanhos/origens dos outros 106 avisos.
Os pacotes preservam prefixos por fonte, COPYRIGHT musl e textos SDK, avisos
Graphviz/Bison/Flex/dados e referência GPL 3 com exceções dos geradores separadas.
Os motores mantêm os hashes anteriores. Corpus e cache offline passaram em
Python 3.12.13/3.14.5: zero chamadas de rede, controles positivos e 49 execuções
dot por slot de integração. O kernel continua sendo o do runner Ubuntu.

A revisão `dcdfcce35bbde2d11c65c579a7ed3c15a4ecbe27` passou no
[CI musl](https://github.com/Extremois/desembaraca-twine/actions/runs/39349837831),
nas regressões [glibc x64](https://github.com/Extremois/desembaraca-twine/actions/runs/39349837783),
[glibc ARM64](https://github.com/Extremois/desembaraca-twine/actions/runs/39349837861)
e [macOS](https://github.com/Extremois/desembaraca-twine/actions/runs/39349837795).
A [fundação de seis slots](evidence/github-actions-foundation-musl-sdk-2026-10-19.json)
passou com 207 testes por slot. Localmente, 207 testes em cada Python passaram,
com oito skips Windows (28,853 s em 3.12; 29,256 s em 3.14).

T030 permanece parcial: observações DWARF não provam retenção de seções ou
fechamento transitivo, e ausência de prefixo não significa ausência de obrigações.
Um builtin gerado por build foi registrado separadamente, sem atribuí-lo ao SDK
fixado. Aplicabilidade por arquivo, auditoria aprovada e oferta completa de fontes
continuam pendentes. T026/T027/T044 conservam as verificações de baseline/versões
e qualificação nativa Alpine; o catálogo e a matriz oficiais não foram promovidos.

## Integração Linux e correção de primeiro uso — 2026-10-19

**T023 concluída; 52/84 tarefas, 32 pendentes.** O teste de integração agora
executa o gerenciador de produção com os bundles reais, além do driver de
aceitação distribuída que continua opt-in. O [recibo consolidado](evidence/linux-runtime-integration-2026-10-19/summary.json)
registra dois testes em cada um dos oito slots: glibc/musl x64/ARM64,
CPython 3.12 e 3.14. A aquisição usa transporte controlado identificado como
fixture; o executável é o Graphviz construído, conferido por ZIP/inventário/
proveniência e executado pelo runner real, sem simulação do motor.

Preparo automático pelo primeiro arquivo e preparo antecipado passaram em caches
novos, com XDG absoluto, espaços/acentos e execução de outra pasta. O teste confere
0755 no motor, 0700 na geração, probe no destino final antes de ready, reutilização
da geração e ausência de nova aquisição offline. O corpus de 13 casos inclui as
seis referências limpas, preserva os originais e verifica integridade semântica e
não regressão. Cada slot registra 49 execuções dot e zero chamadas da classe
de rede sob strace, com controle positivo em processo filho detectado.

Os recibos [glibc x64](evidence/linux-runtime-integration-2026-10-19/glibc-x86_64/summary.json)
e [ARM64](evidence/linux-runtime-integration-2026-10-19/glibc-aarch64/summary.json)
são nativos Ubuntu 24.04; [musl x64](evidence/linux-runtime-integration-2026-10-19/musl-x86_64/summary.json)
e [ARM64](evidence/linux-runtime-integration-2026-10-19/musl-aarch64/summary.json)
usam CPU correspondente em containers Alpine, sem qualificar kernel/versões Alpine.
Foram conferidos após download os pacotes e 44 relatórios/rastros retidos.

Esse percurso encontrou um erro real: se a base XDG ou seus pais não existissem,
o primeiro preparo falhava ao criar a pasta da aplicação. O teste unitário novo
reproduziu a falha antes da correção `caf4c8d`. Agora somente diretórios ausentes
são criados com 0700, inclusive sob umask 000; diretórios existentes mantêm suas
permissões. O WSL existente passou nos cinco testes POSIX e nos dois testes com
motor real após a correção. Seus registros antes/depois são evidência WSL, sem
strace local disponível e sem aprovação de outra célula.

A revisão `860d06a4c5d03ca6ab071c047344443931debb1e` passou nos pipelines
[glibc x64](https://github.com/Extremois/desembaraca-twine/actions/runs/39347852929),
[glibc ARM64](https://github.com/Extremois/desembaraca-twine/actions/runs/39347852726),
[musl](https://github.com/Extremois/desembaraca-twine/actions/runs/39347852760)
e [macOS](https://github.com/Extremois/desembaraca-twine/actions/runs/39347852720).
A [fundação de seis slots](evidence/github-actions-foundation-linux-runtime-2026-10-19.json)
passou com 204 testes por slot. Localmente, a fundação passou nos dois Pythons
com 204 testes/oito skips; a suíte completa passou com 280 testes/13 skips em
cada (57,986 s em 3.12; 58,081 s em 3.14).

O fechamento é da implementação/execução dos testes T023. Catálogo POSIX,
download distribuído real, instalação final e aceitação integral T036–T045,
auditoria, Twine e recuperação por célula continuam pendentes. Nenhum registro
foi promovido no catálogo ou na matriz de suporte; não houve VM local ou
instalação global de ferramentas.

## Fechamento da documentação de instalação — 2026-10-19

**T035, T055 e T079 concluídas; 51/84 tarefas, 33 pendentes.** O README PT/EN
e o quickstart agora apontam para o ZIP público imutável da revisão
`40b3e38f3dc6bef2fe64b17f66e1f812460bd7f1`, que instala o comando atual.
Foram revisados Python nativo/venv/pip, arquitetura, caminhos externos sem PATH,
internet/espaço/permissões, cache/offline/reparo e recuperação macOS sob as
proteções normais. Instruções de desenvolvimento e aceitação condicionada estão
identificadas; nenhuma URL futura é apresentada como disponível.

O [recibo com dez relatórios](evidence/documented-installation-2026-10-19/summary.json)
registra o [CI aprovado](https://github.com/Extremois/desembaraca-twine/actions/runs/39334233456)
da revisão de documentação `ac31e29f57c4adbd2a296ea1ec71c92584adf76e`.
Linux Ubuntu 24.04 x64/ARM64, macOS 15 Intel/Apple Silicon e Windows hospedado
instalaram a mesma origem em CPython 3.12/3.14, em venvs novas fora do checkout,
com espaços/acentos no caminho. PATH continha somente a venv; Git e Graphviz
não estavam disponíveis. Console, módulo do pacote e módulo CLI responderam
ao help; catálogos/matriz/notices foram encontrados no pacote instalado.
O SHA-256 do ZIP registrado pelo pip foi o mesmo nos dez slots:
`e6d09369119ba7c76f2886d5082b9d575aa64e18a0391ea239d78595825bf39c`.
A fundação também passou na [mesma revisão](https://github.com/Extremois/desembaraca-twine/actions/runs/39334233402).

O fechamento é dos requisitos de **documentação e comandos disponíveis**, sem
aprovar um motor POSIX. Os registros anteriores que mantinham T035/T055 abertas
por indisponibilidade de bundles ficam como histórico; os requisitos dessas tasks
permitem documentar a matriz proposta versus validada e explicitar alvos pendentes.
A URL instala código Python; preparo/reparo/processamento Linux/macOS continuam
indisponíveis no catálogo distribuído. T031/T052/T056/T078/T083 e as demais
qualificações permanecem abertas; o ensaio Windows hospedado não aprova Windows
11 limpo nem reabertura Twine. Não houve instalação global ou criação de VM.

## Link e fontes dos builds musl — 2026-10-19

O commit `40b3e38f3dc6bef2fe64b17f66e1f812460bd7f1` passou no
[CI musl das duas arquiteturas](https://github.com/Extremois/desembaraca-twine/actions/runs/39331380978).
O relink aceita host musl da CPU correspondente, preservando o experimento
anterior glibc→musl somente em x64. Arquitetura, tradução e proveniência divergentes
continuam rejeitadas. O teste novo observou a rejeição anterior e passou após
a alteração; ELF é conferido novamente com a arquitetura real do alvo.

Os recibos de [x64](evidence/alpine-musl-link-source-2026-10-19/x86_64/summary.json)
e [ARM64](evidence/alpine-musl-link-source-2026-10-19/aarch64/summary.json) vinculam
181 objetos compilados a 322 fontes Graphviz fixadas por arquitetura. As 322
fontes foram reconferidas contra o tarball original após download. Cada build
registra nove entradas geradas, 58 externas e 66 inputs de link; x64 registra
324 extrações e ARM64, 320. Destas, libc.a contribuiu com 177/173 observações,
mais uma de libzigc.a e uma de libcompiler_rt.a por arquitetura. São extrações
observadas, sem afirmar retenção após descarte de seções ou revisão de licenças.

Os executáveis são byte-idênticos à referência do compilador e ao build original;
ZIPs/motores mantêm os hashes do recibo inicial abaixo. Proveniência, inventário,
inspeção ELF, dependências do link, extrações, corpus e rastros foram conferidos.
Os 13 casos/relocação e zero chamadas de rede passaram em CPython 3.12.13/3.14.5
em cada arquitetura, com controles positivos. Ambiente permanece container
Alpine/CPU correspondente sobre kernel Ubuntu, sem aprovação de célula Alpine.

A [fundação de seis slots](evidence/github-actions-foundation-musl-2026-10-19.json)
passou com 203 testes por slot. Localmente, a fundação passou em Python 3.12 e
3.14 com 203 testes/sete skips em cada. A suíte completa passou com 279 testes,
11 skips Windows em cada (63,331 s em 3.12 e 72,049 s em 3.14). A primeira
execução restrita falhou por acesso ao cache fora do workspace; com acesso ao
cache existente, as duas passaram. Nenhuma instalação global foi necessária.

T029/T030 permanecem parciais: revisão do material gerado/SDK, avisos completos,
fontes correspondentes, auditoria e aceitação instalada/nativa continuam pendentes.
Total **48/84**, catálogo ativo Windows preservado.

Na mesma revisão, passaram também os builds/regressões
[glibc x64](https://github.com/Extremois/desembaraca-twine/actions/runs/39331381030),
[glibc ARM64](https://github.com/Extremois/desembaraca-twine/actions/runs/39331380940)
e [macOS Intel/Apple Silicon](https://github.com/Extremois/desembaraca-twine/actions/runs/39331380907).
Esses resultados confirmam a regressão das candidatas existentes; não ampliam
a qualificação da matriz ou a aprovação dos pacotes.

## Builds musl em Alpine fixado — 2026-10-19

O commit `369c98dbf21094efda66c7abf8bca0644f638b80` passou no
[CI musl x64/ARM64](https://github.com/Extremois/desembaraca-twine/actions/runs/39330306276).
Os recibos de [x64](evidence/alpine-musl-container-2026-10-19/x86_64/summary.json)
e [ARM64](evidence/alpine-musl-container-2026-10-19/aarch64/summary.json) preservam
proveniência, inventário, inspeção ELF, imagens Docker, inventário apk,
corpus e rastros. Hashes/tamanhos/modos de cada arquivo dos ZIPs foram conferidos
após download; nenhum binário/SDK foi incorporado ao Git.

| Variante | Motor SHA-256 | Bytes | ZIP bytes |
|---|---|---|---|
| musl x86_64 | `f4dfee4e052704b1a7efdb7b6a4c43583ccaa062aec800b76224dae24eb2b69b` | 7.229.144 | 7.243.610 |
| musl aarch64 | `2d7a4b6024eb000c33ecf8b14d1a32d0aac8dde65bed00de138604d081fd3ee4` | 7.237.144 | 7.251.610 |

Ambos os ELF são estáticos, sem interpretador, seção dinâmica, bibliotecas
NEEDED ou símbolos glibc. Cada motor passou nos 13 casos e na relocação Unicode
em CPython 3.12.13 e 3.14.5; strace registrou zero chamadas de rede no corpus,
oito execuções de dot e controle positivo de conexão em processo filho por slot.
As imagens oficiais Python/Alpine 3.22 foram fixadas por digest específico da
arquitetura em `tools/runtime/alpine-ci-images.json`. Os pacotes adicionados são
registrados, sem promessa de reprodução byte-idêntica do ambiente.

A CPU corresponde ao alvo e não houve emulação; o kernel continua sendo do
runner Ubuntu (7.0.0-1017-azure x64 e 6.17.0-1022-azure ARM64). Isso não aprova
Alpine nativo, kernels/CPUs mínimos, demais versões, instalação, recuperação ou
reabertura Twine. O pacote inicial tem apenas o motor e Graphviz COPYING;
fontes/avisos do SDK, revisão de licenças e oferta de fontes permanecem abertos.
Os ledgers continuam `approved: false`/`qualified: false`, catálogo Windows
preservado e T026/T027/T029/T030 parciais; **48/84** tarefas concluídas.

As duas suítes locais passaram com 202 testes em Python 3.12 e 3.14, sete skips
Windows em cada. Os dois novos testes observaram falha antes da implementação.
A [regressão de seis slots](https://github.com/Extremois/desembaraca-twine/actions/runs/39330306797)
passou na mesma revisão.

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

### Continuação: inventário e ZIP locais do musl estático

O inventário local passou a separar medição estática de baseline de compatibilidade.
O novo flag explícito `--static-elf` aceita somente receita Linux musl com `-static`,
fatos coerentes do SDK e quatro resultados estáticos cujo relatório tem hash
vinculado à proveniência. Registra `native_linkage: static-elf` e
`minimum_libc: null`. O caminho convencional continua exigindo versão mínima;
combinar os dois modos ou usar o flag fora da criação do inventário é recusado.
Não há mudança no schema do manifesto distribuído, seleção de runtime ou catálogo.
A decisão e seus limites estão registrados em research.md.

Três testes novos cobrem empacotamento sem versão inventada, preservação do gate
de auditoria antes de executar processos, receita/SDK/medição incompatíveis,
relatório alterado e criação explícita com modos POSIX reais no WSL. O caso
positivo falhou inicialmente no contrato anterior de versão obrigatória; passou
após a implementação. A cobertura de criação POSIX é skip no Windows. Na verificação
sintética da barreira de auditoria, o Windows confere conteúdo sem simular modos
POSIX; no WSL os modos reais são conferidos.

O candidato com avisos de proveniência
`daba2f9a893a98f746a101cd3de7d07261b3af51e076690bdbb60891c5055a03`
foi inventariado em 15 arquivos. Dois empacotamentos independentes produziram ZIPs
byte a byte idênticos, com **7.355.837 bytes** e SHA-256
`dfcd0bf5641e28cb6986bbcefe41f77a348016345c824b9c388032dc908b3562`.
Conteúdo, hashes, tamanhos, modos e timestamps foram conferidos. O inventário tem SHA
`f07f0b66e2a997384bcc9041e65c841fdf195747d3c54acf265caf094c02ea5f`.
Há cópia exata do ZIP/inventário/resumo na pasta local ignorada de revisão musl,
junto dos recibos anteriores. O motor mantém os bytes dos ensaios de corpus
anteriores; não se atribuiu nova execução do corpus a esta etapa.

O inspetor real recusou o review.json incompleto com
`Reviewed audit must bind the exact build provenance`, antes do probe. Não foram
criadas auditoria aprovada, baseline nativa, URL remota ou entrada de catálogo.
A auditoria de fontes/licenças e a qualificação Alpine/ARM64/kernel/CPU permanecem
pendentes. Ver [recibo e inventário resumido](evidence/linux-musl-candidate-package.json).

Fundação: **150 testes** em Windows/Python 3.14.6 (21,872 s; 7 skips),
Windows/Python 3.12.10 (21,372 s; 7 skips) e WSL/Python 3.14.8 (43,146 s;
5 skips). Os skips não qualificam ambiente nativo. T029/T030 continuam parciais;
o total permanece **46/84**, sem VM, instalação global, commit, push ou publicação.

### Continuação: fontes dos objetos musl e avisos por arquivo

Novo coletor `tools/runtime/audit-musl-objects.py`: valida hashes do executável,
SDK/inspector, archive musl e TSV de extrações contra a proveniência do relink.
Compara os bytes de cada membro observado com seu objeto real e executa somente
readelf fixado, com profundidade DWARF limitada. Interpreta atributos apenas das
unidades de compilação de nível zero, recusa fontes externas ao SDK e compara
os fontes identificados com os bytes do arquivo SDK fixado. Não compila nem
executa o candidato; limites de 120 s agregados, 5.000 objetos/fontes, 64 MiB de
fontes e 8 MiB por saída de inspeção. Um primeiro script exploratório tentou usar
um campo archive inexistente nas linhas; foi corrigido para archive_sha256 antes
da coleta final. Nenhum resultado dessa tentativa foi usado como evidência.

Os **177 membros** libc.a observados foram associados a **177 fontes**,
237.720 bytes, todas conferidas contra o SDK. **16 fontes** têm comentários
iniciais, incluindo atribuições/termos de arquivos matemáticos, qsort e código
x86_64. O relatório preserva esses prefixos integralmente e registra o hash das
saídas DWARF privadas, sem publicar seus caminhos pessoais. Isso documenta
correspondência de metadados, não prova compilação reproduzível ou retenção de
seções. Ver [fontes observadas](evidence/linux-musl-object-sources.json).

`prepare-draft-notices.py --musl-object-evidence` exige evidência do build/SDK
exatos. Recalcula hashes das fontes e comentários diretamente no SDK fixado,
antes de gerar uma saída nova. O candidato agora tem **30 avisos/referências**
e 31 arquivos no inventário; os candidatos anteriores foram preservados.
Motor inalterado, SHA
`a58b2f30b70a0393ff0cec93d40e7b039015d1ad2bbdc8a9c60634334519942f`.
Nova proveniência SHA
`658e51e830b80642cf2915d1fc7b4cae81c0cc8c1fa12ba3fb71695760d0caf4`.
Dois ZIPs byte a byte idênticos: **7.368.435 bytes**, SHA
`471263cf178713d22502141bda44ef3d3e6c7446f8fb9ec08d219cc1eb5d5ace`.
Conteúdo/modos/hashes foram conferidos e o inspetor real continuou recusando a
auditoria incompleta antes do probe. Não houve nova execução do corpus, pois os
bytes do motor são os mesmos dos ensaios anteriores. Ver
[recibo do pacote com avisos por fonte](evidence/linux-musl-source-notice-package.json).

Quatro testes novos cobrem leitura de unidades de compilação sem confundir
nomes de funções, campos ambíguos, caminhos com espaços, fontes fora do SDK,
raiz relativa desconhecida, preservação de comentários e vínculo exato da
evidência, inclusive duplicatas/travessias. Os três primeiros falharam por falta
do coletor antes da implementação; o contrato adicional da preparação passou.
Fundação: **154 testes**, Windows/Python 3.14.6 (21,811 s; 7 skips),
Windows/Python 3.12.10 (21,159 s; 7 skips), WSL/Python 3.14.8 (44,186 s;
5 skips). Skips continuam sem valor de qualificação nativa.

T030 avançou na coleta por arquivo, mas headers transitivos, demais trechos de
fontes, startup direto, libzigc/compiler_rt/LLVM, geradores/dados e oferta completa
de fontes ainda exigem revisão. Nenhum audit aprovado foi produzido. Total
**46/84 tarefas**; Alpine/ARM64/macOS e baselines nativas permanecem pendentes,
sem VM, instalação global, mudança de catálogo, commit, push ou publicação.

### Continuação: startup e runtimes Zig do candidato musl

`tools/runtime/audit-zig-runtime.py` complementa o coletor musl com crt1.o direto
e os membros observados de libzigc.a/libcompiler_rt.a. Confere proveniência,
executável, SDK/inspector, extrações e bytes de archives/membros/objetos. Executa
somente readelf fixado, com limites de 120 s, 8 MiB por saída, 1 MiB por fonte,
5.000 referências por tabela e 64 MiB agregados de fontes. Interpreta exatamente
uma tabela DWARF4 por objeto e recusa versões/índices ambíguos ou travessias.

O startup aponta a `lib/libc/musl/crt/crt1.c`. Os dois runtimes usam nomes de CU
virtuais zigc/compiler_rt; não foram tratados como caminhos de arquivos existentes.
As tabelas identificam 1, 20 e 245 referências, respectivamente. Junto dos dois
entrypoints explicitamente coletados, foram conferidos **260 arquivos SDK**,
**1.753.358 bytes**, contra o arquivo original fixado. Fonte de entrypoint tem
rótulo próprio e não é apresentada como observação DWARF. Ver
[fontes startup/Zig](evidence/linux-musl-zig-runtime-sources.json).

Um builtin.zig gerado foi observado nos dois runtimes, com hash atual
`0795924d103f617454ad0b2eef7c93ee285efe20d2445b4cb00eba519933bd04`.
Foi copiado sem alteração para a pasta ignorada de revisão, junto do relatório.
Esse hash descreve os bytes atuais e não comprova os bytes durante o build.
Fontes geradas não foram misturadas com arquivos do SDK fixado.

Os **49 prefixos de comentários** completos foram preservados em JSON e arquivos
públicos de evidência com hashes conferidos. Um scanner limitado sinaliza linhas
com referências a licença/origem em todo o conteúdo: 17 arquivos têm indicadores,
todos dentro dos prefixos neste recorte. Existem referências a fontes portadas de
musl e Go; a coleta não decide suas obrigações. Tabelas podem superestimar fontes
com código retido, e busca textual não equivale a revisão semântica exaustiva.
Nenhum aviso foi incorporado automaticamente a um novo candidato ou aprovado.

Quatro testes novos cobrem tabelas com espaços/diretório zero, versão não prevista,
múltiplas tabelas, índices/entradas duplicados ou desconhecidos, travessias,
confinamento de builtin gerado e detecção de indicadores depois do prefixo.
Os três testes iniciais falharam por ausência do coletor antes da implementação;
o quarto validou o scanner adicionado. Fundação: **158 testes** em
Windows/Python 3.14.6 (21,755 s; 7 skips), Windows/Python 3.12.10 (21,232 s;
7 skips) e WSL/Python 3.14.8 (44,242 s; 5 skips). Skips não qualificam SO nativo.

Hashes dos ZIPs anteriores foram novamente conferidos e permanecem idênticos.
Motor e catálogos não foram alterados. T030 segue parcial: faltam revisão de
aplicabilidade por arquivo, fontes transitivas/geradores/dados e auditoria final,
além da qualificação nativa dos bundles. Total **46/84 tarefas**. Sem VM,
instalação global, execução nova do motor/corpus, commit, push ou publicação.

### Continuação: integrar comentários dos runtimes ao candidato musl

`prepare-draft-notices.py` agora aceita `--zig-runtime-evidence`, combinável com
`--musl-object-evidence`. A validação compartilhada exige tipo de relatório,
proveniência, executável e SDK exatos, caminhos canônicos/únicos e fontes dentro
do SDK permitido. Os arquivos gerados são separados e não aceitos como fontes
SDK. Antes da cópia, a preparação recalcula hash/tamanho de cada fonte e de seu
prefixo diretamente nos bytes do arquivo SDK fixado. A leitura dos comentários
presentes no JSON não é usada como fonte dos textos empacotados.

Dois testes novos falharam por ausência das funções antes da implementação e
passaram depois. Cobrem identidade exata do runtime/SDK, recusa de builtin gerado
como fonte SDK e detecção de recibos de fonte/prefixo adulterados. A extração do
validador comum preservou os testes e comportamento anteriores de avisos musl.

A execução real conferiu novamente 58 headers, nove arquivos gerados Graphviz,
177 fontes musl e 260 fontes do startup/runtime Zig. Nova saída independente:
**79 arquivos de comentários/avisos/referências**, somando os 49 prefixos Zig aos
30 anteriores, e 80 arquivos no inventário. Não inclui builtin.zig gerado. Sua
cópia local anterior para revisão permanece separada. O dot mantém SHA
`a58b2f30b70a0393ff0cec93d40e7b039015d1ad2bbdc8a9c60634334519942f`.
Nova proveniência SHA
`63bc32568e16a91385f3eba2f818896ab01fcc390388a98db7d28283dbe146ad`.

Dois ZIPs byte a byte idênticos: **7.393.576 bytes**, SHA-256
`10b37b433a85216f17c65b6e09b58b3c8c26422ea302763efd10a8a11c610410`.
Conteúdo, tamanhos, hashes e modos foram conferidos. Há cópia local ignorada
com ZIP/inventário/proveniência/review/relatório estático; avisos e recibos
públicos de evidência estão vinculados por hash. Ver
[pacote com comentários runtime](evidence/linux-musl-runtime-notice-package.json).
O inspetor real recusou o rascunho de auditoria antes do probe. Não se repetiu
o corpus para o motor inalterado nem se alteraram os candidatos anteriores.

Fundação: **160 testes** em Windows/Python 3.14.6 (22,157 s; 7 skips),
Windows/Python 3.12.10 (21,651 s; 7 skips), WSL/Python 3.14.8 (44,668 s;
5 skips). Skips não qualificam ambientes nativos. Esses comentários preservam
material de revisão, incluindo documentação/origem; não aprovam aplicabilidade,
textos canônicos ou oferta completa de fontes. T030 continua parcial e o total
permanece **46/84**, sem VM, instalação global, novo motor, promoção de suporte,
commit, push ou publicação remota.

### Organização dos commits e branch da implementação parcial

Por solicitação do mantenedor, a implementação parcial foi organizada em
`feat/003-add-cross-platform-support`, criada de `dev`. A dev local avançou por
fast-forward até origin/dev já conhecido, commit
`50105db` (merge da spec 002). O conteúdo dessa base é idêntico ao HEAD anterior
`3ad9b66`; a branch feat/002-manage-layout-runtime foi preservada. Não houve
merge da feature 003 em dev/main nem push.

Separação por assunto: renomeação da CLI; especificação/matriz; runtime POSIX e
testes compartilhados; ferramentas/workflows/testes de qualificação; documentação,
ledger e evidências. Uma única branch da spec mantém essas partes dependentes.
Os ZIPs/binários/SDKs e scratch continuam ignorados e fora dos commits.

Os bytes de código/receitas/evidências existentes foram preservados. Atributos
Git passaram a preservar também arquivos de evidência sem extensão (por exemplo,
AUTHORS/COPYING), evitando normalização CRLF que invalidaria hashes. O cabeçalho
de tasks.md foi atualizado para a branch atual e sua linha vazia final foi
removida. As validações anteriores continuam com seus commits/source_state
originais: gravar commits agora não converte ensaios dirty/WSL em qualificação
nativa. A feature permanece parcial, **46/84 tarefas**, com **160 testes** na
última regressão dos dois Pythons Windows e do Python privado WSL.


### Continuação de 2026-10-19: entrada inválida e recurso para próximo aceite

O worker de qualificação agora testa entrada UTF-8 inválida antes do primeiro
arquivo válido. Exige código 1, original intacto e nenhuma chamada de aquisição
ou rede Python, contando tentativas mesmo quando a CLI captura o erro. A
interceptação é removida antes da aquisição normal. O driver nativo exige a nova
observação; relatórios anteriores não são promovidos retroativamente. Dois testes
novos falharam por ausência do ensaio e passaram após a implementação.

A documentação PT/EN tinha uma inconsistência: o ZIP remoto da spec 002 ainda
instala twine-edge-overlap, mas o exemplo usava o novo desembaraca-twine. O README
agora fixa o commit publicado, usa o comando real dessa revisão e distingue a
branch local 003. HTTPS HEAD confirmou resposta final 200/application/zip; o
entrypoint foi conferido no commit exato do Git. Não houve nova instalação remota
nem download completo com hash. A consulta web falhou; a primeira consulta curl
foi bloqueada pelo sandbox e a consulta autorizada fora dele teve sucesso.

Fundação: **162 testes**, Windows/Python 3.14.6 (34,622 s; 7 skips),
Windows/Python 3.12.10 (34,204 s; 7 skips), WSL/Python 3.14.8 (104,798 s;
5 skips). Os doze hashes de fonte restantes do registro anterior de segurança
permanecem iguais; somente worker e seus testes mudaram nessa lista. A auditoria
anterior foi preservada. Ver [recibo](evidence/local-continuation-2026-10-19.json).

Foram restaurados acentos perdidos na escrita de registros anteriores via
PowerShell. Essa correção é textual: números, hashes e resultados permanecem.
O próximo aceite exige um executor Ubuntu 24.04 x86_64 nativo; o WSL atual não
o substitui. [Recursos e sequência](evidence/next-actions.md) distinguem essa
dependência da auditoria do bundle ainda aberta. Não houve VM, provisionamento,
CI remoto, commit/push ou publicação. T023/T048/T079/T080 seguem parciais;
total **46/84**. Alterações novas permanecem locais na branch 003.

### GitHub Actions: preparação, envio e primeira regressão remota

O mantenedor autorizou commits, envio da branch e execução no Actions. A API
confirmou repositório público, Actions habilitado e acesso de escrita/administração
existente. Nenhum segredo foi cadastrado ou exibido e nenhuma permissão ampliada.
Foram usados runners padrão hospedados, sem VM ou runner local. Workflow com
contents:read, checkout sem persistência de credenciais, 15 minutos por job da
fundação e cancelamento de execuções substituídas na mesma branch. A aceitação
Windows self-hosted continua condicionada à configuração própria e foi skip.

Foram commitados o ensaio de entrada inválida, documentação e configuração CI,
e enviada feat/003-add-cross-platform-support. A primeira execução,
[39237935160](https://github.com/Extremois/desembaraca-twine/actions/runs/39237935160),
passou Ubuntu/macOS, mas falhou em dois contratos nos dois Pythons Windows:
tempfile usava RUNNER~1 e a aplicação retornava o caminho longo equivalente.
As asserções passaram a exigir caminho absoluto, arquivo existente e mesmo
diretório por identidade filesystem, sem modificar a CLI de produção. Os testes
afetados passaram localmente antes do commit/envio da correção.

A revisão c90b18180394c05e77466eea3d571a39ca5ba1c7 passou os **seis jobs** da
[execução 39238641187](https://github.com/Extremois/desembaraca-twine/actions/runs/39238641187):
Ubuntu 24.04 X64, Windows hospedado X64 e macOS 15 ARM64, com Python 3.12/3.14.
Cada job executou **162 testes**: 5 skips em Linux/macOS e 7 em Windows. Versões
das imagens e hashes dos logs originais estão no
[recibo CI](evidence/github-actions-foundation-2026-10-19.json); os logs completos
foram mantidos na pasta local ignorada.

Esse resultado valida a fundação compartilhada sem bundle POSIX qualificado.
Não promove células da matriz nem conclui assinatura/notarização, Windows 11
limpo, macOS Intel, rede nativa offline ou revisão Twine. O total permanece
**46/84**. Não houve merge em dev/main nem publicação de release/bundle.

### Build nativo Linux no GitHub Actions — 2026-10-19

O incremento removeu a dependência de uma máquina Ubuntu fornecida pelo
mantenedor para iniciar o build. `linux-candidate.yml` usa Ubuntu 24.04 x64
hospedado, fonte Graphviz 16.1.0 e Zig 0.15.2 conferidos por tamanho/SHA-256,
SDK privado e registro da imagem/ferramentas. Dois testes novos verificam
recusa de download adulterado/truncado/excessivo e preservação de arquivo
preexistente; a regressão local passou com 164 testes, sete skips Windows.

A primeira execução parou no wrapper CMake: o argv[0] genérico impedia localizar
os módulos da instalação do runner. A correção preserva o caminho absoluto.
O build corrigido e o corpus passaram; em seguida o workflow passou a executar
também a captura de entradas de link e a conferência de fontes compiladas.

A revisão `94792d820e191a351d0fd9673fc3b25ee465e316` passou no
[build nativo 39240832314](https://github.com/Extremois/desembaraca-twine/actions/runs/39240832314)
e nos seis jobs da
[regressão 39240832316](https://github.com/Extremois/desembaraca-twine/actions/runs/39240832316).
Imagem ubuntu24 `20261012.334.1`, kernel `6.17.0-1022-azure`, CPU x64; corpus de
13 casos com Python 3.12.15 e 3.14.8, preservação dos originais, métricas sem
regressão e relocação em caminho com espaços/Unicode. A candidata tem SHA-256
`43ce8d686720467c21be91cab4b8f3b246baae49c2cfe293714ebdf8a82f5716`.

Foram capturadas 73 entradas de link, 147 extrações de bibliotecas e 181 objetos,
com 322 fontes Graphviz verificadas, nove arquivos gerados e 162 dependências
externas. O relink coincidiu em bytes com a referência do compilador. O maior
símbolo GLIBC observado foi 2.14; isso não prova execução no baseline antigo.
O alvo do compilador continua Linux 4.15/glibc 2.27. O loader dinâmico segue
entre as dependências cuja política precisa de revisão. O corpus bloqueia rede
Python, sem substituir observação nativa de rede.

O [recibo nativo](evidence/github-actions-native-linux-2026-10-19.json) vincula
corpus, proveniência, SDK e relatório de fontes preservados. A candidata fica
como artefato experimental de CI por sete dias; nenhuma release/catalogação
foi realizada. T024/T028/T036 avançaram parcialmente, mas os critérios
agregados de build/auditoria/aceite ainda faltam: contagem mantida em **46/84**.
Não foi criada VM local, nem houve merge em dev/main ou mudança global de SDK.

### Corpus Linux com observação de rede nativa — 2026-10-19

`observe-linux-network.py` executa o corpus público sob strace, seguindo
processos filhos e observando `%network,execve`. Antes do corpus, exige detectar
socket/conexão de um filho CPython contra loopback. Cada execução exige zero
chamadas da classe de rede, corpus aprovado e execuções do `dot` observadas;
trace vazio, truncado ou desconhecido reprova. Há limites de 15 s/1 MiB para
o controle e 180 s/8 MiB agregados para os 13 casos, preservando os limites de
processamento existentes por arquivo/motor. `--kill-on-exit` encerra os processos
rastreados se o tracer terminar. Só o runner efêmero recebe strace, se ausente.

Três testes novos foram observados falhando antes de existir o observador,
depois passaram: filhos/execve interrompido, tentativas falhas/sockets locais e
traces ausentes/incompletos/desconhecidos. A regressão local executou 167 testes
com sete skips Windows; o módulo de ferramentas passou com 29 testes e dois
skips específicos de plataforma.

O [primeiro ensaio](https://github.com/Extremois/desembaraca-twine/actions/runs/39241714866)
detectou o controle e aprovou o corpus, mas reprovou duas chamadas `sendfile`
da cópia de relocação feita por shutil. Essa syscall também pertence à classe
de rede do strace. A cópia passou a usar streams de arquivos via copyfileobj;
o observador manteve a exigência de zero chamadas e não recebeu exceção para
sendfile. O teste nativo foi repetido após essa correção.

A revisão `054fdb94236b64a3c9f6cd61346c7830c8d24825` passou no
[ensaio nativo 39242166311](https://github.com/Extremois/desembaraca-twine/actions/runs/39242166311)
e na [regressão das seis combinações 39242166088](https://github.com/Extremois/desembaraca-twine/actions/runs/39242166088).
CPython 3.12.15 e 3.14.8 executaram 13 casos cada, com oito execuções do `dot`
observadas por percurso e zero chamadas da classe de rede. Em cada controle,
foram detectadas socket, connect e getsockopt no processo filho. Tracer 6.8,
kernel `6.17.0-1022-azure`, imagem ubuntu24 `20261012.334.1`; o executável manteve
SHA-256 `43ce8d686720467c21be91cab4b8f3b246baae49c2cfe293714ebdf8a82f5716`.

O [recibo de rede](evidence/linux-network-observation-2026-10-19/summary.json)
vincula relatórios de corpus/rede, proveniência e traces gzip preservados.
O teste ocorreu com rede disponível, usando somente fixtures públicas; não
é isolamento de rede nem sandbox contra código hostil. A aquisição, instalação
remota, recuperação e aceite completo da célula ainda exigem seus próprios
ensaios. Nenhum gate de catálogo foi promovido. Contagem mantida em **46/84**,
com progresso parcial registrado em T036/T080 e sem VM ou mudança global local.

### Notices e ZIP candidato no CI nativo — 2026-10-19

`prepare-draft-notices.py` passou a aceitar a identidade do SDK no formato
aninhado do CI e no legado, recusando conflitos de URL/hash. O preparo confere
o executável Flex registrado no SDK e as macros 2.6.4 do scanner incluído na
evidência de compilação. O COPYING oficial do Flex foi adquirido de sua origem
upstream e fixado por tamanho/SHA-256, incluindo integralmente a exceção para
scanners gerados. Esse texto não foi substituído por uma interpretação ou por
uma classificação automática da licença do bundle inteiro.

Dois novos testes falharam antes dos helpers e depois passaram, cobrindo
identidades SDK conflitantes e versões/macros divergentes do Flex. Os dez
testes de notices passaram; a regressão local executou **169 testes**, com sete
skips Windows. O gate existente de recusa de fonte alterada foi preservado,
antes do preparo de qualquer candidata.

O workflow agora prepara os notices após capturar as fontes, gera inventário
local e ZIP e executa o corpus/rede sobre a candidata resultante. A revisão
`06c7b1c4ba09dddcd447c4c5158a20f797fb8c37` passou no
[job nativo 39243501932](https://github.com/Extremois/desembaraca-twine/actions/runs/39243501932)
e na [regressão compartilhada 39243501864](https://github.com/Extremois/desembaraca-twine/actions/runs/39243501864).
Foram conferidos 162 headers externos e nove arquivos gerados; produzidos
15 notices mais o executável, totalizando 16 entradas no ZIP de **6.137.313 bytes**.
SHA-256 do ZIP candidato:
`6b1fca184ceba8f324d465437d0f5af0b96ca54871db8eaacfe31cf2a0c2c62c`.

Após baixar o artefato Actions, foram reconferidos os hashes/tamanhos de cada
entrada, permissões do inventário, timestamps fixos e a correspondência dos
notices com review.json. CPython 3.12.15 e 3.14.8 passaram nos 13 casos com
zero chamadas da classe de rede, oito execuções do dot por percurso e controle
de conexão detectado. O executável permaneceu com hash
`43ce8d686720467c21be91cab4b8f3b246baae49c2cfe293714ebdf8a82f5716`.

O [recibo do pacote](evidence/linux-native-notice-package-2026-10-19/summary.json)
vincula inventário, proveniência, revisão, avisos originais, fontes e traces
preservados. O ledger `tools/runtime/licenses/linux.json` ganhou esse candidato
nativo, preservando os experimentos WSL anteriores. `approved` e `qualified`
continuam falsos: aplicabilidade por arquivo SDK/dados, proveniência W3C/X11,
fontes correspondentes completas e aceite nativo ainda faltam. O ZIP é somente
artefato de CI por sete dias; não houve release nem entrada POSIX no catálogo.
T028/T030 avançaram parcialmente; contagem mantida em **46/84**.

### Correspondência e reprodução dos dados Graphviz — 2026-10-19

Foram obtidas referências oficiais W3C SVG 1.1 Second Edition (2011), HTML 4.01
(1999) e X.Org rgb 1.1.0 (2022), preservadas com hashes/tamanhos e origem em
`tools/runtime/licenses/data-references/`. O arquivo X.Org foi lido sem executar
seus programas; rgb.txt e COPYING foram preservados separadamente com hashes
dos membros e do arquivo original. O CI usa esses bytes locais sem downloads
adicionais de referências.

`audit-graphviz-data.py` compara os seis inputs originais com o tar Graphviz
fixado, vincula a evidência ao executável/proveniências e recompõe as tabelas
em temporário com os geradores upstream conferidos. As saídas devem coincidir
em bytes com os headers usados na compilação e seus hashes. Limites por gerador:
10 segundos/1 MiB de stdout+stderr; leitura de referência até 1 MiB e headers até
8 MiB. O preparo de notices refaz a conferência do relatório antes de incorporá-lo.

Quatro testes foram observados falhando antes da implementação e depois
passaram: aliases conflitantes/canais inválidos, parsing W3C sem executar HTML,
diferenças inesperadas Graphviz/X.Org e material de referência fixado. A
regressão local passou com **173 testes**, sete skips Windows.

Na revisão `a605dfeb870e3f8c2039971a299272d4f075aab9`, o
[job nativo 39245172539](https://github.com/Extremois/desembaraca-twine/actions/runs/39245172539)
e a [regressão compartilhada 39245172427](https://github.com/Extremois/desembaraca-twine/actions/runs/39245172427)
passaram. Foram reproduzidos `colortbl.h` (102.902 bytes) e `entities.h` (4.751
bytes). As 147 cores SVG e as 252 entidades coincidiram com W3C; 674 cores
coincidiram com X.Org após normalização de caixa/espaços. As cinco diferenças
conhecidas são gray/grey (192 no Graphviz versus 190 no X.Org), e os três nomes
invis/none/transparent com alpha zero, ausentes nessa referência X.Org.

O pacote passou a conter 17 notices e o executável: 18 arquivos, 6.140.748 bytes,
SHA-256 `ada65a144386e1207217f8725a0335e94abc557767c6d12bb068756a8132d210`.
Foram conferidos após download todos os hashes/modos/timestamps do ZIP e
preservados os relatórios/notices/traces no
[recibo dos dados](evidence/linux-native-data-package-2026-10-19/summary.json).
Os 13 casos passaram nos dois Pythons com zero chamadas de rede observadas e
controle de conexão detectado. O executável manteve o hash do incremento anterior.

O novo COPYING X.Org e DATA-ORIGINS preservam o material de origem/referência.
O ledger diferencia correspondência numérica/reprodução de código gerado da
cadeia histórica de cópia e da decisão de aplicabilidade de licença: essas
últimas não foram aprovadas por comparação automática. Auditoria dos inputs
estáticos SDK, fontes correspondentes completas e qualificação permanecem
pendentes. Não houve admissão no catálogo nem release; T030 segue parcial e
a contagem permanece **46/84**.

### Objetos glibc, fontes observadas e texto LGPL integral — 2026-10-19

`audit-glibc-objects.py` confere a candidata, o arquivo/compiler SDK, o inspetor
e o relatório real de extrações. Os objetos de libc_nonshared devem coincidir
com os membros dos arquivos estáticos e permanecer dentro do cache registrado.
Inspeciona unidades DWARF com readelf fixado por hash, resolve fontes apenas
na árvore glibc e compara os bytes ao arquivo SDK. Limites: 120 s agregados,
10 s/8 MiB por inspeção, 64 MiB por objeto/arquivo estático e por fontes agregadas,
1 MiB por fonte. Não executa código da candidata ou faz rede.

No CI nativo foram observados crt1.o e dois membros de libc_nonshared.a,
totalizando três objetos/quatro unidades: start-2.33.S, init.c, fstat-2.32.c e
elf-init-2.33.c. abi-note.S é a quinta fonte fixada como material adicional,
distinta de uma unidade observada. Os 14 inputs SDK, inclusive compartilhados
de link e arquivos sem extrações, ficam registrados sem inferir ausência de
código por zero linhas. Cabeçalhos transitivos, assembly não observado e
retenção de seções continuam fora dessa prova.

Os cinco prefixos de comentários foram preservados por fonte. A revisão
identificou uma lacuna nos notices anteriores: glibc/LICENSES reúne avisos de
terceiros e não é o texto completo da LGPL 2.1. Foi obtido o texto oficial GNU,
fixado em 26.419 bytes/SHA-256 e incluído no pacote glibc. O prefixo de init.c
declara LGPL 2.1 ou posterior sem a exceção de link observada nos outros quatro;
as declarações foram registradas por arquivo, sem aplicar uma exceção global.

Quatro testes novos foram observados falhando antes da implementação e depois
passaram: objetos alterados/fora do cache, variantes/inputs ambíguos, notices
de outra proveniência/SDK e texto canônico alterado ou truncado. A regressão
local passou com **177 testes**, sete skips Windows; módulo de notices com
12 testes aprovados.

A primeira execução dessa etapa de objetos,
[39246694224](https://github.com/Extremois/desembaraca-twine/actions/runs/39246694224),
passou. Após a inclusão do texto LGPL integral, a revisão
`90e0accace407e4d74fef598fc5d56f84e6fc8b3` passou no
[job nativo 39247789821](https://github.com/Extremois/desembaraca-twine/actions/runs/39247789821)
e na [regressão compartilhada 39247789912](https://github.com/Extremois/desembaraca-twine/actions/runs/39247789912).
O pacote corrigido contém 23 notices e o executável: **24 arquivos, 6.177.938
bytes**, SHA-256 `2ed85bdd25236de6e5f4f11905410c30aa9e9199f95acd0c00a58bb436cde858`.
Os hashes/tamanhos/modos/timestamps foram conferidos após download, incluindo
os bytes oficiais da LGPL. Os 13 casos e o controle de rede passaram nos dois
Pythons, com zero chamadas da classe de rede no corpus e oito execuções do dot.

O [recibo glibc](evidence/linux-native-glibc-license-package-2026-10-19/summary.json)
vincula fontes, avisos, inventário, proveniência, corpus e traces preservados.
O ledger distingue declaração de licença e material observado de aprovação
de compatibilidade. Obrigações/aplicabilidade por arquivo, oferta completa de
fontes, baseline antigo e qualificação continuam pendentes. T028/T030 seguem
parciais, total **46/84**, sem admissão de runtime POSIX, release ou VM local.

## Fontes exportadas e reconstrução nativa — 2026-10-19

`pack-sources.py` reúne material de fontes separado do ZIP do runtime: tarball
Graphviz original, árvore `lib/` e licença raiz do SDK fixado, scripts/receitas,
referências de licença e os módulos Python auxiliares com licença Apache.
Não coleta compilador executável, caches ou o restante do checkout. Recusa
archives adulterados, links/traversal, proveniência/receita divergente e saídas
existentes; registra limites de expansão e manifesto por arquivo. Os dois testes
novos verificam essas recusas e a execução da receita fora do checkout.

A primeira execução encontrou falta dos módulos auxiliares exportados; o teste
isolado reproduziu a falha antes da correção. A revisão
`a84931f1464061e4225a5841f3888be3d2d851ce` passou com **179 testes locais**,
sete skips, e nas seis combinações da
[regressão compartilhada](https://github.com/Extremois/desembaraca-twine/actions/runs/39273788359).
O [workflow nativo](https://github.com/Extremois/desembaraca-twine/actions/runs/39273788202)
exportou, extraiu em diretório novo e reconstruiu o motor usando essas fontes e
receitas. O SDK compilador foi adquirido novamente por hash; os geradores e
ferramentas do host vieram da imagem registrada. O corpus usa o checkout da
execução para verificar a aplicação, sem depender dele para compilar o motor.

O pacote contém **18.150 arquivos**, incluindo **18.102 arquivos SDK**, com
68.279.518 bytes comprimidos. Todos os tamanhos/hashes do manifesto foram
conferidos após download, assim como ausência do compilador e vínculo com a
proveniência original. A candidata original passou nos 13 casos em Python
3.12.15/3.14.8; o motor reconstruído passou nos 13 casos em 3.14.8. Os três
ensaios observaram zero chamadas de rede e detectaram o controle em processo
filho. O executável reconstruído tem hash diferente: comprova reconstrução
funcional, sem alegar reprodução byte a byte.

O [recibo](evidence/linux-source-rebuild-2026-10-19/summary.json) preserva
manifesto comprimido, proveniências, corpus, traces e log de reconstrução.
O pacote grande permanece no artifact de CI por sete dias, sem incorporá-lo ao
Git ou ao download do runtime. Essa retenção temporária não constitui oferta
permanente de fontes. Revisão por arquivo, auditoria completa, baseline antigo
e qualificação instalada seguem pendentes; T030/T066 continuam parciais,
**46/84**, catálogo POSIX sem promoção.

## Builds macOS nativos iniciais — 2026-10-19

O workflow `macos-candidate.yml` constrói cada arquitetura em seu próprio runner
macOS 15: Intel e Apple Silicon. O preparador recusa outro SO/arquitetura ou
Rosetta e exige Xcode 16.4 build 16F6 e SDK 15.5; não usa `xcode-select` global,
credenciais Apple ou mecanismos de bypass. Bison vem do runner efêmero, com
instalação Homebrew somente quando ausente. O compilador/CMake são conferidos
pelos hashes do registro SDK antes do build. O alvo mínimo da receita é 15.0.

A revisão `5f7694fe5c9fd9c3995d9e00466d1cc1b2836299` passou nos
[dois jobs nativos](https://github.com/Extremois/desembaraca-twine/actions/runs/39276064428).
Cada arquitetura executou os 13 casos e a relocação com espaços/Unicode em
CPython 3.12.10 e 3.14.7, preservando entradas/dados e sem regressões. A
interceptação de rede desse smoke cobre chamadas Python; não é observação
nativa de syscalls nem ensaio de instalação offline/Gatekeeper.

Após baixar os artefatos, foram conferidos inventário, ZIP, hashes/tamanhos/modos,
timestamps e vínculo com a proveniência. Os load commands Mach-O foram lidos
diretamente dos bytes: arquitetura thin correta, LC_BUILD_VERSION com mínimo
15.0/SDK 15.5, loader `/usr/lib/dyld`, zero LC_RPATH e dependências dinâmicas
somente em `/usr/lib/libSystem.B.dylib` e `/usr/lib/libc++.1.dylib`.
O [recibo inicial](evidence/macos-native-initial-build-2026-10-19/summary.json)
preserva relatórios, comandos otool, logs e proveniências sem incorporar binários.

A conferência encontrou hashes de despachantes `/usr/bin` nos registros de
Flex/make/otool. A revisão seguinte resolve os executáveis reais por `xcrun`,
usa make explícito e propaga `DEVELOPER_DIR` ao build. Foi acrescentado um
inventário limitado da árvore SDK com hashes de arquivos e destinos de links
internos; arquivos Apple não são copiados para o artifact. O teste de identidade
SDK foi observado falhando antes da implementação e depois passou; a regressão
local atual soma **182 testes**, sete skips Windows.

A execução consolidada da revisão `17670cda323ea82af55f5a5910f03068d2997d66`,
[39279242817](https://github.com/Extremois/desembaraca-twine/actions/runs/39279242817),
ainda estava na fila ao preparar este registro. Por isso o recibo inicial não
recebe campos do SDK que não mediu, e T049/T050 continuam parciais. Pacotes de
build têm somente o aviso Graphviz inicial: auditoria/fontes/notices completos,
assinatura/notarização e aceite instalado são pendências T051/T052/T056.

## Conclusão dos builds macOS T049/T050 — 2026-10-19

A [rodada consolidada 39279242817](https://github.com/Extremois/desembaraca-twine/actions/runs/39279242817)
da revisão `17670cda323ea82af55f5a5910f03068d2997d66` passou em ambos os
runners nativos. Os pacotes baixados foram conferidos contra seus inventários,
proveniências e hashes, incluindo cabeçalhos/load commands Mach-O. Os binários
e ZIPs permaneceram iguais aos da rodada inicial em cada arquitetura.

O SDK completo registra **37.452 entradas e 656.877.420 bytes** por build;
o digest canônico `23b430378377d48cf9c2c8c95d87ac0638eef76caaa637b496d87f7ce512ab4c`
foi recalculado do inventário e conferido com o registro SDK de cada arquitetura.
Flex/make/otool agora identificam as ferramentas reais no Xcode 16.4 selecionado.
Os 13 casos/relocação passaram em CPython 3.12.10 e 3.14.7 em cada arquitetura.

O [recibo consolidado](evidence/macos-native-build-2026-10-19/summary.json)
preserva inventários SDK comprimidos, corpus, logs, load commands e proveniências.
Não contém SDK Apple ou binários. T049/T050 estão concluídas, **48/84**;
auditoria completa de dependências/fontes, assinatura/notarização, distribuição
real e aceite instalado permanecem em T051/T052/T056 e gates comuns. Nenhuma
entrada Darwin foi admitida ao catálogo ativo.

## Objetos e fontes macOS para auditoria T052 — 2026-10-19

`audit-macos-link.py` lê o mapa Apple produzido pelo build e exige mesmo destino,
arquitetura, hash do executável e proveniência. Hashes de membros de archives são
conferidos contra os objetos compilados; suas declarações de dependência são
lidas com limites e as fontes Graphviz são comparadas com o tarball fixado.
Inputs SDK são registrados separadamente; não há aprovação automática de licença.

A primeira rodada Intel compilou, mas o coletor recusou a decodificação UTF-8 de
símbolos com bytes arbitrários. O mapa real revelou também destino relativo e
índices sem nome. A correção decodifica estritamente apenas cabeçalho/seção de
objetos, resolve o destino relativo ao diretório de link e preserva o mapa inteiro
por hash. Índices sem nome ficam como `unnamed-map-slot`, com origem não resolvida;
não são descartados ou convertidos em prova de ausência de código. O teste novo
foi observado falhando antes da correção e depois passou; a regressão local soma
**185 testes**, sete skips Windows.

A revisão `ec91469411f9e3796debcd37b151903fd8740103` passou nos
[dois jobs macOS](https://github.com/Extremois/desembaraca-twine/actions/runs/39309593258),
na [regressão compartilhada](https://github.com/Extremois/desembaraca-twine/actions/runs/39309593365)
e no [build/reconstrução Linux](https://github.com/Extremois/desembaraca-twine/actions/runs/39309593277).
Cada arquitetura macOS vinculou **181 objetos a 322 fontes Graphviz**, com nove
entradas geradas e 217 externas. Intel registra 372 índices de objetos e Apple
Silicon 371; ambos contêm 181 índices sem nome ainda não resolvidos. As fontes
fixadas foram reconferidas independentemente após download, assim como vínculos
entre mapas, relatórios, pacotes, inventários, proveniências e corpus nos dois
Pythons. Os executáveis continuam iguais aos dos builds T049/T050.

Recibos de [Intel](evidence/macos-link-source-2026-10-19/macos-x86_64/summary.json)
e [Apple Silicon](evidence/macos-link-source-2026-10-19/macos-arm64/summary.json)
preservam mapas/relatórios comprimidos e metadados, sem binários ou headers Apple.
`tools/runtime/licenses/macos.json` registra observações e pendências por artefato.
O aviso oficial Flex Apple 35, revisão
`8548f53e24244c0a411dea128a21686b61d29df4`, foi obtido e comparado byte a byte:
1.855 bytes, mesmo SHA-256 do texto upstream já preservado. A origem Apple está
fixada em `material-source-lock.json`; essa igualdade não prova correspondência
do scanner gerado ou aprovação do bundle completo.

T052 permanece parcial, sem auditoria aprovada, oferta permanente, assinatura ou
notarização. T051 depende de identidade Developer ID Application e perfil
notarytool em ambiente Mac autorizado; sua disponibilidade foi solicitada ao
mantenedor, sem solicitar valores de credenciais. A auditoria e os trabalhos
Linux podem avançar independentemente dessa informação. Total **48/84**.

## Rascunhos de avisos macOS por build — 2026-10-19

`prepare-macos-notices.py` prepara uma candidata nova, mantendo o build original.
Recalcula a observação de objetos/fontes, confere os arquivos gerados e cada
header contra seus hashes observados e exige o executável Flex real do Xcode.
A variante Apple aceita somente `flex 2.6.4 Apple(flex-35)` com macros de scanner
2.6.4 e o texto fixado na revisão Apple; o percurso Linux continua separado.
Comentários iniciais dos headers são preservados com origem, offset/tamanho e
hash; ausência de prefixo seria registrada como pendência, sem inventar aviso.

Dois testes novos cobrem variante/versão do gerador, origem fora do Xcode e bytes
alterados do header. Foram observados falhando antes da implementação e depois
passaram. A regressão local soma **187 testes**, sete skips Windows. A revisão
`bbdd18a66992e213197c3a8cd2b1160f4348969b` passou nos
[dois builds macOS](https://github.com/Extremois/desembaraca-twine/actions/runs/39311029537),
na [regressão compartilhada](https://github.com/Extremois/desembaraca-twine/actions/runs/39311029512)
e no [build/reconstrução Linux](https://github.com/Extremois/desembaraca-twine/actions/runs/39311029388).

Cada pacote contém **227 arquivos de avisos**, incluindo quatro textos Graphviz,
quatro prefixos Bison, aviso Flex Apple, 217 prefixos de headers e referências de
origem. Os 217 headers de cada build tinham prefixo inicial; isso não significa
que cada prefixo contenha todos os termos aplicáveis. SDK e código dos headers
fora dos comentários não são incorporados aos pacotes. Os executáveis mantiveram
os hashes anteriores, e os 13 casos/relocação passaram nos dois Pythons em cada
arquitetura com o novo diretório de candidata.

Após download foram conferidos hashes/tamanhos/modos/timestamps dos **228 arquivos**
por ZIP e os vínculos entre review, inventário, proveniência pai/filha, fontes e
corpus. O ZIP Apple Silicon tem 1.643.394 bytes; Intel, 1.799.452 bytes. Os recibos
de [Intel](evidence/macos-draft-notices-2026-10-19/macos-x86_64/summary.json) e
[Apple Silicon](evidence/macos-draft-notices-2026-10-19/macos-arm64/summary.json)
preservam os textos de aviso e metadados, sem ZIPs/binários. O ledger macOS
registra esses rascunhos separadamente das observações anteriores.

Todos continuam com `approved: false` e `qualified: false`. Revisão por arquivo,
textos canônicos completos, dados gerados, índices sem nome, oferta de fontes,
assinatura/notarização e aceite instalado permanecem pendentes. Os arquivos
preservados são material de revisão, não uma auditoria aprovada ou liberação.
T052 permanece parcial, total **48/84**, catálogo ativo somente Windows.

### Textos completos e índice offline dos avisos macOS

O preparador agora acrescenta APSL 1.1/2.0, Apache 2.0 com exceções LLVM e GPL 3
quando encontra as respectivas declarações nos avisos preservados. Os textos
foram obtidos dos projetos oficiais Apple/IOSerialFamily/XNU, LLVM e GNU e fixados por URL,
tamanho e SHA-256 em `material-source-lock.json`. O material LLVM é uma
referência de licença, sem alegar equivalência com as fontes do compilador Apple.
Os prefixos Bison e suas exceções permanecem preservados separadamente.

`NOTICE-ORIGINS.json` acompanha a candidata e registra nome, tamanho, hash e
origem de todos os demais avisos, além dos hashes da proveniência pai e da
observação de fontes. O índice exclui explicitamente seu próprio hash para
evitar uma dependência circular; o inventário externo confere também o índice.
Todos os registros continuam sem aprovação ou qualificação.

Dois testes novos foram observados falhando antes da implementação. A suíte
local passou com **189 testes**, sete skips Windows, tanto no Python 3.12 quanto
no 3.14. A revisão `24ed0e9c2a7c1cd26d3aa418f093ed4af1903d0a` passou nos
[dois builds macOS](https://github.com/Extremois/desembaraca-twine/actions/runs/39314104394)
nas [seis combinações de regressão](https://github.com/Extremois/desembaraca-twine/actions/runs/39314104359)
e no [build/reconstrução Linux](https://github.com/Extremois/desembaraca-twine/actions/runs/39314104405).

Os ZIPs baixados contêm **233 arquivos**, sendo o executável preservado e **232
avisos**, incluindo o índice dos 231 demais. Hashes, tamanhos, modos, timestamps,
referências do índice, proveniência e corpus foram conferidos após download.
Os 13 casos passaram nos dois Pythons por arquitetura. Recibos de
[Apple Silicon](evidence/macos-offline-notices-2026-10-19/macos-arm64/summary.json)
e [Intel](evidence/macos-offline-notices-2026-10-19/macos-x86_64/summary.json)
preservam textos novos e metadados comprimidos, sem duplicar os demais headers
ou incorporar executáveis. Os ZIPs medem 1.882.436 e 2.038.789 bytes,
respectivamente. Há duas declarações APSL 1.1 no ARM e três no Intel; APSL 2.0
aparece em 179/183 avisos, LLVM em 24 e GPL nos quatro prefixos Bison.

T052 permanece parcial:
aplicabilidade por arquivo, outros textos eventualmente necessários, dados
gerados, fontes, assinatura e aceite instalado ainda exigem conclusão.

### Primeiro workflow Linux glibc ARM64 nativo

O preparador Linux aceita x86_64/aarch64, exigindo correspondência com o host
antes de criar diretórios ou baixar material. O tarball ARM64 Zig 0.15.2 tem
49.471.996 bytes e SHA-256
`958ed7d1e00d0ea76590d27666efbf7a932281b3d7ba0c6b01b0ff26498f667f`,
conferido contra o índice oficial. O executável de 158.849.208 bytes tem SHA-256
`931b8e9a9327dac87bc439067f07604219510fa541133ff6e542c6243968cc86`.
O alvo é `aarch64-linux.4.15-gnu.2.27`, CPU baseline, sem traduzir flags x86.

Dois testes novos verificam seleção de arquitetura e executam o código do wrapper
com interceptação de execv, incluindo recusa de flags x86 no ARM. Foram observados
falhando antes da implementação; a suíte local passou com **191 testes**, sete
skips Windows. O workflow independente `linux-arm64-candidate.yml` prepara build,
inspeção ELF/loader/símbolos e corpus/rede nos dois Pythons no Ubuntu ARM64 nativo.
O [primeiro build nativo](https://github.com/Extremois/desembaraca-twine/actions/runs/39316088153)
da revisão `3021bdd3d0477d5c94ea3514dd5d0c742a60ad0a` passou. O
[recibo ARM64](evidence/linux-arm64-native-build-2026-10-19/summary.json) preserva
SDK/proveniência, readelf, corpus, observação/controle de rede, inventário e log.
O runner registrou imagem `ubuntu24-arm64` `20261012.149.1`, kernel
`6.17.0-1022-azure` e glibc 2.39. Os Pythons nativos foram 3.12.15 e 3.14.8.

Após download, hashes/tamanhos/modos/timestamps do ZIP foram conferidos;
cabeçalho ELF AArch64 e segmento PT_INTERP foram lidos diretamente do binário.
O motor tem 6.801.616 bytes, SHA-256
`933b6c63370bdd3e814627e2a9a06176416c8da017a21dcbc96d8137dbc17e22`,
loader `/lib/ld-linux-aarch64.so.1`, dependências libc/libm/libpthread e maior
símbolo glibc 2.17 observado. Não foram observados RPATH/RUNPATH no readelf.
Isso não substitui execução em kernel/CPU/glibc antigos.

Os 13 casos e relocação Unicode passaram em cada Python; strace acompanhou
oito execuções do motor por slot, sem chamadas de rede no corpus. O controle
positivo em subprocesso detectou sockets/conexões e todos os hashes dos rastros
foram conferidos. O pacote de 6.816.082 bytes contém somente o motor e COPYING
Graphviz; não há fechamento de fontes/objetos ou avisos completos aprovado.
T025/T028/T030 permanecem parciais, total **48/84**, sem promoção de suporte.

A mesma revisão passou na
[regressão de seis combinações](https://github.com/Extremois/desembaraca-twine/actions/runs/39316088056),
nos [dois builds macOS](https://github.com/Extremois/desembaraca-twine/actions/runs/39316088020)
e no [build/reconstrução Linux x64](https://github.com/Extremois/desembaraca-twine/actions/runs/39316088025).

### Objetos e fontes do link Linux ARM64

`relink-zig.py` agora aceita glibc aarch64 no host nativo correspondente e
confere OS/arquitetura/ABI da receita e proveniência antes de criar a saída.
Permanece exigindo igualdade de bytes entre o link LLD observado e a referência
do compilador. A captura musl continua restrita ao percurso x64 estático existente.
O novo teste de seleção foi observado falhando antes da implementação; os
testes de recusa de link divergente e de musl sem inspeção continuam passando.
A suíte local passou com **192 testes** em Python 3.12 e 3.14, sete skips Windows.

A revisão `5e689a956cb70657e9872609688072ef50e5793b` passou na
[captura ARM64 nativa](https://github.com/Extremois/desembaraca-twine/actions/runs/39317852362).
O [recibo de fontes](evidence/linux-arm64-link-source-2026-10-19/summary.json)
preserva proveniência pai/filha, metadados LLD, evidência de objetos/fontes,
inventário, corpus e rastros. Depois do download foram conferidos hashes e modos
do pacote, vínculos dos relatórios, ELF/loader e as **322 fontes Graphviz**
novamente contra o tarball fixado. O motor e o ZIP permaneceram byte-idênticos
ao primeiro build ARM64, com hashes `933b6c…17e22` e `60d6bb…6f703`.

Foram observados **181 objetos**, **nove arquivos gerados**, **181 entradas
externas**, **73 entradas do link** e **148 linhas de extração**. O SDK teve
dois membros de libc_nonshared (fstat e elf-init) e um de libcompiler_rt,
`libcompiler_rt_zcu.o`, solicitado pelo símbolo `__extendsftf2`. Esses registros
não provam retenção de seções ou fontes correspondentes completas; o membro
compiler_rt exige revisão própria e não recebe aprovação por comparação com x64.

Os 13 casos, relocação e zero chamadas de rede observadas passaram em ambos os
Pythons, com controle positivo conferido. T028/T030 continuam parciais: SDK,
material gerado, avisos completos, fontes/reconstrução e aceite instalado seguem
pendentes. Catálogo somente Windows e total **48/84** preservados.

A revisão também passou na
[regressão compartilhada](https://github.com/Extremois/desembaraca-twine/actions/runs/39317852478),
no [build/reconstrução Linux x64](https://github.com/Extremois/desembaraca-twine/actions/runs/39317852242)
e nos [builds macOS Intel/Apple Silicon](https://github.com/Extremois/desembaraca-twine/actions/runs/39317852374).

### Fontes SDK ARM64: compiler_rt e glibc

A revisão `f3144197249fbbe0774d1c453431b913aea61bc1` passou na
[coleta nativa ARM64](https://github.com/Extremois/desembaraca-twine/actions/runs/39321396516).
Os coletores mantêm os percursos separados: um membro compiler_rt, três objetos
startup/libc_nonshared e nenhuma aprovação automática de novas bibliotecas.
Dois testes foram observados falhando antes da implementação; a regressão local
Python 3.14 passou com 194 testes. Uma falha Windows intermitente na rodada
Python 3.12 foi investigada e corrigida separadamente, conforme registro abaixo.

O [recibo SDK](evidence/linux-arm64-sdk-sources-2026-10-19/summary.json) preserva
os relatórios vinculados à proveniência exata. O runtime teve **246 fontes SDK**
observadas e conferidas, 45 com comentários iniciais e 17 com indicadores de
licença; um `builtin.zig` gerado foi apenas identificado por hash. Glibc teve
**três objetos, quatro unidades observadas e cinco fontes** incluindo material
startup adicional, todas com prefixos preservados. As **251 fontes** foram
reconferidas após download diretamente no tarball SDK fixado, incluindo bytes,
prefixos e indicadores. Corpus/relocação/rede passaram nos dois Pythons;
executável e ZIP permaneceram byte-idênticos ao primeiro ARM64.

Tabelas de arquivos DWARF podem incluir material que não foi retido no binário.
O hash atual de builtin gerado não comprova seus bytes no momento da compilação.
Fechamento transitivo, aplicabilidade por arquivo, avisos completos, fonte
correspondente/reconstrução e qualificação continuam pendentes. T030 parcial,
total **48/84**, sem promoção de catálogo.

A revisão passou também na
[regressão compartilhada](https://github.com/Extremois/desembaraca-twine/actions/runs/39321396490),
no [build/reconstrução x64](https://github.com/Extremois/desembaraca-twine/actions/runs/39321396481)
e nos [builds macOS](https://github.com/Extremois/desembaraca-twine/actions/runs/39321396487).

### Corrida Windows na inicialização do lock de preparação

A regressão local Python 3.12 encontrou `PermissionError` em `stream.flush()`
quando duas preparações concorriam: o byte inicial podia ser gravado depois
que outro processo já o havia bloqueado. A gravação foi removida;
[`_locking` admite bytes além de EOF](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/locking),
portanto não é necessário materializar o byte para coordenar processos.

O teste novo mantém o byte de um arquivo vazio bloqueado em outro processo e
exige timeout limitado do concorrente, sem escrita nem interrupção do dono.
Reproduziu deterministicamente o PermissionError com o código anterior e
passou com a correção; após liberar o dono, o mesmo arquivo pode ser bloqueado.
A suíte passou com **195 testes**, sete skips Windows, em Python 3.12 e 3.14.

Os casos de primeira preparação concorrente e lock vazio passaram também em
três repetições locais cada (seis ensaios). O commit `cadc80c`, incluído na revisão
`cfecd1b28a83abab2700d299635301981759b68f`, passou nos
[seis slots de regressão](https://github.com/Extremois/desembaraca-twine/actions/runs/39322109441),
incluindo execução do caso novo no Windows com Python 3.12 e 3.14. O job separado
de aceite Windows 11 nativo continua pendente/skipped por ausência de runner
configurado; essa regressão não o substitui.

### Pacote ARM64 com avisos e índice offline

`prepare-draft-notices.py` agora aceita o build glibc aarch64 com receita e
proveniência nativas correspondentes. Exige relatórios próprios de glibc,
compiler_rt e dados gerados; recusa relatório de outra variante mesmo se os
demais campos coincidirem. Reconfere bytes do executável, fontes/prefixos,
headers, saídas geradas e material de licença contra as origens fixadas.
Três testes novos cobrem esses contratos; dois foram observados falhando antes
da implementação. A suíte local passou com **198 testes** em Python 3.12/3.14,
sete skips Windows.

A revisão `542d060db9f73797c3b49f290e030fec3c588ac6` passou no
[workflow ARM64 nativo](https://github.com/Extremois/desembaraca-twine/actions/runs/39322753386).
O [recibo da candidata](evidence/linux-arm64-draft-notices-2026-10-19/summary.json)
preserva **229 avisos**, proveniência pai/filha, relatórios e corpus. Inclui
prefixos de 159 headers e 50 fontes SDK, textos SDK e LGPL/GPL completos,
Graphviz/Bison/Flex, referências de dados e índice offline dos **228 outros
avisos**. Os 22 headers sem prefixo estão registrados, sem presumir ausência
de obrigações. O índice exclui seu próprio hash; o inventário externo o inclui.

Após download foram conferidos os **230 arquivos** do ZIP, hashes, modos,
tamanhos/timestamps, origens do índice, todos os **181 headers** e os textos
retirados do SDK diretamente contra o tarball fixado. As 251 fontes dos
relatórios SDK também foram reconferidas com prefixos/indicadores. Os 13 casos,
relocação Unicode e zero chamadas de rede observadas passaram em ambos os
Pythons. O pacote tem **7.262.834 bytes**, SHA-256
`b28c394674b104482710a16d37852b36630d5bfacb971f114491aa5483cfaf65`.
O motor mantém `933b6c…17e22`.

Os textos são rascunhos vinculados aos bytes, com `approved: false` e
`qualified: false`. Não encerram aplicabilidade por arquivo, possíveis textos
adicionais, retenção de seções/fechamento transitivo, oferta completa de fontes,
reconstrução ou qualificação de células. T030 parcial, **48/84**, catálogo ativo
somente Windows.

A revisão passou também na
[regressão de seis slots](https://github.com/Extremois/desembaraca-twine/actions/runs/39322753407),
no [build/reconstrução Linux x64](https://github.com/Extremois/desembaraca-twine/actions/runs/39322753406)
e nos [builds macOS Intel/Apple Silicon](https://github.com/Extremois/desembaraca-twine/actions/runs/39322753572).

### Fontes exportadas e reconstrução ARM64

`pack-sources.py` seleciona o SDK glibc x64/ARM64 pelo artifact_id, confere
arquivo/receita/proveniência e exige identidade nativa aarch64 no percurso ARM.
O novo teste foi observado falhando antes da implementação; valida exportação
ARM e recusa de SDK/arquitetura divergentes antes de criar a saída.
A suíte local inicial passou com **199 testes**, sete skips Windows.

A revisão `162a57bd67817809f38e8801336bb87eecc0ead7` passou na
[reconstrução ARM64](https://github.com/Extremois/desembaraca-twine/actions/runs/39325624157),
no [build/reconstrução x64](https://github.com/Extremois/desembaraca-twine/actions/runs/39325624176)
e nos [builds macOS](https://github.com/Extremois/desembaraca-twine/actions/runs/39325624652).
A regressão compartilhada encontrou a falha numérica descrita abaixo; seu
resultado original não foi substituído por aprovação.

O [recibo ARM64](evidence/linux-arm64-source-rebuild-2026-10-19/summary.json)
preserva manifesto comprimido, proveniências original/reconstruída, log,
corpus e rastros/controlos de rede. O pacote tem **68.324.128 bytes**, SHA-256
`00afe5506d3ba7117a7255bcf9c071882f6aba5d67a3399843b80c0d646a3271`.
Após download foram conferidos **18.158 arquivos**, seus modos/timestamps,
tamanhos/hashes, proveniência e receita. Os **18.102 arquivos SDK** foram também
comparados com o tarball Zig ARM64 fixado, sem incluir o compilador executável.
O material inclui árvore lib/ completa, com componentes de outras plataformas;
isso não declara sua presença no dot.

O workflow extraiu o pacote em pasta nova, readquiriu o compilador por hash,
copiou a árvore SDK exportada e executou as receitas/módulos Python exportados
com cache privado novo. Os testes do resultado usam o checkout público da mesma
execução, conforme REBUILD-SOURCES.md. O motor reconstruído tem SHA-256
`e5cca07b6a9a80b7ba9d58910baf25be550a62dbbb54e498f5f3da83103967bb`;
é diferente de `933b6c…17e22`, portanto a reconstrução demonstrada é funcional.
Os 13 casos/relocação e zero chamadas de rede observadas passaram no Python
3.14.8 reconstruído; a candidata original passou nos slots 3.12.15/3.14.8.
Hashes dos relatórios e rastros, inclusive controles positivos, foram conferidos.
O relatório ABI do reconstruído registra libc/libm/libpthread e maior símbolo
glibc 2.17; não acrescenta qualificação no kernel/CPU ou distribuição mínimos.

O artifact de sete dias não é oferta permanente ou auditoria aprovada. Revisão
por arquivo, fechamento transitivo/obrigações, disponibilidade das fontes e
aceite nativo por célula permanecem pendentes. T030/T066 parciais, **48/84**.

### Limite do timeout rolling após arredondamento

A [rodada inicial](https://github.com/Extremois/desembaraca-twine/actions/runs/39325624416)
falhou somente no Windows Python 3.12 ao verificar que cada consulta recebesse
no máximo cinco segundos. A subtração de ponto flutuante podia resultar em
`5.000000000000002` mesmo sem tempo decorrido. Um relógio controlado em 11.002
reproduziu a falha; `min(SECONDS, deadline - clock())` conserva o prazo agregado
restante e impõe também o teto da consulta. O teste novo falhou antes da correção.

O commit `456059b4fbb5b943cf83b842500d8e5a4a8313b3` passou nos
[seis slots de regressão](https://github.com/Extremois/desembaraca-twine/actions/runs/39326296051).
As suítes locais Python 3.12/3.14 passaram com **200 testes**, sete skips Windows.
Log original e resultado corrigido estão preservados separadamente no recibo
de reconstrução; a falha original continua registrada como failure.

A revisão corrigida também passou novamente nas
[reconstruções ARM64](https://github.com/Extremois/desembaraca-twine/actions/runs/39326296041)
e [x64](https://github.com/Extremois/desembaraca-twine/actions/runs/39326296085),
além dos [builds macOS Intel/Apple Silicon](https://github.com/Extremois/desembaraca-twine/actions/runs/39326296072).
