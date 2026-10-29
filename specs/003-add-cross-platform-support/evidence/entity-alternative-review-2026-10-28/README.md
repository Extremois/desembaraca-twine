# Avaliação de uma tabela alternativa de entidades

**Continuação:** os commits `e681a14`/`46d111d` integram a substituição nas receitas,
avisos e pacotes de fontes. A [evidência da integração](../entity-integration-ci-2026-10-28/README.md)
registra a validação seguinte. O restante deste documento descreve a avaliação original.

O usuário escolheu avaliar uma alternativa para a condição ISO da tabela HTML antiga, mantendo Graphviz 16.1.0. Esta avaliação prepara dois arquivos de fonte propostos; não altera as receitas ou o catálogo de produção.

## Dados e permissões

`inputs.json` fixa os bytes, URLs, tamanhos e hashes das entradas. A tabela JSON WHATWG contém 2.231 entradas e é recuperada de uma revisão imutável do repositório oficial `whatwg/html-build`. O LICENSE desse repositório e a [política WHATWG, seção 7.1.1](https://whatwg.org/ipr-policy#copyright-license-for-whatwg-publications), oferecem BSD de três condições para porções incorporadas em código-fonte. A cópia integral do LICENSE acompanha o snapshot bruto, preservando também o regime CC BY 4.0 da publicação.

Os nomes são selecionados dos três arquivos modernos W3C `xhtml1-lat1`, `xhtml1-special` e `xhtml1-symbol`, acrescidos de `amp`, nome predefinido em XML. Os três arquivos oferecem explicitamente a [licença W3C de software/documentos de 2002](https://www.w3.org/copyright/software-license-2002/); essa é a rota escolhida para os seletores. Seus avisos originais permanecem nas cópias integrais. Não se usa a tabela ISO antiga para selecionar os nomes da candidata.

250 valores modernos coincidem com a tabela atual. `lang` e `rang` têm dois ajustes explícitos de compatibilidade para U+2329 e U+232A, mantendo o comportamento do Graphviz. A [especificação W3C moderna, apêndice C.1](https://www.w3.org/TR/xml-entity-names/#diff-xhtml), documenta a diferença histórica em relação a U+27E8/U+27E9. Os ajustes e a data de transformação estão registrados no lock e nos avisos gerados.

## Prova no Actions

`evaluate.py` verifica os inputs e o tarball original fixado, gera o novo `entities.html` e uma cópia do gerador original com origem/avisos atualizados. Executa os dois geradores Python apenas no Actions. Exige igualdade de todos os nomes e valores e das declarações C geradas, permitindo diferenças apenas nos comentários/atribuições. Também calcula a identidade lógica da árvore de fontes com as duas substituições, independente de timestamps ou compressão. Não executa motor nativo.

O workflow `entity-alternative-review.yml` conserva as duas fontes propostas, o header resultante, a licença Graphviz e o relatório. Nenhum teste de aplicativo ou gerador é executado localmente. A comparação local anterior foi leitura de dados e identificou exatamente as duas diferenças citadas.

## Antes de integrar

Se a prova passar, a integração precisa registrar as duas substituições por hash, empacotar a árvore modificada em vez do tarball original com o antigo input ISO e excluir cópias históricas dessa tabela dos notices/referências distribuídos. Também precisa preservar os novos textos e origens offline e repetir o aceite ABI/pacotes no Actions. O gerador e a versão Graphviz continuam os mesmos, com mudança de dados e comentários de origem.

Esta proposta não relabela a tabela ISO antiga com uma nova licença. Ela usa novos inputs com grants explícitos, preservando seus termos. Ainda não há build qualificado com a alternativa, aprovação integral de licenças ou publicação. A revisão visual existente permanece vinculada aos seus hashes; uma integração futura deve comparar as saídas antes de decidir se há nova revisão necessária.
