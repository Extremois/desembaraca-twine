# Registros por alvo

Reconstrução glibc modificada: [relink com biblioteca glibc modificada comprovado sob LGPL 2.1 §6(a)/§6(d)](modified-glibc-relink-2026-10-21/README.md)
em `linux-glibc-x86_64` e `linux-glibc-aarch64` no checkpoint `bead45d`, sem recompilar
objetos Graphviz e com zero chamadas de rede nativa no corpus.

Incremento de fontes/avisos: [seis bundles conferidos no checkpoint 62489c8](source-access-notices-2026-10-20/README.md).
Declaração EPL e aviso glibc/LGPL confirmados nos ZIPs, cinco workflows aprovados;
compatibilidade e entrega final das fontes continuam pendentes. As provas de
cache anteriores mantêm seus hashes, separadas desses pacotes atualizados.

Cada registro de QualificationEvidence contém:

- id, target_id, python_minor (quando aplicável), python_patch, python_origin;
- application_revision, artifact_id, artifact_sha256, recipe_revision;
- image_id/digest, os/version, kernel, cpu, architecture, environment_kind;
- snapshot_id e inventário canônico do ambiente de teste para rolling;
- captured_at UTC, comandos executados, status/código/resultado e identificação dos logs;
- hashes de originais/saídas, invariantes e três métricas antes/depois;
- observação de tentativas de rede; preparo/reparo/falhas/interrupção/crash/concorrência;
- Twine versão, seis saídas reabertas, revisor e referência à evidência visual;
- limitações, simulações, passos não executados e pending_reason.

environment_kind distingue native, wsl, container, emulated e simulated. Valores simulados não aprovam alvos nativos. Cada SupportTarget possui dois slots PythonQualification, 3.12 e 3.14; só pode ser validado com ambos e gates comuns completos na mesma revisão/artefato/snapshot.

Não conter histórias privadas, caminhos pessoais desnecessários ou credenciais. Inventário público é exclusivamente do ambiente de teste. Não gerar resultado fictício para preencher campos ausentes: manter o ensaio e a tarefa pendentes.

O coletor distingue `checks` observados de `pending_checks`: ausência de ensaio
não é aprovação nem falha observada. `source_state: dirty` impede promoção de
suporte. Logs publicados usam caminhos relativos e SHA-256 verificado; os
registros de regressão local não substituem a evidência nativa por célula.

Somente licenças e revisão Twine podem ser gates comuns aos dois Pythons.
Instalação, primeiro uso, offline e preservação exigem evidência própria em cada
slot. Revisão Twine deve identificar versão, revisor e hashes das seis saídas
efetivamente reabertas; testes de geometria não a substituem. A proposta de
promoção não altera automaticamente o catálogo ou o registro de suporte.

O estado consolidado está em [support-ledger.md](support-ledger.md); os resultados
locais mais recentes e seus limites estão em [validation.md](../validation.md).

`package-installation.json` indexa a evidência parcial da T078: vinte instalações
dos wheel/sdist atuais em dez combinações hospedadas, com recibos/hashes em
`current-packages-2026-10-20/`. A tarefa continua aberta para candidatas finais
remotas, motor privado e restante da matriz, sem promoção de suporte.

`installed-private-engines-2026-10-20/` complementa esse índice com os motores
reais em wheel/sdist instalados, sem aplicação fonte no driver. Os índices
`linux-ubuntu-24.04.json` e `macos.json` continuam parciais: transporte controlado,
guard de rede Python e gates finais pendentes não aprovam uma célula.

`windows-review-003/` contém seis saídas públicas efetivamente produzidas no
Windows atual, com hashes vinculados a `windows-review-collection.json`.
`review_status: pending` registra ausência de revisão visual. Não usar esses
arquivos como prova de execução Linux/macOS. `security-limits.json` consolida a
auditoria dos mecanismos de código/contratos da T080, concluída com a
[revisão de 2026-10-20](security-audit-2026-10-20/README.md). Não encerra ensaios
nativos por célula, aceitação dos pacotes finais ou auditorias de distribuição.

