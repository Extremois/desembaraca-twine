# Ubuntu 26.10 x64 — preparação do ensaio privado

T033/T037/T076/T078, 2026-10-27. A matriz `linux-ubuntu-versions.yml` acrescenta
26.10 a 20.04/22.04/26.04, com glibc/musl e falhas independentes. O fluxo 18.04
continua separado. Reutiliza os motores conferidos em `a825f0d`, sem reconstrução
ou promoção de catálogo.

Imagem oficial fixada em `.github/native-images/ubuntu-26.10-amd64.json`:
[release de 25/10/2026](https://cloud-images.ubuntu.com/releases/stonking/release-20261025/),
876.878.336 bytes, SHA-256
`46d1d848cd8bfc05a2e729f70b02e0b4b97502bf7839b8928186d3c643c13b33`.
O manifesto lista kernel 7.3.0-9-generic, glibc 2.44, strace 7.0 e grub-pc;
são expectativas a confirmar no guest. Checksum e manifesto ficam preservados
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
nativo ainda pendente nesta preparação. A cobertura
de T037 continua parcial até candidata final, modalidades remotas/sdist,
elegibilidade aplicável, Twine, ARM64 e gates comuns completos. Nenhum alvo
de suporte é promovido por esse ensaio.
