# Modelo de dados — perfil Twee / Twine 2.12.1

Snapshot conserva os bytes (até 10 MiB); a orquestração guarda o caminho absoluto.
A orquestração mantém o snapshot de entrada separado do documento inicializado.
Documento pode acrescentar metadados visuais ausentes em memória e sinaliza
`layout_initialized`; o snapshot original continua sendo usado na checagem de concorrência.
As métricas iniciais usam o layout que o importador Twine atribuiria à entrada.
A preservação é conferida por igualdade exata de bytes, sem depender de hashes no runtime.
Hashes SHA-256 identificam os fixtures e as amostras na evidência de validação. Documento conserva
os bytes, nós em ordem de arquivo, ocorrências de relações dirigidas e intervalos exatos
dos valores `position`. Identidade é o nome da passagem; IDs numéricos do motor são
temporários. Nenhum texto narrativo é enviado ao motor. Links repetidos continuam no
documento e no grafo semântico; a projeção visual usa um arco por par dirigido distinto.

Nó: nome não vazio/único, x/y finitos com módulo <=10^7, dimensões finitas positivas
entre 0,001 e 10^6. Layout candidato deve conservar identidades, dimensões e relações.
Coordenadas candidatas são serializadas com 6 casas decimais e reavaliadas após releitura.
Até 100 nós e 300 ocorrências de links; limites conservadores, não capacidade medida.
Os modelos puros não acessam arquivos ou executam subprocessos.

Contagens: tripla de inteiros não negativos (pares de arestas, pares de nós,
pares aresta–nó), usando curvas do perfil. Tolerância espacial 10^-6, resíduos de
interseção de elipses 10^-7 em coordenadas normalizadas. Centro dos traços; espessura,
marcadores de seta e indicador de início não entram nas métricas.

Seleção: avaliar original e um candidato Graphviz TB; somente aceitar candidato se
nenhuma contagem aumentar e pelo menos uma diminuir. Empate mantém original. Serializar,
reler e verificar bytes fora das posições e relações antes de publicar. Sem melhoria,
publicar cópia íntegra da baseline. Relações dinâmicas não são executadas nem inferidas.

Resultado: estado sucesso se as três contagens são zero e a projeção está inteiramente
caracterizada no perfil; dados opacos impedem afirmar sucesso completo. Limitações se resta qualquer
conflito, falha se não há saída íntegra. Resultado válido tem caminho absoluto e contagens
antes/depois; falha não tem caminho de saída. Razões incluem ausência de melhoria,
regressão do candidato, orçamento e motor inválido; ausência de dependência é falha.
Cancelamento não publica nem anuncia cópia parcial. Prazo global 60s, motor até 30s,
saída combinada até 8 MiB; até 2s adicionais para recolher processo. Limite global também
é consultado na análise geométrica. Erro antes de uma baseline íntegra é falha.
O parser verifica o prazo antes de cada passagem e limita cabeçalhos a 8 KiB para conter
o custo de reconhecimento. Chamadas de I/O do sistema operacional não são interrompidas
por esse prazo cooperativo; a publicação de uma baseline já validada pode ser finalizada
após o orçamento de processamento, comunicando a limitação, sem recalcular o grafo.