`linux-wsl-candidate-inventory.json` é inventário real do rebuild experimental sem
RPATH; não é manifesto do runtime e não contém URL. `local-inventory-smoke.json`
vincula o inventário, o log de build redigido e os testes. O corpus correspondente
está em `linux-wsl-no-rpath-corpus.json`. A glibc mínima e a auditoria de dependências
continuam pendentes; esses arquivos não aprovam Linux nativo ou outra arquitetura.

`candidate-packaging-smoke.json` registra dois ZIPs reais do build WSL com bytes
idênticos, inventário/modos conferidos e recusa de sobrescrita. Os ZIPs não foram
publicados; `qualified: false` continua explícito. Empacotar não concede aprovação
de dependências/licenças, ABI, assinatura ou ensaios nativos por célula.

`linux-linkage-capture.json` registra os arquivos reais lidos pelo linker em outro
build WSL e seus hashes, com caminhos SDK redigidos. Não é prova dos membros
incorporados de cada arquivo estático nem aprovação jurídica. O ledger
`tools/runtime/licenses/linux.json` permanece não aprovado; nenhuma variante
recebe suporte por esse levantamento.

`linux-prerequisites.md` documenta a obtenção privada de CPython 3.12.15 e 3.14.8
no WSL existente. `linux-private-python-prerequisites.json` registra arquivos,
hashes, venv/pip e duas execuções da fundação. `linux-package-installation.json`
e seu log registram quatro instalações reais de wheel/sdist fora do checkout.
O catálogo somente Windows recusou processamento POSIX como esperado; esses
ensaios parciais não aprovam primeiro uso, offline ou células nativas.

`linux-zig-baseline.json` registra um experimento privado de Graphviz com Zig
0.15.2/alvo glibc 2.27: build completo, símbolos até 2.14, ausência de RPATH e
recusa de uma dependência não aprovada. Inclui hashes, wrappers redigidos e
logs das quatro tentativas. `linux-zig-corpus-3.12.json` e
`linux-zig-corpus-3.14.json` vinculam o mesmo executável aos 13 casos públicos
e relocação. `qualified: false` é obrigatório: não há auditoria LLVM, captura
equivalente das entradas do linker, execução no baseline antigo ou célula
nativa aprovada. Esses relatórios não substituem os builds GCC anteriores.

`linux-zig-lld-capture.json` registra o build posterior com alvo explícito de
kernel Linux 4.15/glibc 2.27 e captura real de 73 entradas pelo LLD direto.
O hash do executável coincide com a referência do driver; os seis arquivos
estáticos SDK e 11 arquivos de licença observados têm hashes registrados,
sem auditoria aprovada. `linux-zig-lld-corpus-3.12.json` e
`linux-zig-lld-corpus-3.14.json` cobrem 13 casos e relocação desses mesmos bytes.
O corpus foi executado no primeiro relink, e a segunda saída preservou bytes
enquanto passou a classificar os arquivos Graphviz no escopo do build pai.
Logs redigidos estão em `linux-zig-lld-capture.logs/`. O alvo de kernel, a nota
ABI e os símbolos medidos não substituem execução no baseline antigo; os
registros anteriores continuam preservados como evidência histórica.

`linux-zig-sdk-source-audit.json` registra uma nova execução de relink com
`--why-extract`: 147 extrações observadas, vinculadas a arquivos já identificados
por SHA-256. Entre os arquivos estáticos SDK, somente `libc_nonshared.a` teve
linhas de extração neste comando: `fstat-2.32.o` e `elf-init-2.33.o`. `crt1.o`
é entrada direta. Zero linhas dos outros arquivos não dispensam revisão de
templates, código inline ou headers incluídos nos objetos Graphviz.

