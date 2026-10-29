# Ubuntu 24.04 x64 — ensaio privado com imagem fixada

T033/T036/T076/T078, 2026-10-27. O perfil Noble acrescenta uma imagem KVM
independente aos ensaios anteriores no runner hospedado Ubuntu 24.04. A matriz
comum cobre 20.04/22.04/24.04/26.04/26.10 em glibc/musl; 18.04 permanece separado.
Os motores são os mesmos de `a825f0d`, sem reconstrução ou promoção de suporte.

Imagem oficial de [17/10/2026](https://cloud-images.ubuntu.com/releases/noble/release-20261017/),
621.284.352 bytes, SHA-256
`04e8f2461a16a44e78a370284471f29616cdd9baf1893df25807b71f985b6c94`.
Pin em `.github/native-images/ubuntu-24.04-amd64.json`, com hashes do checksum
e manifesto preservados em gzip. Manifesto: kernel 6.8.0-147-generic,
glibc 2.39, strace 6.8; valores confirmados no guest. O perfil exige KVM
ativo por QMP, identidade 24.04 x64, kernel 6.8 e glibc 2.39, recusando
kernel Azure do host, imagem mutável, outra release ou arquitetura.

Download limitado a 1 GiB, overlay descartável de 8 GiB e guest sem internet,
com SSH em loopback e chave efêmera no runner existente. Nenhuma VM local.
CPython 3.12.15/3.14.8 e aplicação em venvs privadas, sem substituir Python do SO.

18 contratos focados e preparo real dos dois bundles/13 DOTs por ABI passaram.
Regressão portátil: 282 testes em cada Python local, nove skips por execução.
Dois YAMLs e seis passos Bash passaram; execução CI conferida abaixo.
T036 permanece aberta para candidata final remota, modalidades wheel/sdist,
ARM64 e gates de integridade/Twine; observação privada não qualifica suporte.

## Resultados conferidos

Checkpoint `4b5625d4b79720e58d50f0919eedb3b39d08e00c`, três workflows aprovados:
[matriz Ubuntu](https://github.com/Extremois/desembaraca-twine/actions/runs/40584914210),
[regressão 18.04](https://github.com/Extremois/desembaraca-twine/actions/runs/40584914146)
e [fundação](https://github.com/Extremois/desembaraca-twine/actions/runs/40584914057).
O primeiro push foi recusado pelo GitHub com `commit_refs`; após conferir a
referência remota, o reenvio do mesmo commit passou. Essa falha de envio não
foi falha de ensaio nem exigiu alterar a revisão.

O [resumo](summary.json) conserva doze artefatos KVM e seis logs de fundação,
com originais comprimidos e hashes. [capture.py](capture.py) reconfere imagem,
revisão, origem dos motores, layouts, instalação, recuperação e rastros.

| Guest x64, KVM ativo | Kernel observado | glibc do SO | Motores |
| --- | --- | --- | --- |
| Ubuntu 24.04 | 6.8.0-147-generic | 2.39 | glibc e musl |
| Ubuntu 18.04 | 4.15.0-212-generic | 2.27 | glibc e musl |
| Ubuntu 20.04 | 5.4.0-216-generic | 2.31 | glibc e musl |
| Ubuntu 22.04 | 5.15.0-198-generic | 2.35 | glibc e musl |
| Ubuntu 26.04 | 7.0.0-38-generic | 2.43 | glibc e musl |
| Ubuntu 26.10 | 7.3.0-9-generic | 2.44 | glibc e musl |

Cada guest passou 13 layouts com hashes e geometria reconferidos. Nos seis
guests glibc, CPython 3.12.15 e 3.14.8 privados instalaram o wheel em venvs
externas e executaram três entrypoints. Os 53 arquivos instalados foram
comparados aos bytes do commit por `git show`. O Python do SO manteve seu
hash e não conta como slot da aplicação.

Por slot glibc: seis referências zeradas e 389 execuções `dot` observadas por
strace, sem syscalls de rede no corpus. O controle positivo socket/connect em
processo filho foi detectado em todos os slots. O transporte permanece privado
e controlado; a execução direta musl no kernel Ubuntu não qualifica Alpine.

A [revisão de recuperação](nested-recovery.json) confere 16 execuções de
cenários/96 referências offline por slot: oito cenários externos, quatro
reparos falhos e quatro cenários de processos aninhados. Total: **192 execuções
de cenários e 1.152 execuções de referências offline** nos doze slots glibc.
Seletores/handles, locks, órfãos e aquisição única entre dois concorrentes
passaram nas verificações registradas.

Fundação: seis jobs com 282 testes cada, oito skips Windows/seis Linux/macOS;
Windows limpo segue skipped. O índice T036 acrescenta evidência da imagem
fixada somente para x64, preservando os relatórios históricos de wheel/sdist,
as contagens e a revisão de origem. A nova observação cobre wheel privado;
não herda aceitação sdist/remota nem estende kernel/rastros para ARM64.

Os índices anteriores de T036, T037, instalação e recuperação ficam preservados
neste diretório. Recuperação conserva nove células/18 slots com observações
parciais e zero células completas; T037 conserva dez alvos/cinco células x64
observadas. Pro/ESM permanece pendente somente em 18.04/20.04.

Recibos finais locais, sem promoção de catálogo, release ou suporte. T033,
T036, T037, T076 e T078 permanecem abertas para seus requisitos restantes e
para a matriz completa.
