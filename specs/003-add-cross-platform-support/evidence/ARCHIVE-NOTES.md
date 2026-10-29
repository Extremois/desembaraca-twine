# Evidências atuais e arquivos históricos

O estado atual está no [encerramento após convergência](convergence-2026-10-29/summary.json):
sete alvos ABI, 14 slots Python e 86 tarefas concluídas. A instalação do comando
sem ativação tem [recibos próprios](../../../docs/evidence/user-installation-2026-10-29/5a1c43f/summary.json).

Os diretórios datados preservam também tentativas, resultados parciais e decisões
superadas. Em particular, `fedora-native-2026-10-27` registra ensaios antigos no
GitHub Actions; não exige nem autoriza novas VMs. Os índices `linux-*.json`
descrevem aqueles checkpoints por distribuição. O aceite atual usa ABI, sem
certificar individualmente as 69 declarações de compatibilidade.

`abi-recovery-ci` e `abi-review-outputs` preservam a tentativa anterior à captura
canônica, incluindo a descoberta de conversão CRLF. Seus campos de revisão
pendente não substituem a [confirmação visual posterior do usuário](twine-visual-review-2026-10-28.json).
Os seis hashes aceitos foram vinculados novamente aos pacotes finais na convergência.

`final-paired-review-2026-10-28/acceptance/3cd7feb` contém apenas recibos aprovados
de cache/notices daquele checkpoint; não concede aceite aos jobs cancelados ou
às instalações remotas que precisaram da correção de finais de linha posterior.
As auditorias e rascunhos antigos de licenças continuam limitados aos próprios
artefatos. A [publicação final](final-paired-review-2026-10-28/publication.json)
identifica os seis pares POSIX efetivamente publicados e seus hashes.
