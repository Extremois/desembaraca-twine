# Entrega das fontes selecionadas de headers Apple

A revisão `721b90f3ab44e16b0e88f2d35118ef6fe5cc820c` inclui `float.h`, `math.h`, a licença APSL 1.1 integral e `notice-review.json` nos dois tarballs de fontes macOS. O exportador exige o recibo quando a proveniência declara esses headers e rejeita alterações nos bytes ou na vinculação ao build.

O [resumo](summary.json) reúne as conferências dos ZIPs, os hashes dos pares binário/fontes, os relatórios de runtime e o resultado dos cinco workflows. A [conferência das fontes](source-delivery.json) leu integralmente os dois tarballs: 131 arquivos por arquitetura, todos conferidos contra o manifesto. Os headers e a licença correspondem exatamente às fontes completas capturadas na revisão anterior; o recibo corresponde ao hash registrado na proveniência. O arquivo completo do SDK Apple continua excluído.

Os dois jobs macOS passaram no [Actions](https://github.com/Extremois/desembaraca-twine/actions/runs/40776418040), incluindo reconstrução pelas fontes e runtime com Python 3.12/3.14. Os [seis jobs de fundação](foundation.json) passaram com 307 testes cada. A conferência local apenas leu arquivos e hashes.

Os motores mantêm os hashes da revisão `f63b43e`; as seis saídas preservam os hashes aceitos pelo usuário no Twine. Não há nova revisão visual pendente por esta alteração.

Esta entrega resolve a ausência dessas duas fontes nos tarballs candidatos. Não comprova a cobertura de todas as contribuições do SDK nem substitui a conclusão do inventário por artefato, a análise das condições W3C/ISO ou a entrega permanente dos pares aprovados. Os candidatos continuam sem promoção; T030/T052/T066 e os gates finais permanecem abertos.
