# Ledger integral de suporte

Gerado por `tools/runtime/report-support.py`; status derivado dos slots e evidências, sem alterar o registro.
Contagens de tarefas são rastreabilidade de trabalho, não aprovação de requisitos ou ambientes.

69 células; 138 slots Python; estados: {'pendente': 69}.

T066/T051/T052: alinhamento do índice de integridade de distribuição e requisitos macOS.
O [índice consolidado](distribution-integrity.json) registra a conclusão da revisão de aplicabilidade
de licenças por componente (ColorBrewer, musl libc/math, glibc startup/nonshared §6(a)/§6(d),
Go math/tan e entidades HTML/SVG/ISO 8879:1986 sob W3C/ASF), restando apenas a vinculação final
da entrega de fontes correspondentes e os pacotes finais distribuídos.
O ledger [macos.json](../../tools/runtime/licenses/macos.json) incorpora a especificação formal de requisitos
de assinatura Developer ID Application e notarização via `tools/runtime/sign-macos.sh` sob proteções normais
do Gatekeeper (com quarentena preservada). 69 células; 138 slots Python; estados: {'pendente': 69}; 57/84.

T030: [revisão de entidades e condições ISO concluída](../../tools/runtime/licenses/LINUX-COMPONENT-REVIEW.md)
no checkpoint `8d0b35c`: declarada a aplicabilidade das entidades HTML/SVG e encerrada a pendência
ISO 8879:1986 no ledger `linux.json`. Dados factuais de mapeamento de caracteres sob W3C Software
Notice and License e precedente ASF LEGAL-386 / NETBEANS-853 compatíveis com EPL-2.0 e Apache-2.0.
Avisos textuais integrais preservados em `W3C-HTML401-ENTITY-DECLARATION-NOTICES.txt`. Relink glibc
§6(a) comprovado no checkpoint `bead45d` e `document_sha256` de `SOURCE-DELIVERY-REVIEW.md` alinhado.
Entrega equivalente de fontes correspondentes na rota §6(d)/EPL-2.0 §3.1 e gates de plataforma permanecem abertos; 57/84.

T066: a [medição independente dos caches](cache-notices-more-2026-10-20/README.md)
agora cobre as sete variantes glibc/musl/macOS/Windows, 14 slots Python e 28
instalações wheel/sdist: 9.792 comparações de arquivos, 28 alterações recusadas
e restaurações exatas. Musl mantém escopo de container Alpine em CPU nativa e
Windows de runner hospedado; não substituem aceites de célula. Licenças/fontes,
artefatos finais e demais gates continuam pendentes. Estados preservados, 57/84.

T066: [medição independente dos avisos em cache](cache-notices-2026-10-20/README.md)
aprovada em oito slots glibc/macOS, wheel/sdist: 6.076 arquivos antes/depois,
16 corrupções recusadas e restaurações exatas, nenhuma aquisição offline. O
[índice consolidado](distribution-integrity.json) preserva a conferência anterior
dos seis bundles e registra cache musl/Windows, compatibilidade/fontes e pacotes
finais ainda pendentes. Estados preservados; 57/84, sem promoção POSIX.

T066: [conferência offline da distribuição](distribution-integrity-2026-10-20/README.md)
registrada para os seis bundles POSIX, sem alterar estados. São 2.419 arquivos
e 2.407 avisos com bytes/índice conferidos, além do wheel/sdist e oito recibos
instalados vinculados por hash. Aplicabilidade de licenças, fontes/retensão,
cache independente/Windows e pacotes finais permanecem gates abertos; 57/84.

T076: [crash/concorrência nos pacotes instalados](installed-posix-processes-2026-10-20/README.md)
aprovados nos oito slots Ubuntu 24.04/macOS, wheel/sdist. A rodada totaliza 128
cenários/768 referências após falhas, com barreira de prontidão, uma aquisição,
seletores/locks e bytes/modos do staging órfão conferidos. O [índice atual](recovery.json)
retira crash/concorrência das pendências desses ensaios privados, preservando
distribuição final, ambientes canônicos e demais células. Sem promoção, 57/84.

