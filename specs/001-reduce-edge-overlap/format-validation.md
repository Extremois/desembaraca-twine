# Caracterização da amostra real

Data: 2026-10-16. **Estado de FMT-01: fechado para o perfil observado na amostra.**
Extensão `.twee` aprovada, preservação verificada e importação confirmada pelo usuário.

## Origem e integridade

Amostra recebida do usuário: `C:/Users/franc/Downloads/o roubo do quadro.twee`.
Proveniência, tamanho e hash estão em [tests/fixtures/README.md](../../tests/fixtures/README.md).
Nenhuma cópia da narrativa foi incorporada ao repositório ou enviada a serviços externos.
O original foi apenas lido. Foi criada somente uma cópia local para teste de importação,
fora dos arquivos versionados; não foi gerado um layout otimizado.

## Observações verificadas por inspeção

| Propriedade | Resultado |
|---|---|
| Conteúdo | Fonte Twee com cabeçalhos `::` e metadados JSON |
| Extensão real | `.twee`, diferente da extensão `.twine` citada inicialmente |
| Codificação | UTF-8 sem BOM |
| Quebras de linha | LF; 130 caracteres de quebra, sem CRLF |
| Passagens especiais | Uma `StoryTitle` e uma `StoryData` |
| Passagens narrativas | 9, todas com nomes distintos |
| Ligações | 14 ocorrências `[[destino]]`; todos os destinos existem |
| Metadados de cada nó | `position` e `size` |
| Tamanhos | Todas as caixas declaram `100,100` |
| Coordenadas | Há valores fracionários; não arredondar sem revalidar a geometria |
| Story format | Harlowe 3.3.9 |
| Dados da história | IFID, início e zoom declarados em `StoryData` |
| Versão do editor | Não consta nos dados inspecionados |
| Identidade de passagens | Nomes; não há PID explícito nessa amostra |

Não foram encontrados marcadores de macros na busca inicial por chamadas `(nome:...)`.
Isso descreve a amostra, não prova que todo documento Harlowe tem grafo estático completo.
Não foi executado conteúdo da história para extrair ligações.

## Correspondência documental

A estrutura observada corresponde aos elementos de fonte Twee descritos na
[especificação oficial Twee 3](https://github.com/iftechfoundation/twine-specs/blob/master/twee-3-specification.md):
cabeçalhos, passagens especiais e metadados de posição/tamanho. A versão do formato de
história não deve ser confundida com a versão do editor ou da especificação de arquivo.

O [importador/exportador atual do Twine](https://raw.githubusercontent.com/klembot/twinejs/develop/src/util/twee.ts)
usa posição e tamanho nas passagens. Isso é evidência documental de compatibilidade de
layout, não um teste de reabertura na versão do editor do usuário. Não copiar sua
implementação para o projeto sem a avaliação de licenças prevista no plano.

## Estratégia de preservação candidata

Com `.twee` confirmado para a primeira versão, conservar os bytes originais e substituir
somente os valores de `position` nos cabeçalhos narrativos reconhecidos. Não reserializar
o corpo das passagens, `StoryData`, nomes, tags ou metadados não visuais. Preservar `size`
na abordagem inicial. Não acrescentar passagens ou alterar texto para simular rotas.

Uma verificação de preservação deve neutralizar apenas os valores de posição autorizados
e comparar os demais bytes, além de comparar nomes, conteúdos e ligações extraídas.
A normalização, os intervalos exatos dos valores e as regras de nomes escapados precisam
constar do contrato antes do parser de produção.

## Ensaio de preservação executado

Utilitário de caracterização: `experiments/validate_twee_sample.py` (stdlib, perfil
deliberadamente restrito à sintaxe observada na amostra; não é o parser de produção).

Comando executado a partir da raiz do projeto:

```powershell
.\.venv\Scripts\python.exe experiments/validate_twee_sample.py 'C:\Users\franc\Downloads\o roubo do quadro.twee' '.tmp/format-validation/position-check.twee'
```

A cópia foi criada com abertura exclusiva, sem sobrescrever arquivo existente. Somente
a primeira posição foi alterada: `Acusar o Conde`, de `700,800` para `710,800`.
O script releu a cópia e confirmou 9 passagens e 14 ligações com os mesmos nomes e destinos.
A comparação dos bytes com os valores de posição neutralizados foi idêntica; o hash do
original permaneceu inalterado. Hash da cópia:
`217846fe1cf38d36af552f54bdb9e632a6d8e23c5e014a4149820e6d1102358b`.

A consulta à integração CUA retornou `apps: []` e `browsers: []`. A tentativa explícita de
criar uma aba para o editor retornou `Browser is not available: iab`. Não foi possível abrir
Twine para confirmar importação, posição exibida e traçados diretamente. O usuário validou
a cópia e respondeu A: abriu corretamente, com 9 passagens, 14 ligações e posição esperada
para “Acusar o Conde”. Essa é evidência reportada pelo usuário, não automação visual.
A versão exata do editor não foi informada; não declarar suporte a todas as versões.
Posteriormente, o usuário confirmou uso pelo site oficial `https://twinery.org/2/` e
conexões curvas/com dobras. Isso identifica a origem do editor, mas não a versão do
bundle carregado ou os parâmetros das curvas. O modelo reto do experimento foi rejeitado.

## Resultado e limites

1. Extensão resolvida: somente `.twee`, conforme resposta A do usuário.
2. Regravação local e preservação resolvidas pelo ensaio acima.
3. Reabertura resolvida para esta amostra por confirmação do usuário. Não há nesta
   amostra laços, arestas paralelas ou ligações dinâmicas; essas variações continuam
   exigindo corpus próprio e testes de geometria, sem inferir validação por este ensaio.
4. Documentar as exclusões do perfil e os limites de extração estática; não generalizar
   cobertura a macros, outros formatos ou versões sem evidência.
5. Graphviz 16.1.0 e ELK.js 0.12.0 foram localizados após instalação pelo usuário.
   A comparação de T006 foi executada sob hipótese geométrica ainda pendente de validação.

## Mudança posterior no caminho fornecido

Na retomada, o caminho em Downloads continha outro documento: 21.139 bytes, 31 cabeçalhos
de passagem sem posições/tamanhos, SHA-256
`30ba53788388fd98037f29c50f823d6e51ae2ad581ff18b1fe98fdc09f80f06f`.
O extrator experimental recusou esse arquivo como fora do perfil. Não foi modificado.
A comparação usou a cópia local de importação já validada, com SHA-256
`217846fe1cf38d36af552f54bdb9e632a6d8e23c5e014a4149820e6d1102358b`;
ela tem uma posição deslocada em 10 unidades, portanto é a baseline medida deste ensaio.

T004 e T005 concluídas para o perfil observado. T006 pode iniciar; as histórias aguardam
a comparação, o desenho e os contratos definidos em T007–T014. O fechamento de FMT-01
não comprova otimização do grafo nem cobertura de sintaxes ausentes na amostra.
