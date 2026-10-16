# Validação local — 2026-10-16

## Correção de compatibilidade do importador

Reproduzidas seis falhas antes da correção; acrescentados nove testes de regressão.
Suporte a links rotulados (->, <-, |), setters preservados sem execução e ausência de
StoryTitle/StoryData. Metadados visuais ausentes recebem os defaults e a grade do
importador Twine 2.12.1, sem modificar o snapshot original. Testes cobrem BOM, CRLF,
Unicode, campos desconhecidos, grade em nova linha, estilos, preservação e destinos
inexistentes identificados nominalmente. Suíte atual: 78 testes aprovados.

A amostra atual de Downloads foi copiada para `.tmp/compatibility` para validação.
SHA-256: `30ba53788388fd98037f29c50f823d6e51ae2ad581ff18b1fe98fdc09f80f06f`.
São 31 passagens e 65 links rotulados, sem metadados visuais. Os dois erros relatados
foram superados; a validação detectou 11 links para nove passagens inexistentes:
ArquivoSecreto, AtirarDuplicata, DesligarTerminal, DestruirIdentificacao,
DestruirTerminal, Fuga, MatarCriatura, PactoAceito e SargentoSegredo.
Nenhuma saída foi publicada para essa entrada incompleta; nenhuma passagem ou conexão
foi inventada/removida. O original em Downloads e a cópia de entrada foram preservados.
A reimportação manual anterior de seis fixtures não valida automaticamente estas novas
variantes; a cobertura desta correção é automatizada.

## Encerramento T041–T045

O usuário selecionou B: Apache-2.0. LICENSE contém o texto oficial integral, incluindo
as nove seções e o apêndice; termos comparados com segunda cópia canônica local. NOTICE
incluído e metadados atualizados. Constituição 1.0.1 resolve a pendência sem mudar os
seis princípios. Os registros de licença pendente abaixo são históricos e superados.

T042: inventário final em `docs/third-party.md`; nenhum import de terceiro em `src/`
pela inspeção AST e `project.dependencies=[]`. Python 3.14.6 e Graphviz 16.1.0 externos;
Node v24.18.0 e ELK.js 0.12.0 somente experimentais. Manifesto de 97 arquivos nativos
da instalação Graphviz, com hashes e metadados, sem incorporar binários. Apache-2.0
não é aplicada a dependências externas. Instalação editável/pytest não exercitados.

T043/T044: README, CONTRIBUTING e quickstart consolidados para o fluxo por checkout.
Executados no Windows: `python --version`, `dot -V`, `python run.py --version`,
preparação do exemplo e `python run.py .tmp/quickstart/exemplo.twee`. Resultado: código 0,
nova cópia com 1/0/0 -> 0/0/0, entrada idêntica ao fixture. Suíte global Python 3.14.6:
**69 testes aprovados em 2,668 s**. `compileall` passou. Instalação editável é alternativa
opcional separada, explicitamente não validada; ela não é necessária para o fluxo entregue.
Nenhuma versão/plataforma adicional ou empacotamento de motores é anunciado como validado.

T045: revisão cruzada dos artefatos e rastreabilidade abaixo. Os seis princípios foram
reavaliados no plano final; nenhuma exceção adotada. Amostras privadas e arquivos originais
preservados. Checklist apenas lido, sem mudar seus marcadores. Sem hooks de extensão
registrados. Nenhum envio externo, publicação ou commit foi realizado.

### Rastreabilidade funcional

