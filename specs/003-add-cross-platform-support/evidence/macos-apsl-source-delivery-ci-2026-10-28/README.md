# Fontes dos headers observados com APSL

A revisão `6279d6ff715abbd4fc8d5fdf778d8a27a4f3ddfb` amplia a seleção de fontes para todos os headers observados que declaram explicitamente APSL 1.1 ou 2.0. A seleção anterior de dois arquivos omitia `i386/_limits.h` no Intel e os headers com APSL 2.0 nas duas arquiteturas. Os arquivos são copiados integralmente, preservando seus caminhos relativos ao Xcode e os dois textos de licença.

| Artefato | Headers APSL 1.1 | Headers APSL 2.0 | Arquivos no tarball |
|---|---:|---:|---:|
| macOS Intel | 3 | 183 | 316 |
| macOS ARM64 | 2 | 179 | 311 |

O [resumo](summary.json) vincula cada par binário/fontes aos hashes de proveniência, aos relatórios do corpus/runtime e à fundação. A [conferência integral dos tarballs](source-delivery.json) verificou todos os arquivos contra os manifestos. Os índices de headers por arquitetura também vinculam cada fonte completa à observação do compilador e aos hashes da revisão anterior. O arquivo completo do SDK Apple permanece excluído.

Os [cinco workflows](workflows.json) passaram. Os dois builds, a reconstrução pelas fontes exportadas e o runtime com Python 3.12/3.14 passaram no [workflow macOS](https://github.com/Extremois/desembaraca-twine/actions/runs/40781012838). Os [seis jobs de fundação](foundation.json) passaram com 307 testes cada, incluindo fontes com ambas as versões APSL, caminhos em subdiretórios, rejeição de omissões e adulteração. A conferência local foi somente leitura de arquivos e hashes.

Os motores mantêm os hashes de `f63b43e`; as seis saídas mantêm os hashes aceitos pelo usuário no Twine. Esta alteração não exige nova revisão visual.

A cobertura demonstrada é das fontes observadas com essas declarações APSL, sem inferir ausência de outras contribuições do SDK ou aprovação integral das licenças. As condições W3C/ISO, a conclusão da auditoria por artefato, a entrega permanente e os gates dos pacotes finais permanecem abertos. Não houve publicação nem promoção de catálogo. Os recibos históricos continuam preservados.
