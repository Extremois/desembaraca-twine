# Reparo falho com pacotes instalados e motores POSIX reais

O checkpoint `a00efdd4ae6df0832a3613e8b93ec34305a7b69f` amplia o ensaio privado
instalado para quatro falhas de reparo. O workflow
[39514473848](https://github.com/Extremois/desembaraca-twine/actions/runs/39514473848)
passou em Ubuntu 24.04 x64/ARM64 e macOS 15 Intel/Apple Silicon, CPython 3.12/3.14.
Cada combinação instala wheel e sdist em venvs externas separadas, sem `src/`
no driver nem Git/Graphviz global no PATH. As candidatas privadas anteriores
são reutilizadas por hash; não houve necessidade de recompilar o motor.

`runtime/summary.json` vincula oito relatórios e seus artefatos Actions. Os
relatórios registram 16 instalações, **64 cenários de reparo falho** e
**384 processamentos das seis referências após as falhas**, todos zerados,
com conteúdo/conexões e bytes dos originais preservados. Também repetem o
corpus normal: 208 casos explícitos, 96 referências zeradas, preparo automático
e explícito, probe no destino final, permissões e caminhos Unicode.

As quatro falhas são:

- Transferência interrompida por `ConnectionError` injetado no transporte.
- Falta de espaço por `ENOSPC` injetado no transporte; o disco não foi preenchido.
- Bytes corrompidos fornecidos ao verificador real de integridade.
- Negação real de execução: somente o executável da nova geração de teste recebe
  modo `0644`; o processo nativo falha com `PermissionError`. A geração anterior
  não tem suas permissões alteradas.

Após cada falha, os bytes de `active.json` permanecem idênticos, o gerenciador
seleciona a geração anterior sem aquisição e o handle anterior processa as seis
referências. Hashes de entrada/saída são registrados. O verificador rejeita
cenário/referência ausente ou duplicado, seleção alterada, aquisição offline,
geometria residual, ausência de preservação ou negação apenas simulada.

O workflow de instalação
[39514473842](https://github.com/Extremois/desembaraca-twine/actions/runs/39514473842)
também passou: dez combinações, 20 instalações wheel/sdist, 60 entrypoints e
53 arquivos por formato, LICENSE/NOTICE e origem conferidos. Os recibos estão
em `packages/`. `foundation.json` preserva os seis jobs aprovados do workflow
`39514473838`, com 243 testes cada. Localmente, 248 testes passaram no Python
3.14; os sete testes do verificador também passaram em 3.12. A diferença de
cinco casos corresponde à revisão glibc que permanece local.

Os quatro workflows de recompilação disparados pelo filtro amplo de testes
receberam solicitação de cancelamento, pois fontes/receitas/motores não mudaram.
Não são falhas dos ensaios necessários acima.

## Limites

Aquisição privada controlada e bloqueio de rede apenas no Python; não é prova
de syscalls de rede do motor. Não há aprovação de assinatura, notarização,
quarentena, licenças, candidata distribuída final ou imagem canônica de suporte.
Gatekeeper/SIP permaneceram nos estados originais dos runners; SIP já estava
desabilitado. O teste não altera essas configurações nem as trata como aprovação.

Crash/concorrência ainda precisam ser exercitados nesses runners e formatos;
os ensaios anteriores Ubuntu 18.04 x64 continuam separados por revisão. O índice
[`recovery.json`](../recovery.json) registra as 69 células e 138 slots, com
observações nativas parciais em cinco células/dez slots e aceite integral pendente.
T076 permanece parcial, total 57/84. Catálogo distribuído continua Windows;
nenhum suporte POSIX foi promovido. Recibos finais locais, sem commit adicional.
