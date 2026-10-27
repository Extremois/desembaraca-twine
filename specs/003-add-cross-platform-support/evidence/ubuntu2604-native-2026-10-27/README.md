# Ubuntu 26.04 x64 — preparação do ensaio privado

T033/T037/T076/T078, 2026-10-27. `linux-ubuntu-versions.yml` agora inclui
26.04 junto de 20.04/22.04, em glibc/musl; 18.04 continua como regressão
separada. Usa os motores já conferidos em `a825f0d`, sem recompilá-los ou
inseri-los no catálogo ativo.

Imagem oficial fixada em `.github/native-images/ubuntu-26.04-amd64.json`:
[release de 16/10/2026](https://cloud-images.ubuntu.com/releases/resolute/release-20261016/),
859.090.944 bytes, SHA-256
`5645d0318ad21f643ebb1ac4567514620e9893380b07b0201fda163baa5b7eb5`.
O manifesto publicado lista kernel 7.0.0-38-generic, glibc 2.43, strace 6.19 e
grub-pc. São expectativas a confirmar em execução; checksums/manifesto ficam
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
Ensaio nativo, candidata final, modalidades remotas/sdist, manutenção, revisão
Twine, ARM64 e demais células continuam pendentes nesta preparação.
