# Feature Specification: Redução de sobreposição de arestas em arquivos .twee

**Feature Branch**: Não criada; nenhum hook de branch configurado.

**Created**: 2026-10-16

**Status**: Implementada e validada localmente no perfil documentado.

**Input**: User description: "Desenvolver uma ferramenta para reduzir a sobreposição visual de arestas em grafos representados em arquivos .twee. Na primeira versão, o usuário informará o caminho de um arquivo .twee existente. A ferramenta deverá processar sua representação gráfica e gerar uma nova cópia com as sobreposições de arestas resolvidas ou reduzidas, preservando o arquivo original, o conteúdo dos nós e suas conexões. O usuário deverá receber o caminho do arquivo gerado e uma indicação clara de sucesso, falha ou limitações que tenham impedido a resolução completa das sobreposições. O escopo inicial se limita ao processamento de um arquivo por execução."

## Clarifications

### Session 2026-10-16

- Q: Qual é a origem dos arquivos `.twee` que você pretende processar? → A: Aplicativo Twine.
- Q: Qual versão do Twine você usa para gerar esses arquivos? → A: Versão desconhecida; identificar a partir de um arquivo de exemplo.
- Q: Quais situações entre arestas a ferramenta deve tentar reduzir? → A: Cruzamentos e trechos coincidentes, excluindo o encontro normal em um nó comum.
- Q: Como você quer informar o caminho do arquivo e receber o resultado na primeira versão? → A: Pelo terminal, com caminho em um comando e resultado em mensagens.
- Q: Ao reorganizar o grafo, como a ferramenta deve tratar sobreposições entre os próprios nós? → A: Eliminar também as sobreposições entre nós já existentes.
- Q: A ferramenta também deve evitar que uma aresta atravesse um nó que não faz parte daquela conexão? → A: Corrigir essas situações existentes e evitar criar novas.

- Q: Qual formato a primeira versão deve aceitar e gerar após a inspeção da amostra? → A: Somente .twee, conforme a amostra real (opção A).
- Q: Como o editor Twine exibe as conexões? → A: Curvas ou linhas com dobras (opção B). O avaliador deve reproduzir o traçado do editor; segmentos retos não validam a melhoria nessa representação.
- Q: Onde o editor Twine é utilizado? → A: No site oficial `https://twinery.org/2/` (opção A). A versão efetivamente carregada pelo navegador ainda não foi identificada.
- Q: Qual licença deve ser aplicada ao código autoral? → A: Apache-2.0 (opção B), com texto em LICENSE e registro na constituição 1.0.1.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Obter uma cópia com arestas mais legíveis (Priority: P1)

Como pessoa que trabalha com um grafo em um arquivo .twee, quero informar seu caminho
em um comando no terminal para obter uma nova cópia com menos conflitos entre arestas
e sem sobreposições entre nós nem arestas atravessando nós alheios à conexão, mantendo meus dados.

**Why this priority**: Entrega o benefício central sem colocar o arquivo original em risco.

**Independent Test**: Processar um arquivo válido com sobreposições resolvíveis, abrir a
cópia gerada e comparar layout, conteúdo e conexões com a entrada.

**Acceptance Scenarios**:

1. **Given** um arquivo válido com sobreposições elimináveis, **When** o usuário informa
   seu caminho e executa a ferramenta, **Then** recebe uma cópia .twee sem esses conflitos,
   o caminho da cópia e uma indicação de sucesso completo.
2. **Given** uma execução que gera uma cópia, **When** original e cópia são comparados,
   **Then** o original permanece idêntico byte a byte, e a cópia preserva todos os nós,
   seus conteúdos, identificadores, atributos não visuais e conexões, incluindo direção
   e multiplicidade quando presentes.
3. **Given** um grafo sem sobreposições, inclusive sem arestas ou com nós isolados,
   **When** o arquivo é processado, **Then** uma cópia válida é gerada sem introduzir
   conflitos, e o resultado informa que não havia sobreposições a resolver.
4. **Given** um caminho com espaços ou caracteres acentuados, ou um nome de saída já
   ocupado, **When** uma entrada válida é processada, **Then** o caminho é aceito e a nova
   cópia recebe um caminho distinto, sem sobrescrever nenhum arquivo existente.
5. **Given** um grafo com nós sobrepostos, inclusive nós isolados, **When** é processado
   sem atingir limitações, **Then** a cópia elimina as sobreposições entre nós sem
   aumentar os conflitos entre arestas e preserva conteúdo e conexões.
6. **Given** uma aresta que atravessa um nó diferente de seus extremos, **When** o grafo
   é processado sem atingir limitações, **Then** a cópia elimina essa travessia sem
   aumentar conflitos entre arestas ou sobreposições entre nós, preservando as conexões.

---

