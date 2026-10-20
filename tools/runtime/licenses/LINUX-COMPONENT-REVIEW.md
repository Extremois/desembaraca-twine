# Revisão de componentes Linux

Estado: revisão parcial das candidatas `7d0476f`, em 2026-10-20. Nenhum inventário
aprovado foi produzido. As observações abaixo foram lidas nos textos vinculados
aos builds, não inferidas apenas dos nomes de licença. Os avisos e as fontes
continuam separados por `artifact_id` no ledger `linux.json`.

| Componente/material | Observação nos termos preservados | Tratamento e pendência |
| --- | --- | --- |
| Graphviz | COPYING EPL-2.0 e declarações em fontes observadas; fontes públicas e receitas conferidas | Manter texto/avisos e fechar oferta/obrigações de fontes. Arquivos sem declaração própria exigem revisão de escopo; não atribuir EPL aos subcomponentes automaticamente |
| Randomkit C | O prefixo contém termos BSD de três condições **e** termos permissivos adicionais para partes do código | Preservar o prefixo completo, incluindo autores e ambos os blocos. Um único rótulo MIT ou BSD para o arquivo inteiro não representa o texto |
| Randomkit header | Permissão de uso/modificação/distribuição com retenção de copyright e permissão | Prefixo próprio preservado, sem substituir o texto do arquivo C pelo do header |
| Rbtree | Permissão de redistribuição e uso; proibição de endosso sem autorização e disclaimer | LICENSE próprio preservado. Não converter para um identificador BSD genérico sem correspondência textual |
| ColorBrewer 1.1 | Além da retenção dos termos, pede reconhecimento e impõe condições relativas ao nome/endosso | Preparo passa a emitir o reconhecimento solicitado em arquivo próprio, validado contra o texto fonte. O nome do produto continua Desembaraça Twine |
| Bison | Quatro arquivos gerados preservam aviso GPL e exceção de uso do parser | Manter exceção junto do aviso e GPL integral como referência. Não tratar a GPL sem a exceção como único termo do parser gerado |
| Flex 2.6.4 | COPYING contém texto BSD e esclarecimento próprio sobre scanners gerados | Gerador/versão/macros conferidos; texto integral preservado. Não estender a exceção do scanner a componentes sem esse fundamento |
| RGB X.Org | O COPYING preservado contém blocos The Open Group e Oracle com suas condições | Manter os dois blocos. Correspondência de valores não demonstra sozinha a origem histórica de todas as entradas Graphviz |
| Glibc startup/nonshared | Fontes observadas declaram LGPL-2.1-ou-posterior; quatro prefixos contêm permissão de link, `csu/init.c` não contém a mesma exceção | Textos e fontes preservados; não aplicar a exceção dos demais arquivos a `init.c`. Fechar atendimento das obrigações de link/fontes por build |
| Runtime Zig | Fontes observadas incluem portas musl; a referência Go de `tan.zig` é anterior à substituição oficial do algoritmo pela musl | COPYRIGHT musl preservado inclusive em glibc ARM64. Histórico Go conferido contra ambos SDKs; preparo passa a preservar BSD Go conservadoramente para documentação/testes históricos. Avisos específicos das portas matemáticas musl continuam sob revisão; o LICENSE raiz Zig não substitui termos de terceiros |
| Entidades HTML/SVG | Avisos W3C datados, copyright/status e avisos ISO internos preservados separadamente | Aplicabilidade/condição ISO e política pertinente permanecem pendentes; ver [revisão W3C](data-references/w3c/REVIEW.md) |

As duas correções de preparo deste incremento são o reconhecimento explícito
ColorBrewer e o COPYRIGHT musl nas candidatas glibc com evidência de runtime.
Novos avisos W3C/ISO também estão implementados localmente. A incorporação desses
materiais foi confirmada nas quatro candidatas da revisão `4784410`, com todos
os workflows aprovados e avisos/índices conferidos após download. Os ZIPs
anteriores permanecem com seus hashes originais; os novos recibos estão em
`specs/003-add-cross-platform-support/evidence/linux-component-obligations-ci-2026-10-20/`.

Para fechar T030, ainda é necessário resolver as questões de escopo/terceiros
listadas, vincular decisões de componentes aos inputs estáticos efetivos, fechar
oferta/retenção de fontes e revisar os avisos da candidata final. A possibilidade
de recuperar bytes públicos e a presença de textos não concedem, isoladamente,
aprovação de compatibilidade ou distribuição.

A recuperação pública foi repetida para as quatro exportações da revisão
`4784410`, com pin explícito e vínculo às respectivas proveniências nativas:
18.173 entradas de fontes por candidata e dois metadados gerados separados.
Os [recibos atuais](../../../specs/003-add-cross-platform-support/evidence/public-source-recovery-current-2026-10-20/summary.json)
preservam o pin e os hashes, sem substituir a revisão anterior nem aprovar
retenção/oferta. O procedimento está em [REBUILD-SOURCES.md](../REBUILD-SOURCES.md).

O ponto histórico Go foi esclarecido pelo commit oficial
[`e243983`](https://github.com/ziglang/zig/commit/e24398361dacc4b995ec67043746561927f5f1d2):
o algoritmo Go foi substituído pelo musl, mas o link Go e partes de testes/documentação
permaneceram. O arquivo da tag Zig 0.15.2 corresponde byte a byte aos dois SDKs
fixados. A revisão não atribui automaticamente o algoritmo Go/Cephes ao código
atual nem afirma que todo material histórico foi substituído. O preparo inclui
o BSD completo do Go como preservação conservadora quando a fonte `tan.zig`
observada corresponde ao hash revisado; outra fonte/hash exige revisão própria.
Essa inclusão ainda aguarda o próximo empacotamento nativo, sem alterar ZIPs existentes.

A inclusão Go foi confirmada nas três candidatas pertinentes da revisão
`dfc93c8`, com conferência dos ZIPs após download. A [captura de seções alocadas](../../../specs/003-add-cross-platform-support/evidence/linux-allocated-sections-ci-2026-10-20/summary.json)
também foi reproduzida independentemente contra os quatro ELF, mapas e inputs
com hash. Todos preservam os bytes dos motores anteriores. Os mapas mostram
que `libcompiler_rt.a` fornece código matemático real, incluindo trigonometria
nas três variantes e exponenciais/logaritmos em glibc ARM64. Assim, a revisão
dos avisos específicos dessas portas continua necessária; não há fundamento
para descartá-los coletivamente como simples imports DWARF. A nova evidência
delimita contribuições alocadas, sem aprovar automaticamente licenças ou fechar
a relação exaustiva entre fonte e instruções.

## Portas matemáticas: preservação histórica conservadora

O preparo verifica 19 fontes Zig exatas e preserva 42 referências C originais
da musl 1.1.18, além do COPYRIGHT histórico. São emitidos 27 prefixos individuais
e o COPYRIGHT nas três variantes pertinentes; os termos Sun/FreeBSD não são
substituídos pelo MIT raiz. Quinze referências sem prefixo permanecem explícitas,
sem indicadores adicionais de copyright/permissão/redistribuição em seus corpos.
Os dois SDKs e as observações dos builds nativos foram conferidos localmente.
Ver `data-references/musl-math/REVIEW.md` e o recibo
`specs/003-add-cross-platform-support/evidence/runtime-math-notices-2026-10-20/summary.json`.

O ensaio comprova seleção/preparo por bytes; não comprova ancestralidade exata
da tradução, aplicabilidade final, pacote nativo atualizado ou fechamento T030.
ISO, outros componentes e oferta/retenção de fontes continuam pendentes.
