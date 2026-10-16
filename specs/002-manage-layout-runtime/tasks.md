# Tasks: Uso sem instalação separada do Graphviz

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/cli.md](contracts/cli.md), [contracts/managed-runtime.md](contracts/managed-runtime.md) e [quickstart.md](quickstart.md).

**Prerequisites**: Desenho concluído; constituição 1.0.1 aplicável. Qualificar o ZIP real e seus avisos antes de ativar o manifesto. Nenhuma tarefa deste arquivo foi executada durante sua geração.

**Tests**: Incluídos para os cenários e critérios de aceitação explicitamente definidos na especificação: instalação limpa, seis referências de layout, preservação, recuperação e offline. A constituição exige evidências proporcionais ao risco. Usar unittest e testar resultados/contratos, sem espelhar detalhes privados de implementação.

**Retomada autorizada (2026-10-16)**: o mantenedor determinou prosseguir no sistema
atual sem criar VM. T022 e T043 ficam adiadas; suas caixas continuam abertas.
T028 depende da reabertura visual e T044 conserva as evidências ausentes como
pendências. O ensaio adicional no host atual está registrado em T045.

**Organization**: Setup e fundação compartilhados; uma fase por história, na ordem US1 (P1), US2 (P1), US3 (P2); fechamento transversal.

## Format: `[ID] [P?] [Story] Description`

- `[P]`: tarefa em arquivo distinto, executável junto às tarefas indicadas depois de cumpridos seus pré-requisitos; não significa ignorar dependências de fase.
- `[US1]`, `[US2]`, `[US3]`: história da especificação. Setup, fundação e fechamento não recebem rótulo de história.
- Os caminhos abaixo são relativos à raiz do repositório; tarefas novas indicam explicitamente o arquivo a criar.

## Path Conventions

Projeto Python existente em `src/twine_edge_overlap/`, testes em `tests/` e documentação desta feature em `specs/002-manage-layout-runtime/`. Não reinicializar o projeto, trocar o motor nem criar framework de plugins. Downloads de qualificação e binários ficam em temporários/cache, fora das fontes versionadas; registrar somente metadados e avisos exigidos.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar evidências e utilitários compartilhados sem alterar o comportamento existente.

- [X] T001 Criar `specs/002-manage-layout-runtime/validation.md` com matriz Windows 11 x64/Python 3.12 e 3.14 x64, requisitos FR-001–011/SC-001–007, comandos e campos de evidência; registrar o resultado inicial de `python -m unittest discover -s tests -v`, distinguindo testes com Graphviz global de evidência da nova feature e sem declarar ambientes indisponíveis como validados.
- [X] T002 Criar `tests/runtime_support.py` com helpers de cache temporário isolado, ZIP sintético, transporte HTTP controlado e bloqueio de conexões; aproveitar `tests/common.py` por importação, sem modificar fixtures Twine existentes, sem rede real por padrão e sem testes específicos de história neste arquivo.

**Checkpoint**: Baseline registrada e meios de testar preparação sem rede externa disponíveis.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Qualificar o artefato e criar os contratos compartilhados de runtime, erros e execução.

**Gate**: Todas as tarefas desta fase precedem a implementação das histórias. Se hash, origem ou compatibilidade de componente não puderem ser comprovados, registrar o impedimento em `validation.md` e não ativar manifesto com valores fictícios nem substituir o artefato silenciosamente.

