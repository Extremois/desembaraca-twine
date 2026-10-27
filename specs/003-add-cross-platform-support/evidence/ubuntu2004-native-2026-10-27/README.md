# Ubuntu 20.04 x64 — ensaio nativo privado

T033/T037/T076/T078, preparação em 2026-10-27. O ensaio usa exclusivamente
KVM no runner efêmero GitHub x64 já utilizado pelo projeto; não cria VM local.
O workflow `linux-focal-baseline.yml` reutiliza os motores glibc/musl medidos
em `a825f0d`, sem recompilação ou promoção de catálogo.

A [imagem oficial datada](https://cloud-images.ubuntu.com/releases/focal/release-20250516/)
está fixada em `.github/native-images/ubuntu-20.04-amd64.json` por tamanho e
SHA-256 publicado em `SHA256SUMS`. O manifesto de pacotes fornecido pela Canonical
lista kernel 5.4.0-216-generic, glibc 2.31, Python de sistema 3.8 e strace 5.5.
Essas são expectativas para o ensaio, não medições de um guest já executado.
Os bytes publicados ficam preservados em `SHA256SUMS.gz` e
`image-packages.manifest.gz`; seus hashes descomprimidos constam do pin.
O coletor exige Ubuntu 20.04/CPU x64/kernel 5.4/glibc 2.31 e KVM ativo por QMP.
Imagem datada não comprova manutenção ESM ou elegibilidade Pro do executor.

O guest fica sem acesso externo, com SSH limitado ao loopback do runner,
chave efêmera e overlay descartável de 8 GiB para os ambientes Python privados.
Discos, chaves e configuração de usuário não integram os artefatos de revisão.
Downloads ocorrem no host com hashes fixados. Uso normal no guest é sem root:
CPython 3.12.15/3.14.8, venvs com `--copies`, wheel instalado fora do checkout,
preparo/cache, corpus, tracing de rede e recuperação/crash/concorrência.
O Python do SO tem seu hash comparado antes/depois.

Verificações locais concluídas antes do checkpoint:

- 14 contratos focados: separação entre versões, identidade/kernel/libc/KVM,
  limites de imagem, referência commit/run e recusa antes de download/boot.
- Fundação: 278 testes em cada Python 3.12.10/3.14.6, nove skips por execução.
- YAML/Bash dos dois workflows e gramática Python 3.6 dos probes aprovados.
- Preparo real dos dois bundles `a825f0d`, 13 DOTs por ABI e referência de origem
  correta; nenhum ELF foi executado localmente.

Execução CI e medições nativas ainda pendentes nesta preparação. Ubuntu 18.04
mantém seleção e limites próprios e será ensaiado novamente como regressão.
Não há qualificação integral: falta candidata final distribuída, instalação
remota/sdist, elegibilidade Pro, revisão Twine e demais gates por célula.
T033/T037/T076/T078 permanecem abertas, assim como as demais versões e ARM64.