Foram comparados 1.947 arquivos de fontes/headers/avisos de cinco diretórios
SDK com o arquivo de distribuição cujo SHA foi verificado. O relatório contém
contagens, hashes canônicos e algoritmo dos manifestos, fontes selecionadas e
avisos copiados em `linux-zig-sdk-source-audit/`, junto dos logs redigidos.
Os manifestos completos permanecem no SDK privado; o arquivo de distribuição
fixado permite recalculá-los. Não são árvores completas dos projetos upstream.
`source_to_binary_complete: false`, `approved: false` e `qualified: false`
registram a revisão ainda incompleta de fontes, includes, exceções por arquivo
e obrigações de distribuição. Nenhum aviso foi adicionado ao bundle candidato
como se a auditoria já estivesse concluída.

`linux-graphviz-source-audit.json` cruza as extrações reais com objetos compilados
por igualdade de bytes e com seus arquivos `.o.d`. São 181 objetos, 322 fontes/
headers Graphviz verificados contra o arquivo original, nove arquivos gerados e
162 headers externos. O relatório revalida executável, proveniência pai,
metadados de linkedição e TSV de extrações antes de aceitar os vínculos.
Referências de dependências usam índices numéricos para evitar repetir caminhos;
o hash do relatório privado original foi preservado, e a cópia pública tem
caminhos privados redigidos.

`linux-graphviz-source-audit/` contém três avisos candidatos copiados do arquivo
original e conferidos por hash: `AUTHORS`, `COPYING` e `lib/rbtree/LICENSE`.
Os demais nomes de avisos do arquivo permanecem candidatos, sem presumir sua
aplicação. Os parsers gerados por Bison e os identificadores de licença dos
headers externos exigem revisão própria. `approved: false`, `qualified: false`
e `declared_source_to_binary_complete: false` permanecem explícitos.

`linux-notice-draft.json` registra uma candidata privada nova com 14 arquivos
de avisos/referências, executável inalterado, 162 headers externos comparados
com o SDK fixado e nove arquivos gerados conferidos contra a evidência.
`linux-notice-draft/` contém os avisos exatos e o log da recusa da auditoria
incompleta pelo inspetor. Inclui o aviso ColorBrewer presente em `brewer_colors`,
preservado além dos arquivos nomeados `LICENSE`/`COPYING`, e os prefixos de
licença/exceção dos quatro arquivos Bison.

O ZIP de 15 arquivos ficou somente em armazenamento local privado; seus hashes, inventário/modos
e conferência de payloads estão no relatório. Nem o ZIP nem o executável foram
copiados para a evidência pública. Fonte/oferta completa, aplicabilidade dos
avisos e origens dos dados W3C/color_names continuam em revisão. Essa candidata
não é um bundle qualificado ou uma auditoria aprovada.

Uma cópia idêntica para revisão no Windows está na pasta ignorada
`tools/runtime/artifacts/linux-glibc/linux-glibc-x86_64-notice-draft/`, com ZIP,
inventário, resumo, proveniência e registro de revisão. A cópia do ZIP preserva
os modos codificados e seus hashes; não foi extraído como runtime Windows.

`linux-musl-static.json` registra um build separado de musl x86_64 totalmente
estático, executado como experimento explícito entre libcs no WSL Ubuntu/glibc.
Contém fatos do SDK/host/alvo, inspeção ELF sem interpreter, seção dinâmica,
NEEDED ou símbolos GLIBC, 66 entradas reais do linker e 324 extrações observadas.
Os bytes do relink coincidem com a referência e com o build original.

`linux-musl-corpus-3.12.json` e `linux-musl-corpus-3.14.json` cobrem os 13 casos
e relocação desse executável. `linux-musl-graphviz-sources.json` registra seus
181 objetos/322 fontes Graphviz, nove gerados e 58 headers externos. Esses 58
headers e 2.467 arquivos da árvore musl distribuída pelo SDK foram comparados
com o arquivo original fixado. Logs redigidos e `musl-COPYRIGHT.txt` ficam em
`linux-musl-static.logs/`. A versão upstream musl não foi inferida: o SDK não
inclui VERSION, e o relatório registra `musl_version: null`.

