# Avisos nos caches nativos dos pacotes instalados

O workflow [39521002551](https://github.com/Extremois/desembaraca-twine/actions/runs/39521002551),
revisão `cf724215f50170847f2fbf15d775db2014543076`, passou nos oito slots de
Ubuntu 24.04 x64/ARM64 e macOS 15 Intel/Apple Silicon × CPython 3.12/3.14.
Cada slot instalou wheel e sdist separados em venvs externas e preparou o
bundle privado correspondente com o gerenciador e probes nativos reais.

O ensaio específico leu todos os arquivos de avisos diretamente no cache,
independentemente do verificador de integridade do gerenciador. Comparou os
bytes, tamanhos, modos e inventário com o bundle fixado, incluindo o índice
offline de origens e um aviso obtido do pacote Python. Depois, o gerenciador
reutilizou a mesma geração offline e uma nova leitura produziu os mesmos hashes.

São **16 instalações e 6.076 comparações de arquivos antes/depois**, distribuídas:

| Bundle | Arquivos de avisos por instalação | Instalações |
|---|---:|---:|
| glibc x64 | 480 | 4 |
| glibc ARM64 | 573 | 4 |
| macOS ARM64 | 233 | 4 |
| macOS Intel | 233 | 4 |

Cada instalação fez uma aquisição controlada e nenhuma aquisição offline.
Em cada uma, somente um aviso do cache temporário de teste recebeu bytes
adicionais: a leitura independente recusou a alteração; um bloco `finally`
restaurou o conteúdo exato, e a terceira leitura confirmou todos os hashes
originais. Foram 16 rejeições de corrupção e 16 confirmações de restauração.
Os testes unitários também recusam avisos ausentes, extras, alterados e links.

`native/summary.json` vincula os oito relatórios brutos, hashes e artefatos
baixados. Cada relatório preserva os mapas de SHA-256 antes/depois por formato,
identidade do bundle/proveniência e contadores. Os validadores do mantenedor
comparam esses mapas com o índice offline já conferido da candidata e com o
aviso fixado no pacote. Nenhum binário foi incorporado ao Git.

O driver específico faz somente preparo/probes e leitura de avisos; não repete
o corpus ou a recuperação. A regressão do modo anterior foi executada em
separado após ampliar o coletor compartilhado: workflow `39521002577`, oito
slots aprovados, 128 cenários/768 referências após falhas e corpus regular.
`runtime-regression/summary.json` preserva seu escopo próprio. Os dez jobs de
instalação `39521002558` também passaram, com 20 instalações e 60 entrypoints,
em `packages/summary.json`. `foundation.json` registra seis jobs aprovados com
247 testes cada. Localmente passaram 256 testes, nove skips; os 11 testes
focados também passaram em Python 3.12, com um skip de symlink não disponível
ao usuário Windows. Os nove casos adicionais locais são cinco da revisão
glibc e quatro da conferência offline de distribuição, ainda sem commit.

## Consolidação e limites

A [rodada posterior](../cache-notices-more-2026-10-20/README.md) concluiu também
a medição dos caches musl/Windows e repetiu os quatro bundles desta rodada na
mesma revisão. As pendências de cache abaixo descrevem o escopo `cf72421`;
o índice atual registra a cobertura técnica das sete variantes.

[`distribution-integrity.json`](../distribution-integrity.json) consolida os
recibos dos arquivos e dos caches. O recibo anterior, com os índices de origens
dos seis bundles, permanece em
[`final-check.json`](../distribution-integrity-2026-10-20/final-check.json).
Os hashes do índice anterior foram atualizados apenas para seu caminho preservado.

Esses resultados concluem a medição independente de avisos dos quatro bundles
glibc/macOS de desenvolvimento, nos slots e formatos acima. Cache musl x64/ARM64
e Windows, aplicabilidade/compatibilidade das licenças, fontes correspondentes e
retenção/oferta permanente, assinatura/notarização e pacotes finais permanecem
pendentes. Aquisição é controlada, rede bloqueada apenas no Python e não há
qualificação de distribuição assinada, célula ou suporte. O ensaio não altera
proteções do SO, instalações globais ou o cache pessoal do mantenedor.

**T066 parcial, 57/84**, catálogo Windows. Checkpoint necessário `cf72421`
enviado; recibos finais locais, sem segundo commit.
