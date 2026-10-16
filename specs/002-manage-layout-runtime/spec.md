# Feature Specification: Uso sem instalação separada do Graphviz

**Feature Branch**: Não criada; nenhum hook de branch configurado.

**Created**: 2026-10-16

**Status**: Implementação local validada; aceitação em ambiente limpo e reabertura no Twine pendentes.

**Escopo da retomada (2026-10-16)**: por instrução do mantenedor, prosseguir no
sistema atual sem criar VM. Primeiro uso real e seis referências offline
revalidados com CPython 3.12 e 3.14; resultados em
[validation.md](validation.md). A aceitação em ambiente limpo fica adiada,
sem ser apresentada como executada ou dispensada; reabertura no Twine pendente.

**Convergência implementada (2026-10-16)**: validação adicional do manifesto,
diagnóstico correto de prazo global e RuntimeHandle obrigatório no adaptador.
Suíte com 122 testes aprovada nas duas versões de Python e novas distribuições
instaladas/testadas fora do checkout. T048 continua pendente por indisponibilidade
da interface do Twine; não se declara aceitação integral. Evidências em
[convergence-results.json](convergence-results.json) e [validation.md](validation.md).

**Input**: User description: "Quero que o Desembaraça Twine funcione sem exigir que o usuário instale ou configure o Graphviz separadamente, simplificando instalação e primeiro uso para pessoas sem conhecimento técnico. Preservar leitura, reorganização e geração da cópia Twine, atender aos sistemas oficialmente suportados e orientar claramente em caso de componente indisponível. Documentar requisitos e necessidades de internet. Avaliar a solução no planejamento técnico."

## Clarifications

### Session 2026-10-16

- Q: Depois que os componentes necessários estiverem disponíveis, o processamento de arquivos deve funcionar sem conexão à internet? → A: Sim. O processamento deve funcionar sem internet após a preparação inicial.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Processar o primeiro arquivo em uma máquina limpa (Priority: P1)

Como pessoa sem conhecimento técnico, quero seguir somente as instruções do projeto para instalar e executar a ferramenta e obter uma cópia reorganizada da história, sem instalar ou configurar o Graphviz separadamente.

**Why this priority**: Remove a barreira de adoção e entrega o benefício central.

**Independent Test**: Em ambiente limpo de cada sistema oficialmente suportado, sem Graphviz ou configurações herdadas, seguir o procedimento publicado e processar um exemplo válido com melhoria conhecida.

**Acceptance Scenarios**:

1. **Given** uma máquina limpa que atende aos requisitos documentados, sem Graphviz, **When** o usuário segue as instruções do projeto e processa um exemplo válido de referência, **Then** obtém uma cópia reorganizada reabrível no Twine, seu caminho e o resultado, sem instalação separada do motor.
2. **Given** um ambiente sem caminhos ou variáveis de ambiente para componentes de processamento, **When** o usuário executa o procedimento recomendado, **Then** a aplicação disponibiliza ou gerencia os componentes sem pedir localização de executáveis ou alteração dessas variáveis.
3. **Given** a preparação inicial concluída e os componentes necessários disponíveis, **When** o usuário processa outro arquivo válido sem conexão à internet, **Then** obtém uma cópia com tentativa efetiva de reorganização, sem refazer configuração manual de componentes e sem depender de acesso à rede.

---

### User Story 2 - Manter a qualidade e a integridade (Priority: P1)

Como usuário atual, quero que a instalação simplificada mantenha a leitura, a melhoria do layout e a geração de cópias íntegras para continuar confiando nos resultados.

**Why this priority**: A simplificação não pode comprometer os arquivos nem o benefício existente.

**Independent Test**: Processar o conjunto de referência existente pelo novo procedimento, comparar dados e contagens de conflitos e reabrir as cópias no Twine.

**Acceptance Scenarios**:

1. **Given** os seis exemplos de referência com resolução já demonstrada, **When** são processados sem Graphviz instalado pelo usuário, **Then** as cópias são reabríveis e mantêm zero conflitos entre arestas, zero sobreposições entre nós e zero travessias de nós alheios por arestas.
2. **Given** uma entrada válida, **When** é gerada uma cópia, **Then** o original permanece idêntico byte a byte e a cópia preserva os dados fora das alterações de posição autorizadas pelo perfil vigente, incluindo conteúdos, identificadores, metadados e conexões com direção e multiplicidade.
3. **Given** um grafo sem melhoria admissível, **When** é possível produzir uma cópia íntegra, **Then** nenhuma das três contagens aumenta e o resultado explica a limitação sem alegar resolução completa.
4. **Given** nome de saída ocupado ou falha de leitura, processamento ou escrita, **When** a ferramenta termina, **Then** nenhum arquivo existente é sobrescrito e nenhuma saída parcial é anunciada como válida; havendo cópia válida, informa caminho absoluto e contagens antes/depois, distinguindo sucesso, limitações e falha.