- [X] T003 Obter o ZIP oficial Graphviz 16.1.0 win32 e seu checksum pelos URLs fixados em `specs/002-manage-layout-runtime/research.md`, comparar SHA-256, inspecionar a árvore e registrar em novo `docs/graphviz-16.1.0-managed-runtime.json` URL, hash integral real, tamanhos, inventário por arquivo, caminho real de `dot.exe`, hosts HTTPS de redirecionamento e configuração de plugins; conferir limites 128 MiB/512 MiB/5.000 sem reutilizar como prova o inventário da instalação global.
- [X] T004 Identificar origem/licença e compatibilidade de cada componente do ZIP de T003 em `docs/third-party.md`, preservando distinção do inventário anterior; criar textos/avisos necessários em `src/twine_edge_overlap/third_party/graphviz-16.1.0/`, com referências às fontes correspondentes e cobertura de DLLs/runtimes transitivos; avisos ausentes ou incompatibilidade não resolvida impedem ativação do manifesto, mesmo com download direto. Registrar em `src/twine_edge_overlap/runtime-manifest.json`, para cada aviso complementar, origem relativa no pacote, destino relativo sob `third-party-notices/` na geração e SHA-256 esperado de 64 caracteres hexadecimais.
- [X] T005 Criar `tests/unit/test_runtime.py` com testes de contrato para manifesto ausente, versão de esquema desconhecida, hash vazio/inválido, caminhos inválidos, inventário inconsistente e plataforma incompatível; verificar que cada rejeição ocorre antes de download ou execução; observar falha dos novos casos antes de implementar o carregador em T007.
- [X] T006 Criar `src/twine_edge_overlap/runtime-manifest.json` a partir de T003–T004 com `engine/version` = "`graphviz` / `16.1.0`", `platform/artifact_arch` = "`windows` / `win32`; matriz de host Windows 11 AMD64", `archive_sha256` = "64 caracteres hexadecimais, valor literal verificado antes da entrega" e identidade engine + version + platform + artifact_arch + archive_sha256; para `files`, cumprir "Inventário do ZIP qualificado: caminho normalizado, tamanho e SHA-256 por arquivo"; para `notices/source_references`, cumprir "Textos e avisos locais e URLs de fontes por componente, verificados antes de ativação"; não aceitar placeholders nem consulta remota a latest/checksum em produção. Incluir os mapeamentos origem/destino/SHA-256 de cada aviso complementar; rejeitar caminho absoluto, subida e destino duplicado.
- [X] T007 Implementar carregador e valores de runtime em novo `src/twine_edge_overlap/runtime.py` e erros de dependência em `src/twine_edge_overlap/errors.py`: `schema_version` = "Inteiro de versão do contrato; rejeitar versão desconhecida"; `url/allowed_redirect_hosts` = "URL HTTPS fixa do ZIP oficial; hosts exatos de origem/redirecionamento qualificados, sem aceitar destinos arbitrários"; limites = "128 MiB / 512 MiB / 5.000"; `executable_relative_path` = "Caminho relativo real do `dot.exe` dentro da árvore; sem caminho absoluto ou subida"; `generated_files` = "Caminhos permitidos e validação de configuração criada pela aplicação, quando necessária; nunca executáveis"; representar RuntimeInstallation, PreparationAttempt e RuntimeHandle conforme o modelo, sem lógica geométrica ou dados de histórias e com causa conhecida, impacto e recuperação nas falhas. Representar geração com `generation_id` único por tentativa, sem caminho absoluto/separadores/subida, e seletor `active.json` com identidade de artefato e identificador de geração validado; o RuntimeHandle fixa a geração sem reler o seletor.
- [X] T008 Criar `tests/unit/test_process_context.py` para passagem de cwd/ambiente por chamada, executável absoluto, `shell=False`, ausência de alteração no ambiente global, limites de tempo/saída e encerramento do filho; verificar que as extensões do contrato falham antes de T009.
- [X] T009 Estender `src/twine_edge_overlap/engines/process.py` para aceitar cwd/env opcionais sem alterar padrões dos consumidores existentes, preservando janela oculta Windows, execução direta, 30s/8 MiB por padrão e limpeza/encerramento em limite ou interrupção; fazer passar T008 sem acrescentar descoberta de executável ou rede ao runner.

**Checkpoint**: Artefato identificável, avisos acessíveis, manifesto real validável e execução de subprocesso com contexto isolado. Ainda não alegar prontidão do novo fluxo ou de máquina limpa.

## Phase 3: User Story 1 — Processar o primeiro arquivo em uma máquina limpa (Priority: P1) — MVP

**Goal**: `python run.py CAMINHO` prepara automaticamente o runtime, gera cópia reorganizada e reutiliza a instalação sem rede ou configuração de caminhos.

**Independent Test**: Cache vazio, sem Graphviz global e sem variável legada: processar `crossing.twee` e obter código 0, cópia íntegra e três contagens finais zero. Com cache pronto, repetir com rede bloqueada e obter nova cópia sem nenhuma tentativa de conexão.

### Tests for User Story 1

- [X] T010 [P] [US1] Criar `tests/contract/test_cli_runtime.py` com contratos do uso automático, `--prepare-runtime`, progresso somente em stderr, resultado em stdout, códigos, ajuda/versão sem rede, argumentos mutuamente exclusivos e entrada inválida sem preparação; usar runtime/transporte injetados e observar falha antes de T020.
- [X] T011 [P] [US1] Ampliar `tests/unit/test_runtime.py` com aquisição HTTPS limitada, hash antes de execução, caminho de cache/fallback, extração e prontidão, sondagem sintética e reutilização offline; incluir cache sob caminho com espaços/acentos, variável legada inválida e Graphviz global incompatível sem efeito; observar falha antes de T013–T017. Testar que aviso complementar ausente ou alterado impede prontidão/reutilização e que os avisos íntegros permanecem acessíveis offline na geração.
- [X] T012 [P] [US1] Criar `tests/integration/test_runtime.py` com casos de runtime real gerenciado usando manifesto fixado, primeira preparação de `crossing.twee`, cache reutilizado sem rede, ausência de dependência da instalação global e preparação antecipada sem gerar `.twee`; separar explicitamente ensaio real da simulação e não passar silenciosamente quando o runtime exigido faltar.

### Implementation for User Story 1

