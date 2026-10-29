# Dossiê para decisão de licenças — spec 003

**Atualização da tabela de entidades:** a [integração validada](../entity-integration-ci-2026-10-28/README.md)
substitui os dois arquivos nos seis builds POSIX e nos kits de fontes, com inputs
WHATWG/W3C e avisos próprios. As condições da tabela antiga abaixo descrevem os
bundles históricos deste dossiê. A revisão dos novos pares deve usar os hashes
da integração; as demais conclusões por componente e a entrega permanente
continuam pendentes.

## Escopo da revisão

Revisar os seis bundles POSIX existentes da revisão `f63b43e8842539336dc93f08cfa5711a94d0003f`, preservando o Graphviz 16.1.0 atual. O [índice de candidatos](candidate-index.json) contém os hashes completos de binário, fontes e proveniência, os recibos originais e os avisos preservados para cada artefato. O índice é material de revisão, com `approved: false`, `qualified: false` e revisor ainda não registrado.

| Artefato | Arquivos no ZIP | Payloads de avisos, além do índice |
|---|---:|---:|
| Linux glibc ARM64 | 573 | 571 |
| Linux glibc x64 | 480 | 478 |
| Linux musl ARM64 | 450 | 448 |
| Linux musl x64 | 450 | 448 |
| macOS ARM64 | 550 | 548 |
| macOS Intel | 550 | 548 |

Total: 3.053 arquivos e 3.041 payloads de avisos conferidos. Todos os seis candidatos estão na mesma revisão. Nos quatro Linux, os motores e os demais arquivos do ZIP mantêm os hashes anteriores; somente `NOTICE-ORIGINS.json` mudou para vincular a nova proveniência. Os hashes antigos de arquivo ZIP continuam históricos.

Os [cinco workflows e 20 jobs](../macos-named-link-inputs-ci-2026-10-28/workflows.json) passaram. Os testes de fundação têm 306 casos por job. A conferência local foi leitura de arquivos e recibos; os testes foram executados no GitHub Actions. As fontes completas foram conferidas nos pares binário/fontes pelo CI; esta captura não baixou novamente todos os tarballs de fontes.

## 1. Entidades HTML e referências W3C/ISO

**Decisão necessária:** fundamentar a aplicabilidade e o atendimento das condições ISO preservadas nas declarações de entidades, além dos termos W3C aplicáveis aos materiais efetivamente incorporados. Registrar eventual fundamento alternativo ou impedimento; a correspondência dos valores não concede uma licença por si só.

