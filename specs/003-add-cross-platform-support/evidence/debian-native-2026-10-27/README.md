# Debian 12/13 x64 — preparo do ensaio privado nativo

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
CI ainda pendente nesta preparação.

Manutenção consultada em 27/10/2026: [Debian 12](https://www.debian.org/releases/bookworm/)
está em LTS até 30/06/2028, incluindo amd64/arm64, com limitações por pacote;
[Debian 13](https://www.debian.org/releases/trixie/) tem suporte regular até
09/08/2028 e LTS até 30/06/2030. Isso não atesta atualização integral desta
imagem nem substitui o aceite dos pacotes/arquiteturas da matriz. Patch real
será medido no guest; ARM64, candidata final/remota, sdist e Twine permanecem
pendentes. T038 continua aberta.
