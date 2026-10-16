# Comparação de motores — preparação de T006

Data: 2026-10-16. **Estado final: T006 concluída com a geometria curva do Twine 2.12.1.**
Graphviz escolhido com seleção sem regressão e fallback. Evidência final na seção de
recebimento do ZIP e nos resultados curvos TB/LR. As seis saídas de referência da aplicação
foram posteriormente reabertas e confirmadas pelo usuário. O texto inicial a seguir
conserva a hipótese de segmentos retos rejeitada para o editor alvo.
O usuário confirmou curvas/dobras (B). As métricas abaixo permanecem como registro
experimental dessa hipótese, sem validade para selecionar o motor nem comprovar melhoria
no Twine. A recomendação de Graphviz continua provisória; T006 permanece aberta.

A fórmula das curvas, os pontos de conexão e o comportamento de laços/conexões recíprocas
ainda não foram obtidos. As tentativas de consultar o diretório e o código de conexões
no repositório oficial retornaram falha de acesso/cache; o shell continua sem acesso à rede.
Foi solicitada a versão do editor ou a indicação de uso pelo site/aplicativo para localizar
a implementação correspondente. Não substituir essa evidência por uma curva arbitrária.

O usuário confirmou o site oficial `https://twinery.org/2/` (A). A
[publicação oficial mais recente consultada](https://github.com/klembot/twinejs/releases/tag/2.12.1)
é 2.12.1, commit abreviado `4ebcce6`; isso não prova a versão carregada no navegador do
usuário. A página do site consultada pelo navegador de pesquisa exige JavaScript e não
expõe o traçado das conexões. As tentativas de obter o diretório das conexões e seus
arquivos continuam falhando; nenhum ZIP do Twine foi encontrado em Downloads ou no projeto.

Para permitir a inspeção local, obter o
[código-fonte oficial 2.12.1 em ZIP](https://github.com/klembot/twinejs/archive/refs/tags/2.12.1.zip)
e guardar em Downloads ou `.tmp`. Não é necessário instalar o aplicativo Twine nem incluir
o ZIP no pacote do projeto. A inspeção deve registrar versão, hash e os arquivos que
determinam pontos de conexão, curvas, laços e relações recíprocas; consultar o código não
autoriza copiá-lo sem a avaliação de licenças já prevista. Depois disso, definir o modelo
e testes de geometria e repetir a comparação. A origem web foi resolvida, sem fechar T006.

O comparador agora recusa `--compare` sem escolha explícita de hipótese. O modo hipotético
exige `--geometry straight-hypothesis` e declara `eligible_for_motor_selection: false`.
Dois testes observaram a falta desse bloqueio e, após a correção, a suíte tem 16 testes.

## Ensaio executado

### Atualização após recebimento do ZIP — T006 concluída

Encontrado `C:/Users/franc/Downloads/twinejs-2.12.1.zip` (3.677.180 bytes), SHA-256
`a18a77989e4f23295e50da2311a81c04d0af74adb806183e8a9ae0817cd0e2a6`.
Os parâmetros SVG foram identificados por leitura local, sem executar, extrair ou copiar
o código do editor para produção. O contrato de perfil lista as fontes consultadas.
Conversão matemática segue [notas SVG do W3C](https://www.w3.org/TR/SVG/implnote.html).
O avaliador independente usa arcos analíticos e interseções de elipses, incluindo laços,
recíprocas e contato com borda. Oito testes específicos passaram após falha inicial.

Executadas duas sessões EVAL-01 independentes: TB e LR, cada uma com um candidato por
motor/caso. Corpus curvo ajustado antes da sessão LR: trechos coincidentes com nós
distintos em posições iguais (resolúveis), tangência real de arco à borda. Os nomes dos
casos antigos de segmentos não foram tomados como prova de suas propriedades curvas.
Resultados: [TB](curved-tb-results.json) e [LR](curved-lr-results.json).

Ambos resolveram cruzamento, nós sobrepostos e travessias nos casos de referência;
LR também resolveu o caso de trecho coincidente corrigido. Laços foram avaliados;
recíprocas permanecem coincidentes e são limitação conhecida da representação. A amostra
local tem 1/0/2: Graphviz TB 4/0/3; ELK TB 6/0/6. Ambas as candidatas seriam rejeitadas.
Na sessão LR a amostra fica 3/0/3 e 5/0/6, também regressões. Nenhum resultado é ótimo
universal. Escolhido Graphviz TB pelo custo operacional e ciclo limpo preservado, com
fallback obrigatório. Cópias de revisão não equivalem a saída aprovada.

O desenho foi identificado pela fonte de referência 2.12.1; não foi automatizada a
reabertura final no navegador do usuário. Essa validação permanece em T027/T044.
O restante deste documento conserva o histórico da hipótese anterior, já superada.

Implementados adaptadores experimentais independentes do pacote de produção em
`experiments/layout_engines.py`, corpus em `experiments/comparison_corpus.py` e modelo
em `experiments/straight_geometry.py`. O modelo representa segmentos retos entre os
centros de retângulos, recortados nas bordas. Não modela largura de traço, pontas de
seta, laços nem deslocamentos de conexões recíprocas. Essa geometria ainda NÃO foi
confirmada no editor do usuário e não é evidência de conformidade visual com Twine.

Comando da execução corrigida e com validação de coordenadas:

```powershell
.\.venv\Scripts\python.exe experiments/compare_layouts.py --compare --geometry straight-hypothesis --dot 'C:\Program Files (x86)\Graphviz\bin\dot.exe' --elk-root 'C:\Users\franc\node_modules\elkjs' --sample '.tmp/format-validation/position-check.twee' --report '.tmp/layout-comparison/comparison-v4.json'
```

Use outro nome de relatório em novas execuções: relatórios e cópias de revisão existentes
não são sobrescritos. Foram comparados 11 casos; dois ficaram explicitamente sem comparação.
O comando acima reproduz a hipótese com o bloqueio atualizado. O relatório v3 foi gerado
antes da confirmação B e antes de exigir o argumento de geometria; ele permanece intacto.
Opções foram fixadas antes da primeira execução: `dot` TB, nodesep 0.7, ranksep 1,
splines line; ELK layered DOWN, POLYLINE, espaços 50/72, semente 1. Apenas posições são
avaliadas, descartando as rotas dos motores. ELK usa seu worker simulado no mesmo processo,
sem `workerUrl` nem processos auxiliares. Nenhum código de terceiros foi copiado.

Resultados completos, coordenadas e tempos: [comparison-results.json](comparison-results.json).
Cada tripla abaixo significa **pares de arestas / pares de nós / pares aresta–nó**.

| Caso | Original | Graphviz | ELK.js |
|---|---|---|---|
| Cruzamento | 1/0/0 | 0/0/0 | 0/0/0 |
| Trecho coincidente | 1/0/2 | 0/0/0 | 0/0/0 |
| Limpo | 0/0/0 | 0/0/0 | 0/0/0 |
| Nós isolados sobrepostos | 0/1/0 | 0/0/0 | 0/0/0 |
| Nós conectados sobrepostos | 0/1/0 | 0/0/0 | 0/0/0 |
| Travessia de nó isolado | 0/0/1 | 0/0/0 | 0/0/0 |
| Travessia de nó conectado | 0/0/1 | 0/0/0 | 0/0/0 |
| Contato só na borda | 0/0/0 | 0/0/0 | 0/0/0 |
| Ciclo | 0/0/0 | 0/0/0 | 0/0/1 — regressão |
| Ocorrências repetidas de link | 0/0/0 | 0/0/0 | 0/0/0 |
| Cópia local validada | 3/0/1 | 0/0/4 — regressão | 0/0/4 — regressão |
| Laço / conexão recíproca | Sem comparação | Geometria desconhecida | Geometria desconhecida |

Graphviz levou 0,0632–0,1766 s por caso; ELK.js, 0,5354–0,6138 s nesta execução.
Esses tempos não são SLA nem medição de memória. Todos os casos caberam em EVAL-01.
Na cópia local, ambos preservaram nomes, relações e todos os bytes fora dos valores de
posição. O arquivo usado como baseline permaneceu intacto. As cópias sob `.tmp` são
artefatos de revisão: NÃO são resultados aprovados, pois pioram uma das métricas no modelo.

O caminho original em Downloads passou a conter outro arquivo, sem metadados de layout;
detalhes em [format-validation.md](format-validation.md). Ele foi recusado e permaneceu intacto.

Conclusão provisória: Graphviz resolve mais casos sem regressão neste corpus e tem
menor custo de inicialização. Ambos precisam de seleção com fallback para preservar a
baseline no caso local. Não promover o modelo nem escolher definitivamente o motor
antes de conferir os traçados reais do editor; T006 continua aberta por essa pendência.

## Evidência de disponibilidade

Comando executado na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe experiments/compare_layouts.py --probe --dot 'C:\Program Files (x86)\Graphviz\bin\dot.exe' --elk-root 'C:\Users\franc\node_modules\elkjs'
```

Resultado observado:

| Motor | Estado | Evidência |
|---|---|---|
| Graphviz | Disponível | `C:\Program Files (x86)\Graphviz\bin\dot.exe`; versão 16.1.0 (20260904.0139), saída 0 |
| ELK.js | Disponível | `C:\Users\franc\node_modules\elkjs`; versão 0.12.0, licença declarada `EPL-2.0 OR GPL-3.0-or-later`, saída 0 |

Após o usuário instalar os motores, a nova busca encontrou os caminhos acima. O PATH
persistido da máquina inclui Graphviz, mas o PATH herdado desta sessão ainda não o inclui.
O probe com caminhos explícitos retornou 0 e `dependencies_ready: true`.

O comando retorna 2 quando falta uma dependência e explicita
`layout_comparison_executed: false`. Se ambos os probes tiverem sucesso, retorna 0 e
informa apenas disponibilidade; isso ainda não comprova capacidade de layout ou melhoria.
O modo `--compare` executa a comparação descrita acima; o modo `--probe` apenas verifica dependências.

## Limites e verificações

`experiments/process_budget.py` executa comandos diretamente, sem shell, aplicando os
30 segundos e 8 MiB de saída combinada de EVAL-01. A fila de leitura também é limitada;
o limite não é verificado somente depois de acumular toda a saída. Os probes não criam
workers ou processos auxiliares; esse utilitário não promete conter árvores arbitrárias
de processos. O comparador completo deve respeitar os demais limites de EVAL-01.

Foram escritos quatro testes antes do controle de processos e observadas quatro falhas
por comportamento ainda não implementado. Após implementar, os quatro passaram:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests/experiments -v
```

Cobertura inicial do ensaio: stdout/stderr preservados, código de saída não zero preservado,
timeout encerrando um processo e limite de saída combinada. Esses testes usam Python
como processo controlado, sem fingir que o motor Graphviz ou ELK.js está disponível.

A suíte ampliada tem 14 testes aprovados: inclui IDs e coordenadas inválidos, cruzamentos,
trechos coincidentes, bordas, travessias, encontros em nó comum, projeção de links repetidos,
geometrias não caracterizadas e prazo da avaliação. Os testes de validação de layout foram
observados falhando por `NotImplementedError` antes da implementação. Os demais testes
geométricos verificam respostas conhecidas do modelo experimental, não o renderer do Twine.

## Preparar as dependências

Graphviz deve ser obtido de sua [distribuição oficial](https://graphviz.org/download/),
incluindo executável, bibliotecas e plugins. É possível informar o caminho do executável
ao probe, sem alterar o PATH:

```powershell
.\.venv\Scripts\python.exe experiments/compare_layouts.py --probe --dot 'C:\caminho\do\Graphviz\bin\dot.exe'
```

Para ELK.js, a preparação local prevista é a seguinte, executada na raiz do projeto por
um ambiente com acesso ao registro npm:

```powershell
npm.cmd install --prefix .tmp/layout-engines --no-audit --no-fund elkjs
```

O probe usa por padrão `.tmp/layout-engines/node_modules/elkjs`; `--elk-root` permite
informar outro diretório. Registrar versões e licenças efetivas quando os pacotes estiverem
disponíveis. A instalação não foi realizada por este agente: o acesso de rede do shell
continua restrito. Não alterar proteções de rede para contornar essa restrição.

## Próxima execução

Confirmar a geometria efetiva no editor, adequar o avaliador e repetir a comparação
se o traçado diferir da hipótese. Corpus e opções desta execução estão registrados acima.
Casos fora do orçamento e limitações do perfil devem aparecer no relatório. Não escolher
um vencedor por um probe de versão nem por contagens obtidas de rotas que o Twine não usa.