| Requisito | Evidência principal |
|---|---|
| FR-001 | `test_cli_success.py` (Unicode/espaços), `test_cli_failures.py` (argumentos) |
| FR-002 | `test_cli_failures.py` (formato, estrutura, referências, limites) |
| FR-003 | `test_geometry.py`, `test_reference_layouts.py`, confirmação de reabertura |
| FR-004 | `test_roundtrip.py` (bytes, tags, scripts/estilos, metadados, multiplicidade) |
| FR-005 | `test_reference_layouts.py`, `test_file_failures.py`, comparação de bytes |
| FR-006 | `test_files.py`, colisão no commit e seis reaberturas confirmadas |
| FR-007 | `test_selection.py`, `test_limited_results.py`, corpus sem regressão |
| FR-008 | três contratos CLI e classificação em `test_limited_results.py` |
| FR-009 | falhas de arquivo/processo e CLI sem anúncio de saída parcial |
| FR-010 | zero/múltiplos caminhos recusados em `test_cli_failures.py` |
| FR-011 | fixtures de nós conectados/isolados e teste de conflitos só entre nós |
| FR-012 | fixtures de travessias conectadas/isoladas e tangência excluída |

### Critérios de aceitação

| Critério | Resultado no conjunto de aceitação |
|---|---|
| SC-001 | Todas as execuções verificadas preservaram os bytes da entrada, inclusive falhas |
| SC-002 | Saídas verificadas por releitura/bytes/identidades/relações; seis reaberturas confirmadas |
| SC-003 | Referências crossing/coincident resolvidas em 0 pares de arestas; layout limpo conhecido incluído |
| SC-004 | Nenhuma métrica aumentou nas saídas; regressão rejeitada e melhoria parcial verificada |
| SC-005 | Estados 0/2/1/130, caminho absoluto somente em resultado válido e causas conhecidas |
| SC-006 | Colisões normais e no commit preservadas; múltiplas entradas recusadas |
| SC-007 | Nós conectados/isolados separados; sucesso completo com três zeros |
| SC-008 | Travessias conectadas/isoladas eliminadas; contato apenas na borda excluído |

As conclusões se limitam ao perfil e ao corpus descritos. Não afirmam solução universal,
ótimo global, suporte a navegação dinâmica ou capacidade medida no limite máximo de entrada.
I/O é cooperativo em relação ao prazo, conforme os contratos. O projeto permanece na
versão 0.1.0.dev0; o fluxo por código-fonte está completo e verificável.

## Histórico de execução

## Estado final das três histórias

T001–T040 concluídas, 40/45 tarefas. Suíte mais recente:
`python -m unittest discover -s tests`, **69 testes aprovados** em 3,056 s nesta execução.
Ambiente Windows / Python 3.14.6 / Graphviz 16.1.0, renderer de referência Twine 2.12.1.
O usuário confirmou A: os seis exemplos de referência reabriram corretamente e sem
os conflitos indicados. Essa é confirmação manual reportada, não automação visual.

US2 (T028–T033): testes de classificação, CLI com código 2 e três métricas, melhoria parcial,
empate, rejeição de regressão, timeout e prazo global com/sem baseline. Conflitos apenas
entre nós ou aresta–nó impedem sucesso completo. Falhas iniciais de comportamento/mensagem
foram observadas antes de implementar a classificação e os retornos de prazo.

US3 (T034–T040): ausência/múltiplos caminhos, diretório, extensão incompatível, UTF-8/JSON
inválidos, referências ausentes, duplicatas, layout ausente, coordenadas não finitas e
cabeçalho excessivo. Escrita testada com permissão negada, falta de espaço, short write,
falha de publicação, colisão no commit e interrupção; nenhum arquivo preexistente foi
sobrescrito e nenhum parcial foi anunciado como válido. Cancelamento retorna 130.
Processo testado com erro de saída, limite combinado de bytes, timeout, JSON e IDs
inválidos, coordenadas inválidas e interrupção com recolhimento do filho sem shell.

Defeitos encontrados e corrigidos: NaN/Infinity aceitos por json.loads em campos opacos
(Twine usa JSON estrito); descritor vazando na falha de os.fdopen; exceção inesperada
escapando da CLI. Testes foram observados falhando antes das correções. O teste de prazo
global foi tornado determinístico com relógio controlado após variação de agendamento.
Roundtrip adicional cobre passagens script/stylesheet, nomes Unicode e chave `position`
aninhada que não pode ser alterada. Os 69 testes incluem os experimentais anteriores.

