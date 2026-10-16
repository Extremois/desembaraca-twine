# Pesquisa técnica: layout e roteamento para arquivos do Twine

Data: 2026-10-16. Referência de requisitos: [spec.md](spec.md).
Estado atual: amostra caracterizada e reaberta pelo usuário; fonte Twine 2.12.1 inspecionada
localmente e comparação com arcos refeita. Graphviz 16.1.0 escolhido, com seleção e fallback
obrigatórios. Resultados em `curved-tb-results.json` e `curved-lr-results.json`;
desenho final em `plan.md` e contratos. As seções abaixo preservam o histórico da pesquisa;
os bloqueios iniciais de amostra e fonte foram resolvidos. T027 ainda aguarda reabertura
das saídas de referência na época desse registro. Atualização final: as seis reaberturas
foram confirmadas pelo usuário, Apache-2.0 foi selecionada explicitamente, a constituição
passou a 1.0.1 e a suíte final de 69 testes passou. O plano final e `validation.md`
substituem os estados pendentes do histórico abaixo.

## Decisão e alcance

**Decisão:** recomendar Graphviz `dot` executado como processo externo para gerar posições
candidatas. A adoção para produção depende da identificação de um arquivo real e da
aprovação dos testes de preservação e geometria do editor. Não implementar um algoritmo
de layout próprio nem copiar código do Graphviz nesta versão.

