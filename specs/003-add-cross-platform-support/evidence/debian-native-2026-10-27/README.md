# Debian 12/13 x64 — ensaio privado nativo conferido

T033/T038/T076/T078, 2026-10-27. Novo workflow `linux-debian.yml` usa quatro
guests Debian 12/13 × glibc/musl, independentes da regressão Ubuntu. Os motores
conferidos em `a825f0d` continuam com os mesmos bytes; não há entrada nova no
catálogo, VM local, emulação ou qualificação de suporte.

Imagens oficiais `generic-amd64`, build datado `20261026-2643`, fixadas pelos
SHA-512 publicados em `SHA512SUMS`, tamanhos e manifestos de pacotes:

| Série | Imagem | Bytes | Kernel/libc esperados |
| --- | --- | --- | --- |
| Debian 12 | [bookworm](https://cloud.debian.org/images/cloud/bookworm/20261026-2643/) | 448.790.528 | 6.1.0-54-amd64 / 2.36 |
| Debian 13 | [trixie](https://cloud.debian.org/images/cloud/trixie/20261026-2643/) | 438.894.592 | 6.12.113+deb13-amd64 / 2.41 |

Pins em `.github/native-images/debian-{12,13}-amd64.json`, com checksum e
manifesto preservados em gzip. SHA-256 dos manifestos é distinto do SHA-512
oficial das imagens; o harness exige o algoritmo próprio de cada perfil.
Exige identidade Debian, release, patch de `/etc/debian_version`, arquitetura,
kernel/libc e KVM ativo por QMP; Ubuntu, kernel do host e TCG são recusados.

Os manifestos não incluem strace. O ensaio fornece strace 6.1 e três bibliotecas
libunwind como ferramenta privada, a partir de dois pacotes oficiais Debian
fixados em `.github/native-images/private-tracer-debian-x64.json`. Extrai
somente quatro arquivos regulares ELF x64, sem scripts de instalação ou links.
O loader usa `--library-path` somente para o tracer; a aplicação não herda
LD_LIBRARY_PATH. Arquivos e versão observados são reconferidos contra o recibo.
Essa ferramenta pertence ao ensaio, não é dependência distribuída da aplicação.

Guest sem internet; host obtém inputs fixados. CPython 3.12.15/3.14.8 e wheel
externo usam venvs privadas, sem substituir Python do SO. Download máximo de
1 GiB e overlay descartável de 8 GiB. Discos, seeds e chaves não são evidência.

23 contratos focados e preparo real dos quatro bundles/13 DOTs passaram.
Regressão portátil final: 287 testes em cada Python local, nove skips por
execução. Três YAMLs/nove passos Bash e sintaxe Python 3.6 dos probes passaram;
CI conferido nos resultados abaixo.

A [primeira tentativa](attempt-1.json), checkpoint `3847fad`, foi recusada
antes do boot dos quatro guests: `cloud.debian.org` redireciona os arquivos
grandes. Os destinos diretos laotzu/chuangtzu em `ftp.acc.umu.se` foram
conferidos por leitura de um byte e SHA512SUMS idêntico ao manifesto oficial.
Os pins passam a esses destinos exatos, mantendo `origin_url`, tamanho e
SHA-512; a recusa de redirecionamentos continua obrigatória. Logs preservados
em gzip. Uma resposta HEAD sem conferir seu destino foi insuficiente na
preparação inicial; a conferência inclui agora o destino real de GET.

Manutenção consultada em 27/10/2026: [Debian 12](https://www.debian.org/releases/bookworm/)
está em LTS até 30/06/2028, incluindo amd64/arm64, com limitações por pacote;
[Debian 13](https://www.debian.org/releases/trixie/) tem suporte regular até
09/08/2028 e LTS até 30/06/2030. Isso não atesta atualização integral desta
imagem nem substitui o aceite dos pacotes/arquiteturas da matriz. Patch real
medido no guest nos resultados abaixo; ARM64, candidata final/remota, sdist e Twine permanecem
pendentes. T038 continua aberta.

## Resultados conferidos

Checkpoint `55a789ea497c2fa74180cbb2e2dee3b81f1a1220`, quatro workflows aprovados:
[Debian](https://github.com/Extremois/desembaraca-twine/actions/runs/40591021352),
[Ubuntu 20.04–26.10](https://github.com/Extremois/desembaraca-twine/actions/runs/40591021318),
[regressão 18.04](https://github.com/Extremois/desembaraca-twine/actions/runs/40591021418)
e [fundação](https://github.com/Extremois/desembaraca-twine/actions/runs/40591021574).
O [resumo](summary.json) conserva dezesseis artefatos conferidos e seis logs,
com 418 arquivos originais dos guests comprimidos e hashes preservados.

| Guest x64, KVM ativo | Patch observado | Kernel observado | glibc do SO | Motores |
| --- | --- | --- | --- | --- |
| Debian 12 | 12.15 | 6.1.0-54-amd64 | 2.36 | glibc e musl |
| Debian 13 | 13.7 | 6.12.113+deb13-amd64 | 2.41 | glibc e musl |

Os seis Ubuntu x64 foram repetidos: 18.04/20.04/22.04/24.04/26.04/26.10,
com ambos os motores. Cada guest passou 13 layouts com inputs/outputs e
geometria reconferidos. Os motores mantêm seus hashes anteriores.

Nos oito guests glibc, CPython 3.12.15 e 3.14.8 privados instalaram o wheel em
venvs externas e executaram três entrypoints. Os 53 arquivos foram comparados
aos bytes do commit por `git show`; o hash do Python do SO permaneceu igual.
Python 3.11/3.13 da imagem Debian controla somente o probe e não conta como
slot da aplicação.

Por slot glibc: seis referências zeradas, 389 execuções `dot` observadas pelo
strace e zero syscalls de rede no corpus. Os controles positivos socket/connect
em processo filho foram detectados. Em Debian, os quatro arquivos do tracer
foram reconferidos contra os bytes extraídos dos dois pacotes oficiais fixados;
o recibo de origem, hashes de arquivos e versão 6.1 coincidem com o observado
no guest. O loader usa diretório privado somente para o tracer, preservando o
ambiente da aplicação. [capture.py](capture.py) registra essas verificações;
sua repetição offline requer os dois `.deb` identificados no pin na pasta
`.tmp`, além dos ZIPs/logs apontados no recibo de downloads.

A [revisão de recuperação](nested-recovery.json) confere 16 execuções de
cenários e 96 referências offline por slot: oito cenários externos, quatro
reparos falhos e quatro cenários de processos aninhados. Total: **256 execuções
de cenários e 1.536 execuções de referências offline** nos dezesseis slots.
Só Debian representa quatro slots, 64 cenários e 384 referências offline;
o restante é regressão Ubuntu. Seletores/handles, locks, órfãos e aquisição
única entre dois concorrentes passaram nas verificações registradas.

Fundação: seis jobs com 287 testes cada, oito skips Windows/seis Linux/macOS;
Windows limpo segue skipped. O novo índice T038 conserva quatro alvos/oito
slots esperados, com dois alvos x64/quatro slots observados e zero completos.
Recuperação passa a onze células/22 slots com observações parciais e zero
células completas. T036/T037 mantêm seus alvos e evidências anteriores;
quatro snapshots dos índices de Ubuntu, instalação e recuperação ficam
preservados neste diretório. A nova observação conjunta de instalação é
registrada separadamente das contagens históricas e cobre somente wheel.

Recibos finais locais. Aquisição do runtime é privada/controlada; candidatas
finais remotas, sdist, revisão Twine, ARM64 e cobertura integral de pacotes/LTS
continuam gates próprios. Musl mede o motor estático nesses kernels, sem
qualificar Alpine ou slots Python musl. Nenhum catálogo, release ou suporte
foi promovido. T033/T038/T076/T078 e a feature permanecem parciais.
