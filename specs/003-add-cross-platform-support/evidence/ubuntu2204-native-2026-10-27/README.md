# Ubuntu 22.04 x64 — ensaio privado em preparação

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
5.15.0-198-generic, glibc 2.35 e strace 5.16. Não são aprovação do guest até a
conferência nativa. A consulta inicial à imagem de 2025 redirecionou para HTTP;
o ensaio usa a URL HTTPS direta da release datada de 2026, sem relaxar esse gate.

O fluxo exige x64, KVM ativo por QMP, identidade/kernel/libc correspondentes,
imagem conferida por hash e overlay descartável de 8 GiB. Guest sem internet,
SSH limitado ao loopback, chave efêmera e sem VM local. A aplicação será
instalada em venvs privadas CPython 3.12.15/3.14.8, com runtime real e transporte
controlado; o Python do sistema deve conservar seu hash.

Verificações locais: 15 contratos focados, sintaxe YAML/Bash da matriz e da
regressão, preparo dos dois pacotes reais com 13 DOTs por ABI. A regressão
portátil passou com 279 testes em cada Python 3.12/3.14 e nove skips por execução.
Execução CI, elegibilidade/manutenção, candidata
final, sdist/remoto, Twine, ARM64 e demais células continuam pendentes nesta
preparação. Nenhum alvo é promovido pelo harness.
