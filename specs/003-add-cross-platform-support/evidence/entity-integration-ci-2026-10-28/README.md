# Integração da tabela alternativa

Os commits `e681a14` e `46d111d` integram as duas substituições reproduzidas na
[avaliação anterior](../entity-alternative-review-2026-10-28/README.md). O Graphviz
continua em 16.1.0; os 252 nomes/valores e as declarações C são preservados.
Os dois ajustes `lang`/`rang` e as alterações de origem estão documentados nos
inputs e avisos. As fontes, seletores e licenças completos acompanham as receitas.

O build aplica as substituições antes do CMake. Os coletores de evidência e os
preparadores de avisos conferem os mesmos bytes efetivos. `source-lock.json`
identifica separadamente o download original e a árvore modificada. O pacote de
fontes leva `graphviz.tar.gz` modificado e exclui os dois snapshots históricos
HTML 4.01. O replay autentica a árvore modificada sem exigir os arquivos antigos.

O primeiro checkpoint revelou uma comparação de caminhos temporários sem
normalização dos dois lados em Windows/macOS. A correção resolve ambos antes
de verificar contenção; [tentativa e logs](initial-attempt.json) permanecem
preservados. Nenhum teste, gerador ou motor nativo foi executado localmente.

A regressão corrigida aprovou seis jobs, com 309 testes cada e skips explícitos, no
[Actions](https://github.com/Extremois/desembaraca-twine/actions/runs/40801175509).
A [prova integrada](https://github.com/Extremois/desembaraca-twine/actions/runs/40801175491)
também aprovou a equivalência e a exportação/replay.

Os seis workflows e 21 jobs passaram na revisão `46d111de81038d6ae0e7e7772813693c5b0a2345`.
O [resumo](summary.json) conserva os recibos e hashes dos seis builds POSIX,
corpus nos dois Pythons, cache offline, reconstrução dos kits exportados e relink
controlado glibc. O workflow musl inclui os oito jobs de compatibilidade Alpine
3.21–3.24 em x64/ARM64, cada um nos dois Pythons, sem VMs.

Os seis tarballs completos foram recuperados e todos os arquivos conferidos
contra seus índices internos. Cada `graphviz.tar.gz` contém as substituições e
reproduz a árvore `54ae15738f636a57581272de3565f933c7c55b8d84005d2d8b3361aeb429f4d0`.
Os dois snapshots antigos estão ausentes. Os seis ZIPs contêm os novos termos
em `ENTITY-DATA-LICENSES.txt`; os índices offline e avisos foram preservados.

Os dois recibos de cada par apontam para o mesmo executável e proveniência;
hash e tamanho dos 12 arquivos reais foram conferidos novamente. O
[plano de entrega](payload-plan.json) conserva os nomes propostos e os caminhos
locais em `.tmp/entity-integration-ci/`, totalizando 390.122.923 bytes.
Não houve publicação. Os rascunhos anteriores precisam usar estes novos pares
antes de aprovação e entrega.

As seis saídas de referência nos 36 relatórios de corpus capturados preservam
os hashes já aceitos pelo usuário no Twine. A alteração da tabela não exige
repetir aquela revisão visual; isso não representa novo ensaio visual local.

Os artefatos anteriores continuam históricos. A integração não aprova o conjunto
das licenças nem promove suporte. Restam conclusões por componente, entrega
permanente dos pares e aceite dos pacotes finais. Contador preservado: 76/84.
