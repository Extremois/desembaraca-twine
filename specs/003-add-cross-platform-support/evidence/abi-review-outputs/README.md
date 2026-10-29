# Saídas para revisão no Twine

Comece em `review-by-hash/`: os 144 resultados correspondem a seis conteúdos
distintos, um por referência. `distinct_outputs` em `summary.json` associa cada
SHA-256 às 24 instalações que produziram exatamente esses bytes. Essa deduplicação
organiza a revisão e não registra aprovação visual para nenhuma instalação.

144 arquivos: seis ABIs POSIX × dois Pythons × wheel/sdist × seis referências.
Cada arquivo foi exportado pelo CI e conferido contra o hash da saída no recibo.
`summary.json` vincula revisão, job, pacote e SHA-256. Nenhum resultado foi marcado
como reaberto: a revisão visual permanece pendente, assim como a revisão Windows.

Abra as seis referências de cada alvo no Twine e registre versão do Twine,
revisor, ambiente e hashes revisados em integrity-twine.json. A existência deste
pacote não aprova licenças, distribuição ou suporte.
