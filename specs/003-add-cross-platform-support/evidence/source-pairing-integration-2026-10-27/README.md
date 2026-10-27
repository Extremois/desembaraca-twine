# Integração do pareamento binário/fontes — 2026-10-27

T030/T066, revisão local de código e contratos. O empacotador não incluía
`executable_sha256`, campo exigido pelo verificador introduzido em 2026-10-22.
O hash agora vem da entrada executável do inventário validado contra a
proveniência e os bytes copiados. Recibos históricos permanecem inalterados.

Os pipelines Linux glibc e musl em x64/ARM64 passam ambos os arquivos reais e
o commit completo ao verificador e conservam `source-pairing.json` junto aos
binários e às fontes. O pipeline macOS não usa o exportador de SDK Zig e
continua com seus gates específicos em aberto.

Validação executada neste checkout:

| Verificação | Resultado observado |
| --- | --- |
| Contratos de pareamento, ZIP e fontes, Python 3.14.6 | 19 testes aprovados |
| `python tests/run_foundation.py`, Windows, Python 3.14.6 | 274 testes, nove skips, aprovado |
| `.tmp/python312/python.exe tests/run_foundation.py`, Windows, Python 3.12 | 274 testes, nove skips, aprovado |
| PyYAML 6.0.3 no WSL existente, três workflows modificados | Parsing aprovado |
| `bash -n` no WSL sobre cada campo `run` desses workflows | 37 passos aprovados |
| `git diff --check` | Aprovado |

O teste dos produtores executa ambos os empacotadores e confere seus arquivos
e recibos juntos, com bytes sintéticos. Testes também recusam arquivos corrompidos,
identidades diferentes, tamanhos booleanos/tipos inválidos, revisão abreviada e
URLs inseguras ou incompletas. A CLI é realmente executada em subprocesso e
não sobrescreve saída existente. `pytest` não estava instalado no Python padrão;
foi usado o runner `unittest` já adotado pelo projeto, sem instalar dependências.

`archive_verification` informa quais arquivos foram lidos; `pairing_valid`
isolado só confirma identidades declaradas. URLs são destinos planejados e
não provam existência, imutabilidade ou acesso equivalente. O estado de entrega
permanece pendente, e o catálogo não é modificado.

Não houve novo build nativo, execução CI, leitura de pacotes finais distribuídos
ou revisão de completude das fontes nesta rodada. Este registro não transfere
evidências históricas para novos arquivos e não aprova licenças ou células.
T030/T066 permanecem abertas: **57/84 tarefas**, 27 pendentes.