### User Story 2 - Compreender uma melhoria parcial ou um limite (Priority: P2)

Como usuário, quero saber quando ainda restam conflitos e por que a ferramenta não os
resolveu completamente, para decidir se preciso ajustar o grafo depois.

**Why this priority**: Evita que uma cópia parcialmente melhorada seja confundida com
uma resolução completa.

**Independent Test**: Processar um grafo que conserva conflitos após a tentativa e conferir
se a cópia válida e a mensagem distinguem redução parcial de ausência de melhoria.

**Acceptance Scenarios**:

1. **Given** um grafo em que somente parte dos conflitos é eliminada, **When** o
   processamento termina, **Then** o usuário recebe a cópia, seu caminho e o estado
   com limitações, com quantidades de conflitos antes e depois e a razão da limitação.
2. **Given** um grafo em que nenhuma melhoria foi obtida dentro dos limites de processamento,
   **When** o processamento termina e ainda é possível salvar uma cópia íntegra,
   **Then** o usuário recebe uma cópia sem aumento de conflitos, o caminho e uma mensagem
   explícita de ausência de melhoria, com limitações, sem alegação de sucesso completo.
3. **Given** um limite de processamento atingido, **When** não existe resultado cuja
   integridade possa ser garantida, **Then** a execução informa falha e a causa,
   preservando o original e sem anunciar uma saída válida.
4. **Given** um grafo sem conflitos entre arestas mas com sobreposições entre nós que
   não foram eliminadas, **When** o processamento termina com uma cópia válida,
   **Then** o resultado informa limitações, as contagens de sobreposições entre nós
   antes e depois e a causa conhecida, sem alegar sucesso completo.
5. **Given** uma cópia íntegra em que ainda há arestas atravessando nós alheios à conexão,
   **When** o processamento termina, **Then** o resultado informa limitações, a contagem
   dessas travessias antes e depois e a causa conhecida, mesmo se as outras contagens forem zero.

---

### User Story 3 - Reconhecer e corrigir uma falha (Priority: P2)

Como usuário, quero receber uma explicação clara quando não for possível ler, processar
ou salvar o arquivo, para corrigir a causa e tentar novamente.

**Why this priority**: Torna a ferramenta utilizável também em condições de erro.

**Independent Test**: Executar separadamente com caminho inexistente, arquivo inválido,
entrada não suportada e destino sem permissão, verificando mensagem e preservação.

**Acceptance Scenarios**:

1. **Given** caminho ausente, inexistente, de diretório ou sem permissão de leitura,
   **When** a execução é solicitada, **Then** informa falha e identifica o problema de entrada.
2. **Given** arquivo corrompido, conteúdo incompatível com o formato suportado ou conexões
   com referências inválidas, **When** é processado, **Then** informa falha com a causa,
   sem descartar dados silenciosamente ou alterar a entrada.
3. **Given** impossibilidade de salvar a cópia, inclusive por falta de espaço ou permissão,
   **When** a gravação falha, **Then** informa falha de escrita, preserva o original
   e não apresenta um arquivo parcial como resultado válido.
4. **Given** mais de um arquivo solicitado na mesma execução, **When** o usuário tenta
   iniciar o processamento, **Then** a ferramenta rejeita a solicitação e explica
   que esta versão aceita exatamente um arquivo por execução.

### Edge Cases

- Grafos com ciclos, autoarestas, arestas paralelas ou sentidos opostos: preservar cada
  relação; se a representação impedir a melhoria, aplicar o estado com limitações.
- Arestas que se encontram apenas no nó compartilhado: não contar esse encontro como conflito.
- Nós sobrepostos, mesmo sem arestas: tentar separá-los; se restarem sobreposições,
  informar limitações. Encostar apenas nas bordas não conta como sobreposição de nós.
- Arestas atravessando nós: não contar o contato com os próprios extremos da conexão;
  contar a entrada no interior de qualquer outro nó, inclusive um nó isolado.
  Contato apenas com a borda de um nó alheio não conta como travessia.
- Grafo vazio ou sem arestas: produzir cópia válida se permitido pelo formato suportado;
  caso a estrutura seja inválida nesse formato, informar falha de entrada.
- Metadados ou extensões desconhecidos: preservar sem perda; se isso não for possível,
  falhar claramente em vez de gerar uma cópia que os omita.
- Dados de layout ausentes ou inconsistentes: informar falha se não for possível
  interpretar a representação gráfica com segurança.
- Interrupção ou esgotamento de recursos: preservar o original e não anunciar uma cópia
  incompleta como válida; limites atingidos devem ser explicados quando houver retorno.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A ferramenta DEVE aceitar o caminho de exatamente um arquivo .twee existente
  por execução, informado em um comando no terminal, incluindo caminhos com espaços
  e caracteres acentuados; ausência ou
  múltiplas entradas DEVEM produzir falha explicativa (US1.4, US3.1, US3.4).