T076: o [índice de recuperação](recovery.json) registra observações nativas
parciais em cinco células/dez slots. A rodada instalada Ubuntu 24.04/macOS
passou em 64 reparos falhos/384 referências offline, wheel/sdist nos dois
Pythons. [Recibos e limites](installed-posix-recovery-2026-10-20/README.md).
Crash/concorrência nos novos runners, candidata final, demais ambientes e gates
comuns continuam pendentes; estados da matriz preservados, total 57/84.

| Alvo | Estado agregado | Python 3.12 | Python 3.14 | Imagem nativa | Artefato qualificado | US1 AC1–3 |
|---|---|---|---|---|---|---|
| `windows-11-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | não se aplica |
| `macos-15-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | não se aplica |
| `macos-15-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | não se aplica |
| `ubuntu-18.04-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `ubuntu-18.04-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `ubuntu-20.04-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `ubuntu-20.04-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `ubuntu-22.04-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `ubuntu-22.04-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `ubuntu-24.04-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `ubuntu-24.04-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `ubuntu-26.04-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `ubuntu-26.04-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `ubuntu-26.10-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `ubuntu-26.10-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `debian-12-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `debian-12-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `debian-13-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `debian-13-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `fedora-43-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `fedora-43-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `fedora-44-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `fedora-44-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `rhel-8.10-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `rhel-8.10-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `rhel-9.8-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `rhel-9.8-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `rhel-10.2-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `rhel-10.2-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `rocky-8.10-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `rocky-8.10-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `rocky-9.8-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `rocky-9.8-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `rocky-10.2-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `rocky-10.2-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `almalinux-8.10-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `almalinux-8.10-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `almalinux-9.8-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `almalinux-9.8-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `almalinux-10.2-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `almalinux-10.2-stable-x86_64-x86-64-v2` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `almalinux-10.2-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `opensuse-leap-16.0-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `opensuse-leap-16.0-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `opensuse-tumbleweed-rolling-tumbleweed-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `opensuse-tumbleweed-rolling-tumbleweed-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `arch-rolling-rolling-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `archarm-rolling-rolling-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `manjaro-rolling-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `manjaro-rolling-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `alpine-3.21-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `alpine-3.21-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `alpine-3.22-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `alpine-3.22-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `alpine-3.23-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `alpine-3.23-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `alpine-3.24-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `alpine-3.24-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `postmarketos-26.06-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `postmarketos-26.06-stable-aarch64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `linuxmint-21-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `linuxmint-21.1-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `linuxmint-21.2-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `linuxmint-21.3-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `linuxmint-22-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `linuxmint-22.1-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `linuxmint-22.2-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `linuxmint-22.3-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |
| `linuxmint-lmde-7-stable-x86_64-distribution-default` | pendente | pendente | pendente | pendente | pendente | pendentes |

## Evidência parcial e limites

- Windows: regressão nos dois Pythons e coletor em venv externa, com código não commitado; Windows limpo e Twine pendentes.
- Ubuntu 26.04 x86_64 WSL: fundação e corpus de biblioteca com build experimental GLIBC_2.38; não aprova uma célula nativa.
- Demais imagens/arquiteturas: não disponíveis nesta sessão; nenhum resultado herdado de outra distribuição/ABI.
- Linux US1 AC1 (instalação/primeiro uso), AC2 (offline) e AC3 (compatibilidade/aviso) ainda exigem ensaio da célula com ambos os Pythons.
- Logs/digests de imagem, rede nativa, falhas, licenças e seis reaberturas Twine precisam estar completos antes de promover.

## FR-001–018 e SC-001–010

| Requisito | Tarefas relacionadas | Tarefas verificadas | Gate de encerramento |
|---|---|---|---|
| FR-001 | T007, T008, T009, T010, T011, T012, T013, T014, T015, T016, T017, T018, T019, T020, T024, T025, T026, T027, T028, T029, T030, T031, T032, T033, T034, T036, T037, T038, T039, T040, T041, T042, T043, T044, T045, T049, T050, T051, T052, T053, T054, T055, T056 | 25/43 | pendente: evidências específicas e matriz completa |
| FR-002 | T007, T008, T009, T010, T011, T012, T013, T014, T015, T016, T017, T018, T019, T020, T024, T025, T026, T027, T028, T029, T030, T031, T032, T033, T034, T036, T037, T038, T039, T040, T041, T042, T043, T044, T045, T049, T050, T051, T052, T053, T054, T055, T056 | 25/43 | pendente: evidências específicas e matriz completa |
| FR-003 | T002, T013, T032, T033, T070, T074, T075, T081, T082 | 7/9 | pendente: evidências específicas e matriz completa |
| FR-004 | T018, T022, T033, T035, T047, T055, T078, T079 | 6/8 | pendente: evidências específicas e matriz completa |
| FR-005 | T021, T023, T036, T037, T038, T039, T040, T041, T042, T043, T044, T045, T048, T056, T062, T076 | 3/16 | pendente: evidências específicas e matriz completa |
| FR-006 | T036, T037, T038, T039, T040, T041, T042, T043, T044, T045, T056, T057, T062, T063 | 2/14 | pendente: evidências específicas e matriz completa |
| FR-007 | T036, T037, T038, T039, T040, T041, T042, T043, T044, T045, T056, T057, T062, T063 | 2/14 | pendente: evidências específicas e matriz completa |
| FR-008 | T058, T059, T060, T061, T064, T065, T067, T068, T069, T070, T071, T072, T073 | 12/13 | pendente: evidências específicas e matriz completa |
| FR-009 | T058, T059, T060, T061, T064, T065, T067, T068, T069, T070, T071, T072, T073 | 12/13 | pendente: evidências específicas e matriz completa |
| FR-010 | T010, T015, T016, T067, T068, T069, T070, T071, T072, T073, T074, T075, T076, T077 | 13/14 | pendente: evidências específicas e matriz completa |
| FR-011 | T010, T015, T016, T067, T068, T069, T070, T071, T072, T073, T074, T075, T076, T077 | 13/14 | pendente: evidências específicas e matriz completa |
| FR-012 | T018, T022, T033, T035, T047, T055, T078, T079 | 6/8 | pendente: evidências específicas e matriz completa |
| FR-013 | T001, T004, T012, T021, T064, T065 | 5/6 | pendente: evidências específicas e matriz completa |
| FR-014 | T019, T020, T030, T031, T049, T050, T051, T052, T066, T080 | 5/10 | pendente: evidências específicas e matriz completa |
| FR-015 | T011, T032, T062, T071, T080 | 5/5 | pendente: evidências específicas e matriz completa |
| FR-016 | T003, T036, T037, T038, T039, T040, T041, T042, T043, T044, T045, T046, T056, T062, T063, T064, T065, T066, T076, T078, T079, T080, T081, T082, T083, T084 | 7/26 | pendente: evidências específicas e matriz completa |
| FR-017 | T002, T013, T032, T033, T070, T074, T075, T081, T082 | 7/9 | pendente: evidências específicas e matriz completa |
| FR-018 | T002, T013, T032, T033, T070, T074, T075, T081, T082 | 7/9 | pendente: evidências específicas e matriz completa |
| SC-001 | T022, T023, T024, T025, T026, T027, T028, T029, T030, T031, T032, T033, T034, T035, T036, T037, T038, T039, T040, T041, T042, T043, T044, T045, T046, T047, T048, T049, T050, T051, T052, T053, T054, T055, T056, T078, T079 | 17/37 | pendente: evidências específicas e matriz completa |
| SC-002 | T057, T058, T059, T060, T061, T062, T063, T064, T065, T066 | 7/10 | pendente: evidências específicas e matriz completa |
| SC-003 | T057, T058, T059, T060, T061, T062, T063, T064, T065, T066 | 7/10 | pendente: evidências específicas e matriz completa |
| SC-004 | T022, T023, T024, T025, T026, T027, T028, T029, T030, T031, T032, T033, T034, T035, T036, T037, T038, T039, T040, T041, T042, T043, T044, T045, T046, T047, T048, T049, T050, T051, T052, T053, T054, T055, T056, T078, T079 | 17/37 | pendente: evidências específicas e matriz completa |
| SC-005 | T067, T068, T069, T070, T071, T072, T073, T074, T075, T076, T077 | 10/11 | pendente: evidências específicas e matriz completa |
| SC-006 | T057, T058, T059, T060, T061, T062, T063, T064, T065, T066 | 7/10 | pendente: evidências específicas e matriz completa |
| SC-007 | T022, T023, T024, T025, T026, T027, T028, T029, T030, T031, T032, T033, T034, T035, T036, T037, T038, T039, T040, T041, T042, T043, T044, T045, T046, T047, T048, T049, T050, T051, T052, T053, T054, T055, T056, T078, T079 | 17/37 | pendente: evidências específicas e matriz completa |
| SC-008 | T002, T003, T070, T074, T075, T081, T082, T083, T084 | 6/9 | pendente: evidências específicas e matriz completa |
| SC-009 | T002, T003, T070, T074, T075, T081, T082, T083, T084 | 6/9 | pendente: evidências específicas e matriz completa |
| SC-010 | T002, T003, T070, T074, T075, T081, T082, T083, T084 | 6/9 | pendente: evidências específicas e matriz completa |

## T078: instalação atual de wheel e sdist

A [integração instalada com motor privado](installed-private-engines-2026-10-20/runtime/summary.json)
acrescenta 16 instalações e 208 casos/96 referências zeradas nos quatro hosts
POSIX, com ambos os Pythons e formatos. Primeiro uso/cache/probe/permissões
foram reais; obtenção e observação de rede permanecem controlada/Python.
Os índices [Ubuntu](linux-ubuntu-24.04.json), [macOS](macos.json) e
[instalação](package-installation.json) não promovem células nem fecham as
tarefas agregadas. T036/T048/T056/T078 continuam parciais; 57/84.

[Dez combinações hospedadas](current-packages-2026-10-20/ci-current/summary.json)
passaram em ambos os formatos, com vinte instalações externas e hashes
conferidos. O [índice canônico](package-installation.json) mantém T078 parcial
para candidatas finais e a matriz inteira; nenhuma célula foi promovida.
Fundação do mesmo commit aprovada nos seis jobs, 239 testes por job.

## T080: auditoria dos mecanismos concluída

57/84 tarefas concluídas; 27 pendentes. A revisão atual está em
[security-audit-2026-10-20/README.md](security-audit-2026-10-20/README.md).
Qualificação nativa, pacotes finais e catálogo POSIX continuam pendentes.
As notas históricas abaixo preservam suas contagens e estados originais.

## Baseline glibc x64 confirmado em kernel antigo

[Ubuntu 18.04 x64 em KVM no CI](ubuntu1804-native-engine-baseline-2026-10-20/summary.json)
fecha T024: kernel 4.15.0-212, glibc 2.27, loader/CPU registrados e o mesmo motor
glibc aprovado nos 13 probes de geometria. Não é aceite da aplicação no Python
3.12/3.14, não confirma elegibilidade Ubuntu Pro nem revisão Twine e não altera
qualificação/catálogo. O [preflight KVM](kvm-preflight-2026-10-20/summary.json)
identificou API acessível com elevação no runner x64 e ausência de dispositivo
no ARM64 atribuído. Todas as distribuições e arquiteturas permanecem na spec.
Progresso de tarefas: 55/84, com 29 pendentes; células qualificadas permanecem
inalteradas. A VM de teste foi criada somente no runner efêmero GitHub.

## Receita musl x64: cobertura e kernel mínimo

A [revisão T026](linux-x64-kernel-baselines-2026-10-20/musl-recipe-completion.json)
combina oito slots Alpine x64 já observados com execução do mesmo ELF estático
no kernel Linux 4.15 nativo em KVM. Fecha a receita privada T026, com fonte/SDK,
hash/proveniência e limites conferidos, sem reutilizar o binário glibc.
O ambiente do novo kernel é Ubuntu e os ensaios Alpine continuam containers:
essa separação é explícita e não promove T044 nem qualquer célula de suporte.
ARM64, auditoria/fontes/catálogo e aceite instalado continuam pendentes.
Progresso: 56/84 tarefas; 28 pendentes, sem alteração das células qualificadas.
# Pré-requisitos Ubuntu 18.04 x64 — 2026-10-20

CPython 3.12.15/3.14.8 privados aprovados no guest KVM Ubuntu 18.04 x64,
kernel 4.15.0-212/glibc 2.27, com venv/pip/SSL e módulos nativos, preservando
o hash do Python do SO. Workflow `39473344773`, revisão `cc0cc76`, aprovado.
Motores glibc/musl preservados, 13 geometrias cada reconferidas após download;
o corpus usou Python 3.6 para o probe do motor, sem aplicação instalada nos venvs.
Regressão `39473344641`: seis combinações aprovadas, 233 testes por job.
[Recibo](ubuntu1804-native-python-2026-10-20/summary.json).
T033/T037 parciais, demais células/elegibilidade Pro/aplicação instalada pendentes.
Nenhuma promoção; catálogo Windows, 56/84 tasks. Checkpoint enviado `cc0cc76`;
recibos finais ficam locais para o próximo commit necessário.

## Wheel instalado no Ubuntu 18.04 x64 — 2026-10-20

Ensaio nativo KVM `39474628694`, revisão `ec14368`, aprovado: CPython 3.12.15/
3.14.8, wheel de desenvolvimento instalado offline, 53 arquivos conferidos
contra o commit e três entrypoints. Gerenciador/motor reais, preparo automático/
explícito, 13 casos por Python com seis referências zeradas, preservação,
permissões, caminhos Unicode e cache sem nova aquisição. Python do SO preservado.
Seis jobs da regressão `39474628708` aprovados com 234 testes cada.
[Recibo](ubuntu1804-installed-wheel-2026-10-20/summary.json).

Aquisição inicial controlada e observação de sockets somente Python; não aprova
candidata remota final, tracing nativo, Pro, Twine ou recuperação completa.
T037/T078 avançaram parcialmente, demais células mantidas; nenhuma promoção,
catálogo Windows e 56/84 tasks. Checkpoint enviado; recibos finais locais.

## Observação nativa de rede Ubuntu 18.04 x64 — 2026-10-20

Revisão `c8f881c`, workflow `39480928288`, aprovado: traces brutos reconferidos
para os dois Pythons privados do guest KVM. Controle socket/connect/getsockopt
detectado em filho; 49 execuções do motor por Python, zero syscalls de rede no
corpus/preparo controlado/cache. Treze casos e seis referências zeradas por
Python, wheel/53 arquivos conferidos contra commit, Python do SO preservado.
Seis jobs `39480928185` aprovados com 235 testes cada.
[Recibo e traces](ubuntu1804-native-network-2026-10-20/summary.json).

Pacote do tracer `4.21-1ubuntu1` segundo manifesto; autoidentificação `UNKNOWN`
preservada com hash real. Duas tentativas anteriores falharam antes do tracing,
sem qualificação. Sem kill-on-exit; encerramento pertence ao guest efêmero sob
controle do host. T037/T078/T080 parciais, candidata remota final/Pro/Twine/
demais gates e células pendentes. Catálogo Windows; 56/84 tasks. Checkpoints
necessários enviados; recibos finais ficam locais até o próximo necessário.

## Recuperação com aplicação instalada — Ubuntu 18.04 x64, 2026-10-20

Revisão `58f69b0`, workflow `39486677086`, aprovado e artefatos reconferidos:
oito cenários por Python 3.12.15/3.14.8, wheel instalado, motor privado real.
Quarenta e oito referências offline por Python, handles antigos utilizáveis,
locks liberados após três crashes, seleção atômica respeitada, staging órfão
preservado. Dois primeiros usos concorrentes compartilharam aquisição/geração.
Negação de execução é real; transferência/ENOSPC/bytes corrompidos são injetados.
Traces ampliados: 245 execuções do motor e zero syscalls de rede por Python,
com controle positivo. Cinquenta e três arquivos do wheel conferidos contra o
commit; Python do SO preservado. Seis jobs `39486677078` com 236 testes aprovados.
[Recibo](ubuntu1804-installed-recovery-2026-10-20/summary.json).

Pré-ensaio WSL separado. T076/T037/T078/T080 parciais; outras células, candidata
remota final, Pro e gates comuns permanecem pendentes. Sem promoção, catálogo
Windows; 56/84. Um checkpoint necessário enviado; recibos finais locais.