São evidências WSL de build/corpus/integridade. Não há instalação dos Pythons
musl, aquisição normal do runtime ou aceite Alpine. Auditorias e avisos glibc
não foram reutilizados como aprovação dessa variante; Alpine nativo, ARM64,
licenças/fontes dos sete arquivos estáticos SDK e mínimos de kernel/CPU
continuam pendentes. O catálogo distribuído segue sem entrada POSIX.

`linux-musl-notice-draft.json` registra a preparação independente de 14 arquivos
de avisos/referências para o executável musl já ensaiado. Os bytes integrais
estão em `linux-musl-notice-draft/`, incluindo COPYRIGHT musl em vez de LICENSES
glibc, os três avisos LLVM, licença raiz Zig e materiais Graphviz/Bison/ColorBrewer.
Foram novamente conferidos os 58 headers e nove arquivos gerados. O relatório
ELF foi vinculado por hash e preservado na saída privada. Recibos exatos estão
também na pasta ignorada `tools/runtime/artifacts/linux-musl/linux-musl-x86_64-notice-draft/`.

As observações do linker incluem membros de libc.a, libzigc.a e compiler_rt;
contagens zero de outros archives não dispensam revisão de headers/inline.
O COPYRIGHT musl remete a termos específicos de arquivos, inclusive matemática.
A coleta não decide sua aplicabilidade nem encerra a oferta de fontes. Não foi
criado inventário/ZIP com versão musl inferida ou baseline não qualificada.
`approved: false` e `qualified: false` permanecem explícitos.

`linux-musl-candidate-package.json` registra o passo posterior: inventário
local com `native_linkage: static-elf`, `minimum_libc: null` e 15 arquivos,
seguido de dois ZIPs byte a byte idênticos de 7.355.837 bytes. A criação foi
explícita, vinculada ao build/SDK/relatório ELF estático. Conteúdo, modos e
timestamps do ZIP foram conferidos. Uma cópia exata do ZIP, inventário e resumo
está na pasta ignorada de revisão musl indicada acima. Esses arquivos complementam
os recibos de avisos existentes, sem substituir sua proveniência.

O inspetor recusou o `review.json` de rascunho por ausência de auditoria revisada
vinculada à proveniência. Inventariar e empacotar não aprovou licenças nem executou
o probe. Os bytes do motor são os mesmos já ensaiados no corpus; não houve nova
execução do corpus ou qualificação nativa. O manifesto/catálogo distribuído não
foi modificado e o ZIP continua local.

`linux-musl-object-sources.json` cruza os 177 membros musl de libc.a observados
nas extrações com os bytes dos objetos reais e suas unidades de compilação
DWARF. As 177 fontes identificadas (237.720 bytes) foram conferidas contra o SDK
fixado. Dezesseis fontes têm comentários iniciais, preservados integralmente no
relatório, incluindo atribuições de arquivos matemáticos, qsort e código x86_64.
Nomes de funções/variáveis DWARF não são tratados como fontes. Nenhum caminho
pessoal foi incluído; os hashes de saídas DWARF referem-se aos dados privados
originais, cujos textos completos não foram publicados.

`linux-musl-source-notice-package.json` registra uma nova cópia com esses 16
comentários por arquivo, somados aos 14 avisos/referências anteriores. O ZIP
tem 31 arquivos e 7.368.435 bytes, foi produzido duas vezes com bytes idênticos
e tem conteúdo/modos conferidos. Os 30 avisos públicos estão em
`linux-musl-source-notices/`; o ZIP/recibos exatos estão na nova pasta ignorada
`tools/runtime/artifacts/linux-musl/linux-musl-x86_64-source-notice-draft/`.
O candidato anterior foi preservado.

