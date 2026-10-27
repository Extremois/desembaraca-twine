# Ubuntu 22.04 x64 — ensaio privado nativo conferido

T033/T037/T076/T078, 2026-10-27. O workflow compartilhado
`linux-ubuntu-versions.yml` combina Ubuntu 20.04/22.04 e motores glibc/musl,
com falhas independentes. Substitui o workflow específico de Focal e mantém
o ensaio 18.04 separado. Motores reutilizados do checkpoint `a825f0d`, sem
recompilação ou alteração do catálogo.

A imagem está fixada em `.github/native-images/ubuntu-22.04-amd64.json`:
[release oficial de 20/10/2026](https://cloud-images.ubuntu.com/releases/jammy/release-20261020/),
730.529.792 bytes, SHA-256
`2099e63da0b822ef8e05e3d596c1b402eaaae658fc08ab919cb8495bfcdc488b`.
Os checksums e o manifesto publicados ficam preservados em gzip, com os hashes
dos bytes descomprimidos no pin. Expectativas do manifesto: kernel
5.15.0-198-generic, glibc 2.35 e strace 5.16, confirmados no ensaio abaixo.
A consulta inicial à imagem de 2025 redirecionou para HTTP;
o ensaio usa a URL HTTPS direta da release datada de 2026, sem relaxar esse gate.

O fluxo exige x64, KVM ativo por QMP, identidade/kernel/libc correspondentes,
imagem conferida por hash e overlay descartável de 8 GiB. Guest sem internet,
SSH limitado ao loopback, chave efêmera e sem VM local. A aplicação será
instalada em venvs privadas CPython 3.12.15/3.14.8, com runtime real e transporte
controlado; o Python do sistema deve conservar seu hash.

Verificações locais: 15 contratos focados, sintaxe YAML/Bash da matriz e da
regressão, preparo dos dois pacotes reais com 13 DOTs por ABI. A regressão
portátil passou com 279 testes em cada Python 3.12/3.14 e nove skips por execução.
Elegibilidade/manutenção, candidata final, sdist/remoto, Twine, ARM64 e demais
células continuam com seus gates. Nenhum alvo é promovido pelo harness.

## Resultados conferidos

Checkpoint `3e7a27e599050776fdacde7f480238e79d22d772`, três workflows aprovados:
[matriz 20.04/22.04](https://github.com/Extremois/desembaraca-twine/actions/runs/40573396667),
[regressão 18.04](https://github.com/Extremois/desembaraca-twine/actions/runs/40573396752)
e [fundação](https://github.com/Extremois/desembaraca-twine/actions/runs/40573396476).
O [resumo](summary.json) registra os seis artefatos baixados e reconferidos,
com os originais comprimidos e seus hashes preservados. As medições anteriores
continuam vinculadas às suas próprias revisões.

| Guest x64, KVM ativo | Kernel observado | glibc do guest | Motores ensaiados |
| --- | --- | --- | --- |
| Ubuntu 22.04 | 5.15.0-198-generic | 2.35 | glibc e musl |
| Ubuntu 20.04 | 5.4.0-216-generic | 2.31 | glibc e musl |
| Ubuntu 18.04 | 4.15.0-212-generic | 2.27 | glibc e musl |

Os 13 layouts de cada guest tiveram seus inputs/outputs e geometria conferidos.
Nos três guests glibc, CPython 3.12.15 e 3.14.8 instalaram o wheel em venvs
privadas e executaram os três entrypoints. Os 53 arquivos foram comparados
com os bytes do commit por `git show`; os hashes do Python do SO permaneceram
iguais antes/depois. Musl continua sendo ensaio de motor estático no kernel
Ubuntu, sem aprovação de células Alpine ou slots Python musl.

Cada um dos seis slots glibc passou 13 casos, seis referências zeradas e
389 execuções `dot` sob strace sem syscalls de rede no corpus. O controle de
socket/connect no filho foi detectado. A aquisição do motor é uma fixture
controlada, distinta de uma instalação remota da candidata final.

A [revisão de recuperação](nested-recovery.json) confere 16 execuções de cenários
e 96 referências offline por slot, incluindo as suítes externa e aninhada:
**96 execuções de cenários e 576 execuções de referências offline** no total.
Falhas de reparo, três crashes e dois concorrentes preservaram seleção/handles,
liberaram locks e compartilharam uma aquisição/geração conforme o caso.
Os seis jobs de fundação passaram com 279 testes cada; oito skips Windows e
seis Linux/macOS. Windows limpo continua como job skipped.

O índice de recuperação passa a sete células/14 slots com observações parciais,
mantendo zero células completas. `linux-ubuntu-other.json` conserva os dez alvos
esperados e registra três células x64/seis slots observados. Índices anteriores
de recuperação/instalação/Ubuntu ficam preservados neste diretório. Recibos
finais locais; não há release publicada, promoção de catálogo ou encerramento
das tarefas agregadas de matriz.
