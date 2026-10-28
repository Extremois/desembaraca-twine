# Feature Specification: Uso do Desembaraça Twine em Linux e macOS

**Política de validação atualizada por instrução do usuário (2026-10-27):** validar exclusivamente pelo GitHub Actions, diretamente nos runners hospedados e em contêineres quando necessários. Não exigir teste nativo, hardware dedicado, runner próprio, kernel específico ou VM; não criar nem iniciar VMs, inclusive dentro do CI. Esta decisão substitui exigências anteriores desses ambientes e suas pendências históricas. Conservar hashes, integridade, instalação, corpus, recuperação e o ambiente efetivamente exercitado nos logs; não inventar cobertura. Resultados de VMs anteriores são somente histórico e não são gates de aceite.


**Feature Branch**: Não criada nesta etapa; nenhum hook de branch configurado. Branch Git atual: `feat/002-manage-layout-runtime`. Identificador independente: `003-add-cross-platform-support`.

**Created**: 2026-10-17

**Status**: Esclarecida e pronta para planejamento. Suporte Linux/macOS ainda não implementado nem validado.

**Input**: User description: "Vamos tornar o nosso projeto usavel em diferentes sistemas operacionais. Agora que temos funcionando um MVP no Windows o proximo passo é tornar usavel em Linux e MacOS."

## Clarifications

### Session 2026-10-17

- Q: Quais sistemas e arquiteturas devem receber suporte oficial nesta primeira expansão para Linux e macOS? → A: Opção C, incluindo Ubuntu 24.04 LTS x64 e ARM64 e macOS 15 Apple Silicon e Intel, com ampliação para as demais distribuições Linux populares; o objetivo é atender quase todas as distribuições, sem exigir cobertura universal caso inviável.
- Q: Como devemos definir o suporte às distribuições Linux para atender esse objetivo de ampla compatibilidade? → A: Opção B: suporte oficial a versões definidas de Ubuntu/Debian, Fedora/RHEL, Arch/Manjaro, openSUSE e Alpine e derivados; demais distribuições com compatibilidade de melhor esforço. Melhor esforço permite uso quando houver componentes compatíveis, com aviso de ambiente não validado e sem garantia de suporte completo.
- Q: Quais versões das distribuições Linux devemos validar oficialmente na primeira entrega? → A: Opção B: todas as versões ainda mantidas por cada distribuição incluída na matriz oficial, incluindo versões que recebem somente correções de segurança. Conforme a definição de manutenção esclarecida abaixo, atualizações disponíveis somente mediante assinatura paga não tornam a versão elegível à matriz obrigatória. Para distribuições de atualização contínua, registrar o ambiente pela data do teste.
- Q: Podemos disponibilizar o suporte a Linux e macOS gradualmente, conforme cada distribuição, versão e arquitetura for validada? → A: Opção A: liberar cada combinação após validação; as restantes continuam pendentes, sem reduzir o escopo total. A liberação de uma parte da matriz não significa conclusão integral da feature.
- Q: Devemos incluir no suporte oficial versões Linux que só continuam recebendo manutenção mediante assinatura paga? → A: Opção A: incluir versões com manutenção oficial disponível sem assinatura paga, inclusive manutenção somente de segurança; versões cuja única manutenção oficial depende de assinatura paga ficam fora da matriz obrigatória.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Processar uma história no Linux (Priority: P1)

Como pessoa que usa Linux, quero instalar o Desembaraça Twine pelo procedimento publicado e reorganizar uma história sem preparar manualmente o motor, para usar a ferramenta com a mesma simplicidade do MVP Windows.

**Why this priority**: Torna o benefício existente acessível a um dos dois novos públicos solicitados.

**Independent Test**: Em cada combinação Linux da matriz oficial das famílias Ubuntu/Debian, Fedora/RHEL, Arch/Manjaro, openSUSE e Alpine e derivados, cobrindo todas as versões elegíveis com manutenção oficial sem assinatura paga na data de referência e incluindo Ubuntu 24.04 LTS x64 e ARM64, com os pré-requisitos documentados e sem motor previamente instalado, seguir o procedimento de instalação e processar um exemplo de referência com melhoria conhecida. Repetir sem internet depois da preparação.

