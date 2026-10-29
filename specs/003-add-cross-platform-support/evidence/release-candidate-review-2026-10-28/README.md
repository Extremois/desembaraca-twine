# Candidatos e auditorias estruturadas para revisão

**Pares históricos:** a [integração da tabela alternativa](../entity-integration-ci-2026-10-28/README.md)
reconstruiu os seis bundles e seus kits. Seu `payload-plan.json` identifica os
12 arquivos novos e conferidos. Estes rascunhos continuam como histórico e
precisam ser atualizados antes de aprovação ou publicação; não usar seus hashes
para distribuir a implementação atual.

Os seis manifestos candidatos e seus rascunhos de auditoria usam a revisão `6279d6ff715abbd4fc8d5fdf778d8a27a4f3ddfb`, já aprovada pelos cinco workflows do Actions. O [resumo](summary.json) fixa os hashes dos manifestos e auditorias. Os rascunhos anteriores continuam históricos.

| Artefato | Arquivos conferidos | Avisos além do índice | Inputs estáticos mapeados |
|---|---:|---:|---:|
| Linux glibc ARM64 | 573 | 571 | 65 |
| Linux glibc x64 | 480 | 478 | 65 |
| Linux musl ARM64 | 450 | 448 | 66 |
| Linux musl x64 | 450 | 448 | 66 |
| macOS ARM64 | 550 | 548 | Revisão por mapa própria |
| macOS Intel | 550 | 548 | Revisão por mapa própria |

Cada diretório contém o par de recibos binário/fontes, proveniência, inventário, payloads dos avisos em gzip/base64, `manifest-draft.json` e `license-audit-draft.json`. Os nomes propostos para publicação incluem os hashes reais dos arquivos. URLs finais continuam vazias e nenhum catálogo foi alterado.

Nos Linux, os 262 inputs `.a`/`.o` têm exatamente um grupo proposto no mapeamento, com hash observado, origem build/SDK, licença proposta, fonte e aviso correspondente. A lista inclui os arquivos de runtime LLVM/Zig, startup/nonshared glibc ou musl, sem transferir inventários entre arquiteturas. A correspondência cobre os inputs, sem atribuir cada símbolo a uma fonte nem aprovar automaticamente os termos.

Nos macOS, os rascunhos vinculam Graphviz e os conjuntos APSL aos [tarballs efetivamente conferidos](../macos-apsl-source-delivery-ci-2026-10-28/README.md). A referência temporária do Actions está identificada como autenticada e sujeita a expiração; ela não substitui a entrega pública permanente. A [revisão dos demais headers](../macos-sdk-terms-review-2026-10-28/README.md) identifica termos e condições por arquivo. O compilador não é redistribuído; não foi criado requisito de obter ou publicar fontes do Apple Clang.

Todos os 3.053 arquivos e 3.041 payloads de avisos foram conferidos novamente contra os ZIPs atuais e seus índices de origem. O CI verificou ambos os arquivos de cada par binário/fontes. Os seis resultados Twine preservam os hashes aceitos pelo usuário nos dois Pythons. Esta preparação apenas leu arquivos e hashes, sem executar motores ou testes locais, disparar novos builds ou publicar arquivos.

O [plano dos arquivos de entrega](payload-plan.json) relaciona os 12 arquivos reais preparados localmente, totalizando 391.746.756 bytes. Os seis ZIPs e os seis tarballs foram recuperados e seus tamanhos/hashes conferidos contra os recibos atuais. Os bytes ficam em `.tmp/release-candidate-review-6279/`, fora do versionamento; os nomes propostos para publicação e os hashes ficam neste plano. Ter esses arquivos prontos não autoriza sua publicação.

Os seis tarballs históricos `6279d6f` precisam ser atualizados antes de aprovação/publicação: falta o NOTICE do aplicativo junto dos scripts e módulos reutilizados. O plano registra essa pendência explicitamente. A correção no exportador inclui o arquivo nos alvos Linux e macOS; os recibos antigos continuam históricos.

## Condições que ainda impedem aprovação

1. Concluir a interpretação da condição ISO de uso com sistemas/aplicações SGML e o atendimento dos termos W3C. Há fundamento técnico para examinar interoperabilidade: a [especificação XML](https://www.w3.org/TR/xml/) descreve XML como forma restrita de SGML, e o [Graphviz documenta saída SVG](https://graphviz.org/docs/outputs/svg/). Isso não certifica conformidade geral do Graphviz nem demonstra, por si só, que todo uso do bundle atende à condição. A resposta W3C do caso NetBeans continua sem autoridade sobre os termos ISO.
2. Concluir as permissões por arquivo, o escopo dos materiais de runtime e a suficiência das fontes. As expressões `LicenseRef-*` são descrições locais dos termos a revisar, não identificadores de licença padronizados nem conclusões aprovadas. O mapeamento mecânico não substitui essa decisão.
3. Preparar e autorizar a entrega permanente equivalente de binários/fontes e executar os gates dos pacotes finais.

Os campos `approved` e `qualified` continuam falsos. Não há requisito de aprovação por advogado, credenciais Apple, testes locais ou VMs. T030/T031/T052/T066/T078/T082/T083/T084 permanecem abertas; esta preparação não altera o contador 76/84.
