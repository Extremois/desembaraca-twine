# Pesquisa e decisões técnicas

**Política de validação atualizada por instrução do usuário (2026-10-27):** validar exclusivamente pelo GitHub Actions, diretamente nos runners hospedados e em contêineres quando necessários. Não exigir teste nativo, hardware dedicado, runner próprio, kernel específico ou VM; não criar nem iniciar VMs, inclusive dentro do CI. Esta decisão substitui exigências anteriores desses ambientes e suas pendências históricas. Conservar hashes, integridade, instalação, corpus, recuperação e o ambiente efetivamente exercitado nos logs; não inventar cobertura. Resultados de VMs anteriores são somente histórico e não são gates de aceite.


**Data**: 2026-10-17. Pesquisa de planejamento, sem novos binários incorporados e sem testes Linux/macOS executados. Fatos de manutenção e decisões de engenharia são separados abaixo.

## 1. Matriz por distribuição, não por nome de família

**Decision**: usar a [matriz nominal](support-matrix.md), com todas as séries mantidas sem assinatura paga das distribuições escolhidas na data de referência. Incluir programas gratuitos condicionados, sem presumir elegibilidade universal. Rolling exige snapshot datado. A disponibilidade de imagem/interpretador e a execução dos ensaios são gates, jamais aprovação presumida.

**Rationale**: ABI compartilhada permite reutilizar componentes, mas não comprova instalação, permissões, kernel, integridade ou experiência de uso de outro SO. O recorte inclui versões com manutenção de segurança e separa port ARM de Arch Linux principal.

**Alternatives considered**: somente Ubuntu recente (reduz escopo confirmado); todas as derivadas por herança (afirmação não verificável); exigir pagamento para sistemas antigos (contraria elegibilidade); excluir Ubuntu Pro/RHEL gratuitos por exigirem conta (usuário excluiu pagamento, não cadastro). Fontes e exclusões constam na matriz.

## 2. Origem e distribuição do motor

**Decision**: preservar Graphviz 16.1.0 Windows original, com seus hashes/notices. Para POSIX, construir bundles mínimos rastreáveis do mesmo código-fonte: glibc x64/ARM64, musl x64/ARM64 e macOS 15 x64/ARM64. Publicar posteriormente como arquivos ZIP imutáveis em releases do repositório, com fontes correspondentes e inventário. Nenhuma URL/hash POSIX será ativada antes de existir e ser qualificada.