**Acceptance Scenarios**:

1. **Given** um ambiente Linux da matriz proposta, com os pré-requisitos publicados e sem componentes de processamento preparados, **When** a pessoa instala a ferramenta e processa o exemplo de referência, **Then** recebe uma cópia reorganizada, seu caminho e as três contagens antes/depois, sem instalar o motor separadamente ou indicar caminhos de executáveis.
2. **Given** a ferramenta instalada e uma história válida, **When** a pessoa chama `desembaraca-twine` de uma pasta diferente da pasta do projeto, usando caminho absoluto ou relativo à pasta atual, **Then** o arquivo é encontrado conforme o caminho informado e a cópia é criada ao lado da entrada.
3. **Given** a preparação concluída, **When** a pessoa processa os seis exemplos conhecidos sem conexão, **Then** obtém seis cópias íntegras com as três contagens finais zeradas, sem tentativa de acesso à rede.

---

### User Story 2 - Processar uma história no macOS (Priority: P1)

Como pessoa que usa um Mac com Apple Silicon ou Intel, quero instalar e executar a ferramenta com instruções próprias do meu sistema, sem descobrir componentes compatíveis ou configurar seus caminhos.

**Why this priority**: Entrega o segundo novo sistema solicitado e evita tratar compatibilidade de arquitetura como responsabilidade do usuário.

**Independent Test**: Em macOS 15 com Apple Silicon e, separadamente, com Intel, seguir as instruções publicadas sem motor previamente instalado; processar um exemplo com melhoria conhecida e repetir com os componentes já disponíveis e sem conexão.

**Acceptance Scenarios**:

1. **Given** um Mac da matriz proposta com os pré-requisitos documentados, **When** a pessoa instala e executa o mesmo comando público da ferramenta, **Then** os componentes necessários são disponibilizados para esse ambiente sem instalação manual do motor, configuração de seus caminhos ou exigência de executar em modo de outra arquitetura.
2. **Given** a ferramenta instalada e uma história em pasta com espaços ou acentos, **When** a pessoa processa o arquivo de outra pasta, **Then** a ferramenta gera uma cópia íntegra e informa corretamente seu caminho.
3. **Given** a preparação concluída, **When** a pessoa processa os seis exemplos conhecidos offline, **Then** as três contagens finais permanecem zeradas nos seis, sem consultas remotas.
4. **Given** um bloqueio conhecido de acesso ou execução no sistema, **When** a ferramenta não consegue preparar ou usar um componente, **Then** informa causa, impacto e recuperação compatíveis com o macOS, preserva o original e não orienta a desabilitar proteções do sistema.

---

### User Story 3 - Confiar nos resultados em qualquer sistema suportado (Priority: P1)

Como pessoa que compartilha histórias entre Windows, Linux e macOS, quero manter os conteúdos, conexões e a qualidade do layout, sem perder arquivos ao mudar de sistema.

**Why this priority**: Portabilidade só entrega valor se conservar as garantias de integridade e o uso existente no Windows.

**Independent Test**: Processar o corpus de referência em cada combinação da matriz. Comparar bytes dos originais, invariantes das cópias e as três métricas; reabrir no Twine as seis cópias de referência geradas em cada sistema.

**Acceptance Scenarios**:

1. **Given** os seis exemplos com resolução conhecida, **When** são processados em cada ambiente suportado, **Then** produzem cópias reabríveis no Twine com zero conflitos entre arestas, zero sobreposições entre nós e zero travessias de nós alheios; não é exigida igualdade de coordenadas entre sistemas.
2. **Given** qualquer entrada válida do perfil vigente, **When** é publicada uma cópia, **Then** o original permanece idêntico byte a byte e a cópia preserva conteúdos, identificadores, metadados e conexões com direção e multiplicidade, exceto pelas alterações de apresentação já autorizadas.
3. **Given** um nome de saída ocupado, uma falha ou uma interrupção, **When** a execução termina, **Then** nenhum arquivo existente é sobrescrito e nenhuma saída parcial é anunciada como válida.
4. **Given** um grafo sem melhoria admissível ou com conflitos restantes, **When** uma cópia íntegra é gerada, **Then** nenhuma das três contagens aumenta e o resultado informa limitações; sucesso completo só é informado com as três contagens zeradas e observadas as demais limitações do perfil.
5. **Given** o procedimento existente no Windows, **When** as adaptações para os outros sistemas são disponibilizadas, **Then** processamento, preparação antecipada, reparo e uso offline continuam funcionando no Windows com os mesmos contratos públicos.

