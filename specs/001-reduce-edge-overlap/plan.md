# Implementation Plan: Redução de conflitos visuais em grafos do Twine

Data: 2026-10-16. Feature: `001-reduce-edge-overlap`. Constituição 1.0.1.
[Especificação](spec.md), [contratos](contracts/cli.md), [perfil](contracts/format-profile.md).

## Estado final

Implementação e validação local concluídas. As três histórias estão disponíveis,
78 testes passaram e os seis exemplos resolvíveis foram reabertos no Twine web com
confirmação do usuário. Licença Apache-2.0 escolhida explicitamente e registrada em
LICENSE/NOTICE. Entrega por código-fonte; instalação editável opcional não verificada.
Não foi criado branch/commit nem realizada publicação remota.

## Decisões de formato e preservação

Uma entrada e uma cópia `.twee` por execução. O termo inicial `.twine` foi substituído
por `.twee` mediante confirmação do usuário e caracterização de arquivo real.
[FMT-01](format-validation.md) fechado para o perfil observado, sem generalizar outros
formatos. A versão efetivamente carregada no navegador do usuário não foi identificada;
referência comportamental: fonte oficial Twine 2.12.1, ZIP SHA-256
`a18a77989e4f23295e50da2311a81c04d0af74adb806183e8a9ae0817cd0e2a6`.

Conservar o snapshot original. Inicializar metadados visuais ausentes conforme o
importador Twine (grade de dez colunas quando todas as posições são zero), somente na
cópia. Aceitar links estáticos com rótulos e StoryTitle/StoryData opcionais.
Após essa inicialização, substituir somente valores top-level de position nos
cabeçalhos narrativos. Preservar corpos, tags, StoryData, campos desconhecidos, dimensões,
direção e ocorrências repetidas. Relê-se a serialização e compara-se tudo fora das
posições antes da publicação. Identidades semânticas são nomes; IDs do motor são
temporários. Scripts não são executados e navegação fora do perfil é recusada.

## Motor e geometria

Escolha: Graphviz 16.1.0 dot, processo externo sem shell, TB, nodesep=0.7, ranksep=1,
splines=line, somente posições. DOT recebe IDs numéricos, dimensões e relações,
sem narrativa. Dimensões /72 em polegadas, saída json0 em pontos; centro -> canto
superior esquerdo, invertendo Y. Não usar as rotas do Graphviz como traçado do Twine.

[TB](curved-tb-results.json) e [LR](curved-lr-results.json) comparam Graphviz e ELK.js
0.12.0 no mesmo corpus por sessão. O primeiro modelo reto foi rejeitado após o usuário
informar curvas; foi substituído por arcos elípticos identificados na fonte do editor.
O avaliador é independente, usando parâmetros SVG e interseções de elipses; nenhum
código GPL do Twine foi incorporado. Conversão matemática: notas SVG do W3C.

Na amostra local TB tem baseline 1/0/2; Graphviz propõe 4/0/3 e ELK 6/0/6. Rejeitar
ambos e conservar baseline. Graphviz TB preservou o ciclo limpo; ELK TB e Graphviz LR
pioraram esse caso. A alternativa ELK também exige Node e ponte JS. Graphviz foi escolhido
pela combinação de casos resolvidos, custo operacional e integração simples. NetworkX
não oferece por si só o roteamento/dimensões necessários. Não foi criado motor próprio.

Cada candidato é serializado e medido com a geometria final do perfil. Aceitar somente
redução de pelo menos uma métrica sem aumento de nenhuma das três; empate mantém
original. Layout original validado é fallback. Recíprocas podem continuar coincidentes;
isso é comunicado como limitação, sem alegar impossibilidade universal.

## EVAL-01 — limites anteriores aos experimentos

| Recurso | Limite |
|---|---|
| Entrada | 10 MiB antes de leitura integral |
| Cada grafo | 1.000 nós e 5.000 arestas |
| Candidatos | Um por motor/caso em cada sessão |
| Chamada do motor | 30s |
| Caso | 120s |
| Sessão | 300s |
| stdout + stderr | 8 MiB, contados durante leitura |
| Recolhimento após limite/cancelamento | Até 2s adicionais |

