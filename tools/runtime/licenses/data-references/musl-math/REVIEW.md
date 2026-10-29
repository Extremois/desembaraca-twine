# Referências históricas das portas matemáticas

O arquivo `sources.json` fixa 19 fontes do SDK Zig 0.15.2 e 42 referências C
da distribuição oficial musl 1.1.18. Os arquivos `.gz` preservam os bytes
integrais dessas referências e do COPYRIGHT histórico. O preparo confere os
hashes antes de incluir os prefixos individuais e o COPYRIGHT nos avisos.

Essa versão histórica preserva avisos Sun e FreeBSD que uma declaração MIT
geral não substitui. Por exemplo, `exp2.c` contém as condições de redistribuição
de David Schultz; as rotinas trigonométricas preservam os avisos Sun e créditos
dos arquivos correspondentes. Os textos originais são mantidos integralmente,
sem substituir os respectivos termos por um identificador genérico.

As URLs `ln.c`, `lnf.c` e `__tand.c` dos comentários Zig são relacionadas
explicitamente a `log.c`, `logf.c` e `__tan.c`. `fmod.zig` menciona musl no
corpo; `sqrt.zig` também recebe referências históricas conservadoras. Esses
mapeamentos não comprovam uma tradução exata de uma revisão específica.
O vínculo definitivo de ancestralidade/aplicabilidade continua em revisão.

Quinze referências não têm prefixo de comentário; a conferência do arquivo
completo também não encontrou indicadores de copyright/permissão/redistribuição
nesses quinze casos. Eles permanecem registrados explicitamente e o COPYRIGHT
histórico acompanha o conjunto. Ausência de prefixo não representa decisão de
domínio público nem dispensa de revisão.

O ensaio local confrontou os arquivos comprimidos com o tarball oficial e as
19 fontes com ambos os SDKs fixados. Usando as observações de fontes dos builds
nativos, o preparo gera 28 materiais adicionais por variante pertinente:
glibc ARM64 e musl x64/ARM64. Glibc x64 não recebe esses materiais por associação.
As observações de fontes não equivalem à presença de todas essas rotinas nas
seções finais do executável; a preservação é conservadora.

Recibo: `specs/003-add-cross-platform-support/evidence/runtime-math-notices-2026-10-20/summary.json`.
Ele registra preparo local, sem aprovação T030, confirmação do novo pacote
nativo ou fechamento da cadeia transitiva de fontes.