---

### User Story 3 - Resolver a indisponibilidade de um componente (Priority: P2)

Como usuário, quero entender por que um componente está indisponível e receber orientação para tentar novamente seguindo as instruções do projeto.

**Why this priority**: Evita diagnóstico técnico e resultados enganosos em condições de erro.

**Independent Test**: Simular componente indisponível e, quando aplicável, falta de conexão, espaço ou permissão; conferir a orientação, corrigir a condição e repetir a execução.

**Acceptance Scenarios**:

1. **Given** um componente ausente, incompatível ou inutilizável que a aplicação não consegue disponibilizar, **When** o processamento é solicitado, **Then** uma mensagem em português identifica o impedimento conhecido, explica seu impacto e indica uma ação ou procedimento de recuperação do projeto, sem exigir instalação separada do motor ou configuração de caminhos.
2. **Given** uma etapa dependente de conexão e a conexão indisponível, **When** a preparação não termina, **Then** a mensagem explica a necessidade de acesso e orienta restabelecer a conexão e repetir a etapa.
3. **Given** preparação interrompida ou bloqueada por falta de espaço ou permissão, **When** a execução retorna, **Then** explica a causa conhecida e a recuperação, preserva a entrada e não anuncia preparação incompleta como pronta nem saída parcial como válida.
4. **Given** o impedimento corrigido conforme a orientação, **When** o usuário repete o procedimento, **Then** consegue preparar os componentes e processar uma entrada válida sem configurar seus caminhos.

### Edge Cases

- Graphviz previamente instalado, incompatível ou inacessível: o procedimento recomendado continua utilizável sem exigir ajuste ou remoção dessa instalação.
- Caminhos de instalação, entrada e saída com espaços ou acentos: o fluxo documentado funciona sem ajustes nos caminhos dos componentes.
- Conexão ausente antes da preparação: explicar a necessidade quando a etapa depender dela; não prometer primeira instalação sem conexão.
- Conexão ausente após a preparação concluída: processar normalmente com os componentes disponíveis; consultas de atualização ou outras operações de rede não podem impedir o processamento.
- Preparação interrompida: não considerar componente incompleto como pronto e permitir nova tentativa após corrigir a causa.
- Falta de espaço ou permissão: explicar o impedimento, preservando entrada e arquivos existentes.
- Sistema ou arquitetura fora da matriz publicada: informar incompatibilidade quando detectada, sem anunciar suporte oficial.
- Entrada inválida: manter a rejeição explicativa, distinguindo problema no arquivo de indisponibilidade de componente.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O procedimento recomendado DEVE permitir instalar e executar a aplicação sem Graphviz previamente instalado, gerando uma cópia de um arquivo `.twee` válido com tentativa efetiva de reorganização (US1.1, US2.1).
- **FR-002**: A aplicação DEVE disponibilizar ou gerenciar os componentes necessários sem exigir instalação separada do Graphviz, localização manual de executáveis ou configuração de caminhos e variáveis de ambiente (US1.2–3).
- **FR-003**: O procedimento DEVE funcionar em todos os sistemas e arquiteturas da matriz de suporte publicada, que DEVE explicitar os requisitos de cada ambiente (US1.1 e Assumptions).
- **FR-004**: O fluxo DEVE manter um arquivo por execução, o perfil `.twee` vigente e as invariantes existentes de leitura, preservação dos dados, cópia sem sobrescrita e original inalterado (US2.2, US2.4).
- **FR-005**: As três contagens de conflitos DEVEM respeitar simultaneamente a não regressão. Os seis exemplos de referência existentes DEVEM manter as três contagens finais zeradas; não se exige igualdade de coordenadas com a versão anterior (US2.1–3).
- **FR-006**: O resultado DEVE manter a distinção entre sucesso completo, limitações e falha, com caminho absoluto e contagens antes/depois quando houver cópia válida. Indisponibilidade de componente ou ausência de melhoria NÃO DEVE ser ocultada por mensagem de sucesso completo (US2.3–4, US3.1).
- **FR-007**: A indisponibilidade de componente DEVE produzir mensagem em português com causa conhecida, impacto e ação de recuperação ou referência ao procedimento do projeto, sem exigir instalação separada do motor ou configuração manual de seus caminhos (US3.1–4).
- **FR-008**: Falhas ou interrupções na preparação DEVEM preservar o original e arquivos existentes, não anunciar componente incompleto como pronto nem saída parcial como válida, e permitir nova tentativa após corrigido o impedimento (US3.3–4).
- **FR-009**: A documentação DEVE oferecer um percurso completo do ambiente limpo ao arquivo gerado, com requisitos, matriz de suporte, comandos, resultado esperado, recuperação e necessidades de conexão em instalação, primeira execução e execuções posteriores. As instruções em português e inglês do README DEVEM refletir o mesmo procedimento (US1, US3).
- **FR-010**: Quando uma etapa de preparação ou recuperação de componentes depender de conexão, a falta de acesso DEVE gerar orientação explícita para restabelecer a conexão e repetir a etapa. Com a preparação inicial concluída e os componentes necessários disponíveis, o processamento DEVE funcionar sem internet e NÃO DEVE depender de consultas de atualização ou outras operações de rede (US1.3, US3.2–4).
- **FR-011**: Componentes disponibilizados pela aplicação DEVEM ter origem e licença identificadas, compatibilidade de inclusão verificada e textos e avisos exigidos acessíveis na distribuição, conforme a constituição (aceitação por verificação documental).