A preparação recalculou hashes dos fontes e prefixos no SDK fixado antes da
cópia. A inspeção real continuou recusando o rascunho de auditoria antes do
probe. O motor conserva o mesmo hash, portanto não houve novo ensaio de corpus.
Essa correspondência DWARF não prova compilação reproduzível, retenção de
seções ou revisão exaustiva de licenças. Headers transitivos, startup direto,
libzigc/compiler_rt/LLVM, dados/geradores e qualificação nativa seguem pendentes.

`linux-musl-zig-runtime-sources.json` complementa a coleta com os três objetos
de startup/runtime: crt1.o direto e um membro observado de cada archive libzigc.a
e libcompiler_rt.a. Hashes de archives/membros/objetos, relatório de extração e
inspector foram conferidos. As tabelas DWARF4 têm 1, 20 e 245 entradas,
respectivamente. O relatório separa referências de tabelas dos dois entrypoints
explicitamente coletados (`lib/c.zig`, `lib/compiler_rt.zig`). Ao todo foram
conferidos **260 arquivos SDK**, 1.753.358 bytes, contra o arquivo original fixado.

Os **49 prefixos de comentários** completos estão no JSON e em
`linux-musl-zig-runtime-sources/`. Dezessete arquivos têm indicadores textuais de
licença/origem, todos no prefixo inicial neste recorte; isso não equivale a uma
busca semântica exaustiva. Há referências a código portado de musl e Go que
continuam exigindo revisão específica de atribuição e termos.

Um `builtin.zig` gerado foi identificado nas tabelas dos dois runtimes e teve
seus bytes atuais inventariados separadamente. Esse hash não autentica os bytes
durante o build nem os transforma em fonte distribuída pelo SDK. Uma cópia exata
para revisão, com o relatório, está na pasta ignorada
`tools/runtime/artifacts/linux-musl/zig-runtime-source-review/`.

Tabelas de arquivos podem listar código sem seções retidas. Esses dados não
substituem fontes transitivas completas, revisão dos componentes restantes ou
auditoria aprovada. Não houve novo candidato/ZIP, alteração de notices existentes,
execução do motor, promoção de suporte ou publicação remota.

`linux-musl-runtime-notice-package.json` registra a integração posterior desses
49 prefixos Zig em uma nova cópia local, somados aos 30 arquivos de comentários/
avisos/referências anteriores. A preparação conferiu novamente todas as 260 fontes
de runtime e seus prefixos no SDK fixado, vinculando os dois relatórios de fontes
por hash à nova proveniência. O builtin gerado permaneceu separado; não há
`builtin.zig` no ZIP.

O pacote tem **80 arquivos**, **7.393.576 bytes** e foi reproduzido duas vezes
com bytes idênticos. Conteúdo, modos e hashes foram conferidos. Os 79 arquivos
de revisão estão em `linux-musl-runtime-notices/`. ZIP, inventário, proveniência,
review e relatório estático exatos estão na pasta ignorada
`tools/runtime/artifacts/linux-musl/linux-musl-x86_64-runtime-notice-draft/`.
Os candidatos anteriores foram preservados.

A auditoria incompleta foi novamente recusada pelo inspetor antes do probe.
Comentários de fontes incluem documentação e referências de origem: sua cópia
não decide aplicabilidade de licenças nem substitui textos canônicos/oferta
completa. O motor não mudou; o corpus não foi repetido. Sem qualificação nativa,
entrada de catálogo, URL de distribuição ou publicação remota.

`local-continuation-2026-10-19.json` registra o novo ensaio de entrada inválida
antes de aquisição/rede Python, a regressão de 162 testes e a conferência do
entrypoint da revisão remota Windows. A URL imutável respondeu HTTP 200 ao HEAD;
não houve nova instalação remota nem aceite POSIX. A auditoria anterior de
segurança foi preservada, com comparação dos hashes de fonte e escopo parcial.