- **FR-002**: A ferramenta DEVE validar acesso, estrutura, representação gráfica e referências
  das conexões antes de disponibilizar um resultado; arquivos inválidos ou variantes não
  suportadas DEVEM ser recusados com causa clara (US3.1–2 e Edge Cases).
- **FR-003**: A ferramenta DEVE tentar reduzir conflitos visuais entre arestas por alterações
  de layout, usando a mesma definição de conflito antes e depois (US1.1, US2.1–2).
- **FR-004**: Somente dados de apresentação gráfica PODEM mudar. Nós, conteúdos, identificadores,
  atributos não visuais, metadados e conexões DEVEM ser preservados semanticamente,
  incluindo direção, autoarestas e multiplicidade quando presentes (US1.2 e Edge Cases).
- **FR-005**: O arquivo original DEVE permanecer idêntico byte a byte em qualquer resultado,
  inclusive falha ou interrupção (US1.2, US2.3, US3 e Edge Cases).
- **FR-006**: Cada execução concluída com saída válida DEVE gerar uma nova cópia .twee,
  reabrível no mesmo contexto de uso da entrada, sem sobrescrever arquivos existentes.
  Por padrão, a cópia DEVE ficar na pasta da entrada com nome distinto e disponível
  (US1.1, US1.3–4, US2.1–2).
- **FR-007**: Uma cópia disponibilizada NÃO DEVE conter mais conflitos entre arestas do que
  a entrada. Se não houver melhoria, DEVE preservar uma disposição sem agravamento
  e comunicar essa ausência de melhoria (US1.3, US2.2).
- **FR-008**: Cada conclusão DEVE exibir mensagens no terminal e informar exatamente um estado:
  sucesso completo quando não restam conflitos entre arestas, sobreposições entre nós
  nem travessias de nós alheios por arestas; com limitações quando há cópia válida
  com qualquer desses problemas remanescentes;
  falha quando não há cópia válida. Havendo saída válida, DEVE informar seu caminho
  absoluto e as quantidades antes e depois, separadas para pares de arestas em conflito
  e pares de nós sobrepostos, além dos pares aresta–nó com travessia indevida.
  Limitações e falhas DEVEM
  explicar a causa conhecida, sem afirmar impossibilidade matemática não demonstrada
  (US1, US2 e US3).
- **FR-009**: Falhas de leitura, processamento, integridade ou escrita NÃO DEVEM ser
  apresentadas como sucesso ou deixar uma saída parcial anunciada como válida
  (US2.3, US3.1–3 e Edge Cases).
- **FR-010**: A versão inicial DEVE se limitar ao processamento de um arquivo por execução;
  processamento em lote e edição manual interativa do grafo ficam fora do escopo (US3.4).
- **FR-011**: A ferramenta DEVE tentar eliminar sobreposições entre nós existentes e NÃO
  DEVE aumentar sua contagem na cópia disponibilizada. Esse objetivo DEVE ser atendido
  juntamente com a não regressão dos conflitos entre arestas prevista em FR-007;
  limitações DEVEM ser comunicadas conforme FR-008 (US1.5, US2.4 e Edge Cases).
- **FR-012**: A ferramenta DEVE tentar eliminar travessias de nós alheios por arestas
  existentes e NÃO DEVE aumentar sua contagem na cópia disponibilizada. As três contagens
  DEVEM respeitar simultaneamente a não regressão, sem compensar o aumento de uma
  pela redução de outra. Travessias remanescentes DEVEM ser comunicadas como limitações
  conforme FR-008 (US1.6, US2.5 e Edge Cases).

### Key Entities *(include if feature involves data)*

- **Arquivo de entrada**: Documento .twee existente, identificado por caminho, contendo
  dados do grafo e sua representação gráfica; permanece inalterado.
- **Grafo**: Conjunto de nós e conexões, com conteúdo, identificadores e metadados preservados.
- **Nó**: Elemento com identidade, conteúdo e atributos; sua posição visual pode mudar.
- **Aresta**: Relação entre nós, com direção e multiplicidade quando presentes; sua
  apresentação visual pode mudar sem alterar a conexão representada.
- **Conflito visual entre arestas**: Par de arestas distintas cujos traçados se cruzam
  ou compartilham um trecho fora do encontro normal em um nó comum. Cada par conflitante
  conta uma vez, mesmo com múltiplas interseções. Proximidade sem interseção e sobreposição
  de rótulos ou de nós não fazem parte dessa contagem.
- **Cópia de saída**: Novo arquivo .twee íntegro, com os mesmos dados semânticos e layout
  sem aumento de nenhuma das três contagens: conflitos entre arestas, sobreposições de nós
  e travessias de nós alheios por arestas.
