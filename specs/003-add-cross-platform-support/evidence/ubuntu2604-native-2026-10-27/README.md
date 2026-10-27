# Ubuntu 26.04 x64 — ensaio privado nativo conferido

T033/T037/T076/T078, 2026-10-27. `linux-ubuntu-versions.yml` agora inclui
26.04 junto de 20.04/22.04, em glibc/musl; 18.04 continua como regressão
separada. Usa os motores já conferidos em `a825f0d`, sem recompilá-los ou
inseri-los no catálogo ativo.

Imagem oficial fixada em `.github/native-images/ubuntu-26.04-amd64.json`:
[release de 16/10/2026](https://cloud-images.ubuntu.com/releases/resolute/release-20261016/),
859.090.944 bytes, SHA-256
`5645d0318ad21f643ebb1ac4567514620e9893380b07b0201fda163baa5b7eb5`.
O manifesto publicado lista kernel 7.0.0-38-generic, glibc 2.43, strace 6.19 e
grub-pc. Kernel/libc/tracer foram confirmados no ensaio abaixo; checksums/manifesto ficam
preservados em gzip, com hashes descomprimidos no pin. A variante escolhida é
`amd64`, com recusa explícita da substituição por `amd64v3`.

O perfil mantém teto de download de 1 GiB e overlay descartável de 8 GiB.
Exige KVM ativo por QMP, x64, identidade 26.04, kernel 7.0 e glibc 2.43;
não aceita o kernel do host ou evidência de 22.04 por associação. O guest
ficará sem internet, com SSH em loopback e chave efêmera, somente no runner
existente; não haverá VM local. CPython 3.12.15/3.14.8 e a aplicação ficam
em venvs privadas, preservando o hash do Python do SO.

Preparo local dos pacotes reais glibc/musl com 13 DOTs por ABI e 16 contratos
focados passaram. Regressão portátil: 280 testes por Python 3.12/3.14, nove
skips por execução; sintaxe YAML/Bash dos workflows aprovada.
Candidata final, modalidades remotas/sdist, revisão Twine, ARM64 e demais
células continuam com seus gates de aceitação.

## Resultados conferidos

Checkpoint `96f765bb19e30536d505fe875fa57b52622cb336`, três workflows aprovados:
[matriz 20.04/22.04/26.04](https://github.com/Extremois/desembaraca-twine/actions/runs/40576914797),
[regressão 18.04](https://github.com/Extremois/desembaraca-twine/actions/runs/40576914754)
e [fundação](https://github.com/Extremois/desembaraca-twine/actions/runs/40576914804).
O [resumo](summary.json) registra os oito artefatos baixados e conferidos,
com os originais comprimidos e seus hashes preservados.

| Guest x64, KVM ativo | Kernel observado | glibc do SO | Motores |
| --- | --- | --- | --- |
| Ubuntu 26.04 | 7.0.0-38-generic | 2.43 | glibc e musl |
| Ubuntu 22.04 | 5.15.0-198-generic | 2.35 | glibc e musl |
| Ubuntu 20.04 | 5.4.0-216-generic | 2.31 | glibc e musl |
| Ubuntu 18.04 | 4.15.0-212-generic | 2.27 | glibc e musl |

Cada guest passou 13 layouts com hashes de inputs/outputs e geometria
reconferidos. Nos quatro guests glibc, os dois CPythons privados instalaram o
wheel em venvs externas e executaram os três entrypoints. Os 53 arquivos foram
comparados aos bytes do commit por `git show`; o Python do SO manteve seu hash.
No Ubuntu 26.04, o Python de sistema usado somente pelo probe não substitui
os slots privados CPython 3.12.15 e 3.14.8.

Por slot glibc: 13 casos, seis referências zeradas, 389 execuções `dot`
observadas por strace e nenhuma syscall de rede no corpus. Cada controle de
socket/connect em filho foi detectado. O transporte do runtime continua
controlado, sem aprovação de candidata final remota. Musl é ensaio de motor
estático no kernel Ubuntu, sem qualificar Alpine ou slots Python musl.

A [revisão de recuperação](nested-recovery.json) confere 16 execuções de
cenários e 96 referências offline por slot, incluindo suítes externa e
aninhada: **128 execuções de cenários e 768 execuções de referências offline**
nos oito slots glibc. Seletores/handles, locks, órfãos e aquisição única dos
dois concorrentes passaram nas verificações registradas. O verificador local
mantém separadas as oito combinações de Python e as seis referências por
cenário; uma adaptação inicial incorreta dessa contagem foi recusada e corrigida
antes de gerar o recibo de revisão, sem alteração dos artefatos CI.

Os seis jobs de fundação passaram com 280 testes cada; oito skips Windows,
seis Linux/macOS. Windows limpo segue como job skipped. O índice de recuperação
passa a oito células/16 slots com observações parciais e zero células completas.
`linux-ubuntu-other.json` conserva os dez alvos esperados e registra quatro
células x64/oito slots observados. Pro/ESM continua pendente para as células
18.04/20.04; não é introduzido como requisito extra para 22.04/26.04.

Índices anteriores de Ubuntu, instalação e recuperação ficam preservados
neste diretório. Recibos finais locais; nenhum catálogo, release ou alvo de
suporte foi promovido. T033/T037/T076/T078 continuam abertas para seus requisitos
restantes e a matriz completa.
