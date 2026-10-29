# Wheel/sdist atuais: instalação isolada

O verificador `tools/validation/check-built-packages.py` compara os arquivos
de ambos os formatos com a árvore fonte atual antes de instalar. Exige os
mesmos 53 arquivos Python/dados/avisos e os textos LICENSE/NOTICE do projeto;
rejeita omissões, alterações, duplicação e entradas especiais no sdist.

Cada formato recebe seu próprio venv temporário, fora do checkout, em caminho
com espaços e acentos. As instalações usam `--no-index --no-deps`, com
ferramentas de build previamente obtidas em wheelhouse privado para o sdist.
Os arquivos são copiados para o diretório externo antes da instalação. O
processo consumidor usa `-I`, perfil isolado e PATH restrito ao venv; o probe
confere importação, ausência de Git/Graphviz global, hashes instalados e hash
do arquivo que o pip registra em `direct_url.json`.

São conferidos console, `python -m twine_edge_overlap` e
`python -m twine_edge_overlap.cli`. O help não pode preparar um motor. Os
subprocessos usam o runner limitado da aplicação, com 120 s/8 MiB por comando.
Os diretórios temporários são removidos ao terminar.

```powershell
python tools/validation/check-built-packages.py --dist-dir CAMINHO_DOS_PACOTES --wheelhouse CAMINHO_DOS_WHEELS_DE_BUILD --report CAMINHO_NOVO/resultado.json
```

É necessário um CPython completo com `venv`/`ensurepip`, além de wheels de
setuptools, wheel e packaging no wheelhouse. Nenhuma instalação global é
feita pelo verificador. `--wheel` e `--sdist` também podem indicar os arquivos
explicitamente. O relatório existente não é sobrescrito.

## Ensaios e limites

O primeiro smoke local `windows-3.14.json` passou nos dois formatos. A suíte
de fundação local passou com 244 testes em cada Python 3.12/3.14, oito skips
por execução; inclui os três testes novos de integridade da distribuição.

O Python 3.12 Windows local é embutido e não contém `venv`; essa tentativa
não produziu relatório de instalação. Uma tentativa de reutilizar os arquivos
Windows no WSL parou na leitura do wheel por permissão, antes de instalar;
também não produziu recibo positivo. A matriz CI usa intérpretes completos
e constrói seus próprios arquivos em cada runner.

Checkpoint `4349b88` adicionou o verificador/testes/workflow; o GitHub recusou
o YAML antes dos jobs devido ao argumento `--only-binary=:all:` em escalar
simples. O checkpoint `986518c` corrigiu esse campo para bloco de texto.

As 20 instalações desse checkpoint passaram e seus dez recibos foram baixados
e conferidos em `ci/summary.json`. A fundação detectou uma comparação de
caminhos não canônicos no teste: o temporário pode usar alias `/var` no macOS
ou nome curto no Windows. `23c0663` resolve ambos os lados antes da comparação
e inclui a rejeição de escape por `..`. O checkpoint final precisa passar
novamente tanto na instalação quanto na fundação; os resultados anteriores
não são substituídos.

## Confirmação do checkpoint final

`23c0663` passou no workflow de instalação `39509399309`: **dez combinações,
20 instalações e 60 invocações de entrypoint**. Os dez relatórios foram
baixados, conferidos e preservados em [ci-current/summary.json](ci-current/summary.json).
São 1.060 conferências de arquivos Python/dados/avisos, além de LICENSE/NOTICE
por instalação. Hashes do verificador, revisão, formato e arquivos instalados
foram reconferidos; wheel e sdist de cada combinação instalaram os mesmos bytes.

O workflow de fundação `39509399274` também passou nos seis jobs, com
**239 testes por job**, seis skips nos runners POSIX e oito no Windows.
O [recibo](foundation.json) preserva contagens, versões de imagem, URLs e hashes
dos logs baixados. Os cinco testes glibc de um incremento anterior continuam
locais e não entraram neste checkpoint; por isso a suíte local conta 244.

O índice canônico da T078 está em [package-installation.json](../package-installation.json).
Ele mantém a tarefa parcial, os 69 alvos/138 slots Python no escopo e as
pendências de candidata final remota/motor privado. Recibos finais locais,
aguardando o próximo commit necessário; os três checkpoints de implementação
e correção já foram enviados à branch da spec.

O novo workflow cobre Ubuntu x64/ARM64, macOS 15 ARM64/Intel e Windows
hospedado, com Python 3.12/3.14. Os resultados só contam após baixar e conferir
os relatórios. São pacotes de desenvolvimento e verificações de instalação/
help; não são candidatas finais remotas nem aceite de todos os alvos Linux.
Auditorias de licenças, assinatura, motor privado, offline com motor, Twine e
qualificação por célula permanecem nas tarefas abertas. Catálogo só Windows.