`next-actions.md` identifica o executor Ubuntu 24.04 x86_64 necessário ao primeiro
incremento, os dados de acesso/ambiente a informar e as etapas de auditoria e
aceitação ainda abertas. Não provisiona infraestrutura nem autoriza publicação.

`github-actions-foundation-2026-10-19.json` registra a regressão remota aprovada:
seis jobs de Ubuntu 24.04 x64, Windows hospedado x64 e macOS 15 ARM64, cada um
com Python 3.12/3.14. Cada job executou 162 testes com skips explícitos. O resumo
tem versão da imagem, URL e hash dos logs originais. Não qualifica bundle POSIX,
Windows 11 limpo, macOS Intel ou revisão Twine.

A primeira execução revelou comparações textuais incompatíveis com o alias
Windows RUNNER~1. A correção exige arquivo absoluto existente e identidade de
diretório por samefile, sem depender da grafia do caminho. A falha inicial e
a revisão corrigida ficam associadas no relatório.

`github-actions-native-linux-2026-10-19.json` registra o build real em Ubuntu
24.04 x64 hospedado, captura do linker/fontes e corpus com CPython 3.12/3.14.
`documented-installation-2026-10-20/summary.json` preserva dez instalações remotas
da revisão atual `d90b567`, com 53 arquivos e LICENSE/NOTICE conferidos, três
entrypoints, venv externa e PATH sem Git/Graphviz. README/quickstart atualizados;
sem preparo de motor ou qualificação de célula. O diretório anterior continua
registrando a URL antiga. Detalhes e limites no README do novo diretório.

`recovery.json` consolida a T076 nas 69 células/138 slots, sem conceder aceite
por observação parcial. `installed-posix-recovery-2026-10-20/` preserva oito
relatórios de motores reais instalados: 64 reparos falhos, 384 referências
offline, seleção e geração anterior preservadas. Há também dez relatórios
de instalação básica e seis jobs de regressão. Escopos de injeção, negação real
e segurança macOS estão no README do diretório; T076 permanece parcial.

`installed-posix-processes-2026-10-20/` amplia os ensaios instalados com três
crashes reais e dois primeiros usos sincronizados em Ubuntu/macOS, ambas as
arquiteturas e Pythons. São 128 cenários/768 referências após falhas somando
os reparos falhos repetidos, sem aquisição offline ou regressão. O diretório
preserva recibos de runtime, pacotes, regressão e o índice anterior; `recovery.json`
mantém distribuição final, ambientes e demais células pendentes. Detalhes no README.

`distribution-integrity.json` preserva a conferência offline da T066: seis
bundles POSIX, 2.419 arquivos, 2.407 avisos vinculados ao índice de origens,
53 arquivos wheel/sdist e LICENSE/NOTICE. Oito recibos instalados foram ligados
aos mesmos quatro bundles glibc/macOS por hash. Ferramenta, fontes preservadas,
testes, entradas e limites estão em `distribution-integrity-2026-10-20/`.
Isso não aprova aplicabilidade das licenças, oferta de fontes, cache independente,
Windows ou pacotes finais; T066 permanece parcial, sem novo CI/commit.

`cache-notices-2026-10-20/` registra a medição independente dos avisos no cache
real em oito slots glibc/macOS, wheel/sdist: 6.076 arquivos comparados antes/depois
do uso offline e 16 alterações de teste recusadas/restauradas. Há recibos brutos,
instalação básica, regressão do modo anterior e seis jobs de fundação aprovados.
`distribution-integrity.json` agora consolida os recibos dos arquivos e dos caches;
o recibo original permanece em `distribution-integrity-2026-10-20/final-check.json`.
Cache musl/Windows, compatibilidade/fontes e pacotes finais continuam pendentes.

