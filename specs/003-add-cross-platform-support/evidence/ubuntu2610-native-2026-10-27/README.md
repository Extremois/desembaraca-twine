# Ubuntu 26.10 x64 — ensaio privado nativo conferido

T033/T037/T076/T078, 2026-10-27. A matriz `linux-ubuntu-versions.yml` acrescenta
26.10 a 20.04/22.04/26.04, com glibc/musl e falhas independentes. O fluxo 18.04
continua separado. Reutiliza os motores conferidos em `a825f0d`, sem reconstrução
ou promoção de catálogo.

Imagem oficial fixada em `.github/native-images/ubuntu-26.10-amd64.json`:
[release de 25/10/2026](https://cloud-images.ubuntu.com/releases/stonking/release-20261025/),
876.878.336 bytes, SHA-256
`46d1d848cd8bfc05a2e729f70b02e0b4b97502bf7839b8928186d3c643c13b33`.
O manifesto lista kernel 7.3.0-9-generic, glibc 2.44, strace 7.0 e grub-pc;
kernel/libc/tracer foram confirmados no guest. Checksum e manifesto ficam preservados
em gzip com hashes descomprimidos no pin. Variante escolhida `amd64`, com
recusa de `amd64v3`, de imagens mutáveis e de evidências de 26.04 por herança.

O perfil conserva download máximo de 1 GiB e overlay privado de 8 GiB. Exige
KVM ativo por QMP, x64, identidade 26.10, kernel 7.3 e glibc 2.44. O guest
fica sem internet, com SSH em loopback e chave efêmera, somente no runner
existente; não há VM local. Dois CPythons privados e a aplicação usam venvs
externas sem substituir o Python do SO.

17 contratos focados e preparo real glibc/musl com 13 DOTs por ABI passaram;
regressão portátil passou em 281 testes por Python local (3.12/3.14), com
nove skips por execução. Os dois YAMLs e seis passos Bash passaram; CI
nativo conferido nos resultados abaixo. A cobertura
de T037 continua parcial até candidata final, modalidades remotas/sdist,
elegibilidade aplicável, Twine, ARM64 e gates comuns completos. Nenhum alvo
de suporte é promovido por esse ensaio.

## Resultados conferidos

Checkpoint `1e0349e28381c68a572c42e0e1889d64fe8d8336`, três workflows aprovados:
[matriz 20.04/22.04/26.04/26.10](https://github.com/Extremois/desembaraca-twine/actions/runs/40582316362),
[regressão 18.04](https://github.com/Extremois/desembaraca-twine/actions/runs/40582316337)
e [fundação](https://github.com/Extremois/desembaraca-twine/actions/runs/40582316372).
O [resumo](summary.json) conserva os dez artefatos conferidos, seus arquivos
originais comprimidos e hashes, além dos seis logs de fundação.

| Guest x64, KVM ativo | Kernel observado | glibc do SO | Motores |
| --- | --- | --- | --- |
| Ubuntu 26.10 | 7.3.0-9-generic | 2.44 | glibc e musl |
| Ubuntu 26.04 | 7.0.0-38-generic | 2.43 | glibc e musl |
| Ubuntu 22.04 | 5.15.0-198-generic | 2.35 | glibc e musl |
| Ubuntu 20.04 | 5.4.0-216-generic | 2.31 | glibc e musl |
| Ubuntu 18.04 | 4.15.0-212-generic | 2.27 | glibc e musl |

Cada guest passou 13 layouts, com inputs/outputs e geometria reconferidos.
Nos cinco guests glibc, CPython 3.12.15 e 3.14.8 privados instalaram o wheel
em venvs externas e executaram os três entrypoints. Os 53 arquivos instalados
foram comparados aos bytes do commit por `git show`; o Python do SO conservou
seu hash. O Python fornecido pela imagem controla o probe e não conta como
slot da aplicação.

Cada slot glibc passou seis referências zeradas, com 389 execuções `dot`
observadas pelo strace e zero syscalls de rede no corpus. O controle positivo
de socket/connect em processo filho foi detectado em todos os slots. O
transporte do runtime é privado e controlado. Musl foi executado diretamente
no kernel Ubuntu; esse resultado não qualifica Alpine nem Python musl.

A [revisão de recuperação](nested-recovery.json) confere 16 execuções de
cenários e 96 referências offline por slot, incluindo oito cenários externos,
quatro reparos falhos e quatro cenários de processos aninhados. São **160
execuções de cenários e 960 execuções de referências offline** nos dez slots.
Seletores/handles, locks, órfãos e aquisição única entre dois concorrentes
passaram nas verificações registradas.

Os seis jobs de fundação passaram com 281 testes cada; oito skips no Windows
e seis em Linux/macOS. Windows limpo permanece skipped. O índice de recuperação
registra nove células/18 slots com observações parciais e zero células completas.
O índice T037 conserva dez alvos e registra cinco células x64/dez slots
observados. Pro/ESM continua pendente em 18.04/20.04; não é exigido como gate
extra para 22.04/26.04/26.10.

Os índices anteriores de Ubuntu, instalação e recuperação ficam preservados
neste diretório. Os recibos finais estão locais; catálogo e releases permanecem
sem promoção. T033/T037/T076/T078 seguem abertas para candidata distribuída,
modalidades remotas/sdist, Twine, ARM64 e os demais requisitos da matriz.
