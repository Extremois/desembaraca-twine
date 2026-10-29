# Manifestos candidatos para revisão

Seis rascunhos foram preparados a partir dos artefatos do GitHub Actions da revisão `f5e1ad22aea915e9d42e7da1f76de86ffbd23a4f`. O catálogo ativo conserva seu hash original. Nenhum arquivo foi publicado ou promovido.

Cada pasta conserva os recibos originais, o inventário e a proveniência. `manifest-draft.json` contém os campos de runtime e nomes propostos para binário/fontes, identificados pelo SHA-256 real. URLs permanecem `null`, hosts vazios e `approved: false`; o arquivo é um envelope de revisão, ainda incompatível com a ativação pelo aplicativo.

| Artefato | Arquivos conferidos | Avisos com origem e hash |
|---|---:|---:|
| `linux-glibc-aarch64` | 573 | 571 |
| `linux-glibc-x86_64` | 480 | 478 |
| `linux-musl-aarch64` | 450 | 448 |
| `linux-musl-x86_64` | 450 | 448 |
| `macos-arm64` | 233 | 231 |
| `macos-x86_64` | 233 | 231 |

## Conferências realizadas

- ZIP e inventário: caminhos, bytes, tamanhos e modos POSIX codificados.
- Todos os avisos do bundle constam no índice offline de origens, com hashes correspondentes.
- Licença canônica Graphviz conferida contra o hash da fonte fixada; nenhum inventário de dependências Windows foi reutilizado.
- O CI conferiu os dois arquivos do par binário/fontes. A preparação local inspecionou arquivos e metadados, sem executar motores ou testes locais.
- As seis saídas dos binários atuais coincidem com os hashes aprovados pelo usuário no Twine 2.12.1, nos dois Pythons. Os caminhos e hashes dos relatórios atuais constam em `visual_review_binding`; os mesmos bytes já têm aceite visual.

## Antes de ativar

1. Concluir e registrar a auditoria de licenças/fontes por artefato (T030/T052/T066). A presença de avisos não concede aprovação de compatibilidade.
2. Após autorização de publicação, hospedar cada binário e suas fontes com acesso equivalente e URLs HTTPS permanentes. Os nomes propostos ainda não identificam arquivos publicados.
3. Preencher URL/hosts do manifesto, adicionar a URL real das fontes e validar o manifesto final. Os limites e mínimos vieram do inventário, da política ABI e do target do compilador; não representam novos ensaios de kernel ou distribuição.
4. Executar o aceite dos pacotes finais e integrar os manifestos/catalogar/promover os alvos (T031/T052/T078/T082/T083/T084).

Assinatura Developer ID e notarização continuam opcionais. Licenças/fontes, integridade e os demais gates continuam obrigatórios.
