# Fontes completas dos dois headers Apple em revisão

Revisão `ae786485b720dfe63fd21d177dc69a988b15205f`, validada no [Actions macOS](https://github.com/Extremois/desembaraca-twine/actions/runs/40770628204). A coleta preserva apenas os dois inputs do SDK selecionados por nome/caminho e SHA-256, acompanhados do texto integral APSL 1.1. O teste de regressão rejeita hashes alterados, arquivos faltantes e coleta indiscriminada de headers.

| Arquivo por arquitetura | Bytes | SHA-256 |
|---|---:|---|
| `float.h` | 4.498 | `4346c126d6f51ea8b63ea394f609f2474b26fdb9257c65cf3d2b43aaef36cd3e` |
| `math.h` | 34.155 | `00606d7b27eb5db0a3b93c575a7084f432d1e783cfca2eedcdc234c01cb15134` |
| `APSL-1.1-COPYING.txt` | 19.930 | `359a21ed59e82096455398ea10c5bc8c3ff28e7acf7935b77751d70e3630fc95` |

Os três arquivos são idênticos nas capturas Intel/ARM64 e mantêm os bytes originais. Os comentários declaram APSL 1.1; não se aplica automaticamente a versão 2.0. As fontes e a licença permanecem juntas em cada pasta. `summary.json` vincula arquivos, origens Xcode/SDK, proveniência e recibos.

## O que a fonte completa esclareceu

`math.h` contém implementações `inline`, incluindo classificação de ponto flutuante, sinal e wrappers trigonométricos. A hipótese de que todo o conteúdo relevante seria apenas declaração/tipo não está estabelecida. A presença dessas implementações no header não prova, isoladamente, sua retenção em cada executável.

`float.h` documenta a interação com o header Clang e define aliases/macros sobre valores e builtins do compilador. O comentário sobre redefinições não foi tratado como prova de ausência de contribuição no binário.

Essas observações orientam a análise das obrigações de fonte/notices e da contribuição efetiva. O material coletado é fonte para revisão; não constitui entrega permanente de fontes correspondentes nem aprovação de um bundle.

## Validação e limites

Os dois builds, reconstruções e ensaios de runtime passaram no Actions. Os motores mantêm os hashes da revisão `f63b43e`; as seis saídas continuam idênticas às aprovadas no Twine. Os seis jobs de fundação passaram com 307 testes cada. A captura local somente conferiu arquivos e recibos.

Os arquivos completos ficam na pasta de revisão, separados do ZIP de runtime e da exportação de fontes Graphviz, que conserva a política atual sobre o SDK. T052/T066 continuam abertas para concluir aplicabilidade e atendimento das obrigações; o catálogo ativo permanece inalterado.
