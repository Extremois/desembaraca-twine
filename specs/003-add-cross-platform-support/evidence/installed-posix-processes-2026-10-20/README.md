# Crash e concorrência com motores POSIX instalados

Checkpoint `eea100c37599517e09b6626d1edb82b599a1b19c`, workflow
[39515644989](https://github.com/Extremois/desembaraca-twine/actions/runs/39515644989):
os oito slots Ubuntu 24.04 x64/ARM64 e macOS 15 Intel/Apple Silicon × CPython
3.12/3.14 passaram com wheel e sdist instalados em venvs externas separadas.
O driver copiado contém auxiliares/fixtures, sem `src/`; os processos filhos
usam o Python isolado do venv e o pacote instalado. Nenhuma VM local foi criada.

Cada uma das 16 instalações cobre oito cenários: quatro falhas de reparo da
rodada anterior e quatro cenários de processos agora implementados. São
**128 cenários e 768 processamentos offline das seis referências**, todos zerados,
além de quatro provas adicionais de uso do handle anterior por instalação.
O corpus regular também passou: 208 casos explícitos e 96 referências zeradas.

Os novos cenários executam operações reais do sistema:

- `during_download`: o processo encerra com `os._exit(77)` segurando o lock;
  a seleção anterior permanece utilizável e o staging órfão fica preservado.
- `before_select`: o processo encerra após validar a nova geração, antes da
  troca do seletor; a geração anterior continua selecionada.
- `after_select`: o processo encerra após a troca atômica; a nova geração válida
  é retomada offline e o handle anterior continua funcional.
- `concurrent_first_use`: dois processos sinalizam prontidão e aguardam a mesma
  barreira. Depois da liberação, há uma aquisição e ambos retornam a mesma geração.

Após cada crash, um novo reparo bem-sucedido comprova que o lock foi liberado
pelo SO. Os bytes e permissões dos arquivos/diretórios órfãos são comparados
antes/depois desse reparo. Cada cenário processa as seis referências pelo
gerenciador sem aquisição, preserva originais/conteúdo/conexões e executa
adicionalmente uma referência pelo handle anterior. Os recibos registram hashes.
Os validadores recusam saída normal no lugar do crash, seleção incorreta,
referências ausentes, lock não recuperado, órfão alterado e aquisições/gerações
duplicadas ou barreira sem ambos os processos prontos.

`runtime/summary.json` vincula os oito relatórios, hashes e artefatos baixados.
`packages/summary.json` registra o workflow `39515644954`: dez combinações,
20 instalações básicas wheel/sdist, 60 entrypoints e os 53 arquivos e
LICENSE/NOTICE conferidos. `foundation.json` preserva seis jobs aprovados do
workflow `39515644946`, com 244 testes cada. Localmente, a fundação passou
com 249 testes no Python 3.14; os oito testes do verificador passaram também
em 3.12. Cinco testes da revisão glibc permanecem apenas locais.

As quatro recompilações de motores disparadas pelo filtro amplo receberam
pedido de cancelamento; fontes/receitas/motores não mudaram. O baseline
Ubuntu 18.04 é uma regressão separada do driver compartilhado.

Essa [regressão do driver](../ubuntu1804-process-driver-2026-10-20/README.md)
também passou em glibc e musl. O wheel glibc instalado nos dois Pythons do guest
executou as suítes externas/nativas, com 389 execuções dot e zero syscalls de
rede por Python sob strace, controle positivo detectado. São ambientes e
contagens separados dos oito slots hospedados acima; não herdam sua qualificação.

## Limites e índice

Aquisição e falhas de transferência/ENOSPC/corrupção são controladas. A negação
de execução por modo do arquivo, processos, locks e motores são reais. O bloqueio
de rede desses slots é apenas Python, sem prova de syscalls do motor. Os controles
Gatekeeper/SIP permaneceram como antes; SIP já estava desabilitado no runner.
Não houve alteração das proteções, aceite de assinatura/notarização/quarentena,
licenças, candidata distribuída final ou promoção de suporte.

[`recovery.json`](../recovery.json) mantém as 69 células/138 slots e as
observações parciais anteriores; `previous-recovery-index.json` preserva os bytes
do índice anterior. Para os oito slots atuais, crash/concorrência deixam de ser
pendências do ensaio privado instalado. Distribuição final, ambientes canônicos,
demais células e gates comuns continuam pendentes. **T076 parcial, 57/84**;
catálogo distribuído Windows. Recibos finais locais, sem commit adicional.