- **Sobreposição entre nós**: Par de nós distintos cujas áreas visuais compartilham uma
  região de área positiva. Cada par conta uma vez; contato apenas nas bordas não conta.
- **Travessia de nó alheio por aresta**: Par formado por uma aresta e um nó que não é
  nenhum de seus extremos, em que o traçado da aresta entra no interior da área visual
  do nó. Cada par conta uma vez, mesmo com múltiplas entradas; contato apenas na borda
  não conta. Essa contagem é separada dos conflitos entre arestas e entre nós.
- **Resultado da execução**: Estado, caminho de saída quando válido, contagens inicial
  e final e explicação de limitações ou falhas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos cenários de aceitação, o arquivo original permanece idêntico
  byte a byte, inclusive nos cenários de falha.
- **SC-002**: Em 100% das cópias válidas de aceitação, todos os nós, conteúdos, identificadores,
  atributos não visuais e conexões são preservados; todas as cópias podem ser reabertas
  no mesmo contexto de uso da entrada.
- **SC-003**: Em cada exemplo de referência com sobreposição resolvível selecionado para
  aceitação, o resultado tem zero pares de arestas em conflito. O conjunto de referência
  DEVE incluir ao menos um cruzamento e um trecho coincidente entre arestas distintas,
  cada qual com uma disposição sem conflitos conhecida.
- **SC-004**: Em 100% dos casos de aceitação com saída válida, a contagem final de conflitos
  entre arestas, a de sobreposições entre nós e a de travessias de nós alheios não superam
  suas respectivas contagens iniciais; melhoria parcial exige redução de pelo menos um
  par em uma das contagens, sem aumento das demais. Contagens inicialmente iguais a zero
  permanecem com zero.
- **SC-005**: Em 100% dos cenários de conclusão, o usuário recebe o estado correto e,
  quando há cópia válida, seu caminho absoluto utilizável; nenhuma falha informa uma
  cópia incompleta como válida, e todo resultado com limitações explica a restrição.
- **SC-006**: Em 100% dos casos de aceitação com colisão de nome de saída ou múltiplas
  entradas, nenhum arquivo existente é sobrescrito e nenhuma execução processa mais
  de um arquivo.
- **SC-007**: Em cada exemplo de referência com nós sobrepostos e separação conhecida,
  a cópia apresenta zero pares de nós sobrepostos sem aumentar os conflitos entre
  arestas. O conjunto DEVE incluir nós conectados e nós isolados. Em 100% dos resultados
  de sucesso completo, as três contagens finais são zero.
- **SC-008**: Em cada exemplo de referência com travessia de nó alheio e disposição
  conhecida sem essa travessia, a cópia apresenta zero pares aresta–nó com travessia,
  sem aumentar as outras duas contagens. O conjunto DEVE incluir travessia de nó conectado,
  travessia de nó isolado e contato apenas na borda para verificar a exclusão deste último.

## Assumptions

- Os arquivos .twee são provenientes do aplicativo Twine, cuja versão o usuário não
  conhece. A extensão, isoladamente, não define o formato interno.
- O planejamento deve identificar a versão de origem e a variante de .twee a partir
  de um arquivo de exemplo, documentar a compatibilidade, obter exemplos válidos e
  confirmar como seu layout é exibido. Esses exemplos são uma
  dependência para demonstrar preservação e melhoria; variantes incompatíveis serão
  recusadas de forma explícita na primeira versão.
- O usuário permite reorganizar posições e demais dados de apresentação que o formato
  suportar. Não há exigência de manter posições originais; conteúdo e conexões são invariantes.
- Conforme confirmado pelo usuário, conflitos entre arestas incluem cruzamentos e trechos
  coincidentes; eliminar sobreposições entre nós e travessias de nós alheios por arestas
  também integra o escopo inicial.
  Eliminar sobreposições de rótulos ou garantir um layout ótimo fica fora do escopo.
- Não se presume que todo grafo admita eliminação completa dos conflitos. Uma cópia
  íntegra sem melhoria é um resultado com limitações, nunca sucesso completo.
- A pasta da entrada é o destino padrão e precisa permitir escrita. Seleção avançada de
  destino, interface gráfica, interface pelo navegador, visualização interativa e lote
  ficam fora do escopo inicial. A interface de uso será pelo terminal.
- Os limites operacionais e a seleção dos exemplos de referência serão documentados no
  planejamento. Não há nesta solicitação meta de tempo ou tamanho máximo de grafo.
- O planejamento deve observar a constituição 1.0.1: avaliar soluções existentes antes
  de criar algoritmos próprios e verificar licenças. A seleção da licença do projeto
  foi resolvida por escolha explícita Apache-2.0, com texto em LICENSE e aviso em NOTICE.
