# Conclusões parciais por componente

Complemento ao [dossiê](README.md). A [revisão estruturada](component-findings.json) vincula sete grupos de termos aos avisos dos seis candidatos `f63b43e`: 42 vínculos por artefato, com hashes de binário, proveniência, fontes e notices. Trata-se de revisão textual de implementação; os registros continuam com `approved: false` e não substituem a auditoria completa dos bundles.

| Grupo | Conclusão delimitada |
|---|---|
| Parsers Bison | Os quatro avisos gerados de cada candidato preservam GPL e a exceção Bison 2.2. A rota da exceção permite a obra maior nos seus próprios termos quando ela não é um gerador de parsers que usa o skeleton. O candidato é `dot`; preservar a exceção com cada aviso. |
| Scanner Flex | O COPYING preservado permite o uso dos scanners gerados. As condições do gerador não impõem por si só GPL ao scanner Graphviz. O texto integral permanece no bundle. |
| Randomkit | C e header têm grants próprios. Preservar ambos os blocos do C e o aviso do header, com copyright, permissões, disclaimers e condição de não endosso. |
| Rbtree | O LICENSE inspecionado permite redistribuição de fonte/binário com condição de não endosso. Preservar o texto próprio, sem atribuir um identificador BSD genérico. |
| ColorBrewer | A rota exige preservação dos termos, reconhecimento e restrições de nome/endosso. Os seis bundles já têm o reconhecimento; o NOTICE do aplicativo passou a reproduzi-lo também. |
| Referência X.Org | Os blocos Open Group e Oracle permitem reutilização com suas condições de notices. Ambos estão preservados. A conclusão não estabelece a origem histórica de cada entrada de cor Graphviz. |
| Graphviz/EPL | Licença e identificação de fontes estão preservadas. Permanecem a entrega permanente das fontes correspondentes e a conclusão dos demais componentes. |

Fundamentos: [exceção Bison](https://spdx.org/licenses/Bison-exception-2.2.html), [COPYING Flex 2.6.4](https://raw.githubusercontent.com/westes/flex/v2.6.4/COPYING), [Randomkit](https://gitlab.com/graphviz/graphviz/-/raw/16.1.0/lib/neatogen/randomkit.c), [Rbtree](https://gitlab.com/graphviz/graphviz/-/raw/16.1.0/lib/rbtree/LICENSE), [ColorBrewer](https://gitlab.com/graphviz/graphviz/-/raw/16.1.0/lib/common/brewer_colors), [referências X.Org fixadas](../../../../tools/runtime/licenses/data-references/sources.json) e [EPL Graphviz](https://graphviz.org/license/). Os bytes efetivamente revisados e suas origens constam dos recibos, permitindo conferir esses fundamentos contra cada build.

## Correção do NOTICE do aplicativo

O [NOTICE](../../../../NOTICE) agora explica o runtime Graphviz separado no cache privado e conserva as licenças dos componentes externos. Inclui o reconhecimento ColorBrewer exato que os avisos dos seis candidatos já preservam.

`MANIFEST.in` inclui esse arquivo no sdist. O verificador existente `check-built-packages.py` exige seus bytes exatos no wheel e nas instalações. A validação do NOTICE alterado deve ocorrer no Actions; os recibos anteriores continuam vinculados às suas revisões originais.

## Pendências mantidas

Continuam abertas aplicabilidade ISO/W3C, contribuições e obrigações dos headers Apple, escopo das portas matemáticas/runtime, cobertura completa dos inputs/fontes por artefato e entrega permanente equivalente das fontes. Esta revisão não altera T030/T052/T066, o catálogo ativo ou o aceite visual já registrado.