**Justificativa:** o problema envolve um grafo dirigido, com ciclos e caixas de tamanho
conhecido. `dot` organiza hierarquias e tenta reduzir cruzamentos e comprimento de arestas.
Isso oferece um ponto de partida existente, mas não garante eliminação de conflitos.
Fonte: [Graphviz dot](https://graphviz.org/docs/layouts/dot/).

**Alternativas consideradas:** ELK.js é a alternativa principal, sobretudo quando houver
suporte real a portas e pontos de dobra. NetworkX não oferece, sozinho, a combinação
de posicionamento de caixas e roteamento requerida. Algoritmo próprio adicionaria custo
de manutenção sem evidência de necessidade. Nenhum motor deve escrever o documento final.

## 1. Formato e representação do Twine

**Decisão:** manter um bloqueio explícito de formato. Não inventar um esquema JSON ou XML
para `.twine`, não tratar a extensão como prova de estrutura e não substituí-la
silenciosamente por `.html` ou `.twee` no escopo aprovado.

**Justificativa:** a especificação oficial de saída HTML do Twine 2 define `tw-storydata`,
passagens `tw-passagedata`, conteúdo e metadados. Para geometria das passagens, define
`position` como canto superior esquerdo e `size` como dimensões. Não define pontos de
controle de arestas. O modelo atual de passagens no código do editor também contém
posição e dimensões, sem uma entidade persistente de rota de aresta. Essa evidência
é sobre Twine 2; não identifica o arquivo do usuário nem prova como uma versão desconhecida
o interpreta. Fontes: [formato HTML oficial](https://github.com/iftechfoundation/twine-specs/blob/master/twine-2-htmloutput-spec.md),
[modelo do editor](https://raw.githubusercontent.com/klembot/twinejs/develop/src/store/stories/stories.types.ts).

**Alternativas consideradas:** assumir Twine 2 HTML renomeado; assumir formato de projeto
legado; converter automaticamente para outro formato. Todas rejeitadas sem amostra.

### Gate FMT-01 — fechado para o perfil observado

O usuário forneceu `C:/Users/franc/Downloads/o roubo do quadro.twee`, que foi inspecionado
sem copiar a narrativa para o repositório. A amostra contém fonte Twee e dados de layout;
ver [format-validation.md](format-validation.md). A versão do editor permanece desconhecida
e o usuário confirmou entrada/saída `.twee`. A regravação com preservação dos demais bytes
foi verificada em cópia local, conforme o relatório, e o usuário confirmou a reabertura.
O gate está fechado para esse perfil, sem inferir suporte a outros casos. Seus critérios são:

1. Inspecionar estrutura, codificação, versão quando identificável e número de histórias.
2. Identificar os campos que representam posições, dimensões, conteúdo, IDs e metadados.
3. Demonstrar leitura e regravação sem mudanças semânticas; enumerar os únicos campos
   visuais que poderão mudar. Preservar campos desconhecidos ou recusar a entrada.
4. Reabrir uma cópia no aplicativo de origem e confirmar a correspondência entre posição
   persistida e exibida, incluindo geometria das ligações, laços e sentidos opostos.
5. Registrar versão ou perfil de compatibilidade, exemplos licenciados para testes e
   método de validação. Se o formato real contrariar o escopo, retornar à clarificação.

Uma amostra sintética serve ao teste de um adaptador já identificado; não comprova
compatibilidade com o arquivo real desconhecido.

## 2. Roteamento: o resultado deve existir no editor

**Decisão:** avaliar posições candidatas usando os traçados que o editor de destino
efetivamente desenha. Enquanto o gate de formato estiver aberto, não presumir que sejam
segmentos retos nem que sejam splines. Persistir rotas somente se o formato e o editor
as suportarem comprovadamente.

**Justificativa:** Graphviz oferece splines e linhas ortogonais. `splines=ortho` tem
limitações documentadas para portas e rótulos de arestas. Rotas produzidas pelo motor
não se tornam automaticamente rotas do Twine. A conclusão de que posições devem ser
a integração inicial é uma inferência da ausência de campos de rota no formato HTML
documentado, a confirmar na amostra. Fonte: [Graphviz splines](https://graphviz.org/docs/attrs/splines/).

**Alternativas consideradas:** inserir nós artificiais nas conexões para simular dobras;
exportar SVG como substituto do `.twine`; alterar o texto das passagens. Rejeitadas:
mudariam as relações ou deixariam de entregar o arquivo solicitado.

Três métricas independentes devem ser medidas antes e depois: pares de arestas em
conflito, pares de nós sobrepostos e pares aresta–nó com travessia indevida. Só aceitar
um candidato quando nenhuma contagem aumentar. Se nenhum melhorar, reutilizar o layout
original em uma nova cópia íntegra e comunicar limitações quando houver conflitos.
Um layout visualmente bom no Graphviz não basta para satisfazer FR-007, FR-011 e FR-012.

## 3. Comparação de motores

| Solução | Adequação | Custo e limitações | Decisão |
|---|---|---|---|
| Graphviz `dot` | Grafo dirigido; hierarquias; dimensões explícitas | Executável nativo; heurística; rotas podem não persistir no Twine | Primeiro candidato condicionado ao gate |
| Graphviz `neato` | Organização por forças/stress para estruturas gerais | Precisa tratar colisões; não elimina conflitos por garantia | Candidato secundário se corpus justificar |
| Graphviz `sfdp` | Layout multinível para grafos maiores | Escala não resolve compatibilidade nem preservação | Fora da integração inicial |
| ELK.js Layered | Nós com dimensões, portas, laços, multiarestas e roteamento | Runtime JS para integração com CLI Python; pontos de dobra podem se perder no Twine | Alternativa de comparação empírica |
| NetworkX `spring_layout` | Análise de grafos e geração de coordenadas | Não é roteador de arestas; dimensões das caixas exigem tratamento adicional | Não escolher como motor principal |
| Layout e roteador próprios | Controle específico do objetivo | Maior implementação, verificação e manutenção | Rejeitados antes de evidência de inadequação dos existentes |

Fontes primárias por alternativa: [neato](https://graphviz.org/docs/layouts/neato/),
[sfdp](https://graphviz.org/docs/layouts/sfdp/),
[ELK Layered](https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html),
[ELK.js](https://github.com/kieler/elkjs),
[NetworkX spring_layout](https://networkx.org/documentation/stable/reference/generated/networkx.drawing.layout.spring_layout.html).

ELK tem vantagem em diagramas com portas e rotas explícitas. Essa vantagem não demonstra
benefício para um consumidor que só restaura posições. Não adicionar dois motores ao
produto inicial: comparar em corpus e incorporar somente o vencedor necessário.

## 4. Integração Graphviz proposta

**Decisão:** CLI Python 3.12 ou posterior com `subprocess`, chamando uma instalação
externa de Graphviz; sem PyGraphviz, NetworkX ou wrapper Python em tempo de execução.
Escolha de linguagem proposta pelo planejamento, sem stack preexistente no projeto.

**Justificativa:** separar o motor do modelo evita compilação de bindings e permite
substituí-lo. Enviar somente IDs sintéticos, dimensões e incidência das arestas em DOT;
manter nomes, texto, scripts e metadados no documento original. Para nós, usar caixas
de dimensão fixa e label vazio. Não usar `strict digraph` nem concentração de arestas:
a multiplicidade semântica permanece no modelo independentemente da projeção visual.
Fonte de dimensões: [fixedsize](https://graphviz.org/docs/attrs/fixedsize/).

Preferir `-Tjson0`: geometria estruturada de layout, sem operações de desenho xdot.
Não confundir com `dot_json`, que não calcula layout. IDs de nós e arestas devem ser
mapeados de volta sem depender da ordem de saída. Fonte: [saída JSON](https://graphviz.org/docs/outputs/json/).

Converter explicitamente o centro do nó retornado em `pos` para o canto do editor,
invertendo Y e convertendo unidades conforme o perfil comprovado. Posições de saída
Graphviz usam pontos; dimensões de nó usam polegadas. Não assumir que um pixel equivale
a um ponto. Validar após arredondamento e nova leitura do documento, não apenas no
layout em memória. Fontes: [pos](https://graphviz.org/docs/attrs/pos/),
[dimensões de nós](https://graphviz.org/docs/nodes/).

Não passar texto de usuário ao shell. Limitar tempo, bytes de saída e valores geométricos;
tratar processo ausente, timeout, código de erro, JSON inválido e coordenadas não finitas.
Não executar JavaScript/macros da história para descobrir conexões.

O parser de links do editor deriva destinos do texto e remove destinos repetidos.
Isso não equivale ao grafo de todas as execuções possíveis de uma narrativa com macros.
Preservar o texto integral mantém as ligações semânticas, mas a projeção visual precisa
ser validada contra a versão do editor; não alegar cobertura dinâmica não demonstrada.
Fonte: [parser de links do Twine](https://raw.githubusercontent.com/klembot/twinejs/develop/src/util/parse-links.ts).

## 5. Preservação e publicação da cópia

**Decisão:** o documento original é a fonte de verdade; DOT e JSON são projeções descartáveis.
O adaptador específico deve alterar apenas campos visuais permitidos, conservando todo
o restante. Não reconstruir a história a partir do grafo extraído.

**Justificativa:** conversão genérica pode perder scripts, estilos, tags, IFID, IDs,
conteúdo escapado, extensões ou multiplicidade. Guardar bytes originais e mapa de campos
permite comparar invariantes antes de publicar. O formato real decidirá se são necessários
patches de intervalos ou outra técnica de preservação; não escolher um serializer antes
do gate FMT-01.

**Alternativas consideradas:** serializar tudo por DOT/NetworkX; reformatar HTML inteiro;
converter por Twee. Rejeitadas como padrão por risco de perda ou mudança desnecessária.

A publicação deve usar arquivo novo reservado exclusivamente, sem sobrescrita em colisões.
Revalidar conteúdo e as três métricas sobre a cópia serializada. Não anunciar resultado
válido antes da conclusão; tratar falha de gravação e interrupção. A escolha do mecanismo
de publicação sem sobrescrita depende da plataforma documentada na Fase 1.

## 6. Dependências e ambiente observado

| Item | Necessidade proposta | Situação local observada |
|---|---|---|
| Python | CLI, domínio, orquestração e I/O específico do formato | Python disponível em `C:/Python314/python.exe` |
| Distribuição Graphviz | `dot`, bibliotecas e plugins de layout/saída | `dot` e `neato` não encontrados no PATH |
| pytest | Desenvolvimento: contratos, regressões e integração | Não instalado nem verificado nesta pesquisa |
| Node.js + ELK.js | Somente experimento comparativo, se necessário | Node disponível; ELK.js não instalado nesta pesquisa |
| Arquivo real e editor compatível | Confirmar formato, renderização e reabertura | Ausentes nesta execução |

Instalar Graphviz completo, não apenas copiar `dot.exe`. Antes de fixar a release,
verificar `dot -V`, suporte a `-Tjson0`, componentes de licença e repetibilidade no corpus.
Não foi instalado software nem executado benchmark. Fonte: [distribuições Graphviz](https://graphviz.org/download/).

Antes da primeira execução comparativa, aplicar o orçamento experimental EVAL-01 de
[plan.md](plan.md): entrada de até 10 MiB, até 1.000 nós e 5.000 arestas, um candidato
por motor/caso, 30 segundos por chamada, 120 segundos por caso, 300 segundos por sessão
e 8 MiB de saída combinada por processo, com até 2 segundos adicionais para encerramento.
Esses valores são decisões provisórias de engenharia, não resultados de benchmark.
Os limites finais do produto e as tolerâncias geométricas serão definidos após o corpus
e o perfil de renderização; não declarar capacidade ou SLA com base somente em documentação.

## 7. Licenças e distribuição

**Decisão:** manter Graphviz como dependência instalada separadamente na primeira proposta;
não incorporar seu código nem empacotar binários neste planejamento. A licença do código
autoral continua dependendo da escolha dos mantenedores.

**Justificativa:** a página oficial atual do Graphviz declara EPL-2.0. Conferir o LICENSE
da release fixada, avisos e componentes transitivos. Se houver redistribuição do programa,
atender às condições de avisos e disponibilização do código correspondente. Processo
externo não elimina essas condições. Fonte: [licença Graphviz](https://graphviz.org/license/).

ELK.js declara `EPL-2.0 OR GPL-3.0-or-later` nos metadados consultados. Verificar licença
e dependências da versão escolhida antes de distribuição; não confundir a opção GPL
com obrigação automática de escolher esse ramo. Fonte: [package.json oficial](https://github.com/kieler/elkjs/blob/master/package.json).

NetworkX usa BSD-3-Clause, com preservação dos avisos e condições de redistribuição;
a licença mais permissiva não supre sua ausência de roteamento adequado neste caso.
Fonte: [LICENSE oficial NetworkX](https://raw.githubusercontent.com/networkx/networkx/main/LICENSE.txt).

O repositório do Twine consultado usa GPL-3.0. Consultar os contratos públicos não autoriza
copiar parser ou renderer sem avaliar as condições de licenciamento. Esta proposta prevê
implementação independente do adaptador e avaliador; eventual reutilização de código exige
decisão explícita compatível com a licença autoral escolhida.
Fonte: [LICENSE oficial Twine](https://raw.githubusercontent.com/klembot/twinejs/develop/LICENSE).

As fontes de código foram consultadas nas branches públicas indicadas, em 2026-10-16;
não constituem uma versão de integração fixada. O perfil validado deve registrar o commit
ou a versão do Twine que determina o comportamento esperado.

**Conclusão de compatibilidade:** a separação por processo torna a integração tecnicamente
plausível sem copiar código do motor. A compatibilidade final de distribuição não está
comprovada enquanto faltarem licença do projeto, release fixada e inventário transitivo.
Essa é uma avaliação de engenharia condicionada aos textos das licenças, não uma dispensa
das obrigações. O gate de licença bloqueia distribuição, não esta pesquisa documental.

## 8. Critério de seleção empírica após FMT-01

Comparar original, `dot` e ELK.js sobre os mesmos exemplos, com o mesmo extrator e
avaliador de geometria do Twine, sob EVAL-01 desde a primeira execução. Incluir ciclos,
nós isolados, laços, relações opostas,
cruzamentos, trechos coincidentes, nós sobrepostos, travessias, Unicode e metadados.
Registrar versão de cada ferramenta, opções, tempo, memória observável, três contagens
e validação de preservação. Priorizar preservação e não regressão; depois, número de
casos totalmente resolvidos, redução parcial e custo operacional. Não escolher por SVG.

Graphviz permanece a recomendação documental inicial; promover essa recomendação a
decisão validada somente após resultado reproduzível. Se nenhum motor atender ao corpus
de referência, registrar a evidência e rever a solução antes de criar algoritmo próprio.

## Resultado da Fase 0

Respondidos documentalmente: família de algoritmo, alternativa principal, integração,
unidades, preservação, dependências e condições de licença. Amostra real identificada
como fonte Twee com extensão `.twee`, aprovada pelo usuário para entrada e saída. Um ensaio
local confirmou preservação fora dos valores de posição e o usuário confirmou a reabertura.
**FMT-01 fechado para o perfil observado.** A Fase 0 ainda aguarda a execução comparativa
de T006: Graphviz e ELK.js foram executados sob hipótese geométrica explícita, ainda sem
validação do traçado efetivo do editor, conforme [layout-comparison.md](layout-comparison.md).
Fase 1 e contratos definitivos aguardam a consolidação dessa comparação.

Atualização após resposta B: o usuário informou curvas/dobras no editor. O modelo
experimental de segmentos retos não representa esse traçado e suas métricas não sustentam
a escolha definitiva de motor. Obter versão/fonte do renderer e caracterizar os parâmetros
das curvas antes de substituir o avaliador; não presumir que as splines de Graphviz ou as
rotas do ELK sejam persistidas ou reproduzidas pelo Twine.
