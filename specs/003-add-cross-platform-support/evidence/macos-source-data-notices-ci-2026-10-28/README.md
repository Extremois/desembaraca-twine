# Avisos Graphviz e dados nos bundles macOS

Correção `a192890556a437a772a5997e3908564df3c59777`, validada no [GitHub Actions](https://github.com/Extremois/desembaraca-twine/actions/runs/40762408332).

Os dois ZIPs passaram por conferência independente de bytes, inventário, modos e origens. Cada um contém 550 arquivos, com 548 payloads de avisos e um índice de origens. O preparo confere 322 fontes Graphviz observadas e preserva seus prefixos, incluindo Randomkit. Acrescenta o reconhecimento ColorBrewer, os três avisos ISO das entidades e as referências W3C/X.Org com hashes.

As referências de dados são materiais conservadores de revisão. Este preparo não reproduz os geradores de tabelas macOS nem conclui aplicabilidade ou compatibilidade das licenças.

Os motores mantêm os hashes dos candidatos anteriores. As saídas atuais nos dois Pythons coincidem com os seis hashes já aprovados pelo usuário no Twine. A reconstrução a partir das fontes exportadas e os testes de runtime passaram no Actions. O par binário/fontes foi conferido no CI; esta captura local inspecionou arquivos e recibos sem executar motores ou testes.

Os seis jobs de fundação passaram com 306 testes cada; logs comprimidos e hashes estão em `foundation.json`. `summary.json` vincula os resultados aos arquivos originais, preservados em gzip. `notice-payloads.json.gz` conserva os próprios avisos, permitindo nova conferência offline.

O catálogo permanece inalterado. T052/T066 continuam abertas para aplicabilidade por arquivo, contribuição de SDK/runtime, suficiência das fontes e entrega permanente equivalente. Os rascunhos de manifestos da revisão `f5e1ad2` continuam históricos: seus hashes macOS não identificam estes novos ZIPs.
