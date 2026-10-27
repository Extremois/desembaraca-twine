# Pré-requisitos Python Linux: evidência parcial

## Ubuntu 24.04 x64 com imagem fixada — 2026-10-27

O [ensaio KVM conferido](ubuntu2404-native-2026-10-27/README.md) executou
CPython 3.12.15 e 3.14.8 privados no kernel 6.8.0-147/glibc 2.39 da imagem
datada de 17/10/2026. Venv/pip/SSL, wheel externo, três entrypoints,
53 arquivos contra o commit, corpus, rastros e recuperação passaram; o Python
do SO manteve seu hash. Os outros cinco Ubuntu x64 foram repetidos.
Arquivos fixados obtidos pelo host, guest sem internet e transporte privado
controlado, sem VM local. Evidências históricas dos runners x64/ARM64 e
wheel/sdist mantêm sua revisão/escopo; o ensaio novo acrescenta somente wheel
no guest x64 fixado. T033 permanece aberta para as demais células.

## Ubuntu 26.10 x64 nativo — 2026-10-27

O [ensaio KVM conferido](ubuntu2610-native-2026-10-27/README.md) executou
CPython 3.12.15 e 3.14.8 privados no kernel 7.3.0-9/glibc 2.44. Venv/pip/SSL,
wheel externo, três entrypoints, 53 arquivos contra o commit, corpus, rede e
recuperação passaram; o hash do Python do SO permaneceu igual. O Python da
imagem controla o probe e não substitui os slots privados da aplicação.
18.04/20.04/22.04/26.04 foram repetidos. Arquivos fixados obtidos pelo host,
guest sem internet, transporte privado controlado e nenhuma VM local.
T033 permanece aberta para ARM64 e demais famílias/versões da matriz;
modalidades remotas/sdist e candidata final continuam pendentes.

## Ubuntu 26.04 x64 nativo — 2026-10-27

O [ensaio KVM conferido](ubuntu2604-native-2026-10-27/README.md) executou
CPython 3.12.15 e 3.14.8 privados no kernel 7.0.0-38/glibc 2.43. Venv/pip/SSL,
wheel externo, três entrypoints, 53 arquivos contra o commit, corpus, rede e
recuperação passaram; o hash do Python do SO permaneceu igual. O Python
fornecido pela imagem é somente controlador do probe, distinto dos dois slots
da aplicação. 18.04/20.04/22.04 foram repetidos como regressão. Arquivos fixados
obtidos pelo host, guest sem internet e transporte privado controlado; nenhuma
VM local ou instalação global. T033 permanece aberta para ARM64, 26.10 e demais
famílias/versões da matriz.

## Ubuntu 22.04 x64 nativo — 2026-10-27

O [ensaio nativo conferido](ubuntu2204-native-2026-10-27/README.md) cobre
CPython 3.12.15 e 3.14.8 privados em Ubuntu 22.04 x64 com kernel
5.15.0-198/glibc 2.35. Venvs/pip/SSL, wheel externo, três entrypoints,
53 arquivos contra o commit, corpus/rede/recuperação passaram; o Python do SO
conservou seu hash. A mesma revisão repetiu 18.04 e 20.04 como regressão.
Os arquivos dos interpretadores continuam fixados pelos pins abaixo e são
obtidos pelo host, sem instalação global ou rede no guest. Não conclui T033
para a matriz, modalidades remotas/sdist, manutenção, ARM64 ou demais versões.

## Ubuntu 20.04 x64 nativo e regressão 18.04 — 2026-10-27

O [ensaio KVM conferido](ubuntu2004-native-2026-10-27/README.md) executou
CPython 3.12.15 e 3.14.8 privados, fixados pelos mesmos arquivos e hashes abaixo,
em Ubuntu 20.04 x64 com kernel 5.4.0-216/glibc 2.31. Venvs com `--copies`, pip,
SSL/módulos, wheel externo e três entrypoints passaram sem substituir o Python
do SO; seu hash permaneceu igual antes/depois. Ubuntu 18.04 x64 foi repetido
como regressão no kernel 4.15.0-212/glibc 2.27. Fontes instaladas, corpus,
rede nativa e recuperação também foram conferidos. Guest sem internet; arquivos
obtidos pelo host com pins, runtime privado com transporte controlado.
Não comprova elegibilidade Pro/ESM, candidata final, ARM64 ou as demais células.
T033 permanece aberta para a matriz completa.

