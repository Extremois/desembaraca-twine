# Avisos de fontes e uso glibc nos pacotes

Checkpoint `62489c84dfd4cf95a11f38877087b795f7d5274c`, enviado para executar
o empacotamento nativo. Os cinco workflows passaram. A [consolidação](summary.json)
vincula jobs, artefatos, hashes e seis diretórios de recibos. `capture.py`
preserva a ferramenta de coleta; os executáveis ficam apenas nos ZIPs ignorados
em `.tmp`, sem inclusão no repositório ou publicação de release.

Foram conferidos os seis bundles glibc/musl x64/ARM64 e macOS Intel/Apple
Silicon: 2.419 arquivos, 2.407 payloads com origem offline, inventários exatos,
bytes/tamanhos/modos POSIX codificados e proveniências. Todos os motores
preservam seus hashes anteriores. `SOURCE-REFERENCES.txt` coincide com o
gerador Linux e com o prefixo comum macOS, incluindo a declaração EPL-2.0,
URL/revisão/hash Graphviz e os avisos próprios de glibc somente nos dois
bundles pertinentes. O índice de origens cobre os bytes atualizados.

A fundação executou 251 testes em cada um dos seis jobs Python 3.12/3.14
em Windows/Linux/macOS, com skips registrados. Localmente passaram 260 testes
em cada Python, nove skips; a diferença são nove casos anteriores ainda locais.
O workflow musl também passou seus oito jobs Alpine 3.21–3.24 × duas CPUs,
nos dois Pythons. São containers sobre o kernel Ubuntu, sem aceite Alpine nativo.
Os relatórios de corpus/runtime preservados pertencem aos builds dessa revisão.

A [decisão de entrega de fontes](../../../../tools/runtime/licenses/SOURCE-DELIVERY-REVIEW.md)
escolhe a rota LGPL 2.1, seções 6(a)/6(d), sem emitir a oferta escrita da
alternativa 6(c). Os avisos agora identificam essa rota e o uso de código glibc
incorporado ao executável. Isso não comprova entrega final das fontes nem
relink com uma biblioteca modificada. As reconstruções originais no CI passaram;
os pacotes completos de fontes não foram reconferidos por este coletor.

T030/T052/T066 continuam parciais: falta demonstrar o relink modificado,
fechar a entrega correspondente de fontes e a compatibilidade dos demais
componentes, incluindo condições ISO dos dados. Assinatura macOS, publicação
autorizada e aceites nativos/visuais mantêm seus gates próprios. **57/84**,
27 pendentes, catálogo ativo Windows.

As provas anteriores de cache estão vinculadas a seus respectivos arquivos.
Mesmo com motores idênticos, elas não são automaticamente atribuídas aos ZIPs
desta revisão, cujo aviso e hash mudaram. T066 mantém ambas as evidências
separadas. Os recibos finais deste incremento permanecem locais.
