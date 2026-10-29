# Fedora 43/44 x64 — ensaio privado nativo conferido

T033/T039/T076/T078, 2026-10-27. Novo workflow `linux-fedora.yml` usa quatro
guests Fedora 43/44 × glibc/musl. Ubuntu/Debian mantêm regressões separadas;
Fedora 45 não entra na matriz. Usa os motores conferidos em `a825f0d`, sem
recompilação ou promoção de catálogo/suporte. Nenhuma VM local ou emulação.

Imagens oficiais Cloud Base Generic, fixadas por URL de build/SHA-256/tamanho:

| Série | Build | Bytes | SHA-256 |
| --- | --- | --- | --- |
| Fedora 43 | [43-1.6](https://dl.fedoraproject.org/pub/fedora/linux/releases/43/Cloud/x86_64/images/) | 583.335.936 | `846574c8a97cd2d8dc1f231062d73107cc85cbbbda56335e264a46e3a6c8ab2f` |
| Fedora 44 | [44-1.7](https://dl.fedoraproject.org/pub/fedora/linux/releases/44/Cloud/x86_64/images/) | 583.729.152 | `28680fe5b371a5a82ebf43a31926e086a168e59949d03969c5093e7071f90b7f` |

Pins `.github/native-images/fedora-{43,44}-amd64.json`; checksums oficiais e
observações de origem em gzip neste diretório. GET de 72 bytes e HEAD
confirmaram origem direta sem redirecionamento, tamanho comprimido e disco
virtual qcow2 de 5 GiB. Usa teto de download de 1 GiB e overlay de 8 GiB.
A variante Generic é distinta de UEFI-UKI; o perfil recusa sua substituição.

O perfil exige identidade Fedora/versão/x64, KVM ativo por QMP e kernel com
sufixo `fc43.x86_64` ou `fc44.x86_64`. Confere o kernel em execução contra
`kernel-core` instalado, glibc e `fedora-release-common` por consulta RPM
somente de leitura, com formato fixo/limites. Não inventa patch de kernel a
partir do host; versão completa foi registrada no guest. Perfis libc
2.42/2.43 seguem os [toolchains 43](https://fedoraproject.org/wiki/Changes/GNUToolchainF43)
e [44](https://fedoraproject.org/wiki/Changes/GNUToolchainF44), a confirmar no guest.

SELinux deve estar **enforcing**, com contexto de processo registrado.
Modo permissive/disabled, outro kernel/RPM/release/arquitetura são recusados;
o ensaio não altera políticas ou desativa proteções. O tracer Debian 6.1
previamente fixado é somente ferramenta privada de observação, com suas três
bibliotecas e hashes conferidos; sua execução aqui precisa passar por si.
Não transfere aprovação Debian a Fedora nem constitui dependência distribuída
da aplicação. O loader limita a busca privada ao tracer, sem LD_LIBRARY_PATH
herdado pela aplicação.

Guest sem internet; inputs fixados obtidos pelo host. CPython 3.12.15/3.14.8
e wheel em venvs privadas, preservando o Python do SO. Discos/seeds/chaves não
são exportados. Preparo real dos quatro conjuntos/13 DOTs e 25 contratos
focados passaram. Regressão portátil: 289 testes por Python local, nove skips
por execução; quatro YAMLs/doze passos Bash e sintaxe Python 3.6 dos probes
passaram. CI conferido nos resultados abaixo.

T039 continua aberta para ARM64, candidata final/remota, sdist, revisão Twine
e os demais gates. Imagem GA fixada não atesta atualização integral, manutenção
ou compatibilidade de futuros updates; não há herança RHEL ou Fedora 45.

## Resultados conferidos

Checkpoint `7b30c80a7a1b980860e0fa9e6b16a14d8245c28e`, cinco workflows aprovados:
[Fedora](https://github.com/Extremois/desembaraca-twine/actions/runs/40594066437),
[Debian](https://github.com/Extremois/desembaraca-twine/actions/runs/40594066172),
[Ubuntu 20.04–26.10](https://github.com/Extremois/desembaraca-twine/actions/runs/40594066145),
[regressão 18.04](https://github.com/Extremois/desembaraca-twine/actions/runs/40594066334)
e [fundação](https://github.com/Extremois/desembaraca-twine/actions/runs/40594066322).
O [resumo](summary.json) conserva vinte artefatos conferidos e seis logs,
com 524 arquivos originais dos guests comprimidos e hashes preservados.

| Guest x64, KVM ativo | Release / RPMs observados | Kernel observado | glibc do SO | SELinux | Motores |
| --- | --- | --- | --- | --- | --- |
| Fedora 43 | fedora-release-common 43-25 / kernel-core 6.17.1-300.fc43 / glibc 2.42-4.fc43 | 6.17.1-300.fc43.x86_64 | 2.42 | enforcing (`unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023`) | glibc e musl |
| Fedora 44 | fedora-release-common 44-17 / kernel-core 6.19.10-300.fc44 / glibc 2.43-2.fc44 | 6.19.10-300.fc44.x86_64 | 2.43 | enforcing (`unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023`) | glibc e musl |

Debian 12/13 e os seis Ubuntu x64 foram repetidos: 18.04/20.04/22.04/24.04/26.04/26.10,
com ambos os motores. Cada guest passou 13 layouts com inputs/outputs e
geometria reconferidos. Os motores mantêm seus hashes anteriores.

Nos dez guests glibc, CPython 3.12.15 e 3.14.8 privados instalaram o wheel em
venvs externas e executaram três entrypoints. Os 53 arquivos foram comparados
aos bytes do commit por `git show`; o hash do Python do SO permaneceu igual.
Python da imagem Fedora controla somente o probe e não conta como slot da aplicação.

Por slot glibc: seis referências zeradas, 389 execuções `dot` observadas pelo
strace e zero syscalls de rede no corpus. Os controles positivos socket/connect
em processo filho foram detectados. Em Fedora, o SELinux enforcing com contexto
de processo `unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023` foi verificado,
e a ferramenta strace Debian privada funcionou sem alterar políticas.
[capture.py](capture.py) registra essas verificações; sua repetição offline requer
os pacotes e artefatos apontados no recibo de downloads.

A [revisão de recuperação](nested-recovery.json) confere 16 execuções de
cenários e 96 referências offline por slot: oito cenários externos, quatro
reparos falhos e quatro cenários de processos aninhados. Total: **320 execuções
de cenários e 1.920 execuções de referências offline** nos vinte slots.
Só Fedora representa quatro slots, 64 cenários e 384 referências offline;
o restante é regressão Debian e Ubuntu. Seletores/handles, locks, órfãos e
aquisição única entre dois concorrentes passaram nas verificações registradas.

Fundação: seis jobs com 289 testes cada, oito skips Windows/seis Linux/macOS;
Windows limpo segue skipped. O novo índice T039 conserva quatro alvos/oito
slots esperados, com dois alvos x64/quatro slots observados e zero completos.
Recuperação passa a treze células/26 slots com observações parciais e zero
células completas. T036/T037/T038 mantêm seus alvos e evidências anteriores;
snapshots dos índices de Ubuntu, Debian, instalação e recuperação ficam
preservados neste diretório. A nova observação conjunta de instalação é
registrada separadamente das contagens históricas e cobre somente wheel.

Recibos finais locais. Aquisição do runtime é privada/controlada; candidatas
finais remotas, sdist, revisão Twine, ARM64 e cobertura integral de pacotes/manutenção
continuam gates próprios. Musl mede o motor estático nesses kernels, sem
qualificar Alpine ou slots Python musl. Nenhum catálogo, release ou suporte
foi promovido. T033/T039/T076/T078 e a feature permanecem parciais.