## Ensaio inicial e procedimento

T033 continua aberta para a matriz inteira. O ensaio abaixo cobre somente o
Ubuntu 26.04 x86_64 no WSL já existente, sem aprovação de célula nativa.

## Procedimento ensaiado

Foram obtidos os builds CPython **3.12.15** e **3.14.8** de
[python-build-standalone, release 20261003](https://github.com/astral-sh/python-build-standalone/releases/tag/20261003),
mantidos pela Astral. São builds de terceiro, não instaladores publicados pelo
projeto CPython. A variante escolhida foi `x86_64-unknown-linux-gnu`, GIL normal,
`install_only_stripped`; não se usou x86_64_v2/v3, musl ou free-threaded.

Os arquivos HTTPS e seus SHA-256 publicados foram conferidos antes de extração.
A extração ocorreu em diretórios privados novos, com verificação de caminhos,
filtro de dados de tar e limites de quantidade/expansão. Não foram substituídos
`/usr/bin/python3`, links do sistema, PATH ou pacotes da distribuição.

| CPython | SHA-256 do arquivo obtido | Resultado |
|---|---|---|
| 3.12.15 | `731af898886c5f821890dc901eca3c651cca8e51fa7308c159d12a1194aeac91` | venv/pip/SSL e módulos padrão verificados |
| 3.14.8 | `d9ec7a6935ade8b671a57ebaf111083d7314eab8dae5071d167054dadd2b97d6` | venv/pip/SSL e módulos padrão verificados |

Com os arquivos extraídos em um diretório privado escolhido pelo executor, usar
o caminho absoluto de cada interpretador, sem ativação nem mudança global:

```sh
"$PYTHON312_ROOT/python/bin/python3" -I -m venv --copies "$TEST_ROOT/venv312"
"$PYTHON314_ROOT/python/bin/python3" -I -m venv --copies "$TEST_ROOT/venv314"
export PIP_CACHE_DIR="$TEST_ROOT/pip-cache"
"$TEST_ROOT/venv312/bin/python" -I -m pip --version
"$TEST_ROOT/venv314/bin/python" -I -m pip --version
```

`PYTHON312_ROOT`/`PYTHON314_ROOT` são diretórios das extrações verificadas;
`TEST_ROOT` deve ser um diretório novo com acesso de escrita/execução. Não apontar
essas variáveis para diretórios do Python do SO. A
[documentação do fornecedor](https://docs.astral.sh/python-build-standalone/distributions/)
descreve os arquivos install-only; requisitos declarados pelo fornecedor não
substituem testes de cada distribuição/arquitetura.

## Resultados e limites

O [registro dos interpretadores](linux-private-python-prerequisites.json) contém
URLs exatas, hashes, tamanhos, patch, arquitetura, pip/ensurepip/OpenSSL e prova de
venv ativa. O hash do Python do sistema permaneceu igual. A fundação passou com
126 testes em cada interpretador privado, com cinco skips em cada execução.

Foram construídos wheel/sdist da árvore atual e feitas quatro instalações locais
em venvs novas fora do checkout: dois formatos × dois Pythons. Console/módulo,
importação da venv e caminhos com espaço/acento passaram. A licença Apache-2.0
foi conferida nos dois formatos e os 29 arquivos de avisos existentes no wheel.
Ver [instalações e hashes](linux-package-installation.json).

O arquivo válido de teste foi recusado com código 1, sem saída, alteração do
original ou aquisição de cache, pois o catálogo distribuído continua somente
Windows. Essa recusa esperada não é aceite de execução Linux. Não houve instalação
remota do projeto, Graphviz global, apt/sudo ou nova VM. As ferramentas de build
foram obtidas do PyPI somente para o ambiente privado; não viraram dependências
de execução do projeto.

O ensaio de sdist usou o cache de wheels de usuário já existente do pip. Isso
não instalou pacotes no Python do sistema, mas deve ser isolado em repetições
com `PIP_CACHE_DIR` privado, como no exemplo acima. Os caminhos pessoais foram
redigidos no log publicado.

As demais células glibc/musl e ARM64, inclusive versões antigas, continuam
pendentes. Não se estende o resultado WSL por parentesco de distro, ABI ou pelo
mínimo glibc anunciado para o interpretador. Em rolling, os dois Pythons devem
estar preparados antes da captura de referência do inventário.

## Alpine: CPython/venv/pip em quatro userlands

O [recibo de 16 slots](alpine-userland-compatibility-2026-10-20/summary.json) confirma CPython oficial, venv/ensurepip e pip sem substituir o Python do SO. Execução em containers efêmeros de imagem fixada, sobre CPU correspondente e kernel do runner; não qualifica o ambiente Alpine nativo nem conclui T033 para as demais distribuições. Aquisição do runtime usa fixture controlada.

| Alpine observado | CPU | CPython | venv/pip | Runtime/rede offline |
| --- | --- | --- | --- | --- |
| 3.21.5 | x86_64 | 3.12.12 | PASS | PASS |
| 3.21.5 | x86_64 | 3.14.1 | PASS | PASS |
| 3.21.5 | aarch64 | 3.12.12 | PASS | PASS |
| 3.21.5 | aarch64 | 3.14.1 | PASS | PASS |
| 3.22.4 | x86_64 | 3.12.13 | PASS | PASS |
| 3.22.4 | x86_64 | 3.14.5 | PASS | PASS |
| 3.22.4 | aarch64 | 3.12.13 | PASS | PASS |
| 3.22.4 | aarch64 | 3.14.5 | PASS | PASS |
| 3.23.6 | x86_64 | 3.12.15 | PASS | PASS |
| 3.23.6 | x86_64 | 3.14.8 | PASS | PASS |
| 3.23.6 | aarch64 | 3.12.15 | PASS | PASS |
| 3.23.6 | aarch64 | 3.14.8 | PASS | PASS |
| 3.24.2 | x86_64 | 3.12.15 | PASS | PASS |
| 3.24.2 | x86_64 | 3.14.8 | PASS | PASS |
| 3.24.2 | aarch64 | 3.12.15 | PASS | PASS |
| 3.24.2 | aarch64 | 3.14.8 | PASS | PASS |

## Ensaio nativo Ubuntu 18.04 x64 — aprovado em 2026-10-20

O workflow `linux-baseline.yml` passou a levar os mesmos dois arquivos CPython
3.12.15/3.14.8 já fixados no ensaio WSL ao guest KVM Ubuntu 18.04 x64.
Os pins independentes estão em `.github/native-images/private-python-x64.json`.
O host efêmero baixa os arquivos via HTTPS e verifica tamanho/SHA-256; o guest,
sem acesso à internet, reconfere os arquivos e os extrai em diretórios privados.
Não há instalação de Python no sistema nem inclusão desses interpretadores nos
pacotes do projeto.

A rotina exige os patches exatos, CPython x64 de 64 bits com GIL, venv com cópias
em caminho Unicode com espaços, pip/ensurepip, SSL e contexto de certificados,
além da importação de ctypes/sqlite3/zlib. Compara o hash do Python do sistema
antes/depois. O relatório é conferido pelo host e seu hash fica vinculado à
medição de kernel/glibc/KVM do mesmo guest. A execução nativa passou no workflow
`39473344773`, revisão `cc0cc76`, e os arquivos baixados foram reconferidos em
[ubuntu1804-native-python-2026-10-20/summary.json](ubuntu1804-native-python-2026-10-20/summary.json).
Os dois interpretadores, venv/pip/SSL e módulos nativos passaram; o Python do SO
manteve o hash. Os resultados WSL anteriores continuam identificados separadamente.
O corpus de 13 grafos por ABI foi executado pelo probe do motor no Python 3.6
do guest, sem representar execução da aplicação instalada nos novos venvs.
T033/T037 permanecem abertas para a
matriz completa, elegibilidade Pro e percurso da aplicação instalada.

### Aplicação instalada no mesmo guest — aprovado em 2026-10-20

O modo `--python-application` constrói um wheel de desenvolvimento da revisão
do workflow, registra SHA-256/arquivos e instala esse wheel offline nos dois
venvs privados. O driver leva somente helpers/fixtures de teste ao guest, sem
`src/`, e exige importação do venv, hashes dos arquivos instalados e os três
entrypoints. Reutiliza `test_linux_runtime.py` com o motor privado real para
preparo automático/explícito, corpus de 13 casos, seis referências zeradas,
preservação, permissões, caminhos Unicode e cache sem nova aquisição.

A transferência inicial do motor continua controlada por fixture; o bloqueio
de sockets do teste observa Python, sem substituir tracing nativo de rede.
O wheel mantém o catálogo público atual, somente Windows. O workflow
`39474628694`, revisão `ec14368`, passou e foi reconferido após download:
53 arquivos do wheel coincidem com o commit; CPython 3.12.15/3.14.8 passaram
os 13 casos cada, incluindo as seis referências zeradas e preparo automático/
explícito. Cada modo fez uma aquisição controlada inicial e nenhuma no cache
íntegro. O Python do SO manteve o hash. Os seis jobs da regressão `39474628708`
passaram com 234 testes cada.
[Recibos](ubuntu1804-installed-wheel-2026-10-20/summary.json).
Isso avança T037/T078 parcialmente e não aprova pacote final, elegibilidade
Pro, tracing nativo de rede, Twine, recuperação completa ou demais células.

### Observação nativa de rede no kernel 4.15 — aprovada em 2026-10-20

O manifesto público da imagem fixada lista `strace 4.21-1ubuntu1`; a rotina usa
esse executável já presente no guest, sem instalar tracer ou substituir Python.
O filtro `%network,execve` e `-f` acompanham a aplicação e seus filhos. Um controle
separado deve detectar `socket`/`connect` num filho real, antes de exigir zero
chamadas de rede durante preparo controlado/corpus/cache. Os traces brutos serão
reconferidos no host e vinculados aos relatórios por SHA-256.

Essa versão do tracer não oferece `--kill-on-exit`; isso fica explícito no
relatório. O encerramento do guest efêmero pertence ao `finally` do driver host,
inclusive após falha. O teste não promete contenção de código hostil.

Workflow `39480928288`, revisão `c8f881c`, aprovado. Os traces baixados foram
reprocessados independentemente: em cada CPython 3.12.15/3.14.8, o controle
detectou socket/connect/getsockopt em filho real; o corpus executou o motor
49 vezes e registrou zero chamadas da classe de rede. Os 13 casos por Python,
seis referências zeradas, preparo automático/explícito e cache continuaram
aprovados. Os 53 arquivos do wheel coincidem com o commit; Python do SO preservado.
Seis jobs de regressão `39480928185` passaram com 235 testes cada.
[Recibos e traces](ubuntu1804-native-network-2026-10-20/summary.json).

O pacote no manifesto da imagem é `4.21-1ubuntu1`, mas o binário se identifica
literalmente como `strace -- version UNKNOWN`. O recibo preserva os dois fatos,
o SHA-256 do executável, o manifesto e a imagem fixada, sem inventar versão.
As duas tentativas anteriores falharam na consulta/comparação da versão antes
do tracing e têm recibos/logs separados. T037/T078/T080 continuam parciais;
distribuição final, Pro, Twine e demais gates/células permanecem nesta spec.

### Recuperação instalada no kernel 4.15 — aprovada em 2026-10-20

O driver de recuperação acrescenta oito cenários à aplicação instalada sob
tracing: transferência falha, ENOSPC injetado, negação real de execução por modo
do arquivo, arquivo corrompido, morte via `os._exit(77)` durante aquisição/antes/
depois da seleção e dois processos de primeiro uso concorrentes. Cada cenário
exige seis referências offline e um handle anterior ainda utilizável. Os crashes
devem liberar o lock do SO; concorrência deve adquirir uma vez e escolher a mesma
geração; um staging órfão de outro processo deve permanecer intocado.

Todos os caminhos e caches pertencem a diretórios temporários de teste. Rede,
erro ENOSPC e bytes corrompidos são injeções declaradas; motor, permissões,
publicação, processos e locks são reais. O pré-ensaio no WSL existente é parcial,
sem instalação global/VM nova e sem aprovação de célula.

O workflow `39486677086`, revisão `58f69b0`, passou no guest Ubuntu 18.04 x64
com CPython 3.12.15/3.14.8 instalados. Artefatos baixados e reconferidos: oito
cenários, 48 referências offline e 245 execuções do motor por Python, sem
syscalls de rede no corpus ampliado e com controle positivo detectado. Crashes
liberaram locks e respeitaram a seleção antes/depois da publicação; staging
órfão permaneceu intocado. Os dois concorrentes compartilharam uma aquisição/
geração e o cache funcionou offline depois. Handles anteriores e Python do SO
preservados; 53 arquivos do wheel conferidos contra o commit. Seis jobs de
regressão `39486677078` passaram com 236 testes cada.
[Recibos e traces](ubuntu1804-installed-recovery-2026-10-20/summary.json).
T076 permanece agregada à matriz: candidata remota final, outras células e
gates comuns continuam pendentes, sem promoção ou alteração do catálogo.

## Estratégia de obtenção de CPython 3.12 e 3.14 por família da matriz (T033)

Conforme estabelecido em `contracts/support-policy.md` e na tarefa T033, a obtenção dos interpretadores CPython 3.12 e 3.14 para qualificação e uso do `desembaraca-twine` em qualquer distribuição Linux deve obedecer estritamente aos seguintes princípios:
1. **Não substituição do Python do SO**: `/usr/bin/python3`, symlinks do sistema e bibliotecas em `/usr/lib/python*` nunca devem ser modificados, substituídos ou desinstalados. O SHA-256 do binário de sistema deve ser registrado antes e depois dos ensaios.
2. **Sem exigência de `sudo` no uso normal**: a execução e a criação de ambientes virtuais devem ocorrer inteiramente no espaço de usuário do executor (`$HOME` ou diretório de trabalho de teste).
3. **Não exclusão de versões antigas**: versões LTS mais antigas (como Ubuntu 18.04/20.04, RHEL 8, Debian 12) onde o Python padrão do SO é inferior a 3.12 utilizam interpretadores privados isolados (como `python-build-standalone`), sem exigir pacotes globais ou compilação local complexa.
4. **Isolamento de venv e pip**: ambientes virtuais devem ser criados com `--copies` para evitar links frágeis para interpretadores voláteis, e `PIP_CACHE_DIR` deve apontar para diretório privado temporário para evitar contaminação do cache do usuário.
5. **Pré-requisito em distribuições rolling**: em Arch Linux, openSUSE Tumbleweed e Manjaro, ambos os interpretadores (3.12 e 3.14) devem estar instalados e testados antes da captura canônica do fingerprint de inventário de pacotes.

### Taxonomia por família de distribuição

| Família | Versões da matriz | Python padrão do SO | Obtenção do slot 3.12 | Obtenção do slot 3.14 | Método de isolamento recomendado |
|---|---|---|---|---|---|
| **Ubuntu** | 24.04 (Noble) | 3.12.x | Padrão do sistema (`/usr/bin/python3`) | Standalone em `$HOME/.local/python314` | `venv --copies`, sem `sudo` |
| **Ubuntu** | 22.04, 20.04, 18.04 | 3.10, 3.8, 3.6 | Standalone em `$HOME/.local/python312` | Standalone em `$HOME/.local/python314` | Extração isolada `install_only_stripped` |
| **Ubuntu** | 26.04, 26.10 | 3.13 / 3.14 | Standalone ou pacote compatível | Padrão do sistema (`python3`) | `venv --copies` |
| **Debian** | 12 (Bookworm) | 3.11.x | Standalone em `$HOME/.local/python312` | Standalone em `$HOME/.local/python314` | Extração de usuário sem alterar `apt` |
| **Debian** | 13 (Trixie) | 3.12 / 3.13 | Padrão do sistema (`python3.12`) | Standalone em `$HOME/.local/python314` | `venv --copies` |
| **Fedora** | 43, 44 | 3.13 / 3.14 | Pacote oficial `python3.12` ou standalone | Padrão do sistema (`python3.14`) | Instalação paralela de repositório ou standalone |
| **RHEL / Rocky / Alma** | 8.10 | 3.6.8 | Standalone em `$HOME/.local/python312` | Standalone em `$HOME/.local/python314` | Extração de usuário, glibc 2.28 compatível |
| **RHEL / Rocky / Alma** | 9.8 | 3.9.x | AppStream `python3.12` ou standalone | Standalone em `$HOME/.local/python314` | AppStream paralelo ou standalone |
| **RHEL / Rocky / Alma** | 10.2 | 3.12.x | Padrão do sistema (`python3`) | Standalone em `$HOME/.local/python314` | `venv --copies` |
| **openSUSE** | Leap 16.0 | 3.12.x | Padrão do sistema (`python3`) | Standalone em `$HOME/.local/python314` | `venv --copies` |
| **openSUSE** | Tumbleweed | Rolling | Pacote `python312` ou standalone | Pacote `python314` ou standalone | Preparo pré-snapshot rolling |
| **Arch / Manjaro** | Rolling / Stable | Rolling | Pacote oficial ou standalone | Pacote oficial ou standalone | Preparo pré-snapshot `pacman -Q` |
| **Alpine Linux** | 3.21, 3.22, 3.23, 3.24 | 3.12 / 3.14 | `apk add python3 py3-pip` (3.12) | Repositório `testing` ou standalone musl | venv isolada com ensurepip |
| **Mint / LMDE** | Mint 21/22, LMDE 7 | 3.10 / 3.12 | Segue base Ubuntu/Debian correspondente | Standalone em `$HOME/.local/python314` | `venv --copies`, sem `sudo` |
| **postmarketOS** | v26.06 Generic | Alpine edge | Repositório `apk` oficial | Repositório `apk` oficial | venv isolada sem sobrescrever sistema |

### Padrão de execução para scripts de qualificação

Em cada ambiente, a criação das venvs de qualificação deve seguir a seguinte sequência determinística:

```sh
# 1. Definir caminhos isolados
WORK_DIR="$(mktemp -d /tmp/twine-python-qual.XXXXXX)"
VENV_312="$WORK_DIR/venv312"
VENV_314="$WORK_DIR/venv314"
export PIP_CACHE_DIR="$WORK_DIR/pip-cache"

# 2. Registrar hash do Python do sistema antes
SYSTEM_PYTHON_SHA_BEFORE="$(sha256sum /usr/bin/python3 2>/dev/null | awk '{print $1}' || true)"

# 3. Criar venvs com isolamento estrito (--copies)
"$PY312_BIN" -I -m venv --copies "$VENV_312"
"$PY314_BIN" -I -m venv --copies "$VENV_314"

# 4. Validar pip e módulos fundamentais
"$VENV_312/bin/python" -I -m pip --version
"$VENV_314/bin/python" -I -m pip --version
"$VENV_312/bin/python" -I -c "import ctypes, sqlite3, ssl, zlib; print('Python 3.12 stdlib OK')"
"$VENV_314/bin/python" -I -c "import ctypes, sqlite3, ssl, zlib; print('Python 3.14 stdlib OK')"

# 5. Conferir que o Python do sistema permaneceu rigorosamente inalterado
SYSTEM_PYTHON_SHA_AFTER="$(sha256sum /usr/bin/python3 2>/dev/null | awk '{print $1}' || true)"
if [ "$SYSTEM_PYTHON_SHA_BEFORE" != "$SYSTEM_PYTHON_SHA_AFTER" ]; then
    echo "ERRO: O Python do sistema foi modificado!" >&2
    exit 1
fi
```