### Key Entities *(include if feature involves data)*

- **Ambiente suportado**: Sistema operacional, arquitetura e requisitos declarados para validar instalação e uso.
- **Componente de processamento**: Recurso necessário à reorganização cuja disponibilidade é responsabilidade da aplicação.
- **Entrada e cópia de saída**: História no perfil `.twee` vigente e sua cópia, com as mesmas invariantes de preservação e layout existentes.
- **Resultado**: Estado, impedimento conhecido e recuperação; quando há cópia válida, caminho e três contagens antes/depois.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos ambientes da matriz de suporte, uma instalação limpa seguindo somente as instruções do projeto permite obter uma cópia reorganizada de um exemplo válido de referência, sem instalação separada do motor ou configuração manual de caminhos e variáveis de ambiente.
- **SC-002**: Os seis exemplos de referência produzem cópias reabríveis no Twine com as três contagens finais iguais a zero pelo novo procedimento.
- **SC-003**: Em 100% dos cenários de aceitação, inclusive falhas de preparação, o original permanece idêntico byte a byte e nenhum arquivo existente é sobrescrito. Em 100% das cópias válidas, os dados fora das alterações autorizadas são preservados e nenhuma das três contagens aumenta.
- **SC-004**: Em 100% dos cenários de indisponibilidade aplicáveis à solução escolhida, o usuário recebe causa conhecida, impacto e orientação de recuperação; corrigido o impedimento, consegue repetir o procedimento sem configurar caminhos de componentes.
- **SC-005**: O percurso documentado cobre 100% dos ambientes suportados, explicita conexão para instalação, primeira execução e execuções posteriores e não omite etapas necessárias à preparação dos componentes para o primeiro resultado.
- **SC-006**: Em 100% dos cenários de conclusão, o estado corresponde ao resultado: nenhuma falha anuncia saída parcial válida e nenhuma cópia sem melhoria por indisponibilidade de componente é apresentada como sucesso completo.
- **SC-007**: Em 100% dos ambientes da matriz de suporte, após a preparação inicial, os seis exemplos de referência são processados com a conexão à internet desabilitada e os componentes disponíveis, gerando cópias íntegras com as três contagens finais zeradas, sem etapas adicionais de preparação.

## Assumptions

- A matriz oficial definida para esta entrega é Windows 11 x64 com CPython 3.12 x64 ou CPython 3.14 x64; ambas exigem validação completa antes da entrega. O mínimo `requires-python >=3.12` do código/metadados não implica suporte oficial às demais versões. Essa delimitação parte da referência Windows anterior; não há ampliação para Linux ou macOS.
- A solicitação remove a preparação separada do Graphviz; não exige eliminar os demais requisitos do projeto, criar interface gráfica ou instalador de um clique. O uso por terminal e os requisitos gerais permanecem até decisão técnica documentada.
- A instalação e a preparação inicial podem precisar de internet, desde que informado. Não se exige primeira instalação sem conexão. Após a preparação concluída, o processamento com os componentes disponíveis deve funcionar sem internet; eventual recuperação de componentes ausentes ou inutilizáveis pode precisar de conexão, conforme documentado.
- Distribuir Graphviz, gerenciar sua obtenção ou substituir a solução são alternativas para o planejamento, com avaliação de manutenção e licenças conforme a constituição 1.0.1. Esta especificação não escolhe a implementação.
- Os contratos e exemplos da [funcionalidade existente](../001-reduce-edge-overlap/spec.md), incluindo o [perfil de formato](../001-reduce-edge-overlap/contracts/format-profile.md), são dependências para demonstrar preservação e qualidade. Não há ampliação de formatos, limites ou processamento em lote, nem promessa de eliminar conflitos de qualquer grafo.
- A atualização das instruções de instalação integra a implementação futura; a descrição atual não será substituída por instruções de um procedimento ainda não entregue.