- A [revisão W3C](../../../../tools/runtime/licenses/data-references/w3c/REVIEW.md) relaciona os textos datados, os três avisos ISO e as limitações da resposta pública W3C.
- O capítulo [HTML 4.01 de entidades](https://www.w3.org/TR/1999/REC-html401-19991224/sgml/entities.html) preserva uma condição referente ao uso com sistemas/aplicações SGML conformes. A conformidade do Graphviz não foi demonstrada por esta implementação.
- A resposta W3C ligada a NETBEANS-853 não fala pelos termos ISO; o [registro de correção de escopo](../license-scope-review-2026-10-28/summary.json) impede tratar esse caso como aprovação deste bundle.
- Nos dois macOS, os [mapas atuais](../macos-named-link-inputs-ci-2026-10-28/README.md) vinculam o símbolo vivo `_entities`, de 4.032 bytes, a `utils.c.o` e ao header gerado já reproduzido na revisão de dados. Há evidência de retenção; não se pode encerrar esse ponto presumindo descarte.

Os avisos integrais de cada candidato estão em `notice-payloads.json.gz`, indicados no índice. Cada entrada contém bytes em base64 e SHA-256, permitindo conferência offline.

## 2. Headers Apple e obrigações de fontes

**Decisão necessária:** determinar quais contribuições dos headers são material coberto incorporado e quais obrigações de notices/fontes decorrem disso. A identificação de um header em dependências de compilação não determina sozinha a extensão da contribuição protegida ao executável.

Nos dois macOS, os headers observados `usr/include/float.h` e `usr/include/math.h` declaram APSL 1.1. Seus hashes são, respectivamente:

```text
4346c126d6f51ea8b63ea394f609f2474b26fdb9257c65cf3d2b43aaef36cd3e
00606d7b27eb5db0a3b93c575a7084f432d1e783cfca2eedcdc234c01cb15134
```

Os prefixos e origens estão nos recibos `review.json.gz` e `notice-payloads.json.gz` macOS. Estão preservados os textos [APSL 1.1](../../../../tools/runtime/licenses/apsl-1.1-COPYING.txt), [APSL 2.0](../../../../tools/runtime/licenses/apsl-2.0-COPYING.txt) e suas [origens fixadas](../../../../tools/runtime/licenses/material-source-lock.json). Não se deve substituir a versão 1.1 pela 2.0 automaticamente. A seção 2.2(d) da APSL 1.1 e a seção 2.3 da APSL 2.0 precisam ser consideradas se houver distribuição de código coberto em forma executável.

Os novos mapas têm zero entradas anônimas, 181 objetos de build vinculados às fontes por arquitetura e zero inputs estáticos `.o`/`.a` do SDK observados. Isso resolve a rastreabilidade dos objetos; a análise de headers/macros permanece separada. A exportação de fontes macOS conserva Graphviz, receitas e proveniência, com zero arquivos do SDK Apple.

## 3. Demais componentes e condições preservadas

**Decisão necessária:** concluir o inventário por artefato e registrar a compatibilidade das permissões e obrigações efetivamente aplicáveis, incluindo eventuais ressalvas. Os textos já estão preservados; esta revisão não lhes atribui uma licença homogênea.

- [Revisão de componentes Linux](../../../../tools/runtime/licenses/LINUX-COMPONENT-REVIEW.md): Graphviz/EPL, Randomkit, Rbtree, ColorBrewer, parsers Bison com exceção, Flex, cores X.Org e materiais de runtime.
- [Portas matemáticas](../../../../tools/runtime/licenses/data-references/musl-math/REVIEW.md): fontes Zig observadas e referências históricas musl/Sun/FreeBSD/Go. A preservação conservadora dos textos não comprova ancestralidade exata de cada tradução.
- [Rota de fontes Graphviz/glibc](../../../../tools/runtime/licenses/SOURCE-DELIVERY-REVIEW.md): obrigações EPL e rota LGPL 2.1, seções 6(a)/6(d), com reconstrução/relink já registrados. O acesso permanente equivalente às fontes ainda depende da entrega final.

Os arquivos próprios do aplicativo permanecem Apache-2.0; os componentes externos conservam seus termos. A aprovação precisa cobrir os inputs estáticos reais de cada Linux, conforme `verify-artifact.py`, e os notices/fontes correspondentes.

## Como registrar a conclusão

Para cada decisão e `artifact_id`, registrar: conclusão, fundamento com texto/seção de licença, obrigações aplicáveis, evidência de atendimento, pendências e identificação do revisor. Os registros de auditoria aprovados devem vincular a proveniência exata e os hashes de fontes/notices; o formato é conferido por `validate_audit` em `tools/runtime/verify-artifact.py`.

Uma conclusão pendente continua pendente. Se houver impedimento concreto, registrar o componente e o fundamento para decidir uma substituição direcionada, preservando as demais revisões aproveitáveis.

## Caminho para encerrar as tasks

1. Usar as conclusões para completar a auditoria Linux T030 e a parte de auditoria macOS T052.
2. Preparar as URLs permanentes dos pares binário/fontes e os manifestos com os hashes deste índice; publicação externa continua aguardando autorização.
3. Integrar o catálogo e executar o aceite dos pacotes finais no Actions para T031/T052/T066/T078, promovendo suporte e encerrando T082/T083/T084 apenas com evidências completas.

O aceite visual permanece aproveitável para as seis saídas com hashes idênticos. Assinatura Developer ID e notarização continuam opcionais. Progresso permanece 76/84 encerradas; este dossiê não altera os checkboxes de auditoria nem o catálogo ativo.
