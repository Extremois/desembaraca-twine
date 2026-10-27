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
glibc 2.39, strace 6.8; valores a confirmar no guest. O perfil exige KVM
ativo por QMP, identidade 24.04 x64, kernel 6.8 e glibc 2.39, recusando
kernel Azure do host, imagem mutável, outra release ou arquitetura.

Download limitado a 1 GiB, overlay descartável de 8 GiB e guest sem internet,
com SSH em loopback e chave efêmera no runner existente. Nenhuma VM local.
CPython 3.12.15/3.14.8 e aplicação em venvs privadas, sem substituir Python do SO.

18 contratos focados e preparo real dos dois bundles/13 DOTs por ABI passaram.
Regressão portátil: 282 testes em cada Python local, nove skips por execução.
Dois YAMLs e seis passos Bash passaram; execução CI ainda pendente.
T036 permanece aberta para candidata final remota, modalidades wheel/sdist,
ARM64 e gates de integridade/Twine; observação privada não qualifica suporte.