---

### User Story 4 - Entender e recuperar falhas no próprio sistema (Priority: P2)

Como pessoa sem conhecimento dos componentes internos, quero receber uma orientação aplicável ao meu sistema quando a preparação falhar, para corrigir o impedimento e repetir o procedimento sem perder histórias ou uma instalação saudável.

**Why this priority**: Diferenças de permissões, conexão e arquitetura não devem resultar em sucesso enganoso ou instruções exclusivas do Windows.

**Independent Test**: Em cada sistema da matriz, provocar indisponibilidade de conexão, espaço ou permissão e interromper uma preparação. Conferir mensagem, arquivos preservados e sucesso após corrigir a condição; verificar uso offline após reparo malsucedido de uma instalação saudável.

**Acceptance Scenarios**:

1. **Given** uma etapa que precisa de conexão e acesso indisponível, **When** a preparação falha, **Then** a mensagem em português explica o impacto, orienta restabelecer acesso e repetir e não anuncia cópia válida.
2. **Given** falta de espaço, permissão insuficiente ou preparação interrompida, **When** a ferramenta retorna, **Then** informa o impedimento conhecido, conserva os arquivos existentes e permite nova tentativa após correção.
3. **Given** componentes saudáveis já preparados, **When** um reparo falha, **Then** o processamento posterior continua utilizável offline com os componentes anteriores, sem configuração manual.
4. **Given** sistema, arquitetura ou pré-requisito incompatível com os componentes disponíveis, **When** essa incompatibilidade é identificada, **Then** a ferramenta explica o impedimento e não prepara nem anuncia componentes incompatíveis como prontos. Estar fora da matriz de validação oficial, isoladamente, não caracteriza incompatibilidade técnica.
5. **Given** uma distribuição Linux fora da matriz oficial, mas com componentes comprovadamente compatíveis com o ambiente, **When** a pessoa executa a ferramenta, **Then** o uso pode prosseguir em melhor esforço com aviso de ambiente não validado, sem anunciar suporte oficial nem reduzir as verificações de integridade e preservação.
6. **Given** uma combinação alvo que concluiu os ensaios exigidos enquanto outras permanecem pendentes, **When** uma versão da ferramenta é disponibilizada, **Then** essa combinação pode ser anunciada como oficialmente suportada e as demais continuam identificadas como pendentes, sem declarar a feature inteira concluída ou reduzir o escopo acordado.

### Edge Cases

