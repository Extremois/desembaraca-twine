# Cobertura técnica dos avisos em cache: musl e Windows

Checkpoint `ec5ff25f838416aea8a7526367bb1820df04e9a2`, cinco workflows aprovados.
O novo workflow [39525752863](https://github.com/Extremois/desembaraca-twine/actions/runs/39525752863)
passou em quatro slots musl x64/ARM64 × Python 3.12/3.14 e dois slots Windows
× Python 3.12/3.14, sempre em wheel e sdist externos separados. São 12
instalações e 3.716 arquivos de avisos comparados antes/depois do uso offline.

## Ambientes medidos

- **musl**: motores estáticos já produzidos, sem recompilação, CPU correspondente
  do runner e imagens Python/Alpine 3.22 fixadas por digest em `alpine-ci-images.json`.
  Os testes rodam como usuário não root; fonte montada somente para leitura,
  ferramentas e projeto copiados para volume privado, venvs externas. Foram
  conferidos ID/versão Alpine, Python, CPU, UID, imagem e inspeção Docker.
  É medição de cache real em userland Alpine sobre kernel Ubuntu; não aprova
  kernel, dispositivo ou célula Alpine nativa. Aquisição do motor é controlada.
- **Windows**: motor oficial fixado no manifesto distribuído, obtido por HTTPS
  com a política de redirecionamento e SHA-256 do gerenciador real. Cada cache
  temporário é novo e privado, com uma operação inicial de download. Depois,
  reutilização offline sem aquisição, leitura independente dos 29 avisos,
  detecção de alteração e restauração exata. Não mede modos POSIX e não
  substitui instalação/aceite limpo em Windows 11. `windows-manifest.json`
  preserva os bytes exatos do manifesto empregado.

Os seis relatórios e as quatro inspeções Docker estão em `additional/`;
`additional/summary.json` vincula seus hashes e artefatos Actions. Cada formato
registrou antes/depois idênticos, uma alteração deliberada de aviso recusada
e confirmação da restauração. Somente caches de teste foram modificados.

## Consolidação da mesma revisão

A regressão glibc/macOS também passou na revisão atual, workflow `39525752771`;
`posix/` preserva oito relatórios, 16 instalações e 6.076 comparações.
O [índice T066](../distribution-integrity.json) agora reúne:

| Bundle | Arquivos de avisos por instalação | Instalações |
|---|---:|---:|
| Linux glibc x64 | 480 | 4 |
| Linux glibc ARM64 | 573 | 4 |
| Linux musl x64 | 450 | 4 |
| Linux musl ARM64 | 450 | 4 |
| macOS ARM64 | 233 | 4 |
| macOS Intel | 233 | 4 |
| Windows legado distribuído | 29 | 4 |
| **Total** | **9.792 comparações** | **28** |

São sete variantes, 14 slots Python, 28 alterações recusadas e 28 restaurações
confirmadas. Cada comparação corresponde ao mesmo caminho/SHA-256 antes e
depois do uso offline; os mapas completos estão nos relatórios brutos. O índice
anterior permanece em `previous-distribution-index.json`; os recibos anteriores
de arquivos/fontes e seus hashes continuam referenciados.

Os demais workflows também passaram: `39525752730`, dez jobs de instalação
básica/20 instalações/60 entrypoints, em `packages/`; `39525752853`, oito slots
do modo de integração anterior/128 cenários de recuperação/768 referências após
falhas e corpus regular, em `runtime-regression/`; `39525752804`, seis jobs de
fundação com 249 testes cada, em `foundation.json`. Localmente passaram 258
testes, nove skips; os 13 testes focados também passaram em 3.12, um skip.
Nove testes anteriores permanecem locais: cinco glibc e quatro de distribuição.

## Pendências que permanecem

A medição independente dos avisos nos caches dos sete bundles está concluída
para os ambientes e formatos registrados. Ela não aprova compatibilidade ou
ancestralidade das licenças, oferta/retenção de fontes, assinatura/notarização,
pacotes finais ou suporte. Os resultados musl mantêm o limite de container e
os Windows mantêm o limite do runner hospedado. Rede offline foi bloqueada no
Python; não é uma nova observação de syscalls dos motores.

**T066 parcial, 57/84**: agora aguarda as revisões por componente/fontes e os
artefatos finais, com os aceites nativos/visuais preservados nas tarefas próprias.
Catálogo continua Windows. Checkpoint necessário enviado; recibos finais locais,
sem segundo commit.
