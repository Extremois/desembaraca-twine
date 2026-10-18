# Como contribuir

Consulte a [especificação](specs/002-manage-layout-runtime/spec.md), o
[plano](specs/002-manage-layout-runtime/plan.md), as [tarefas](specs/002-manage-layout-runtime/tasks.md)
e a [constituição](.specify/memory/constitution.md).

## Desenvolvimento e testes

Use Windows 11 x64 com CPython 3.12 x64 ou 3.14 x64, conforme o [README](README.md).
O fluxo pelo checkout usa somente a biblioteca padrão. Na raiz:

```powershell
python run.py --version
python -m compileall -q src tests run.py
```

Exemplos de testes isolados sem download, descobertos a partir de `tests` para
manter os helpers no caminho:

```powershell
python -m unittest discover -s tests -p 'test_runtime_archives.py' -v
python -m unittest discover -s tests -p 'test_runtime_repair.py' -v
python -m unittest discover -s tests -p 'test_cli_runtime.py' -v
```

Os testes unitários usam ZIP/transporte controlados de `tests/runtime_support.py`.
Integração e referências exigem o motor nativo fixado; prepare online e execute:

```powershell
python run.py --prepare-runtime
python -m unittest discover -s tests -v
```

Com cache saudável, a suíte funciona offline. Casos específicos interceptam conexões
e falham se houver tentativa. Motor real ausente não é convertido em sucesso ou skip.
Concorrência usa processos Windows reais com payload controlado: prova lock/publicação,
não portabilidade do ZIP nativo. Registre versões e limitações em
[validation.md](specs/002-manage-layout-runtime/validation.md). Siga o
[quickstart](specs/002-manage-layout-runtime/quickstart.md) para máquina limpa e Twine;
cache vazio no computador do desenvolvedor não é máquina limpa.

## Manifesto e dependências

O runtime é fixado em `src/twine_edge_overlap/runtime-manifest.json`.
Não consultar latest/checksum remoto ou Graphviz global durante o processamento.
Para atualizar deliberadamente:

1. Obtenha ZIP/checksum oficiais e compare SHA-256 calculado localmente. Mantenha
   binários em temporários ignorados, nunca no repositório ou wheel/sdist.
2. Inventarie todos os caminhos, tamanhos e SHA-256. Confira limites, DLLs e plugins;
   registre metadados em `docs/`.
3. Identifique fontes/licenças por componente, mantenha textos completos em
   `src/twine_edge_overlap/third_party/` e documente em [third-party.md](docs/third-party.md).
   Não presumir que EPL cobre todas as DLLs. Redistribuir binários exige revisão própria.
4. Atualize identidade, URL/hosts HTTPS exatos, inventário e avisos origem/destino/SHA-256.
5. Sonde versão/json0 no caminho definitivo e perfil com espaços/acentos. Execute
   preservação, seis referências, recuperação, offline e matriz limpa. Não ajustar
   fixtures/geometria para encobrir regressões.

O ZIP 16.1.0 inclui `config8` portátil: não precisa de `dot -c` e exige
`generated_files` vazio. Há 302 arquivos e 29 avisos, com fontes no `SOURCES.json`.
Aviso ausente/alterado invalida pacote/cache. Reparos preservam gerações anteriores.
Os avisos têm hashes de bytes fixados no manifesto; `.gitattributes` impede
conversão de finais de linha nesses arquivos, inclusive com `core.autocrlf=true`.
Conserve essa regra ao atualizar os avisos.

Para construir distribuições, use venv isolada:

```powershell
python -m venv .tmp/build-env
.\.tmp\build-env\Scripts\python.exe -m pip install build setuptools wheel
.\.tmp\build-env\Scripts\python.exe -m build --no-isolation --outdir .tmp/dist
```

Build pode precisar de internet; suas ferramentas não são dependências de produção.
Inspecione wheel/sdist: manifesto, avisos, LICENSE/NOTICE presentes, sem EXE/DLL/cache.
Instale cada um em venv fora do checkout, execute de outra pasta e prepare cache próprio
sem Graphviz global. Repita com rede bloqueada e confira os hashes dos avisos instalados.

## Alterações e amostras

Descreva problema, comportamento esperado e evidências. Separe arquivos, geometria,
motor e CLI. Escreva testes proporcionais ao risco e atualize documentação afetada.
Não marcar tarefas/checklists concluídos sem evidência. Não alterar checklists durante
implementação.

Informe origem e permissão de inclusão das amostras. Histórias privadas ficam fora
do repositório; fixtures sintéticos não substituem confirmação do formato real.
Trabalhe em cópias: original idêntico byte a byte, conteúdos, IDs, metadados e conexões
preservados. Scripts/macros das histórias não são executados.

Código autoral sob [Apache-2.0](LICENSE), aviso em [NOTICE](NOTICE). Conserve avisos
e identifique origem/licença de materiais incorporados. ELK.js/Node são experimentais,
sem novas dependências Python de produção.