- Sistema identificado apenas como Linux: identificar a distribuição e versão para distinguir suporte oficial de melhor esforço; não presumir equivalência entre todas as distribuições. Fora da matriz, só prosseguir quando houver componentes compatíveis e informar que o ambiente não foi validado.
- Distribuição derivada de uma família suportada: não herdar automaticamente a classificação oficial pelo nome da família; versões e combinações oficialmente cobertas precisam ser nomeadas na matriz, incluindo as distribuições de referência para Alpine e derivados.
- Versão mantida somente para correções de segurança: continua incluída quando essa manutenção oficial está disponível sem assinatura paga; registrar o estado, a elegibilidade sem assinatura paga e sua fonte na data de referência. Versões encerradas antes dessa data não entram automaticamente no suporte oficial.
- Versão cuja única manutenção oficial depende de assinatura paga: fica fora da matriz obrigatória. Essa exclusão de compromisso oficial não representa incompatibilidade técnica; uso em melhor esforço continua possível quando houver componentes compatíveis e aviso de ambiente não validado.
- Distribuição de atualização contínua: identificar o ambiente validado pela data do teste; não prometer que qualquer atualização futura já esteja validada. Novas versões ou arquiteturas publicadas após a data de referência exigem qualificação antes de serem anunciadas como suportadas.
- Arquitetura do ambiente diferente da suportada: não escolher componentes de outra arquitetura nem exigir que a pessoa configure uma camada de compatibilidade. Mac Intel e Linux ARM64 integram o escopo e precisam de validação própria, assim como Apple Silicon e Linux x64.
- Instalação global do motor presente, incompatível ou inacessível: não exigir removê-la ou ajustá-la para usar o procedimento recomendado.
- Diretório do projeto, perfil, entrada ou saída com espaços, acentos e outros nomes válidos no sistema: conservar leitura, publicação e apresentação corretas dos caminhos.
- Diferenças de maiúsculas/minúsculas e de representação de nomes entre sistemas: não sobrescrever um arquivo existente nem apontar para outro arquivo por suposição de equivalência.
- Arquivo com finais de linha e metadados originados em outro sistema: conservar os bytes do original e os dados fora das alterações autorizadas.
- Perfil ou pasta de instalação sem permissão para escrita/execução, temporários indisponíveis ou pasta de destino sem escrita: falhar com orientação sem exigir privilégios de administrador para o uso normal.
- Duas preparações ou um reparo concorrendo com processamento: não expor componentes incompletos, remover componentes em uso ou prejudicar processos alheios.
- Componente ausente, alterado, interrompido ou preparado para outro ambiente: não tratá-lo como pronto; explicar como repetir ou reparar sem alterar histórias.
- Conexão ausente antes da preparação versus depois dela: distinguir uma etapa que precisa de acesso de processamento já pronto para funcionar offline.
- Entrada inválida: rejeitar o arquivo antes de iniciar preparação desnecessária.
- Restrições conhecidas de segurança do macOS ou de execução no Linux: não recomendar desligar proteções ou elevar privilégios como procedimento normal.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O procedimento recomendado DEVE permitir instalar e processar uma história válida em cada ambiente Linux/macOS da matriz proposta, sem motor previamente instalado, produzindo melhoria efetiva no exemplo conhecido (US1/AC1, US2/AC1).
- **FR-002**: A aplicação DEVE disponibilizar os componentes de processamento adequados ao sistema e arquitetura suportados sem exigir instalação separada do motor, localização de executáveis, edição de caminhos de componentes ou uso manual de outra arquitetura (US1/AC1, US2/AC1).
- **FR-003**: A documentação DEVE publicar uma matriz explícita de sistema, versão, arquitetura e pré-requisitos, distinguindo suporte oficial validado, alvos ainda propostos e compatibilidade de melhor esforço. O escopo oficial DEVE incluir Linux x64 e ARM64 nas famílias Ubuntu/Debian, Fedora/RHEL, Arch/Manjaro, openSUSE e Alpine e derivados, além de macOS 15 Apple Silicon e Intel. Cada distribuição e versão oficialmente coberta DEVE ser nomeada; pertencer à mesma família não implica validação automática. Fora da matriz Linux oficial, o uso DEVE poder prosseguir quando houver componentes compatíveis, com aviso de ambiente não validado e sem garantia de suporte completo. Incompatibilidade técnica DEVE impedir uso de componentes inadequados, independentemente do nível de suporte (US4/AC4–5).
- **FR-004**: A ferramenta instalada DEVE poder ser usada de qualquer pasta pelo comando `desembaraca-twine`, aceitando caminho absoluto ou relativo à pasta atual; a documentação DEVE explicar sua disponibilização no terminal e uma alternativa que não dependa de ajuste manual dessa localização. O uso pelo checkout continua disponível (US1/AC2, US2/AC2).
- **FR-005**: Após preparação concluída e com os componentes íntegros disponíveis, a ferramenta DEVE processar arquivos sem internet e sem tentar conexões ou consultas de atualização em todos os ambientes suportados (US1/AC3, US2/AC3).
- **FR-006**: Os contratos existentes de um arquivo por execução, perfil `.twee`, conteúdo, identidade dos nós, metadados, direção/multiplicidade de conexões e alterações visuais autorizadas DEVEM permanecer válidos nos três sistemas (US3/AC2).
- **FR-007**: As três contagens DEVEM respeitar simultaneamente a não regressão; os seis exemplos de resolução conhecida DEVEM manter as três contagens finais zeradas e gerar cópias reabríveis no Twine em cada ambiente da matriz, sem exigir coordenadas idênticas entre plataformas (US3/AC1/4).
- **FR-008**: Em conclusão normal, falha, cancelamento e colisão de nomes, o original e arquivos preexistentes DEVEM permanecer intactos; somente cópia íntegra e verificada pode ser anunciada como saída válida, ao lado da entrada (US3/AC2–3).
- **FR-009**: O resultado DEVE conservar a distinção entre sucesso, limitações e falha, os códigos de saída existentes e, quando houver cópia válida, caminho absoluto e três contagens antes/depois. Indisponibilidade do motor não pode ser ocultada por sucesso completo (US3/AC4–5).
- **FR-010**: Preparação antecipada e reparo DEVEM continuar disponíveis nos mesmos comandos públicos em todos os ambientes suportados. Reparo malsucedido e interrupção da preparação DEVEM conservar uma instalação anterior saudável utilizável offline, sem promover componentes incompletos (US3/AC5, US4/AC2–3).
- **FR-011**: Falhas conhecidas de conexão, integridade, espaço, acesso, execução, concorrência e compatibilidade DEVEM gerar mensagem em português com causa conhecida, impacto e recuperação aplicável ao sistema. A mensagem não DEVE recomendar desabilitar proteções, configurar caminhos do motor ou instalar o motor separadamente (US2/AC4, US4/AC1–4).
- **FR-012**: README em português e inglês DEVE oferecer instruções equivalentes para cada sistema: pré-requisitos, instalação remota sem checkout obrigatório, execução de qualquer pasta, preparação, reparo, resultado esperado e necessidades de internet. O procedimento de uso normal não DEVE exigir privilégios de administrador ou alterar configurações globais do sistema (US1/AC1–2, US2/AC1–2, US4).
- **FR-013**: O fluxo Windows existente DEVE permanecer utilizável nas combinações já definidas, com preservação, qualidade, limites operacionais, cancelamento e uso offline sem regressão decorrente da expansão (US3/AC5).
- **FR-014**: Componentes disponibilizados para cada plataforma DEVEM ter origem, integridade e licença verificadas e avisos exigidos acessíveis na distribuição e no ambiente preparado, inclusive offline. Ausência de evidência de compatibilidade ou de pré-requisito necessário DEVE impedir declarar aquela combinação como entregue (US1/AC1, US2/AC1; constituição).
- **FR-015**: O processamento DEVE continuar local: histórias, títulos, conteúdos e caminhos não podem ser enviados a serviços externos para reorganização ou preparação de componentes; funcionalidades do conteúdo da história não DEVEM ser executadas (US3/AC2; garantias existentes).
- **FR-016**: A entrega DEVE registrar evidências de instalação, primeiro processamento, seis referências offline, preservação, reparo, interrupção, concorrência e reabertura no Twine por ambiente da matriz. Ensaios de um sistema não podem ser apresentados como validação de outro, e testes não executados ou simulados DEVEM ser identificados como tal (US1–4; constituição).
- **FR-017**: A matriz oficial Linux DEVE abranger todas as versões com manutenção oficial disponível sem assinatura paga de cada distribuição explicitamente incluída, inclusive manutenção somente de segurança, em uma data de referência registrada no planejamento com fontes de manutenção e elegibilidade identificadas. Versões cuja única manutenção oficial depende de assinatura paga ficam fora da matriz obrigatória, sem impedir uso em melhor esforço tecnicamente compatível. Para distribuições de atualização contínua, DEVE identificar o ambiente pela data de teste. Ubuntu 24.04 LTS x64 e ARM64 permanecem alvos obrigatórios. A matriz DEVE distinguir versões e arquiteturas efetivamente disponibilizadas pela distribuição, sem exigir combinações inexistentes, e não pode reduzir silenciosamente os alvos elegíveis por dificuldade de implementação ou validação. Combinações ainda não qualificadas permanecem pendentes; novos lançamentos não herdam validação automática (US1/AC1–3, US4/AC4–5).
- **FR-018**: A entrega DEVE permitir liberar gradualmente combinações de distribuição/sistema, versão e arquitetura após conclusão dos ensaios exigidos para cada uma. Cada liberação DEVE identificar as combinações oficialmente validadas e os demais alvos pendentes. Liberação parcial não elimina alvos acordados nem comprova conclusão integral da feature; os critérios de cobertura total permanecem exigíveis para seu encerramento (US4/AC6).