T041–T045 continuam pendentes: seleção explícita de licença e acabamento/inventário final.
Instalação editável/pytest não verificados neste ambiente sem acesso ao índice; o fluxo
documentado pelo checkout (`python run.py`) e a suíte unittest funcionam sem essas dependências.
Os registros abaixo conservam a evolução anterior da validação, substituída por este estado.

## Histórico da etapa US1

Atualização: o usuário respondeu A, confirmando que os seis arquivos do ZIP abriram
corretamente no Twine web e sem os conflitos indicados. T027 concluída por confirmação
manual reportada, sem alegar automação visual. US2/US3 liberadas para implementação.
Essa resposta não seleciona a licença; T041 continua pendente.

Estado: T001–T026 implementadas/verificadas, T027 aguarda reabertura manual no Twine web.
US2, US3 e acabamento ainda não concluídos. Licença autoral aguardando escolha explícita.
Nenhuma distribuição pública realizada. Checklist de requisitos apenas lido: 16/16.

Ambiente: Windows, Python 3.14.6, Graphviz 16.1.0, fonte geométrica Twine 2.12.1.
ELK.js 0.12.0 apenas na comparação. Instalação editável/pytest não validada por restrição
de rede; testes usam unittest da biblioteca padrão. Uso local: `python run.py CAMINHO`.

## Evidência de execução

Suíte `python -m unittest discover -s tests -v`: 39 testes, todos aprovados na revisão
final. Testes de US1 foram escritos contra stubs e falharam por `NotImplementedError`
antes da implementação. Conversão de BOM foi corrigida após uma falha de roundtrip.
Novos invariantes de documento foram observados falhando antes da correção.
Testes incluem identidade e referências, intervalos de patch, geometria, bytes preservados,
BOM/CRLF, metadados aninhados, links repetidos, publicação com colisão e Graphviz real.

Corpus de 13 casos sintéticos autorizado em `tests/fixtures/cases.json`, com hashes,
contagens esperadas e disposições sem conflitos conhecidas independentes do motor.
Em todas as execuções do corpus, original intacto e nenhuma métrica aumentou na cópia;
os seis casos de referência terminaram em 0/0/0:

| Caso | Antes (arestas/nós/travessias) | Depois |
|---|---|---|
| crossing | 1/0/0 | 0/0/0 |
| coincident | 1/2/0 | 0/0/0 |
| isolated_overlap | 0/1/0 | 0/0/0 |
| connected_overlap | 1/1/1 | 0/0/0 |
| through_isolated | 0/0/1 | 0/0/0 |
| through_connected | 0/0/1 | 0/0/0 |

Contagens de arcos derivadas do perfil da fonte oficial; reabertura ainda pendente.
SC-001/002/004/006 cobertos parcialmente pelos cenários US1; SC-003/007/008 demonstrados
numericamente nos exemplos, aguardando confirmação visual. SC-005 ainda requer testes
de limitações/falhas de US2/US3. Não declarar os critérios globais concluídos.

Foi criado `.tmp/acceptance/review-layouts.zip`, com as seis cópias, e solicitado ao usuário
importar e conferir no Twine web: nós e links preservados, sem os três tipos de conflito.
Resultados locais em `.tmp/acceptance/results.json`, amostras sintéticas sem narrativa privada.

## Amostra privada e limites

A cópia anterior autorizada `.tmp/format-validation/position-check.twee` tem baseline
1/0/2. Graphviz propôs 4/0/3; a aplicação rejeitou e gerou
`position-check.layout.twee` com 1/0/2, estado limitações e causa de regressão explícita.
Nenhuma narrativa privada entrou nos fixtures. Downloads agora contém outro documento,
31 passagens sem metadados visuais; CLI recusou com erro de formato e nenhuma saída.

O ZIP do editor foi apenas lido; hashes e origem no contrato de perfil.
Nenhum código de Twine ou binário Graphviz/ELK é incorporado ao pacote.

Pendências: reabertura T027, testes e integração US2/US3, refinamento de falhas de processo
e de publicação, licença T041, inventário transitivo e documentação final, instalação
editável/versões adicionais não exercitadas. T044/T045 continuam abertas.