**Rationale**: a [página upstream](https://graphviz.org/download/) oferece canais diferentes por SO, sem demonstrar um único artefato relocável para toda a matriz. O projeto precisa controlar fechamento de dependências e relocação. Usar [build documentado](https://graphviz.org/doc/build.html), configurar o mínimo necessário ao layout e à [saída JSON](https://graphviz.org/docs/outputs/json/), verificando funcionalidade por corpus. Plugins opcionais podem ser desativados conforme o [CMake 16.1.0](https://gitlab.com/graphviz/graphviz/-/raw/16.1.0/CMakeLists.txt).

**Alternatives considered**: instalar Graphviz via apt/brew/apk (exige configuração externa); wrapper Python graphviz (não entrega motor); extrair conda-forge diretamente (fechamento/prefixos exigiriam resolvedor adicional, conforme [conda-build](https://docs.conda.io/projects/conda-build/en/stable/resources/define-metadata.html)); um estático musl universal (hipótese a medir, não base comprovada); WASM/outro motor (altera arquitetura e risco sem necessidade).

## 3. ABI, relocação e requisitos mínimos

**Decision**: detectar SO, arquitetura nativa, libc/loader e mínimos do artefato. Registrar CPU, símbolos de bibliotecas e kernel mínimo qualificados. Linux glibc deve contemplar Ubuntu 18.04; musl tem lane própria. RPATH privado relativo com `$ORIGIN`/`@loader_path`, dependências aprovadas e `GVBINDIR` privado; não usar PATH global para localizar Graphviz. Confirmar relocalização do bundle em caminhos distintos, com espaços/acentos.

**Rationale**: glibc e musl não são intercambiáveis; a [orientação musl](https://wiki.musl-libc.org/guidelines-for-distributions) descreve a distribuição de executáveis e bibliotecas. Requisitos exatos são saídas mensuráveis do build, não números inventados no catálogo. CPU mínima do SO pode ser superior à do motor. O uso de [GVBINDIR](https://graphviz.org/doc/info/command.html) deve permanecer restrito ao subprocesso.

**Alternatives considered**: selecionar por `platform.system()` apenas (insuficiente); decidir por `ID_LIKE` (não comprova ABI nem suporte); executar componente de outra arquitetura (contraria uso nativo); presumir baseline porque compilou em CI (não comprova hosts antigos). Se uma lane falhar, criar variante adicional explicitamente qualificada, sem retirar alvos.

## 4. Cache, locks e publicação

**Decision**: conservar raiz/identidade Windows. Linux usa XDG_CACHE_HOME absoluto ou ~/.cache; macOS usa ~/Library/Caches. Em POSIX, flock não bloqueante com prazo de 10 s; Windows conserva msvcrt. Cache tem gerações imutáveis, seletor substituído atomicamente e handle estável por execução. Não coletar gerações antigas nesta feature.

**Rationale**: respeitar [XDG](https://specifications.freedesktop.org/basedir/0.8/) e [diretórios macOS](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/FileSystemOverview/FileSystemOverview.html). [fcntl](https://docs.python.org/3.12/library/fcntl.html) fornece locking POSIX, dispensando dependência nova. Canonicalizar a base legítima uma vez e proteger componentes dentro da raiz gerenciada: rejeitar todo symlink ancestral indiscriminadamente quebraria caminhos legítimos do sistema/perfil.

**Alternatives considered**: lock via existência de arquivo (crash deixa bloqueio obsoleto); sobrescrever geração ativa (rompe processamento concorrente); usar rename POSIX no arquivo de saída (pode sobrescrever). Manter os.link com exclusão atômica de destino em POSIX e caminho seguro Windows: [semântica Python](https://docs.python.org/3.12/library/os.html). Sistemas de arquivos sem publicação segura devem falhar com diagnóstico, sem fallback de cópia parcial.

## 5. Segurança e licença da distribuição

**Decision**: inventário por bundle inclui hashes, tamanhos, modos POSIX, fontes, licenças e dependências; ZIP contém somente arquivos regulares/diretórios. Materializar links necessários no build, com resolução segura e inventário, nunca criar links provenientes do ZIP. Não admitir setuid/setgid ou escrita pública. Assinar e notarizar bundles macOS antes de qualificação pública, validando execução sob proteções normais.

**Rationale**: [Graphviz 16.1.0 COPYING](https://gitlab.com/graphviz/graphviz/-/raw/16.1.0/COPYING) é EPL-2.0; manter componentes separados do código Apache-2.0, verificar obrigações de redistribuição e disponibilizar fontes correspondentes, inclusive modificações. Não copiar cegamente as 29 licenças do bundle Windows para builds POSIX diferentes. [Developer ID](https://developer.apple.com/developer-id/) e [notarização](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution) orientam distribuição macOS.

**Alternatives considered**: omitir inventário de bibliotecas opcionais (licenças incompletas); remover quarentena/desativar Gatekeeper (contraria spec); declarar aprovação por execução em máquina de desenvolvimento (não valida distribuição). Credenciais/conta do mantenedor são dependência futura; ausência mantém macOS pendente. Build rastreável não promete ZIP assinado idêntico byte a byte entre execuções com timestamps.

## 6. Instalação e evidência

**Decision**: recomendar ambiente virtual Python em espaço do usuário, instalar wheel ou ZIP remoto de commit/release real e chamar o console script; alternativa por caminho absoluto ou `python -m twine_edge_overlap`. README PT/EN deve explicar o interpretador nativo, venv e primeira preparação online. Não ampliar suporte Python além de 3.12/3.14.

**Rationale**: ambientes [externally managed](https://packaging.python.org/en/latest/specifications/externally-managed-environments/) tornam pip global/--user inadequado como instrução universal. Venv evita modificar o Python do SO. Compilar o motor na instalação prejudicaria simplicidade e não será exigido.

**Alternatives considered**: pip global com sudo/--break-system-packages (alterações globais); somente checkout (contraria instalação remota); empacotar toda a matriz nativa no wheel (download excessivo). CI pode usar [runners hospedados](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), mas imagens e rótulos devem ser confirmados na execução. Contêiner userland, emulação e testes mockados ficam registrados como evidência parcial; não substituem SO/arquitetura reais nem revisão Twine.

## 7. Unidade de suporte e agregação Python — A1

**Decision**: SupportTarget representa uma combinação de ambiente/arquitetura/variante e snapshot rolling; PythonQualification é seu ensaio filho. Há exatamente dois slots, 3.12 e 3.14. Só agregar `validada` com os dois e todos os gates comuns completos, com mesma revisão da aplicação/artefato e snapshot. Patch/origem do interpretador pertence à evidência, sem exigir igualdade entre séries Python diferentes.

**Rationale**: a spec já exige ambos os interpretadores por ambiente. Separar identidade do ambiente da execução de ensaio elimina a possibilidade de considerar um único Python como suporte integral ou misturar resultados de baselines diferentes. É decisão de modelagem interna, não mudança do escopo confirmado.

**Alternatives considered**: manter Python na identidade da célula e exigir o outro na mesma linha (agregação implícita e ambígua); aceitar qualquer Python aprovado (reduz cobertura); duplicar gates comuns para cada Python (gera evidência ficticiamente repetida). A relação e regras de unicidade/estado estão em [data-model.md](data-model.md).

## 8. Reconhecimento offline de snapshots rolling — U1

**Decision**: usar `package-inventory-v1` para inventário e `rolling-host-v1` para fingerprint de distribuição/canal/arquitetura/kernel e inventário exato. Fazer duas leituras consecutivas iguais, limitadas a 5 s/8 MiB agregados e 100.000 tuplas por leitura. Comparar com alvo validado empacotado; coleta ausente, excedida, instável ou diferente produz melhor esforço com aviso se a ABI for compatível. Data/label são metadados, não entrada manual para forçar suporte.

**Rationale**: [os-release](https://raw.githubusercontent.com/systemd/systemd/main/man/os-release.xml) descreve ID/VERSION_ID/BUILD_ID, mas isso não identifica sozinho o conjunto instalado. [pacman --query](https://man.archlinux.org/man/pacman.8.en) consulta os pacotes locais; [rpm --query --all](https://rpm.org/docs/4.20.x/man/rpm.8) e [tags RPM](https://rpm.org/docs/latest/manual/tags) fornecem nome/epoch/versão/release/arquitetura. A [documentação Manjaro](https://wiki.manjaro.org/index.php?title=Pacman-mirrors) descreve Branch em pacman-mirrors.conf: ler esse arquivo evita invocar um utilitário que também oferece operações de rede. São fontes dos dados, não garantia externa do algoritmo de aprovação escolhido pelo projeto.

**Alternatives considered**: data da ISO ou VERSION_ID/BUILD_ID isolado (pode permanecer igual depois de atualizações); presumir última versão consultando servidor (viola offline e não comprova estado local); conjunto reduzido de bibliotecas (não representa o snapshot integral prometido); herdar família/ID_LIKE (não equivale a ensaio); bloquear todo rolling desconhecido (contraria melhor esforço compatível).

**Tradeoff**: inventário integral e kernel exato são conservadores: alteração sem relação com Graphviz pode retirar classificação oficial. O uso pode continuar com aviso, sem exigir desfazer atualização. Hash não autentica arquivos do sistema contra administrador malicioso. Limites são política do projeto; qualificar o custo real em cada alvo, sem aumentar os 60 s de processamento. Inventário de usuário fica local. Coletas e hashes de referência só serão preenchidos após ensaio real; canonicalização e comandos fixos estão no [contrato](contracts/support-policy.md#reconhecimento-de-rolling).

## Dependências conhecidas, sem decisão de produto pendente

- Construir e qualificar artefatos POSIX, suas baselines e todos os dois interpretadores por alvo antigo; não disponíveis como entrega nesta pesquisa.
- Identificar imagens/dispositivos ARM mantidos de Manjaro/postmarketOS; registrar disponibilidade real antes de expandir/excluir células.
- Obter ambiente macOS Intel e ARM nativo e credenciais de assinatura/notarização; nenhum bypass de segurança.
- Obter ambientes das versões Linux e condições gratuitas RHEL/ESM; documentar elegibilidade e não expor tokens.
- Concluir evidência de aceitação Windows e revisão visual anteriores; não criar VM local nesta etapa.

Esses pontos são gates de implementação/liberação com resultado verificável. Todas as escolhas de arquitetura necessárias ao design estão resolvidas; nenhuma ausência de evidência é apresentada como compatibilidade já comprovada.

## Implementação: variantes de imagem AlmaLinux 10

CPU flags não distinguem a instalação padrão de uma imagem v2 em hardware mais
novo. O [spec oficial do pacote de release](https://git.almalinux.org/rpms/almalinux-release/src/commit/3c70f4e3e8e7c725136b5dbc09f2862b588238d8/almalinux-release.spec)
separa builds por arquitetura; os-release não publica ali um identificador próprio
da variante. Inferência adotada: consultar ARCH/VERSION do pacote instalado
almalinux-release e conferir VERSION_ID, por comando fixo offline limitado a
1 s/64 KiB. Saída ausente, múltipla ou inconsistente fica desconhecida. Não herdar
a célula padrão quando a família contém variantes e a instalada não foi reconhecida.
O reconhecimento é dado declarativo do banco de pacotes, sem atestar arquivos do SO.
Ensaios reais das imagens seguem pendentes; testes do parser/classificador usam
registros explicitamente sintéticos. A leitura simples do caminho do cache não
repete a consulta; o tempo de classificação continua no orçamento existente.

## Inventário local e RUNPATH das receitas estáticas

### Experimento musl com CPU nativa e host glibc

O ensaio de 2026-10-18 confirmou que a toolchain privada Zig fixada consegue
construir e executar Graphviz musl totalmente estático no kernel do WSL Linux
x86_64 existente. Não foi criado ambiente Alpine. O percurso foi separado por
`--cross-libc-experiment`; o padrão exige a família libc correspondente.
OS/arquitetura e ausência de tradução continuam obrigatórios, e a conclusão do
build experimental depende da inspeção ELF estática com ferramenta fixada.

O resultado tem corpus/relocação nos dois Pythons e evidência independente em
[linux-musl-static.json](evidence/linux-musl-static.json). Isso permite avançar
build e auditoria locais sem provisionar máquinas. Mantém pendentes os kernels,
CPUs e sistemas Alpine nativos, os interpretadores musl e a auditoria própria
dos componentes estáticos. A hipótese de um musl universal não foi adotada.

O primeiro build experimental WSL continha RUNPATH composto por componentes
vazios (`::::::::::::::::::::::::::::::::::::::`), recusado pelo verificador.
As receitas usam bibliotecas internas Graphviz estáticas e somente dependências
aprovadas do SO; não necessitam dessa busca dinâmica. Decisão: configurar
`CMAKE_SKIP_RPATH=ON` nas seis receitas e exigir novo build/proveniência. Não
alterar ou reutilizar silenciosamente os bytes de um build anterior.

O rebuild glibc x86_64 com o SDK existente removeu RPATH/RUNPATH e passou o corpus
de 13 casos, inclusive relocação com espaços/acentos. A maior versão GLIBC
observada continua 2.38; isso não atende o baseline 2.27. A alteração das demais
receitas ainda requer execução em seus próprios SDKs/arquiteturas.

A inspeção anterior exigia um manifesto de distribuição, criando dependência
indevida de URL real antes da auditoria local. O verificador agora aceita um
inventário local distinto do manifesto, vinculado por SHA-256 à proveniência,
arquivos, tamanhos e modos. Criar inventário não aprova auditoria; inspeção ainda
exige o registro revisado de fontes/licenças, dependências/ABI e assinatura macOS
aplicável antes do probe. Nenhum URL fictício ou entrada de catálogo é necessário
para essa etapa. [Evidência e limites](evidence/local-inventory-smoke.json).

### Inventário local de ELF musl totalmente estático

O candidato musl ensaiado não tem interpreter, seção dinâmica, bibliotecas
NEEDED ou referências GLIBC. Uma versão mínima da libc do host não descreve
essa medição; registrar uma versão upstream musl desconhecida como baseline
do host seria um dado inventado. Para permitir revisão do pacote antes da
qualificação, o inventário local agora oferece um modo explícito `--static-elf`.
Ele exige receita musl com `-static`, fatos coerentes do SDK, resultados estáticos
e relatório completo conferido contra o hash na proveniência exata do build.

Esse modo registra `native_linkage: static-elf` e `minimum_libc: null` somente
no inventário local. Não muda ArtifactDescriptor, catálogo, seleção por ABI ou
schema do manifesto distribuído; não autoriza usar a variante em outra família
libc. Auditoria revisada, nova inspeção ELF e qualificação real de kernel/CPU/
Alpine continuam gates independentes. Inventários Linux convencionais conservam
a baseline explícita. O ZIP é uma cópia para revisão, sem URL ou publicação.
Ver [evidência do pacote estático](evidence/linux-musl-candidate-package.json).

## Investigação de infraestrutura para os kernels Linux

Os 16 slots Alpine já conferidos executam userlands sobre o kernel do runner;
isso mantém os critérios nativos de baseline/aceitação pendentes. O próximo
experimento consulta a API KVM nos runners efêmeros x64/ARM64 do GitHub, sem
criar ou iniciar VMs e sem alterar o computador do mantenedor. Consulta normal
e elevada distinguem disponibilidade do dispositivo de permissões do usuário.

A [referência GitHub](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
documenta aceleração de hardware Linux, mas não comprova a capacidade de cada
runner atribuído. A [API Linux KVM](https://docs.kernel.org/virt/kvm/api.html#kvm-get-api-version)
exige versão 12; `KVM_CHECK_EXTENSION(KVM_CAP_USER_MEMORY)` consulta a capacidade
de memória de usuário. Essas duas consultas não demonstram boot ou execução
acelerada de um guest. O preflight em `.github/scripts/probe-kvm.py` registra
somente essa distinção, sem `KVM_CREATE_VM` e sem fallback para emulação.

Qualificação continuará exigindo kernel/CPU/imagem observados no ambiente real,
ambos os Pythons e os demais gates. Nenhuma capacidade de runner ou resultado
de container será promovido automaticamente a suporte de distribuição.

O preflight `28a03bb` confirmou KVM API 12 acessível somente com elevação no
runner x64; `/dev/kvm` está ausente no ARM64 atribuído mesmo com elevação.
Os recibos estão em `evidence/kvm-preflight-2026-10-20/summary.json`.
O próximo ensaio usa exclusivamente o runner efêmero x64, com KVM obrigatório,
imagem Ubuntu 18.04 de 20230607 fixada contra SHA256SUMS oficial e uma camada
de escrita descartável. O mesmo motor glibc previamente construído será medido
no kernel/loader/glibc reais do guest. `query-kvm` precisa confirmar aceleração;
não há fallback TCG. A execução do driver é recusada fora do GitHub Linux x64.

A imagem histórica serve para medir baseline, sem atualizar ou anunciar sua
manutenção de segurança. Elegibilidade Pro, os dois Pythons suportados, revisão
Twine e aceite instalado continuam gates próprios. O Python 3.6 do sistema
conduz somente o probe de motor; não será contado como slot da aplicação.
SSH usa chave efêmera, encaminhamento restrito a loopback e rede do guest
restrita; discos/seeds/chaves não entram no artefato de evidência.

O baseline de kernel do motor musl x64 será medido separadamente do glibc no
mesmo tipo de guest Ubuntu 18.04/KVM. O ELF musl precisa permanecer estático,
sem interpretador/seção dinâmica, e corresponder ao hash do motor ensaiado nos
quatro userlands Alpine. Essa combinação investiga receita/ABI e kernel mínimo,
sem substituir o ambiente Alpine nativo ou contar o Python 3.6 do guest como
slot suportado. T044 e os gates de distribuição/aceitação continuam próprios.
