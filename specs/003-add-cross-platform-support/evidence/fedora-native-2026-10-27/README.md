# Fedora 43/44 x64 — preparo do ensaio privado nativo

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
partir do host; versão completa será registrada após o boot. Perfis libc
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
passaram. CI ainda pendente nesta preparação.

T039 continua aberta para ARM64, candidata final/remota, sdist, revisão Twine
e os demais gates. Imagem GA fixada não atesta atualização integral, manutenção
ou compatibilidade de futuros updates; não há herança RHEL ou Fedora 45.