### Key Entities

- **Ambiente de execução**: Sistema operacional, versão, arquitetura e pré-requisitos que determinam se uma combinação integra a matriz proposta e se foi validada.
- **Componentes de processamento preparados**: Recursos compatíveis com o ambiente, sua integridade, origem, avisos e estado de disponibilidade para processamento e reparo.
- **História de entrada e cópia reorganizada**: Arquivo no perfil vigente, dados preservados, posições autorizadas e métricas de conflito antes/depois.
- **Resultado e evidência de compatibilidade**: Estado da operação, caminhos e contagens aplicáveis, diagnóstico/recuperação e registro dos ensaios realizados em cada ambiente.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das combinações da matriz proposta, seguir somente as instruções publicadas, com os pré-requisitos documentados e sem motor previamente instalado, permite instalar a ferramenta e obter uma cópia com melhoria efetiva do exemplo de referência.
- **SC-002**: Em cada combinação da matriz, 6 de 6 exemplos conhecidos geram cópias reabríveis no Twine com as três contagens finais iguais a zero; no restante do corpus, nenhuma das três contagens aumenta.
- **SC-003**: Em 100% dos cenários de preservação, colisão, falha e cancelamento, o original e arquivos preexistentes permanecem idênticos byte a byte; todas as cópias anunciadas como válidas preservam os dados fora das alterações autorizadas.
- **SC-004**: Após preparação, 6 de 6 referências são processadas com sucesso em cada ambiente quando a rede está indisponível, sem nenhuma tentativa de conexão durante o processamento.
- **SC-005**: Em 100% dos cenários de erro aplicáveis e exercitados, há causa conhecida, impacto e recuperação compreensíveis; após corrigir o impedimento recuperável, repetir o procedimento produz o resultado esperado sem configuração manual do motor. Reparo malsucedido de componentes saudáveis não impede processamento offline posterior.
- **SC-006**: Em 100% dos cenários de conclusão, estado, código e arquivos publicados correspondem ao resultado real; nenhuma saída parcial ou preparação incompleta é anunciada como válida, e o corpus Windows mantém os resultados funcionais exigidos antes da expansão.
- **SC-007**: Os percursos de instalação e uso em português e inglês cobrem todas as linhas da matriz, permitem executar de fora da pasta do projeto e explicitam os pré-requisitos e as etapas dependentes de conexão, sem exigir aquisição manual do motor, privilégios administrativos no uso normal ou desativação de proteções.
- **SC-008**: Toda combinação anunciada como suportada possui registro identificável dos ensaios exigidos e dos avisos/origens aplicáveis; combinações não ensaiadas permanecem explicitamente propostas ou pendentes, sem herdar aprovação de outra plataforma.
- **SC-009**: A matriz identifica 100% das versões elegíveis com manutenção oficial sem assinatura paga das distribuições incluídas na data de referência e o estado de validação de cada combinação alvo. Cada exclusão de versão encerrada, manutenção exclusivamente paga ou combinação inexistente possui justificativa verificável; cada distribuição de atualização contínua validada possui data de teste registrada.
- **SC-010**: Em 100% das liberações graduais, todas as combinações anunciadas como oficialmente suportadas possuem as evidências exigidas e todos os demais alvos continuam identificados como pendentes. Os critérios de 100% da matriz aplicam-se ao encerramento integral da feature e não impedem liberar antecipadamente uma parte já validada.

