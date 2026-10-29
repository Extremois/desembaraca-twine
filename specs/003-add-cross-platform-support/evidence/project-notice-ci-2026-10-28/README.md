# NOTICE atualizado nos pacotes

Revisão `993bc6fc3d0c9a4eaa2f16e268cb11212dc6b54f`. O [workflow de instalação](https://github.com/Extremois/desembaraca-twine/actions/runs/40768639752) aprovou dez combinações: Ubuntu x64/ARM64, macOS Intel/ARM64 e Windows, com Python 3.12/3.14. Foram 20 instalações, uma de wheel e uma de sdist por combinação.

Os recibos confirmam os 53 arquivos do aplicativo, LICENSE/NOTICE completos, três entrypoints e importação em venv externa, com PATH sem Git ou Graphviz global. Os hashes de NOTICE correspondem aos bytes do commit, admitindo somente a convenção LF ou CRLF do checkout. O texto inclui o reconhecimento ColorBrewer exigido e a descrição corrigida do cache gerenciado.

Os seis jobs de [fundação](https://github.com/Extremois/desembaraca-twine/actions/runs/40768639862) também passaram, com 306 testes cada. `summary.json` vincula os resultados aos recibos e à [revisão parcial de componentes](../license-review-2026-10-28/COMPONENT-FINDINGS.md). Os JSONs e logs originais estão preservados em gzip com hashes.

Esta execução valida os pacotes atuais e os metadados de licença. Não adquiriu nem qualificou motores privados pelo workflow de instalação. As auditorias POSIX, as fontes permanentes e o aceite da distribuição final permanecem pendentes em T030/T052/T066/T078; o catálogo e o aceite visual foram preservados.