TB e LR foram sessões independentes, com opções fixadas antes de cada chamada.
Processos diretos e ELK com worker simulado, sem filhos auxiliares. Avaliação geométrica
consulta relógio monotônico. Casos limitados ou não comparados são registrados.
Memória não foi medida; não há SLA ou capacidade máxima comprovada pelo ensaio.

## Limites e estados do produto

Python >=3.12 como requisito de código; ambiente exercitado Python 3.14.6 e Windows.
Sem bibliotecas Python de produção. Graphviz externo completo; ELK/Node só no experimento.

Entrada 10 MiB, cabeçalhos 8 KiB, 100 nós, 300 ocorrências de links, 60s cooperativos
de processamento, até 30s por motor, saída combinada de 8 MiB. Coordenadas finitas
com módulo <=10^7, dimensões 0,001..10^6, serialização com seis casas decimais.
Tolerância espacial 10^-6 e resíduos normalizados 10^-7. Arcos são analíticos, sem
substituir curvas por cordas. Avaliam-se centros de traço, sem espessura ou marcadores.

I/O do sistema operacional não é interrompido pelo prazo. Após esgotamento com baseline
íntegra, permite-se finalizar a cópia de fallback sem recalcular o grafo e informar
limitação. Sem baseline íntegra, falhar sem resultado anunciado.

Sucesso completo exige três zeros e projeção caracterizada. Limitações têm cópia íntegra,
caminho e causa conhecida. Falha não anuncia arquivo válido. Códigos 0/2/1/130 conforme
[CLI](contracts/cli.md). Dados opacos impedem afirmar sucesso completo mesmo com métricas
estáticas zeradas.

## Publicação e arquitetura

Snapshot de bytes imutável; temporário exclusivo ao lado da entrada; gravação completa,
flush/fsync, releitura e verificação. No Windows, rename sem substituição; colisão escolhe
outro nome. Em sistemas com rename substitutivo, hard-link exclusivo, sem afirmar suporte
validado fora do Windows. Limpeza de temporários/descritores e cancelamento testados.

- `formats/profile.py`: fonte e patches sem perdas.
- `domain/model.py`, `arcs.py`, `geometry.py`, `selection.py`, `result.py`: domínio puro.
- `engines/graphviz.py` e `process.py`: subprocesso limitado.
- `files.py`: snapshot e publicação.
- `application.py`, `cli.py`, `__main__.py`: coordenação e mensagens.
- `run.py`: execução do checkout sem backend de build.
- `tests/`: modelos, contratos, geometria, preservação e falhas.
- `experiments/`: comparação independente do código de produção.

## Revisão constitucional final

| Princípio | Evidência |
|---|---|
| I. Open source | Apache-2.0, LICENSE, NOTICE, README e CONTRIBUTING |
| II. Clareza | Módulos por responsabilidade e contratos explícitos |
| III. Separação | Domínio sem acesso a arquivos, CLI separada de publicação/motor |
| IV. Integridade | Patch limitado, releitura, comparação de bytes e fallback sem regressão |
| V. Qualidade | 78 testes e seis exemplos reabertos, defeitos reproduzidos antes de correções |
| VI. Decisões justificadas | Graphviz/ELK comparados; NetworkX avaliado; sem motor próprio |

Nenhuma exceção constitucional adotada. Inventário e licenças em
[third-party.md](../../docs/third-party.md). Os 97 arquivos nativos do Graphviz externo
foram inventariados, mas não incorporados ao projeto. Materiais privados e downloads
permanecem fora das fontes versionadas.

## Validação e limites da entrega

[Modelo](data-model.md), [quickstart](quickstart.md), [validação](validation.md) e
[tarefas](tasks.md) consolidados. Quickstart pelo checkout e suíte exercitados no
Windows. Instalação editável, outras versões/plataformas e redistribuição de motores
não foram validados e não fazem parte da composição entregue.
