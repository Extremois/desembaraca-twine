# Perfil suportado

Fonte Twee UTF-8 (BOM permitido), LF ou CRLF, uma história com `StoryTitle` e `StoryData`
opcionais e únicos; StoryData deve ser objeto JSON. `start`, quando presente, deve nomear passagem existente. Vazio válido
com os dois especiais e sem `start`. Nomes simples Unicode, sem escapes de cabeçalho nem
`[]{}`; tags simples opcionais. Corpo e quebras preservados byte a byte, inclusive `\::`.
Script/stylesheet com uma dessas tags é preservado e não é nó; ambas juntas são recusadas.
Metadados JSON `position` e `size`, quando presentes, são strings `x,y`; pares numéricos
finitos, dimensões positivas. Demais propriedades são preservadas literalmente, inclusive
JSON aninhado. Chaves duplicadas, nomes duplicados, cabeçalhos incompletos, referências
ausentes e histórias agregadas são recusados claramente, listando destinos inexistentes.
Campos ausentes recebem posição 0,0 e tamanho 100,100. Se todas as posições narrativas
forem zero, aplica-se a grade do importador: x=25+125*(índice%10),
y=25+125*floor(índice/10), na ordem do arquivo, excluindo especiais, scripts e estilos.
Com alguma posição não zero, as demais continuam em 0,0. Valores explícitos inválidos
são recusados. A inicialização ocorre em memória e é publicada somente na cópia.

Após inicializar metadados visuais ausentes, somente os bytes dentro da string
`position` de cada cabeçalho comum podem mudar durante a otimização.
Tags, corpos, atributos desconhecidos e StoryData permanecem idênticos. Parser nunca
executa scripts. Links estáticos: `[[destino]]`, `[[texto->destino]]`,
`[[destino<-texto]]`, `[[texto|destino]]`. Setters são preservados sem execução.
Prioridade de destino: último ->, primeiro <-, último |. Macros
de navegação são recusadas em vez de presumir conexões. Scripts/estilos são opacos e geram
limitação de análise estática. Não prometer correção de referências dinâmicas.
Essa limitação impede afirmar sucesso completo mesmo com contagens estáticas zeradas.

Cabeçalhos são limitados a 8 KiB e o BOM é permitido somente no início do arquivo.
Constantes JSON NaN/Infinity são recusadas inclusive em campos desconhecidos.

Referência de geometria: fonte oficial Twine 2.12.1, ZIP SHA-256
`a18a77989e4f23295e50da2311a81c04d0af74adb806183e8a9ae0817cd0e2a6`.
Arquivos consultados: `passage-connection.tsx`, `self-connection.tsx`,
`passage-connection-group.tsx`, `util/geometry.ts`, `util/svg.ts`, `util/parse-links.ts`,
`util/twee.ts` e `store/stories/defaults.ts` (defaults e grade de importação).
Implementação independente, sem incorporar o código GPL do editor. Versão carregada
no navegador do usuário não identificada; suporte declarado a este perfil de referência.

Nós são retângulos com coordenadas no canto superior esquerdo. Conexões normais são
arcos SVG de raios (d, 0,75d), rotação do segmento, arco menor e sweep definido pelo
sentido horizontal (no empate, vertical), entre interseções centro–centro com as bordas.
Prioridade das bordas: esquerda, direita, topo, base. Sem interseção, traço ausente.
Laço: da metade esquerda ao canto superior esquerdo, raio 0,4 min(largura,altura),
arco maior e sweep positivo. Correção de raios segue SVG. Recíprocas podem coincidir;
ocorrências repetidas na mesma direção formam uma conexão visual, preservando semântica.

Contar pares distintos uma vez; contato no nó comum é excluído, trecho coincidente fora
dele conta. Retângulos exigem área positiva. Travessia exige interior de nó alheio;
tangência à borda é excluída. Interseções de elipses por parametrização racional e raízes
de polinômio até grau quatro; não substituir arcos por linhas. Conversão Graphviz:
dimensões /72 para polegadas, saída em pontos; centro -> canto e inversão do eixo Y.
