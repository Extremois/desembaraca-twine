# Ferramentas do mantenedor

Estas ferramentas não são executadas na instalação do usuário. O catálogo ativo
continua com o artefato Windows legado; nenhuma receita POSIX constitui suporte
oficial antes de build, auditoria e qualificação de suas células.

## Build experimental no GitHub Actions

O workflow `linux-candidate.yml` constrói Graphviz 16.1.0 em Ubuntu 24.04 x64
hospedado. `prepare-linux-ci.py --work DIRETORIO_NOVO` baixa explicitamente a
fonte e Zig 0.15.2, verifica tamanho/SHA-256 antes de extrair e prepara wrappers
privados para `x86_64-linux.4.15-gnu.2.27`, sem instalação global. O CMake e os
geradores vêm da imagem do runner; seus caminhos, hashes e versões ficam no
registro SDK, junto da identificação da imagem. A imagem hospedada pode mudar:
esse registro identifica a execução, sem prometer rebuild idêntico.

Depois do build, o corpus de 13 casos e a relocação em caminho com espaços e
Unicode são executados em CPython 3.12 e 3.14. Logs, candidata e proveniência
ficam em artefato de Actions por sete dias. `observe-linux-network.py` executa
esse corpus sob `strace -f`, com a classe `%network` e registro de `execve`.
Antes de observar a candidata, exige detectar uma tentativa de conexão local
feita por um processo filho. O aceite desse ensaio exige zero chamadas de
socket/rede, inclusive chamadas que falhem e sockets locais, além de execuções
do `dot` observadas. O tracer encerra os processos rastreados caso termine;
tempo e saída têm limites, e logs desconhecidos/incompletos reprovam o ensaio.
Ver [opções oficiais do strace](https://github.com/strace/strace/blob/v6.8/doc/strace.1.in).

Esse ensaio observa o corpus público com rede disponível no runner; não isola
a máquina da rede nem cobre aquisição/instalação/recuperação. O relatório
registra versão/hash do tracer e hashes do corpus e dos traces, incluindo o
controle. Se necessário, o workflow instala o tracer apenas no runner efêmero.
Não há publicação de release ou
admissão automática no catálogo. Auditoria de fontes/licenças, baseline antigo,
instalação da distribuição e aceite completo continuam como etapas separadas.

## Build offline por variante

### Candidatas macOS nativas

`macos-candidate.yml` usa runners macOS 15 separados: `macos-15-intel` e
`macos-15` Apple Silicon. `prepare-macos-ci.py --work PASTA_NOVA --arch x86_64`
(ou `aarch64`) exige arquitetura nativa, Xcode 16.4 build 16F6 e SDK 15.5.
Seleciona o Xcode por `DEVELOPER_DIR` no processo, sem alterar `xcode-select`.
Registra hashes dos compiladores, ferramentas reais obtidas por `xcrun`,
SDKSettings, arquivos/links da árvore SDK e versões/imagem do runner. O inventário
preserva somente nomes relativos, tamanhos/hashes e destinos de links, sem copiar
o SDK Apple para o artifact. Isso identifica a execução, sem prometer rebuild
idêntico ou qualificar a imagem como célula de suporte.

O workflow fornece Bison 3 via Homebrew somente no runner efêmero quando ausente.
A receita fixa deployment target 15.0 e usa bibliotecas Graphviz internas
estáticas. Cada arquitetura executa o corpus e relocação Unicode em Python
3.12/3.14 e preserva inventário, medições Mach-O, proveniência e ZIP por sete
dias. `prepare-macos-notices.py` cria uma candidata nova com textos Graphviz,
prefixos Bison, aviso Flex Apple e comentários iniciais dos headers observados.
Confere novamente as fontes/objetos e os bytes dos headers; arquivos sem prefixo
identificável permanecem registrados para revisão. O runtime é copiado sem
alteração de bytes, e `review.json` vincula cada aviso à sua origem. A candidata
inclui também `NOTICE-ORIGINS.json`: índice offline com tamanho, hash e origem
de todos os demais avisos, vinculado à proveniência e à observação de fontes.
Declarações explícitas nos prefixos acrescentam textos completos APSL 1.1/2.0,
Apache 2.0 com exceções LLVM e GPL 3, fixados em `material-source-lock.json`.
As versões APSL permanecem separadas; o texto LLVM não estabelece equivalência
com as fontes do compilador Apple. Esses textos não concedem aprovação por
arquivo ou ao pacote. Outros textos necessários, dados gerados, aplicabilidade e oferta de fontes continuam
pendentes em T052. Não há uso de credenciais Apple,
assinatura Developer ID, notarização ou promoção de suporte nessa execução.

`audit-macos-link.py` confere o mapa produzido pelo linker Apple contra o
executável concluído, os objetos/membros de archives e as declarações de entradas
do compilador. Fontes Graphviz observadas são comparadas com o tarball fixado.
A seção de objetos é decodificada estritamente; bytes arbitrários nos nomes de
símbolos permanecem no mapa original, preservado por hash. Índices sem nome são
registrados como origem pendente. O relatório não prova retenção de seções ou
fechamento completo de fontes e não aprova licenças. O ledger
`licenses/macos.json` acompanha essas pendências por artefato.

Para revisar as fontes da candidata glibc x64, `pack-sources.py --help` descreve
o coletor separado do ZIP do runtime. O workflow também reconstrói o motor a
partir desse pacote em uma pasta nova. As entradas e comandos estão em
[REBUILD-SOURCES.md](REBUILD-SOURCES.md). O artifact de fontes dura sete dias;
não substitui a oferta permanente nem a revisão completa de licenças.

`source-lock.json` fixa os bytes reais do arquivo-fonte Graphviz 16.1.0,
revisão Git e licença. Obtenha esse arquivo da URL registrada e confira o hash.
As seis receitas não instalam compiladores nem dependências automaticamente.

```sh
python3 tools/runtime/build-common.py --artifact-id linux-glibc-x86_64 --source-archive /caminho/graphviz-16.1.0.tar.gz --output /caminho/novo-build
```

Sem `--execute`, o comando verifica a fonte e mostra o plano. A execução exige
host/arquitetura/libc correspondentes e `--sdk-record arquivo.json`. Esse registro
contém `environment_digest` SHA-256 e objetos `cmake`, `c_compiler`, `cxx_compiler`,
cada um com `path` absoluto e `sha256`. Registrar também imagem/sysroot, inventário,
versões e origem do SDK revisado. O script confere os três executáveis; o registro
não substitui auditoria da toolchain ou ensaios no SO mínimo.

Usar diretório novo em filesystem POSIX. No WSL, preferir `/var/tmp` para preservar
resultados entre sessões. O build produz `provenance.json`, `candidate/bin/dot`
e o aviso Graphviz. Não instala Graphviz global, não publica arquivo nem altera
o catálogo. A fonte e as bibliotecas internas ficam estáticas; libc e bibliotecas
do SO continuam sujeitas a inspeção e qualificação próprias. A compilação pode
produzir avisos upstream, que devem permanecer no log de build.

As receitas estáticas desabilitam RPATH com `CMAKE_SKIP_RPATH=ON`: não precisam
de caminhos de bibliotecas Graphviz dinâmicas. Isso evita inclusive o RUNPATH de
componentes vazios observado no primeiro build experimental. A mudança de receita
exige novo build/proveniência; não altera silenciosamente binários existentes.

## Inspeção antes de qualquer admissão

Para ensaiar musl estático no host Linux glibc da mesma arquitetura, existe a
opção explícita `--cross-libc-experiment` de `build-common.py`, somente junto de
`--execute`. O percurso normal continua exigindo a mesma família libc. O
experimento exige receita musl com `-static`, SDK com fatos `target_os`,
`target_arch`, `target_libc_family: musl`, `static_linking: true` e ferramenta
`elf_inspector` com caminho absoluto/SHA-256, além dos três executáveis usuais.

Mantém OS/CPU correspondentes e proíbe tradução/emulação; não transforma host
glibc em ambiente Alpine. Registra `build_execution_kind:
cpu-native-cross-libc-experiment`, libc do host, alvo e kernel. Antes de marcar
o build concluído, confere arquitetura ELF e usa o inspetor fixado para exigir
ausência de interpreter, seção dinâmica, NEEDED e símbolos GLIBC. O relatório
estático fica vinculado por hash. Falha de inspeção deixa o build incompleto.

As duas receitas musl declaram linkedição totalmente estática; isso ainda é
uma candidata por variante, sem promessa de compatibilidade universal. O
experimento x86_64 foi executado no WSL existente. ARM64 e os ambientes nativos
Alpine permanecem pendentes. `relink-zig.py` aceita esse build x86_64 somente
com medição estática registrada, refaz a inspeção e exige igualdade de bytes.

Para o experimento Zig 0.15.2 em Linux glibc x86_64, o driver `cc` rejeita
`--dependency-file`, embora o LLD interno a aceite. Depois do build privado,
`relink-zig.py` permite capturar as entradas em um novo candidato:

```sh
python3 tools/runtime/relink-zig.py --source-output /caminho/build-original --output /caminho/novo-relink --zig /caminho/sdk/zig
```

O comando exige host Linux glibc x86_64, proveniência concluída, executável
original íntegro, wrapper C++ e Zig conferidos contra hashes do SDK. Lê a linha
do CMake como argumentos, sem shell, recusa response files e saída inesperada.
Produz uma referência com saída detalhada do driver e executa seu LLD com
dependências habilitadas. Exige bytes idênticos à referência antes de copiar o
candidato e registrar entradas reais, comando, metadados e proveniência pai.
Mantém o build original intacto; saída existente é recusada. Os arquivos do
Graphviz preservam escopo `build` do pai; os arquivos da toolchain ficam em `sdk`.

Isso captura arquivos lidos, sem provar quais membros de cada arquivo estático
foram incorporados ou aprovar licenças. O procedimento não baixa ferramentas,
altera catálogo ou substitui a inspeção abaixo. WSL não aprova células nativas.
Fixar também o kernel no alvo do compilador: o experimento anterior de Zig usava
Linux 5.10 por padrão; `x86_64-linux.4.15-gnu.2.27` foi ensaiado depois. Essa opção,
a glibc observada e a nota ABI ELF não substituem execução no baseline antigo.

O relink também gera `why-extract.tsv` com `--why-extract` do LLD. A ferramenta
lê esse TSV como dados limitados a 8 MiB/100.000 linhas, vincula cada extração
a um arquivo estático já identificado por hash e registra membro, referência e
símbolo. Recusa cabeçalho/linhas inválidos e arquivos estáticos desconhecidos.
O resumo fica em `linkage.archive_extractions`, junto com o hash do relatório.
Zero linhas para um arquivo é uma observação desse comando, sem provar ausência
de código. Um membro extraído pode ter seções descartadas; modos como
`--whole-archive` também exigem interpretação própria. Não transformar esses
dados em aprovação automática de licenças ou dispensa de fontes/notices.

`verify-artifact.py --root ... --manifest ... --provenance ... --audit ...`
confere inventário completo, hashes/modos, identidade do executável e relatório
de dependências. O manifesto candidato precisa passar pelo mesmo carregador da
aplicação, incluindo notices empacotados. Não usar URL fictícia para ativá-lo.

Para inspecionar um build **antes de existir URL de distribuição**, criar um
inventário local fora da árvore candidata:

```sh
python3 tools/runtime/verify-artifact.py --root /caminho/build/candidate --provenance /caminho/build/provenance.json --write-inventory /caminho/inventario-novo.json --minimum-libc 2.27
python3 tools/runtime/verify-artifact.py --root /caminho/build/candidate --provenance /caminho/build/provenance.json --inventory /caminho/inventario-novo.json --audit /caminho/auditoria-revisada.json
```

O primeiro comando exige host POSIX/arquitetura correspondentes, proveniência de
build concluído e inventaria arquivos regulares com SHA/tamanho/modo, sem links,
modos privilegiados ou escrita de terceiros. Recusa arquivo de saída existente.
Em Linux, `--minimum-libc` declara o baseline a verificar; não prova que o build o
atende. Para musl, informar a versão musl correspondente. Em Darwin, omitir essa
opção. Alterar proveniência ou executável invalida o vínculo do inventário.

Esse JSON tem `kind: local-candidate-inventory`, não possui URL e não serve como
manifesto do runtime. O segundo comando continua exigindo auditoria revisada e
verifica bytes/modos/arquitetura/dependências/ABI antes de executar o probe. Usar
`--manifest` ou `--inventory`, nunca ambos. Uma inspeção local não adiciona entrada
ao catálogo, não qualifica célula, não assina nem publica o artefato. Manifesto de
distribuição e seus notices empacotados continuam obrigatórios para admissão.

## ZIP candidato local

Para preparar **avisos em rascunho por build**, usar
`python3 tools/runtime/prepare-draft-notices.py --help`. Fornecer `--linked-build`,
`--source-build`, o relatório privado de `audit-graphviz-sources.py` em
`--evidence`, os arquivos fixados `--graphviz-archive`/`--sdk-archive`,
`--sdk-root` e `--output` novo. A ferramenta não baixa arquivos.

Antes da cópia, confere proveniências, executável, arquivos originais e SDK.
Compara cada header externo declarado com seus bytes no arquivo SDK e confere
os arquivos gerados. Preserva o prefixo completo de comentários ColorBrewer,
incluindo licença/atribuição, e os comentários de licença/exceção presentes nos
quatro arquivos Bison. Copia também avisos Graphviz/SDK selecionados dos arquivos
verificados, sem decidir automaticamente que a coleção está completa.

O registro SDK pode usar `facts.archive: {url, sha256}` (CI) ou os campos
legados `archive_url`/`archive_sha256`; identidades conflitantes são recusadas.
O preparo também exige `facts.host_tools.flex` com caminho absoluto, SHA-256
e versão `flex 2.6.4`. Confere o executável do gerador e as três macros de versão
do scanner já vinculado à evidência de compilação. O texto oficial de COPYING
do Flex, incluindo a exceção de scanners gerados, está fixado por tamanho/hash
em `licenses/material-source-lock.json` e entra no pacote sem alterações.
Essa conferência resolve esse material do gerador; a aplicação das demais
licenças e a completude das fontes continuam sob revisão.

`audit-graphviz-data.py` confere os seis inputs originais das tabelas de cores
e entidades contra o arquivo-fonte fixado. Executa os dois geradores upstream
com tempo/saída limitados, em temporário isolado, e exige igualdade de bytes
entre a reconstrução e os headers registrados na evidência de compilação.
Também compara os valores com referências W3C SVG 1.1/HTML 4.01 e X.Org rgb
1.1.0, preservadas com hashes em `licenses/data-references/`, sem rede no CI.
Registra as cinco diferenças conhecidas da tabela Graphviz em relação ao rgb
do X.Org e recusa outras diferenças; aliases de caixa/espaços só são aceitos
quando os valores coincidem.

O preparo de notices recebe esse relatório em `--data-evidence`, refaz a
conferência e adiciona o COPYING do X.Org e `DATA-ORIGINS.txt`, preservando o
comentário de origem SVG presente na fonte. A comparação prova correspondência
dos valores e dos bytes gerados. Ela não prova a cadeia histórica de cópia nem
conclui a aplicação das licenças; os indicadores de aprovação continuam falsos.

O CI nativo executa esse preparo, gera inventário e ZIP candidato e repete o
corpus com rastreamento de rede nos dois Pythons. O ZIP mantém os bytes/modos
inventariados e timestamps fixos. É um artefato experimental de revisão com
`approved: false`/`qualified: false`, sem manifesto de distribuição ou promoção
automática do catálogo. A receita de inspeção mantém a exigência de auditoria
aprovada, mesmo quando o inventário e o pacote foram gerados com sucesso.

`audit-glibc-objects.py` confere os inputs SDK e o relatório de extrações do
linker antes de inspecionar `crt1.o` e os membros observados de libc_nonshared.
Os objetos do cache devem coincidir com os bytes dos membros dos arquivos
estáticos. As unidades de compilação DWARF são resolvidas apenas dentro da
árvore glibc do SDK e as fontes são comparadas com seu arquivo fixado. O
relatório distingue fontes observadas de `abi-note.S`, que é material adicional
de startup e não recebeu vínculo por unidade de compilação nessa inspeção.
Também registra inputs compartilhados de link e arquivos estáticos sem extrações;
zero linhas de extração não vira aprovação ou prova automática de ausência.

Com `--glibc-object-evidence`, o preparo de notices exige a mesma variante,
proveniência, executável e SDK, depois reconfere os prefixos de comentários nos
bytes originais. O pacote glibc inclui ainda a LGPL 2.1 integral da origem GNU,
fixada por tamanho/hash. O arquivo glibc/LICENSES cobre avisos adicionais e não
substitui esse texto. Exceções de link são tratadas por arquivo: o prefixo de
csu/init.c declara LGPL 2.1 ou posterior e não contém a exceção observada em
outros arquivos. Essa coleta não aprova a compatibilidade do bundle inteiro.

O percurso experimental aceita glibc x86_64 ou musl x86_64 estático. Para musl,
exige fatos do SDK compatíveis e o relatório ELF medido, confere seu hash e
recusa interpreter, dependências dinâmicas ou símbolos GLIBC. Preserva uma
cópia desse relatório na saída. Seleciona o `lib/libc/musl/COPYRIGHT` integral
do SDK fixado; o aviso glibc não é herdado. Esse arquivo inclui referências a
licenças por arquivo que ainda exigem revisão, assim como libzigc/compiler_rt.
O ensaio registrado em `linux-musl-notice-draft.json` não gerou inventário/ZIP:
a baseline explícita exigida pelo inventário ainda não foi qualificada.

Um checkpoint posterior separou inventário estático local de requisitos de
compatibilidade: `verify-artifact.py --write-inventory CAMINHO --static-elf`
aceita somente receita musl Linux estática com fatos do SDK e relatório ELF
medido vinculados à proveniência. Registra `native_linkage: static-elf` e
`minimum_libc: null`; não preenche versão upstream musl nem mínimos do host.
O flag é exclusivo da criação de inventário e não pode ser combinado com
`--minimum-libc`. Sem esse flag, Linux continua exigindo baseline explícita.
`pack-candidate.py` aceita esse inventário local; a inspeção mantém a exigência
de auditoria revisada e repete a medição dos ELF antes de executar o probe.
Ver `linux-musl-candidate-package.json`: ZIP local repetível, ainda não qualificado.

Para aprofundar a revisão por arquivo, `python3 tools/runtime/audit-musl-objects.py
--help` descreve o coletor de objetos musl x86_64. Fornecer relink privado,
raiz/arquivo SDK fixados e relatório novo. Confere o executável, SDK, inspector,
TSV de extrações e archive libc.a por hash; compara cada membro observado com
o objeto real antes de executar somente o readelf registrado. Usa unidades de
compilação DWARF de nível zero e recusa fontes fora do SDK. Confere os bytes das
fontes contra o arquivo original, preservando comentários iniciais completos.
Limites: 120 s agregados, até 5.000 objetos/fontes, 64 MiB de fontes, 8 MiB por
saída readelf; não compila nem executa o candidato.

O relatório pode ser passado a `prepare-draft-notices.py --musl-object-evidence`.
A preparação exige identidade exata de build/SDK e recalcula hashes dos arquivos
e prefixos a partir do SDK fixado; não confia no texto de comentários do JSON.
Gera nova saída com comentários separados por fonte, sem substituir a anterior.
O ensaio `linux-musl-source-notice-package.json` tem 30 avisos/referências.
DWARF e comentários iniciais são evidência parcial: não encerram revisão de
headers transitivos, trechos posteriores, outros componentes ou fontes completas.

`python3 tools/runtime/audit-zig-runtime.py --help` complementa essa coleta com
`crt1.o`, `libzigc.a` e `libcompiler_rt.a` do mesmo relink musl x86_64. Confere
archive/membros/objetos e usa somente o readelf fixado. Interpreta exatamente uma
tabela DWARF4 por objeto; versões diferentes, índices ambíguos ou fontes fora do
SDK/cache permitido são recusados. Fontes geradas são limitadas a `builtin.zig`
sob `cache/b` e registradas separadamente por hash atual, sem tratá-las como
bytes do SDK ou comprovação do estado durante a compilação.

Confere as fontes das tabelas e dois entrypoints explícitos contra o SDK fixado.
Preserva comentários iniciais e sinaliza linhas com referências a licenças em
todo o conteúdo para revisão; esses indicadores não determinam aplicabilidade.
Limites: 120 s, 8 MiB por saída readelf, 1 MiB por fonte, 5.000 referências por
tabela e 64 MiB agregados de fontes. O relatório não altera candidato/notices,
aprova auditoria ou prova retenção das fontes listadas. Ver a coleta de 260
fontes em `linux-musl-zig-runtime-sources.json` e seus 49 prefixos de comentários.

Para incorporar esses prefixos a uma **nova cópia em rascunho**, fornecer também
`prepare-draft-notices.py --zig-runtime-evidence RELATORIO`. A preparação confere
identidade de build/SDK e relê as fontes no arquivo SDK fixado. Hash/tamanho da
fonte e hash/tamanho do prefixo precisam coincidir com a evidência. Arquivos
gerados não são aceitos na lista de fontes do SDK nem incluídos como tais.
Pode combinar `--musl-object-evidence` e `--zig-runtime-evidence`; o candidato
ensaiado em `linux-musl-runtime-notice-package.json` tem 79 arquivos de comentários/
avisos/referências e o mesmo executável. Os arquivos são material de revisão;
origem/aplicabilidade, textos canônicos e oferta de fontes ainda exigem auditoria.

A saída tem `candidate/`, `review.json` e proveniência nova. O executável mantém
o hash original; os avisos recebem modo 0644. Os campos `approved: false` e
`qualified: false` registram que ainda faltam decisões de aplicabilidade,
proveniência dos geradores/dados e oferta completa das fontes. O inspetor exige
auditoria revisada vinculada à proveniência nova; `review.json` não a substitui.
É possível inventariar/empacotar esse rascunho localmente com os comandos abaixo,
sem alterar catálogo ou publicar. `SOURCE-REFERENCES.txt` continua identificado
como material de revisão incompleto.

Para cruzar objetos Graphviz com fontes antes da revisão de licenças:

```sh
python3 tools/runtime/audit-graphviz-sources.py --source-build /caminho/build-original --linked-build /caminho/relink-com-extracoes --source-archive /caminho/graphviz-16.1.0.tar.gz --report /caminho/relatorio-novo.json
```

O coletor exige proveniências vinculadas, fonte fixada, executável íntegro e
metadados reais de linkedição/extrações conferidos. Lê arquivos estáticos `ar`
regulares como dados limitados; suporta nomes GNU/BSD, recusa arquivos thin,
truncados ou com membros ambíguos. Compara os bytes de cada membro observado
com um único objeto compilado e lê seu `.o.d` sem executar make/shell. Confere
as fontes declaradas contra o arquivo Graphviz original, sem extraí-lo no disco.

O JSON separa fontes Graphviz verificadas, arquivos gerados e headers externos,
com hashes e indicadores SPDX/Bison para revisão. Nomes de arquivos de licença
geram candidatos, sem decidir sua aplicação. Não aprova licenças, dispensa
headers/código inline, gera auditoria admissível ou modifica bundles/catalogo.
O relatório local pode conter caminhos privados: redigir somente a cópia de
evidência pública, preservando hashes dos objetos, fontes e metadados originais.

Depois de criar o inventário, empacotar seus bytes sem publicar ou executar o motor:

```sh
python3 tools/runtime/pack-candidate.py --root /caminho/build/candidate --inventory /caminho/inventario.json --provenance /caminho/build/provenance.json --output /caminho/pacote-novo
```

O diretório de saída deve ser novo, fora da árvore inventariada. Recebe
`candidate.zip`, cópia exata de `inventory.json` e `candidate.json` com hashes,
tamanho e pendências. O ZIP contém todos os arquivos inventariados, incluindo
notices presentes na candidata, com caminhos relativos e modos aprovados. Não
inclui a proveniência completa, que pode conter caminhos locais do SDK; registra
seu SHA-256 para conferência com o original mantido pelo executor.

O empacotador recusa arquivos extras/ausentes, links e conteúdo alterado, e confere
novamente tamanho/hash durante a cópia. Limita o ZIP inteiro a 128 MiB, incluindo
cabeçalhos e diretório central. Ordem, timestamp e modos são fixos; usa entradas
sem compressão para não depender da versão zlib na geração dos bytes. O limite
continua obrigatório, mesmo para uma candidata cujo conteúdo caiba nos 512 MiB
permitidos para expansão. Não é uma promessa de builds assinados reproduzíveis.

A conclusão do arquivo usa hardlink exclusivo no mesmo filesystem. Se não houver
essa garantia, falha sem fallback que sobrescreva; usar filesystem compatível.
Uma tentativa interrompida pode deixar o novo diretório de trabalho; repetir com
outro diretório novo. Não reaproveitar resultados sem `candidate.json` íntegro.
Em POSIX, confere modos reais; ao empacotar uma cópia no Windows, só codifica os
modos do inventário e registra `source_modes_checked: false`. Isso não substitui
a inspeção POSIX nativa.

`qualified: false` é obrigatório: gerar esse ZIP não aprova fontes/licenças,
dependências/ABI, assinatura, instalação ou as células de suporte. Não é um
instalador público. O catálogo e os manifestos ativos não são alterados; auditoria,
URL HTTPS imutável real e admissão do runtime continuam etapas posteriores.

A auditoria JSON precisa ter `approved: true`, `reviewer`, `provenance_sha256`
dos bytes exatos do registro, `source_references`, `system_libraries` e `components`.
Cada componente exige `name`, `license_expression`, `source_url`, `source_sha256`,
`notice_path` relativo à candidata e `notice_sha256`. Incluir fontes correspondentes
de todos os componentes, inclusive runtimes de compilador incorporados. Aprovação
é uma decisão de revisão sobre esses bytes; o script não decide compatibilidade
jurídica a partir do nome da licença.

Em builds Linux, a proveniência agora registra `linkage`: hashes do comando de
linkedição, do arquivo de dependências GNU ld e dos arquivos efetivamente lidos
pelo linker, incluindo bibliotecas/objetos do SDK. Caminhos da proveniência são
locais ao ambiente de teste; não copiá-la integralmente para um relatório público.
O coletor lê a regra gerada como dados, sem executar make/shell, com limites de
8 MiB de metadados, 10.000 referências e 1 GiB de entradas distintas.

`components[].link_input_sha256` da auditoria deve cobrir todos os hashes dos
arquivos estáticos `.a` e `.o` registrados. O inspetor Linux recusa auditoria sem
esse vínculo, sem metadados de linkedição ou com cobertura incompleta. Conferir
fontes e notices dos runtimes de compilador e objetos de inicialização, além dos
subcomponentes Graphviz. Em toolchains sem esse arquivo, o gate fica pendente até
obter evidência equivalente revisada; não inferir cobertura só de `NEEDED`.

O [manual GNU ld](https://sourceware.org/binutils/docs/ld/Options.html) descreve
`--dependency-file` como registro dos arquivos lidos. Isso não identifica sozinho
os membros de cada arquivo estático incorporados nem decide compatibilidade de
licenças. `licenses/linux.json` é o ledger de pendências, não um `--audit` aprovado.
O build experimental registrou também nove entradas estáticas do SDK que exigem
revisão; a disponibilidade do COPYING upstream não encerra essa auditoria.

Em ELF, inspeciona todos os objetos inventariados, arquitetura, NEEDED, RPATH e
símbolos GLIBC. A lista de bibliotecas do sistema é explícita. Em Darwin, a receita
base só admite um Mach-O thin da arquitetura esperada e bibliotecas de sistema
aprovadas; objetos adicionais são recusados. Exige verificação codesign e evidência
revisada `notarization_verified: true`. Assinatura/notarização, deployment target,
CPU/kernel mínimos e proteções normais ainda precisam de evidências do pipeline
macOS. O relatório de inspeção não aprova uma célula de suporte.

## Corpus e relocação de desenvolvimento

```sh
python3 tools/runtime/smoke-corpus.py --build-output /caminho/build --environment-kind wsl --report /caminho/relatorio-novo.json
```

Confere o executável contra a proveniência, copia para um caminho com espaços e
acentos, processa o corpus público, verifica preservação e não regressão e exige
as seis referências com `(0,0,0)`. Bloqueia chamadas DNS/socket Python. Isso não
observa syscalls de rede do processo nativo: traçamento nativo permanece um gate
distinto. Em Linux registra NEEDED e o maior símbolo GLIBC observado, sem deduzir
kernel/CPU mínimos apenas desse resultado.

O relatório não cobre instalação, cache normal, Twine, assinatura, auditoria nem
aceitação completa. `environment_kind=wsl`, container ou emulação não vira prova
nativa de outra célula. As qualificações Python 3.12/3.14 e os gates comuns ficam
separados em `support-targets.json`; todos os 69 alvos continuam pendentes.

## Aceitação de um pacote instalado

`python tools/runtime/qualify-target.py --help` lista os parâmetros. Informar alvo
exato do registro, pacote local wheel/sdist e SHA-256, artifact_id, revisão da
aplicação, origem dos Pythons, ambos os executáveis 3.12/3.14, slot corrente e
imagem/ambiente de referência com digest. Ambos os interpretadores precisam existir
antes de capturar rolling. O host deve corresponder ao alvo; WSL/container
reconhecidos são classificados dessa forma, mesmo se o chamador pedir `native`.

O coletor cria uma venv temporária fora do checkout, instala sem índice, verifica
console/módulo, usa cache isolado e faz primeiro processamento/preparo normais.
O worker importa somente o pacote instalado e executa o corpus público pelo
runtime normal. Não injeta um motor alternativo. Para instalar sdist, fornecer
`--wheelhouse` local com setuptools/wheel e dependências de build, sem compilador
Graphviz nem alteração do Python do SO.

`--source-state dirty` ou `unverified` permite medir uma candidata em andamento;
essas evidências não podem ser promovidas. `committed` exige revisão e pacote
conferidos no pipeline/revisão. O digest do pacote não prova sozinho a revisão.

O JSON de saída é exclusivo, acompanhado de diretório `.logs` com texto redigido
para retirar caminhos temporários/do checkout. `passed: true` significa que as
etapas observadas passaram, não que todos os gates estão aprovados. O coletor
registra somente a modalidade de instalação executada e observação de rede Python;
`installation` e `offline` ficam em `pending_checks` até comprovar demais modalidades
e traçamento nativo. Em `checks`, falso significa ensaio conhecido como falho;
não se usa falso para uma etapa não executada. Revisão real Twine, licenças e falhas/crash/concorrência exigem
evidências complementares. Não transformar campos pendentes em verdadeiros para
liberar suporte.

Para preservar os arquivos necessários à revisão visual, acrescentar
`--review-output CAMINHO_NOVO` ao comando de coleta. O diretório novo recebe
somente as seis saídas das referências públicas e um `manifest.json`, com alvo,
Python, revisão, hash do artefato e SHA-256 de cada arquivo. O coletor confere
esses hashes contra o corpus antes de exportar e recusa sobrescrita. Não copia
cache, inventário ou o restante da pasta temporária. Os workflows de qualificação
incluem esse diretório no artifact de evidências.

O manifesto continua com `review_status: pending`. Abrir exatamente esses arquivos
no Twine em uma biblioteca de teste isolada, conferir dados/layout e registrar
versão, revisor e hashes no registro de revisão; a exportação não aprova o gate.
As fixtures compartilham IFID: evitar importá-las sobre histórias de uma biblioteca
de uso pessoal. O bundle não contém uma história privada do usuário.

Os workflows manuais `qualify-linux.yml` e `qualify-macos.yml` consomem candidatas
já existentes por run/artifact e SHA. Reutilizam `qualify-cell.yml` e o registro;
cada célula/arquitetura e Python avança independentemente, sem gate agregado ou
cancelamento por falha de outra variante. Não provisionam máquinas nem recebem
credenciais de assinatura. Exigem runners existentes com SO/kernel/arquitetura
reais e imagem registrada. Hosts antigos sem suporte ao runner/actions precisam
do percurso CLI nativo; container prova apenas userland. Ausência de runner,
candidata assinada ou ambiente correto deixa a célula pendente. Não executados
remotamente nesta sessão.

## Promoção revisável

`python tools/runtime/promote-support.py --help` descreve entradas. Fornecer registro,
target_id, um ou mais JSON de evidência revisada, raiz de logs e saída nova.
O comando não modifica o registro original, o catálogo ou arquivos existentes.

Exige dois slots Python únicos, revisão/artefato/imagem/kernel consistentes,
origem e patch dos interpretadores, fontes/licenças revisadas, corpus completo sem
regressão e seis casos zerados. Verifica hashes dos logs locais, prova de rede
nativa sem tentativas e seis reaberturas Twine com versão/revisor. Evidência precisa
de revisor identificado e source_state committed. Um gate falho, WSL/container,
slot ausente, duplicata ou status manual não pode promover a célula. Cada modalidade
de pacote registra seu próprio SHA; wheel e sdist não precisam ter bytes iguais.
Auditoria compartilhada usa `python_minor: null`, `evidence_scope: artifact-license-audit`
e somente o gate licenses, sem inventar uma segunda execução do SO. Mantém vínculo
com alvo/revisão/artefato/snapshot. Somente licenses e Twine podem ser gates comuns;
ensaios dependentes do Python precisam de evidência dos dois slots. Hashes reabertos
no Twine devem corresponder às saídas efetivamente verificadas do corpus.

Para rolling, a primeira captura pode preencher o snapshot_id nulo do alvo
pendente; o inventário inteiro é revalidado/canonicalizado. Nunca substitui o
snapshot de uma célula já capturada: uma atualização precisa de nova célula.
Inventários/corpus completos ficam nos arquivos de evidência; o resumo empacotável
inclui SHA-256 do registro canônico revisado, evitando duplicá-los em cada slot.
Limites de leitura dos relatórios de manutenção são maiores para acomodar JSON
indentado de inventários completos (32 MiB no coletor, 64 MiB nas entradas de
promoção); isso não amplia 5 s/8 MiB das consultas nem limites do runtime.

Os drivers `tests/integration/test_linux_runtime.py` e `test_macos_runtime.py`
exigem `TWINE_NATIVE_ACCEPTANCE=1` no SO correspondente e configuração explícita
de candidata/SDK/imagem descrita em `tests/native_acceptance.py`. Sem isso são skips,
nunca aprovação. WSL/container detectados não passam pelo gate de célula nativa.
O percurso usa pasta externa com espaços/acentos e confere cache, modos, corpus e
prontidão idempotente. Em Mac exige Developer ID, timestamp/hardened runtime,
codesign e avaliação spctl habilitada, sem contornar proteções.

Antes do primeiro arquivo válido, o worker também executa uma entrada UTF-8
inválida e exige código 1 sem chamar a aquisição do runtime ou tentar rede Python.
As tentativas são contadas mesmo quando a CLI captura o erro. A interceptação é
removida antes da aquisição normal; não simula download, motor ou aprovação de
offline nativo. O resultado é registrado em
`observations.invalid_input_refused_without_acquisition` e exigido pelo driver
de aceitação. Relatórios antigos não ganham esse resultado retroativamente.

## Assinatura macOS (execução nativa ainda pendente)

`sh tools/runtime/sign-macos.sh --help` prepara o fluxo explícito do mantenedor.
Requer build Darwin nativo correspondente, auditoria de fontes/licenças vinculada
à proveniência e identidade **Developer ID Application** e perfil notarytool já
autorizados no Keychain. Credenciais não são criadas, armazenadas pelo script ou
recebidas pelos workflows de qualificação.

Cria cópia nova, assina o único Mach-O da receita estática com hardened runtime e
timestamp, verifica codesign, submete ZIP ao notarytool e exige Accepted, log e
avaliação spctl normal. Não altera a candidata unsigned. Qualquer recusa mantém o
gate aberto; não remove quarentena nem muda proteções. O fluxo segue a
[documentação Apple](https://developer.apple.com/documentation/security/customizing-the-notarization-workflow).

O ZIP de notarização não é automaticamente o ZIP final do runtime. Empacotamento,
manifesto, auditoria atualizada para a proveniência assinada, distribuição real e
ensaio offline/Gatekeeper continuam obrigatórios. Timestamp torna bytes assinados
não necessariamente reprodutíveis. Neste host só foram verificados sintaxe e
recusa fora do macOS; T051 continua aberta até executar ambas as variantes.
