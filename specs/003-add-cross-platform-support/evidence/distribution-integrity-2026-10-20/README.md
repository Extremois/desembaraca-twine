# Conferência offline de integridade da distribuição

O recibo [`final-check.json`](final-check.json), da T066,
foi produzido por `tools/validation/check-distribution-integrity.py` sem executar
motores, extrair arquivos, alterar caches ou iniciar nova rodada de CI. Os seis
bundles privados já construídos foram lidos dos ZIPs de artefatos Actions locais;
somente o bundle glibc x64 já usado nos ensaios precisou ser baixado novamente.
Não houve publicação nem instalação global.

| Bundle | Arquivos conferidos | Avisos vinculados ao índice offline |
|---|---:|---:|
| Linux glibc ARM64 | 573 | 571 |
| Linux glibc x64 | 480 | 478 |
| Linux musl ARM64 | 450 | 448 |
| Linux musl x64 | 450 | 448 |
| macOS ARM64 | 233 | 231 |
| macOS Intel | 233 | 231 |
| Total | 2.419 | 2.407 |

Para cada bundle, o verificador confere arquivo, inventário e proveniência por
SHA-256; inventário exato, bytes, tamanhos e modos POSIX codificados; identidade
do executável; cobertura de todos os avisos pelo `NOTICE-ORIGINS.json`; e presença
do texto da licença Graphviz fixado na proveniência. O índice de origens completo
está preservado no recibo, permitindo consultar seus metadados offline depois
da expiração dos artefatos Actions. Os binários não foram adicionados ao Git.

O [índice atual](../distribution-integrity.json) conserva este recibo e acrescenta
as medições independentes dos caches glibc/macOS em
[`cache-notices-2026-10-20/`](../cache-notices-2026-10-20/README.md). Os limites
de cache descritos abaixo se referem ao escopo desta primeira conferência.

O wheel e sdist locais de desenvolvimento também passaram na comparação dos
53 arquivos Python/dados/avisos e dos textos integrais LICENSE/NOTICE contra o
checkout atual. Os oito recibos instalados da revisão `eea100c` foram vinculados
por hash ao mesmo arquivo/proveniência dos quatro bundles glibc/macOS usados
naquela matriz. Nenhum resultado de execução foi transferido para musl por
associação. A fonte da aplicação permanece igual; o novo verificador e testes
estão locais, ainda sem commit.

Quatro testes novos cobrem inventário e origem omitidos/alterados, arquivo extra,
modo incorreto, bytes de proveniência/inventário trocados e escolha do inventário
do pacote quando o artefato também contém metadados de builds intermediários.
Python 3.12: 253 testes de fundação aprovados, oito skips. Python 3.14: 252 testes
na primeira rodada, oito skips; após acrescentar o quarto caso, os quatro testes
focados passaram. Não houve nova rodada de testes nativos nem CI.

`initial-check.json` e `initial-check-tool.py` preservam o primeiro recibo e sua
fonte exata. A conferência final também limita os caminhos dos recibos vinculados
ao diretório de evidências; seu hash de ferramenta corresponde ao arquivo atual.
`summary.json` registra entradas, hashes e limites para revisão.

## O que continua pendente

Integridade do índice não comprova por si só a ancestralidade histórica das
cópias ou a compatibilidade das licenças. EPL, LGPL, material SDK/geradores,
dados W3C/ISO e demais componentes continuam nos ledgers de revisão próprios.
O verificador não gera um audit aprovado nem altera o catálogo ativo.

Os recibos de execução existentes cobrem o gerenciador real em modo offline,
mas esta conferência não captura independentemente os bytes de todos os avisos
do cache. Windows/cache, fontes correspondentes e retenção/oferta permanente,
aprovação por componente, assinatura/notarização macOS, pacotes finais e aceites
da matriz continuam necessários. **T066 parcial, 57/84**. Nenhuma célula foi promovida.

Para repetir com os mesmos artefatos preservados, use caminhos locais explícitos:

```sh
python tools/validation/check-distribution-integrity.py --wheel CAMINHO.whl --sdist CAMINHO.tar.gz --bundle ARTEFATO_ACTIONS.zip --report NOVO_RECIBO.json
```

Repetir `--bundle` para cada variante. `--runtime-summary` aceita o resumo de
recibos instalados e exige os bundles correspondentes. Relatórios existentes
não são sobrescritos; resultados de compatibilidade/qualificação permanecem falsos.
