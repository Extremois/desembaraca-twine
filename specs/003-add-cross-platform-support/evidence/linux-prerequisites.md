# Pré-requisitos Python Linux: evidência parcial

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

### Recuperação instalada no kernel 4.15 — ensaio preparado

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
sem instalação global/VM nova e sem aprovação de célula. Execução no guest CI
com os dois venvs instalados ainda pendente; T076 permanece agregada à matriz.