- [X] T013 [US1] Implementar transferência em `src/twine_edge_overlap/runtime.py` por urllib com TLS padrão, URL/hosts fixados, até cinco redirecionamentos HTTPS, até 128 MiB realmente recebidos, timeout socket até 30s e prazo cooperativo de preparação de 300s; gravar ZIP temporário e conferir SHA-256 fixado antes de extração, sem dados de histórias, telemetria, checksum remoto ou retries ilimitados.
- [X] T014 [US1] Implementar extração em `src/twine_edge_overlap/runtime.py` com staging exclusivo e limites reais de 512 MiB/5.000 entradas; rejeitar absoluto, drive/UNC, subida, ADS, nomes reservados Windows, ponto/espaço final, links/reparse points, entradas especiais e colisões após normalização sem caixa; manter destino dentro da raiz canônica, árvore completa e avisos, verificando inventário e separando arquivos gerados permitidos. Copiar os avisos complementares do pacote para `third-party-notices/` na geração, conferindo origem/destino/SHA-256 do manifesto sem modificar avisos originais do fornecedor.
- [X] T015 [US1] Implementar armazenamento/lock em `src/twine_edge_overlap/runtime.py` sob `%LOCALAPPDATA%\DesembaracaTwine\runtimes\graphviz\` com fallback `Path.home()/AppData/Local/DesembaracaTwine/runtimes/graphviz`, chave com versão/plataforma/hash integral, estrutura `generations/<generation_id>/`, seletor `active.json` por chave de artefato e staging/seletor temporário no mesmo volume e lock msvcrt por handle; cumprir "Outras execuções esperam até 10s pelo lock e depois falham com orientação para tentar novamente", revalidar após adquirir lock e não seguir links para fora da raiz.
- [X] T016 [US1] Implementar sondagem e RuntimeHandle em `src/twine_edge_overlap/runtime.py` usando o runner de T009: validar versão e layout `json0` de dois nós, com até 10s/1 MiB por sondagem, executável absoluto, cwd local e ambiente restrito ao filho; gerar configuração por `dot -c` somente se T003 demonstrar necessidade, registrar/validar arquivos gerados e neutralizar redirecionamentos herdados de plugins/DLLs sem mudar o ambiente global. Configurar e sondar a nova geração em seu caminho definitivo antes de gravar ready ou alterar o seletor, evitando referências a staging na configuração persistida.
- [X] T017 [US1] Integrar `ensure_runtime(force_repair=False)` em `src/twine_edge_overlap/runtime.py`: validar cache pelo manifesto/arquivos e sondagem sem rede, preparar uma vez se ausente/inválido, mover staging para geração exclusiva, verificar arquivos/avisos/sondagem no caminho definitivo, escrever ready e então selecionar via arquivo temporário exclusivo descarregado/sincronizado/fechado e `os.replace` de `active.json` sob lock no mesmo volume; cumprir "Um arquivo `ready` sozinho nunca promove uma tentativa", emitir handle uma vez e limitar limpeza a staging e seletor temporário da própria tentativa sob raiz conferida, sem coletar gerações ativas, anteriores ou órfãs, preservando arquivos externos e saída Twine.
- [X] T018 [US1] Adaptar `src/twine_edge_overlap/engines/graphviz.py` para receber RuntimeHandle validado e usá-lo em layout, removendo descoberta por PATH/Program Files/`TWINE_GRAPHVIZ_DOT` no fluxo padrão e segunda resolução dentro do motor; conservar geração DOT geométrica, IDs sintéticos, repetição de arestas e conversão/validação de coordenadas existentes.
- [X] T019 [US1] Integrar preparação única em `src/twine_edge_overlap/application.py` após snapshot/parse local e antes da baseline/fallback; suspender apenas a contagem dos 60s durante preparação, conservando consumo de leitura/parse, repassar handle ao motor e manter falha de preparação como DependencyError sem cópia, inclusive para entrada limpa; prover injeção interna explícita para testes sem rede.
- [X] T020 [US1] Implementar em `src/twine_edge_overlap/cli.py` preparação automática, ação `--prepare-runtime` sem história e reserva mutuamente exclusiva de `--repair-runtime` para T034, ajuda/versão sem preparação e progresso breve em stderr; manter a invocação por arquivo e os códigos 0/2/1/130, sem pedir caminho de motor ou variável de ambiente e sem anunciar ação de reparo como pronta antes de implementá-la.
- [X] T021 [US1] Ajustar `tests/common.py` e `tests/unit/test_graphviz.py` para runtime/provedor explícito nos testes geométricos e motor real gerenciado no teste de integração pertinente; remover dependência acidental de Graphviz global sem transformar teste real em mock nem produzir downloads silenciosos em testes unitários.
- [ ] T022 [US1] Executar T010–T012 e o ensaio inicial de `specs/002-manage-layout-runtime/quickstart.md` em conta/VM Windows 11 x64 limpa, registrando em `specs/002-manage-layout-runtime/validation.md` versão/hash, prontidão real, primeiro layout melhorado e repetição sem rede; inspecionar eventual dependência nativa ausente e gerenciá-la pela aplicação antes de aceitar o fluxo, sem instrução de instalar Graphviz separadamente.

**Checkpoint**: Primeiro processamento e repetição offline demonstráveis. US1 pode ser demonstrada isoladamente; preservação e recuperação completas ainda exigem US2 e US3 para entrega da feature.

## Phase 4: User Story 2 — Manter a qualidade e a integridade (Priority: P1)

**Goal**: Conservar os contratos existentes de layout, dados, estados e cópia sem sobrescrita com o runtime gerenciado.

**Independent Test**: Executar todos os fixtures e especialmente os seis casos `known_resolvable` com o novo runtime; verificar três contagens zero nos seis, não regressão nos demais, original idêntico, cópias íntegras/reabríveis e estados/caminhos corretos.

### Tests for User Story 2

- [X] T023 [P] [US2] Adaptar `tests/integration/test_reference_layouts.py` para runtime gerenciado e cobertura de todos os casos em `tests/fixtures/cases.json`, exigindo três contagens finais zero nos seis `known_resolvable`, não regressão simultânea nos demais e preservação de direção/multiplicidade, sem impor coordenadas idênticas à versão anterior.
- [X] T024 [P] [US2] Adaptar `tests/integration/test_roundtrip.py` e `tests/integration/test_file_failures.py` à injeção explícita do runtime, verificando original byte a byte, invariantes do perfil fora das posições autorizadas, metadados, colisões de saída e ausência de arquivo parcial anunciado em falha/cancelamento; reutilizar verificadores existentes.
- [X] T025 [P] [US2] Criar `tests/integration/test_runtime_budget.py` e ajustar `tests/integration/test_engine_failures.py` com relógio/provedor controlados para comprovar preparação fora dos 60s sem devolver o tempo já gasto na leitura/parse, limites 30s/8 MiB do motor e distinção entre DependencyError antes do fallback e falhas do motor após baseline íntegra.

### Integration for User Story 2

- [X] T026 [US2] Integrar os contratos existentes em `tests/contract/test_cli_success.py`, `tests/contract/test_cli_limitations.py`, `tests/contract/test_cli_failures.py` e `tests/integration/test_limited_results.py` com o provedor gerenciado; manter estados/códigos e contagens/caminho absoluto, verificar ausência de sucesso completo por indisponibilidade e corrigir somente regressões demonstradas em `src/twine_edge_overlap/application.py`, sem reformular algoritmo de seleção ou formato.
- [X] T027 [US2] Estender `tests/integration/test_runtime.py` para executar os seis exemplos com runtime real pronto e abertura de conexões interceptada para falhar; garantir cópias íntegras, três contagens zero e nenhuma operação de rede, mantendo os casos de primeiro uso de US1.
- [ ] T028 [US2] Executar a suíte de preservação/layout e reabrir no Twine as seis cópias geradas pelo runtime gerenciado; registrar hashes, contagens, resultados da reabertura e falhas reais em `specs/002-manage-layout-runtime/validation.md`, sem usar confirmação antiga de outro runtime como evidência desta entrega.

**Checkpoint**: Layout e integridade demonstrados separadamente do mecanismo de download. Não flexibilizar critérios dos seis exemplos para acomodar mudança de distribuição.

## Phase 5: User Story 3 — Resolver a indisponibilidade de um componente (Priority: P2)

**Goal**: Diagnóstico em português, nova tentativa e reparo seguro sem configuração manual de componentes.

**Independent Test**: Induzir indisponibilidade de componente/rede/espaço/permissão, conferir causa/impacto/recuperação e original preservado; corrigir a condição e repetir com sucesso. Reparo malsucedido deve deixar runtime anterior saudável utilizável offline.

### Tests for User Story 3

- [X] T029 [P] [US3] Ampliar `tests/contract/test_cli_runtime.py` com falhas em preparação e reparo, português com causa/impacto/ação, ausência de traceback/credenciais, nenhuma cópia em falha de dependência e códigos 1/130; testar `--repair-runtime` exclusivo, download da mesma versão e ausência de instruções de Graphviz/PATH/TLS manual; observar falha antes de T032–T034.
- [X] T030 [P] [US3] Criar `tests/unit/test_runtime_archives.py` com ZIPs hostis/truncados e transporte controlado para todas as rejeições de caminhos do contrato, hash divergente, tamanhos reais acima dos limites, excesso de entradas, TLS/HTTP/redirecionamento não autorizado e prazo excedido; exigir rejeição antes de executar payload e nenhum arquivo fora do staging.
- [X] T031 [P] [US3] Criar `tests/unit/test_runtime_repair.py` para cache com DLL ausente/extra, ready falso, versão/plugin inválido, interrupção em cada transição, erro de espaço/permissão/publicação, falha de reparo conservando instalação saudável e nova tentativa após correção; validar que limpeza não segue reparse points nem alcança diretórios externos. Incluir encerramento abrupto imediatamente antes/depois da substituição de `active.json`: nova resolução offline usa, respectivamente, a anterior saudável ou a nova validada; geração sem referência ativa não é selecionada.

### Implementation for User Story 3

- [X] T032 [US3] Implementar reparo em `src/twine_edge_overlap/runtime.py` mediante `force_repair=True`: obter novamente o ZIP fixado, preparar geração exclusiva, copiar/verificar avisos e validar no caminho definitivo; escrever/sincronizar/fechar seletor temporário e substituir `active.json` atomicamente com `os.replace` sob lock, preservando a geração anterior e handles em uso. Encerramento antes da seleção mantém a anterior saudável offline; depois, a nova validada fica disponível offline. Falha na substituição conserva a seleção anterior; não coletar gerações nesta entrega.
- [X] T033 [US3] Completar em `src/twine_edge_overlap/runtime.py` e `src/twine_edge_overlap/errors.py` o mapeamento de rede/TLS/HTTP, integridade, manifesto, plataforma, espaço/permissão, lock, sondagem e publicação para erros de dependência com causa conhecida, impacto e recuperação; não mascarar interrupção nem sugerir desativar TLS/segurança, não expor credenciais ou dados de histórias e fazer passar T030–T031.
- [X] T034 [US3] Conectar `--repair-runtime` e as mensagens de recuperação em `src/twine_edge_overlap/cli.py`, explicando necessidade de internet para reparo forçado e mantendo `--prepare-runtime` offline com cache saudável; respeitar exclusão com caminho/ação, não gerar `.twee` nessas ações e fazer passar T029.
- [X] T035 [US3] Criar e executar `tests/integration/test_runtime_concurrency.py` com processos Windows reais e artefato controlado para duas preparações simultâneas, lock liberado após término abrupto, espera máxima de 10s, reutilização do vencedor e erro controlado na substituição de active.json e handles anteriores em uso preservados; provar que não há cache parcial anunciado pronto nem encerramento de processo alheio. Encerrar o preparador real imediatamente antes e depois da seleção atômica e comprovar, em outro processo sem rede, uso da geração esperada e ausência de seleção de geração incompleta/órfã.
- [X] T036 [US3] Estender `tests/integration/test_runtime.py` com cache vazio sem rede, correção e repetição do mesmo comando, corrupção detectada, recuperação automática e reparo forçado sem rede preservando instalação anterior; verificar ausência de alterações na entrada/saídas existentes e uso offline posterior do cache saudável.
- [X] T037 [US3] Executar cenários de recuperação de `specs/002-manage-layout-runtime/quickstart.md` e registrar em `specs/002-manage-layout-runtime/validation.md` mensagens, códigos, estado antes/depois, falhas de preparação e repetição bem-sucedida, sem apresentar mocks como comprovação de portabilidade do pacote real.

**Checkpoint**: Três histórias cobertas; falhas e recuperação preservam os contratos anteriores e não exigem configuração manual de caminhos.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Fechar distribuição, instruções e evidências da entrega completa.

- [X] T038 [P] Atualizar `README.md` em português e inglês com percurso do ambiente limpo à saída, matriz oficial Windows 11 x64 com CPython 3.12 x64 ou 3.14 x64, distinguindo-a do requisito mínimo de código/metadados `requires-python >=3.12` e registrando as evidências efetivamente obtidas, download automático/versionado, conexão inicial/reparo e uso offline, comandos novos e migração de `TWINE_GRAPHVIZ_DOT`; remover instruções contraditórias de instalar Graphviz separadamente, sem prometer validações não executadas.
- [X] T039 [P] Atualizar `CONTRIBUTING.md` com testes isolados/integração, qualificação e atualização do manifesto, artefato/hash/avisos e ausência de downloads unitários por padrão; atualizar `specs/002-manage-layout-runtime/quickstart.md` para refletir comandos implementados, conservando cenários e distinguindo evidências obtidas de pendências reais.
- [X] T040 [P] Configurar `pyproject.toml` e novo `MANIFEST.in` para incluir `src/twine_edge_overlap/runtime-manifest.json` e `src/twine_edge_overlap/third_party/graphviz-16.1.0/` no wheel e sdist, com LICENSE/NOTICE aplicáveis e sem binários/cache; assegurar acesso aos recursos independentemente do cwd e sem dependências Python de produção novas.
- [X] T041 Construir wheel e sdist e instalar cada um em venv isolada fora do checkout; executar a CLI com cache próprio e sem Graphviz global, verificar manifesto/avisos incluídos, preparação real e repetição offline, e registrar comandos/resultados em `specs/002-manage-layout-runtime/validation.md`; acesso a build backend/índice deve ser registrado, não confundido com dependência de processamento. Em cada distribuição instalada, verificar que a geração preparada contém todos os avisos complementares em `third-party-notices/` com hashes iguais aos do manifesto, acessíveis sem rede.
- [X] T042 Executar `python -m compileall -q src` e `python -m unittest discover -s tests -v` após as mudanças, registrar em `specs/002-manage-layout-runtime/validation.md` resultados, skips e cobertura de falhas sem rede/artefato real; corrigir falhas materiais antes de declarar conclusão, sem ampliar testagem sem motivo nem usar instalação global como fallback.
- [ ] T043 Executar o percurso completo documentado em Windows 11 x64 limpo com CPython 3.12 x64 e CPython 3.14 x64 em ensaios separados, cobrindo ambas as combinações da matriz oficial, conta sem administração, sem Graphviz/cache/configuração herdados; comprovar primeira melhoria, seis referências offline, preservação e recuperação, e registrar ambiente/comandos/códigos em `specs/002-manage-layout-runtime/validation.md`; qualquer pré-requisito nativo necessário deve ser gerenciado pela aplicação ou permanecer como impedimento explícito da entrega. Não estender o status de suporte às demais versões a partir do mínimo `requires-python >=3.12`; registrar também retomada offline antes/depois da seleção e avisos complementares da geração ativa.
- [ ] T044 Fechar em `specs/002-manage-layout-runtime/validation.md` a rastreabilidade FR-001–011/SC-001–007 com evidências de T022/T028/T037/T041–T043, verificar instruções PT/EN seguindo o quickstart, integridade/distribuição dos avisos de `docs/third-party.md` e conformidade constitucional; atualizar `specs/002-manage-layout-runtime/spec.md` somente quanto ao status efetivamente alcançado, sem marcar validações ausentes como concluídas.
- [X] T045 Executar o percurso adicional no sistema atual, sem VM por instrução do mantenedor: primeiro uso da CLI com download real e cache separado por Python 3.12/3.14, seis referências com DNS/conexões bloqueados no teste, avisos offline e reparo indisponível preservando seletor/saídas; registrar resultados e limites em `validation.md` e `current-host-results.json`, sem substituir T022/T028/T043.

## Dependencies & Execution Order

### Phase Dependencies

```text
Setup T001–T002
  -> Fundação T003–T009
    -> US1 T010–T022
      -> US2 T023–T028
      -> US3 T029–T037
        -> Fechamento T038–T044 (exige US2 e US3)
