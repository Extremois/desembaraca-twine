# Ubuntu 20.04 x64 — ensaio nativo privado

T033/T037/T076/T078, preparação em 2026-10-27. O ensaio usa exclusivamente
KVM no runner efêmero GitHub x64 já utilizado pelo projeto; não cria VM local.
O workflow `linux-focal-baseline.yml` reutiliza os motores glibc/musl medidos
em `a825f0d`, sem recompilação ou promoção de catálogo.

A [imagem oficial datada](https://cloud-images.ubuntu.com/releases/focal/release-20250516/)
está fixada em `.github/native-images/ubuntu-20.04-amd64.json` por tamanho e
SHA-256 publicado em `SHA256SUMS`. O manifesto de pacotes fornecido pela Canonical
lista kernel 5.4.0-216-generic, glibc 2.31, Python de sistema 3.8 e strace 5.5.
Essas foram as expectativas da preparação, confirmadas no ensaio abaixo.
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

Ubuntu 18.04 mantém seleção e limites próprios e foi ensaiado como regressão.
Não há qualificação integral: falta candidata final distribuída, instalação
remota/sdist, elegibilidade Pro, revisão Twine e demais gates por célula.
T033/T037/T076/T078 permanecem abertas, assim como as demais versões e ARM64.

## Resultados conferidos

Checkpoint `1c556872f4b74af61038ff53acac382ab1eb368a`, três workflows aprovados:
[Ubuntu 20.04](https://github.com/Extremois/desembaraca-twine/actions/runs/40568979583),
[regressão Ubuntu 18.04](https://github.com/Extremois/desembaraca-twine/actions/runs/40568979492)
e [fundação multiplataforma](https://github.com/Extremois/desembaraca-twine/actions/runs/40568980087).
O [resumo](summary.json) registra os quatro artefatos baixados e reconferidos;
os arquivos originais ficam comprimidos com hashes dos bytes descomprimidos.

| Guest x64, KVM ativo | Kernel observado | glibc do guest | ABIs do motor |
| --- | --- | --- | --- |
| Ubuntu 20.04 | 5.4.0-216-generic | 2.31 | glibc e musl |
| Ubuntu 18.04 | 4.15.0-212-generic | 2.27 | glibc e musl |

Os 13 layouts de cada uma das quatro execuções diretas do motor tiveram
inputs/outputs e geometria conferidos localmente. O musl continua estático e
o guest continua Ubuntu; esse resultado não equivale a ensaio nativo Alpine.

Nos dois guests glibc, CPython 3.12.15 e 3.14.8 criaram venvs isoladas, instalaram
o wheel e executaram os três entrypoints. Os 53 arquivos instalados foram
confrontados com os bytes do commit, usando `git show` para não confundir a
normalização CRLF do checkout Windows com alteração do pacote Linux. O Python
do SO manteve o mesmo hash antes/depois.

Por slot Python: 13 casos de corpus, seis referências zeradas, 389 execuções
`dot` observadas por strace e nenhuma syscall de rede no corpus. O controle
positivo de socket/connect no filho foi detectado em cada slot. Aquisição
continua controlada por fixture; não é instalação da candidata final remota.

A [revisão das suítes aninhadas](nested-recovery.json), reproduzível por
[verify-nested-recovery.py](verify-nested-recovery.py), confere oito cenários
externos e oito no driver instalado, com quatro reparos falhos, três crashes
e dois primeiros usos concorrentes por suíte. São 16 execuções/96 referências
offline por slot; no conjunto de quatro slots, **64 execuções de cenários e
384 execuções de referências offline**. Seleção, handles anteriores, locks,
órfãos e aquisição única dos concorrentes passaram nas verificações registradas.

Os seis jobs de fundação executaram 278 testes cada, com oito skips Windows e
seis skips Linux/macOS. A aceitação Windows limpa segue como job skipped.
Índices `linux-ubuntu-other.json`, `recovery.json` e `package-installation.json`
referenciam essa revisão separadamente das anteriores; snapshots anteriores
dos índices alterados ficam preservados aqui. Recibos finais locais, sem
publicação de release ou alteração da matriz oficial.
