# Regressão do driver compartilhado no Ubuntu 18.04

Workflow [39515645035](https://github.com/Extremois/desembaraca-twine/actions/runs/39515645035),
revisão `eea100c37599517e09b6626d1edb82b599a1b19c`: jobs glibc e musl aprovados
em guests KVM efêmeros no GitHub, kernel `4.15.0-212-generic`.
Nenhuma VM foi criada no computador do mantenedor.

`summary.json` registra o job glibc: wheel instalado fora do checkout nos
CPythons privados 3.12.15/3.14.8, 53 arquivos conferidos contra o commit,
três entrypoints e corpus regular aprovados. A suíte externa de recuperação
repetiu seus oito cenários; o teste explícito instalado também executou quatro
reparos falhos e os quatro novos cenários de crash/concorrência. São 16 execuções
de cenários e 96 referências após recuperação por Python, com sobreposição
intencional entre as duas suítes. Os números ficam separados dos 128 cenários
dos runners Ubuntu 24.04/macOS.

Traces baixados e reprocessados registram **389 execuções do dot e zero syscalls
de rede por Python** no percurso completo. O controle positivo com socket e
conexão em processo filho foi detectado. Seletores, locks, geração/handle anterior,
órfãos, barreiras e uma aquisição concorrente foram verificados. Transferência,
ENOSPC, corrupção e pontos de encerramento continuam injeções explícitas;
processos, permissões, locks e motor são reais. Os arquivos de trace preservam
seus hashes; os relatórios JSON brutos não foram alterados.

`musl/summary.json` vincula os três relatórios preservados do segundo job.
Os 13 outputs do motor estático musl foram conferidos por hash, input DOT e
decodificação de geometria. Esse job não executa pacote Python instalado nem
qualifica Alpine; é regressão do motor inalterado no kernel Ubuntu antigo.

O índice [`recovery.json`](../recovery.json) referencia os dois slots glibc
atuais, preservando o recibo anterior de outra revisão. T076 permanece parcial:
candidata final, elegibilidade/ambientes e restante da matriz continuam pendentes.
Não há aprovação de licenças, distribuição, suporte POSIX ou encerramento da spec.
Total **57/84**; recibos finais locais, sem commit adicional.
