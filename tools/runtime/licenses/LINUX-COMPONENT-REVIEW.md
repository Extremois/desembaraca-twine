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
| Runtime Zig | Fontes observadas incluem portas musl; `tan.zig` também referencia Go | Incluir COPYRIGHT musl quando houver evidência de fontes de runtime, inclusive em glibc ARM64. Referência Go e demais proveniências exigem fechamento próprio; o LICENSE raiz Zig não substitui termos de terceiros |
| Entidades HTML/SVG | Avisos W3C datados, copyright/status e avisos ISO internos preservados separadamente | Aplicabilidade/condição ISO e política pertinente permanecem pendentes; ver [revisão W3C](data-references/w3c/REVIEW.md) |

As duas correções de preparo deste incremento são o reconhecimento explícito
ColorBrewer e o COPYRIGHT musl nas candidatas glibc com evidência de runtime.
Novos avisos W3C/ISO também estão implementados localmente. A incorporação desses
materiais precisa ser confirmada em candidatas novas no CI antes de atualizar os
recibos de empacotamento. Os ZIPs anteriores permanecem com seus hashes originais.

Para fechar T030, ainda é necessário resolver as questões de escopo/terceiros
listadas, vincular decisões de componentes aos inputs estáticos efetivos, fechar
oferta/retenção de fontes e revisar os avisos da candidata final. A possibilidade
de recuperar bytes públicos e a presença de textos não concedem, isoladamente,
aprovação de compatibilidade ou distribuição.