`cache-notices-more-2026-10-20/` conclui a medição técnica de avisos nos caches
dos sete bundles: 14 slots Python, 28 instalações wheel/sdist e 9.792 comparações
antes/depois do uso offline, 28 alterações recusadas/restauradas. Musl é CPU
nativa em Alpine fixado sobre kernel Ubuntu; Windows é runner hospedado com
aquisição oficial fixada. Não há aceite nativo Alpine ou Win11 limpo por associação.
`distribution-integrity.json` mantém licenças/fontes, pacotes finais e aceites
pendentes, preservando índices anteriores. Detalhes e todos os recibos no README.

Os dois relatórios `github-actions-native-linux-corpus-*.json` preservam cada
caso e suas métricas. Proveniência e SDK estão nos arquivos correspondentes;
`github-actions-native-linux-sources-2026-10-19.json.gz` preserva em gzip os
bytes originais do relatório de fontes (hashes comprimido e original no resumo).
Os relatórios continuam disponíveis após expirar o artefato Actions de sete
dias. Esse incremento é build/corpus nativo, com auditoria/aceite pendentes;
não constitui qualificação de célula, revisão de licença ou entrada de catálogo.

`linux-network-observation-2026-10-19/summary.json` registra o corpus público
da candidata Linux sob rastreamento de syscalls em Ubuntu 24.04 x64, com
CPython 3.12/3.14. Os dois controles de processo filho detectaram socket e
conexão locais; os dois percursos do corpus tiveram zero chamadas da classe
de rede e oito execuções do `dot`. O diretório preserva proveniência, relatórios
e traces gzip com hashes dos bytes comprimidos e originais. O runner tinha
rede disponível: este é um ensaio observado do corpus, sem concluir instalação,
aquisição, recuperação ou o gate offline de uma célula inteira.

`linux-native-notice-package-2026-10-19/summary.json` registra o primeiro ZIP
glibc x64 gerado no CI nativo com 15 notices, inventário e proveniência
correspondentes. Os relatórios e notices foram preservados sem os binários;
o relatório de fontes e os traces estão em gzip com hashes dos bytes originais.
Os 16 arquivos do ZIP tiveram conteúdo, tamanho, permissões e timestamps
verificados após download do artefato Actions. Inclui conferência do Flex 2.6.4,
162 headers SDK, nove arquivos gerados e corpus/rede nos dois Pythons. A
coleção permanece rascunho: não é auditoria aprovada nem distribuição admitida.

`linux-native-data-package-2026-10-19/graphviz-data-evidence.json` vincula os
seis inputs do arquivo Graphviz fixado aos dois headers reproduzidos e aos
valores das referências oficiais: 147 cores SVG, 252 entidades e 674 cores
X.Org coincidentes, com cinco diferenças Graphviz explícitas. `summary.json`
vincula esse relatório ao novo ZIP com 17 notices, inventário, proveniência,
corpus e traces nos dois Pythons. As referências usadas estão fixadas por hash
em `tools/runtime/licenses/data-references/`. Igualdade de valores e reprodução
dos headers são verificações técnicas; a cadeia histórica de cópia e a
aplicabilidade das licenças continuam sob revisão.

`linux-native-glibc-license-package-2026-10-19/glibc-object-evidence.json`
registra a inspeção de três objetos, quatro unidades de compilação e cinco
fontes glibc verificadas no SDK. Distingue abi-note.S adicional das fontes
observadas, e registra os 14 inputs SDK, incluindo bibliotecas sem extrações
reportadas e inputs compartilhados de link. `source-declarations.json` registra
as declarações nos comentários preservados; csu/init.c não contém a exceção de
link presente nos outros quatro prefixos. O pacote tem 23 notices, incluindo
cinco prefixos por fonte e a LGPL 2.1 integral fixada por hash. O summary vincula
inventário, relatório, notices, corpus e traces; tudo permanece não aprovado.
