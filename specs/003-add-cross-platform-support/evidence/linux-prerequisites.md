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