```

US2 e US3 dependem do fluxo gerenciado US1, mas seus critérios são verificáveis isoladamente. Por compartilharem testes e `runtime.py`/`application.py`, a execução padrão é sequencial US1 -> US2 -> US3. Trabalho entre histórias só pode ocorrer em paralelo nos arquivos distintos explicitamente indicados; integração/execução dos checkpoints exige os predecessores completos.

### Dependências de tarefas

- T001 e T002 preparam a fase seguinte; T003 -> T004 -> T005–T007. T006 só ativa artefato após T003/T004; T007 consome T006 e deve satisfazer T005. T008 -> T009, ainda na fundação.
- Após a fundação, T010/T011/T012 podem ser escritos simultaneamente. T013 -> T014 -> T015 -> T016 -> T017 ocorre sequencialmente no mesmo módulo. T018 -> T019 -> T020 -> T021 -> T022 integra e valida US1.
- Após T022, T023/T024/T025 podem ocorrer simultaneamente em arquivos distintos. T026 integra; T027 e T028 encerram US2 com runtime real e reabertura.
- Após US1 (na execução padrão, também após T028), T029/T030/T031 podem ocorrer simultaneamente. T032 -> T033 -> T034 -> T035 -> T036 -> T037 integra e comprova US3.
- T038/T039/T040 podem ocorrer simultaneamente após os checkpoints das histórias. T041 exige T040 e a qualificação do runtime; T042 e T043 consolidam validação, e T044 exige todas as evidências anteriores.
- T022/T028/T037/T041–T044 escrevem no mesmo arquivo de evidências: executar suas gravações sequencialmente, sem sobrescrever resultados prévios. Nunca alterar geometrias/fixtures para fazer um ZIP não qualificado passar.

### Within Each User Story

Escrever os casos indicados antes da implementação relacionada e observar a falha relevante. Modelos/infraestrutura antes de integração; implementação antes dos ensaios reais. Uma mudança exige apenas testes proporcionais, mas os critérios de preservação, layout, offline e ambiente limpo não podem ser omitidos. Nenhum teste com pacote sintético prova o funcionamento do ZIP oficial.

### Parallel Opportunities

Grupos seguros após seus pré-requisitos: T010/T011/T012, T023/T024/T025, T029/T030/T031 e T038/T039/T040. Cada grupo altera arquivos distintos. A fase de aquisição/extração/cache/reparo trabalha sobre `runtime.py` e não recebe `[P]`.

## Parallel Example: User Story 1

Após T009, em arquivos distintos:

```text
T010: contratos de CLI em tests/contract/test_cli_runtime.py
T011: aquisição e cache em tests/unit/test_runtime.py
T012: integração real em tests/integration/test_runtime.py
```

## Parallel Example: User Story 2

Após T022, em arquivos distintos:

```text
T023: corpus em tests/integration/test_reference_layouts.py
T024: preservação em tests/integration/test_roundtrip.py e test_file_failures.py
T025: orçamento em tests/integration/test_runtime_budget.py e test_engine_failures.py
```

## Parallel Example: User Story 3

Após US1 e sem outro trabalho nos mesmos arquivos:

```text
T029: mensagens/argumentos em tests/contract/test_cli_runtime.py
T030: arquivos e transporte hostis em tests/unit/test_runtime_archives.py
T031: estados/reparo em tests/unit/test_runtime_repair.py
```

## Implementation Strategy

### MVP First (User Story 1)

Concluir Setup + Fundação + US1: T001–T022. Esse incremento demonstra primeiro uso e repetição offline, sem Graphviz instalado separadamente. As proteções mínimas de integridade e falha de preparação já são obrigatórias nesse MVP. A entrega completa exige também US2, US3 e fechamento; demonstração não equivale a autorização para publicar ou ignorar evidências pendentes.

### Incremental Delivery

1. Qualificar o pacote e estabelecer contratos compartilhados; não contornar origem/licença/hash ausentes.
2. Concluir US1 e demonstrar a jornada em cache limpo e pronto.
3. Concluir US2 para comprovar continuidade da qualidade e dos dados.
4. Concluir US3 para comprovar diagnóstico, repetição e reparo.
5. Concluir documentação, distribuição e matriz real de aceitação antes de alterar status para implementada/validada.

### Parallel Team Strategy

Os grupos `[P]` permitem divisão futura de trabalho, mas este arquivo não inicia agentes nem execução. Responsáveis por `runtime.py`, CLI e arquivo de evidências devem integrar sequencialmente. Não dividir a mesma implementação entre pessoas/agentes simultaneamente.

## Requirement Coverage

| Requisitos/critério | Tarefas principais |
| --- | --- |
| FR-001–002; SC-001 | T003–T022, T043 |
| FR-003 | T001, T007, T022, T038, T043 |
| FR-004; SC-003 | T019, T024, T026, T028, T036 |
| FR-005; SC-002 | T018, T023, T027–T028, T043 |
| FR-006; SC-006 | T010, T019–T020, T025–T026, T029, T033–T034 |
| FR-007; SC-004 | T029–T037 |
| FR-008 | T014–T017, T030–T037 |
| FR-009; SC-005 | T038–T039, T041, T043–T044 |
| FR-010; SC-007 | T011–T017, T022, T027, T034, T036, T043 |
| FR-011 | T003–T007, T040–T041, T044 |

## Notes

- Marcar uma tarefa concluída somente quando seu resultado e evidência exigida existirem. Ausência de ambiente/rede/licença não equivale a aprovação de uma simulação substituta.
- Não há tarefa de publicação, deploy, commit, troca de branch ou mudança constitucional nesta solicitação.
- Não substituir o runtime fixado nem elevar limites silenciosamente para contornar falhas de qualificação; registrar evidência e ajustar o desenho se necessário.


## Phase 7: Convergence

**Assessment (2026-10-16)**: 11 FR, 7 SC, 11 cenários de aceitação, 8 casos de borda, 12 decisões técnicas, 6 princípios constitucionais e 45 tarefas avaliados no estado atual. Achados: 6 partial e 1 contradicts; 3 HIGH, 3 MEDIUM e 1 LOW; nenhum CRITICAL ou unrequested identificado. Esta fase trata as lacunas F1–F7 abaixo, sem modificar tarefas anteriores ou repetir como concluídas evidências ausentes.

**Scope**: manter a instrução do mantenedor de prosseguir no sistema atual sem criar VM. T022/T043 continuam adiadas, com validação limpa não demonstrada. Não provisionar VM nem exigir essa etapa para executar as correções locais abaixo. T028 continua sendo a origem da revisão visual; T044 conserva o fechamento integral pendente enquanto faltarem as evidências originalmente exigidas. Os achados de cobertura abaixo não demonstram, por si, falha do produto nos cenários ainda não testados.

- [X] T046 [HIGH] Completar a cobertura de preparação em `tests/unit/test_runtime_archives.py` e `tests/unit/test_runtime_repair.py`, com transporte/relógio/runner controlados e sem rede real: verificar falhas TLS/HTTP, aceitação de até cinco redirecionamentos e rejeição do sexto, prazo global cooperativo de 300s, timeout de rede até 30s, contagem efetiva de bytes recebidos/extraídos e sondagens com versão incorreta, `json0` inválido e limites de 10s/1 MiB. Conferir `DependencyError`, causa/impacto/recuperação, ausência de seleção incompleta e preservação da geração anterior; corrigir apenas falhas de comportamento demonstradas em `src/twine_edge_overlap/runtime.py`. Evidência F3: os testes anteriores usavam erro de timeout injetado diretamente e atributos do ZIP, sem relógio de preparação controlado, falhas TLS/HTTP, cadeia de seis redirecionamentos ou respostas inválidas controladas de sondagem. Rastreabilidade: T013/T016/T030/T031/T033, FR-007/FR-008 e plan: limites de preparação (partial).
- [X] T047 [HIGH] Acrescentar a `tests/unit/test_runtime_repair.py` ou `tests/integration/test_runtime_concurrency.py` cenários Windows de link/junction/reparse point já presente na raiz, seletor ou árvore do cache e na limpeza do staging/seletor temporário da própria tentativa. Usar diretórios descartáveis e sentinelas externas para demonstrar rejeição sem executar payload nem alterar conteúdo externo ou gerações anteriores; registrar limitação explícita se a criação do tipo de link exigir permissão indisponível, sem apresentar atributos de entrada ZIP como prova equivalente. Corrigir em `src/twine_edge_overlap/runtime.py` somente problemas demonstrados, preservando a limpeza restrita à própria tentativa. Evidência F4: `test_symlink_and_reparse_member_and_duplicate_case` cobria membros do ZIP; faltava cenário de link no sistema de arquivos do cache ou sentinela externa durante limpeza. Rastreabilidade: T014/T015/T017/T031, FR-008/SC-003 e plan: contenção e preservação de gerações (partial).
- [ ] T048 [HIGH] Concluir a parte pendente de T028 no sistema atual: reabrir no Twine as seis cópias identificadas em `specs/002-manage-layout-runtime/layout-results.json` ou `current-host-results.json`, confirmar os hashes dos arquivos efetivamente abertos e conferir visualmente passagens, conexões e layout; registrar versão do Twine, resultado por caso e evidência em `validation.md` e no relatório correspondente. Não executar histórias/scripts nem substituir reabertura por parser/roundtrip; se a interface continuar indisponível, manter a tarefa pendente com o impedimento real. Não criar VM. Evidência F5: `twine_reopened: false` nos relatórios e falha de acesso à interface registrada em `validation.md`. Rastreabilidade: T028, US1/AC1, US2/AC1 e SC-002 (partial).
- [X] T049 [MEDIUM] Reforçar `load_manifest()` em `src/twine_edge_overlap/runtime.py` e seus testes em `tests/unit/test_runtime.py` para rejeitar inventário com colisão arquivo/diretório ancestral, destinos de avisos que não sejam descendentes de `third-party-notices/` e `source_references` fora do formato de lista de URLs de fontes. Validar antes de qualquer transferência ou execução, mantendo o manifesto qualificado e os avisos atuais aceitos. Evidência F1: sondagens em memória com `_read_json` controlado aceitaram arquivo no prefixo ancestral do executável, destino exatamente `third-party-notices` e `source_references='placeholder'`. Rastreabilidade: T005/T006/T007, FR-011 e plan: manifesto/inventário/avisos validados (partial).
- [X] T050 [MEDIUM] Remover a preparação implícita de dentro de `graphviz.layout()` em `src/twine_edge_overlap/engines/graphviz.py`, exigindo o RuntimeHandle fornecido pela aplicação e conservando geometria e contexto da geração. Ajustar os testes com runner/motor falso, especialmente `tests/integration/test_engine_failures.py` e `tests/integration/test_limited_results.py`, para injetar handle/provedor falso explicitamente, sem aquisição real acidental; manter os testes nativos identificados usando o runtime gerenciado real. Acrescentar uma verificação comportamental de que o fluxo isolado não resolve ou baixa runtime e de que a aplicação continua preparando uma única vez. Evidência F2: `layout(..., runtime=None)` executava `runtime or ensure_runtime()` e testes com motor falso chamavam layout/run sem injeção de runtime. Rastreabilidade: T018/T019/T021 e plan: decisão 4, preparação na aplicação e nenhuma segunda resolução em layout (contradicts).
- [X] T051 [LOW] Atualizar as seções de estado do `README.md` em português e inglês para refletir os ensaios locais reais com CPython 3.12 e 3.14 registrados em `current-host-results.json`, distinguindo-os da validação em Windows limpo adiada e da reabertura no Twine conforme a evidência disponível após T048. Manter os dois idiomas equivalentes e os comandos de uso existentes. Evidência F6: ambas as seções descreviam validação local somente com CPython 3.14. Rastreabilidade: T038, FR-009/SC-005 (partial).
- [X] T052 [MEDIUM] Consolidar em `specs/002-manage-layout-runtime/validation.md` a rastreabilidade FR-001–011/SC-001–007 após T046–T051, registrando correções, testes efetivamente executados e revisão constitucional proporcional; conferir as instruções PT/EN e o status da especificação contra as evidências. Preservar T022/T043 como adiadas por decisão do mantenedor, não inferir ambiente limpo dos ensaios locais e não declarar T044 ou a aceitação integral concluídas enquanto faltar evidência exigida. Se T048 estiver bloqueada, registrar a revisão visual como pendente. Evidência F7: T044 segue aberta e o registro anterior documenta apenas a aceitação local, com reabertura e matriz limpa ausentes. Rastreabilidade: T044, FR-003/FR-009/FR-011, SC-001/SC-002/SC-005/SC-007 e plan: estratégia de validação (partial).
