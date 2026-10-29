# Entradas de link macOS vinculadas às fontes

Revisão `f63b43e8842539336dc93f08cfa5711a94d0003f`, validada no [GitHub Actions](https://github.com/Extremois/desembaraca-twine/actions/runs/40764323087). As receitas usam `MinSizeRel`, uma configuração padrão do CMake que não ativa o bloco LTO de Release/RelWithDebInfo do Graphviz 16.1.0 fixado. O workflow exige zero entradas anônimas antes de preparar os avisos.

| Observação | Intel | ARM64 |
|---|---:|---:|
| Entradas sem nome no mapa | 0 | 0 |
| Objetos de build com hashes e dependências de fonte | 181 | 181 |
| Inputs estáticos do SDK (`.o`/`.a`) observados | 0 | 0 |
| Stubs `.tbd` do SDK observados | 9 | 8 |
| Fontes Graphviz conferidas | 322 | 322 |
| Arquivos no ZIP | 550 | 550 |
| Payloads de avisos, além do índice de origens | 548 | 548 |

Os mapas anteriores tinham 181 entradas anônimas em cada arquitetura, inclusive com símbolos reais. Os novos mapas, objetos e arquivos de dependências têm hashes preservados nos recibos. Isso fecha essa pendência de rastreabilidade; ausência de inputs estáticos do SDK não exclui contribuições de headers/macros.

Ambos os mapas registram o símbolo vivo `_entities`, de 4.032 bytes, pertencente ao objeto `utils.c.o`. Suas dependências incluem o header gerado de entidades com o mesmo SHA-256 já reproduzido na revisão de dados Graphviz. Este é um vínculo de mapa/objeto/fonte; não uma reconstrução byte a byte da tabela executável. O material não pode ser descartado da auditoria como comprovadamente ausente.

Runtime e reconstrução pelas fontes exportadas passaram nos dois Pythons. Os motores mudaram de hash com a configuração, mas as seis saídas coincidem exatamente com as já aprovadas no Twine. Os seis jobs de fundação passaram com 306 testes cada. A captura local conferiu arquivos, modos, hashes, avisos e recibos; testes continuam exclusivos do Actions.

`summary.json` aponta para os recibos gzip, mapas originais e relatórios. O catálogo continua inalterado. Aplicabilidade das condições W3C/ISO, obrigações dos headers e entrega permanente de fontes ainda impedem aprovação T052/T066. Os rascunhos de manifestos anteriores continuam históricos e precisam dos novos hashes antes de qualquer ativação.