## Assumptions

- **Matriz e abrangência confirmadas pelo mantenedor**: Ubuntu 24.04 LTS em x64 e ARM64; macOS 15 em Apple Silicon (ARM64) e Intel (x64). O escopo oficial Linux inclui todas as versões com manutenção oficial sem assinatura paga das distribuições explicitamente nomeadas nas famílias Ubuntu/Debian, Fedora/RHEL, Arch/Manjaro, openSUSE e Alpine e derivados, com x64 e ARM64 como arquiteturas alvo quando efetivamente disponibilizadas pela distribuição. As distribuições concretas de referência, suas versões elegíveis e combinações publicadas devem ser nomeadas e verificadas; não se promete validação de todas as derivadas de uma família. O planejamento registrará a matriz completa e sua data de referência conforme FR-017, sem reduzir silenciosamente os alvos elegíveis. Versões cuja única manutenção depende de assinatura paga ficam fora da matriz obrigatória. Outras distribuições ou versões Linux podem ser utilizadas em melhor esforço quando houver componentes compatíveis, com aviso de ambiente não validado e sem suporte completo. Essa é uma definição de escopo futuro, não uma declaração de compatibilidade atual. Ambientes de emulação não substituem a validação de cada arquitetura nativa.
- **Política de liberação confirmada**: o suporte oficial pode ser disponibilizado gradualmente por combinação validada, sem esperar a matriz inteira. O escopo completo continua sendo o compromisso da feature; alvos ainda não validados permanecem pendentes e os critérios de cobertura total são a condição de encerramento integral, não uma condição para cada liberação parcial.
- Windows 11 x64 permanece como alvo de regressão. Mantêm-se os requisitos de interpretador já publicados para o MVP: CPython 3.12 x64 e 3.14 x64; nas novas plataformas, as mesmas versões devem corresponder à arquitetura nativa da linha da matriz. O mínimo de metadados do pacote não amplia o suporte a outras versões. Versões de correção e condições dos ambientes devem ser registradas nos ensaios.
- Instalação do interpretador continua sendo um pré-requisito documentado. A solicitação não exige executável autônomo, interface gráfica, suporte móvel, processamento em lote, novos formatos, mudança de idioma da CLI ou expansão dos limites de histórias. A aplicação continua sendo usada por terminal.
- A simplicidade do gerenciamento de componentes da feature [002](../002-manage-layout-runtime/spec.md), incluindo preparação automática e uso offline, é requisito de continuidade. Não se impõe nesta especificação um mecanismo de aquisição, motor alternativo, formato de distribuição ou solução de isolamento; essas decisões cabem ao planejamento com avaliação de alternativas e licenças.
- O comando público alvo é `desembaraca-twine`, conforme a renomeação já presente no checkout. A renomeação e as instruções remotas ainda não publicadas da feature anterior são dependências de integração; esta especificação não pressupõe que já estejam disponíveis na branch principal ou em uma versão distribuída.
- O corpus, as seis referências e os contratos de formato/preservação da feature [001](../001-reduce-edge-overlap/spec.md) permanecem a base de aceitação. O objetivo é ampliar a compatibilidade, não trocar o problema geométrico nem prometer resolver todos os grafos.
- O MVP Windows é a base funcional, não prova de aceitação integral: [as pendências registradas](../002-manage-layout-runtime/validation.md), inclusive a revisão visual anterior e a aceitação em Windows limpo adiada pelo mantenedor, não são convertidas em evidência concluída. Não se cria VM nesta etapa; ambientes de validação Linux/macOS serão definidos no planejamento, mantendo evidências indisponíveis como pendentes.
- Instalação e primeira preparação podem depender de conexão, desde que explícito. Processamento com componentes disponíveis deve permanecer local e offline. Não se exige primeira instalação sem internet nem se autoriza publicação de pacotes, releases ou mudança de branch nesta etapa de especificação.
