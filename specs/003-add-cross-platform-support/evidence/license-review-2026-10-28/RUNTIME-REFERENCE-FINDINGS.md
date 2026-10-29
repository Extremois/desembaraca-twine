# Grants das referências matemáticas musl

Complemento à [revisão de componentes](COMPONENT-FINDINGS.md). O [registro estruturado](runtime-reference-findings.json) conferiu os bytes das 42 referências da distribuição musl 1.1.18 fixada, seu `COPYRIGHT` e 31 materiais preservados em cada uma das três candidatas pertinentes: glibc ARM64 e musl x64/ARM64.

## Referências sem comentário individual

Quinze referências não têm prefixo de copyright/licença nem indicadores adicionais desses termos no corpo. O `COPYRIGHT` da mesma distribuição começa com o grant MIT para a biblioteca e explica expressamente o tratamento dos arquivos sem comentários individuais de copyright. Essa combinação fornece uma rota MIT documentada para as referências enumeradas no registro, sem presumir domínio público.

O fundamento é o texto do próprio tarball [musl 1.1.18](https://musl.libc.org/releases/musl-1.1.18.tar.gz), fixado por hash no [lock de referências](../../../../tools/runtime/licenses/data-references/musl-math/sources.json). A conclusão se limita a essa distribuição de referência; não atribui MIT indiscriminadamente a arquivos de outros SDKs.

## Termos individuais preservados cumulativamente

Os 27 prefixos históricos restantes incluem grants Sun de uso/cópia/modificação/distribuição com preservação do aviso e condições FreeBSD de redistribuição em fonte/binário com copyright, condições e disclaimer. Eles continuam preservados junto do COPYRIGHT musl, do MIT Zig e do BSD Go conservadoramente mantido para as referências históricas.

Não se escolheu o MIT raiz para apagar os termos individuais. O registro confirma os mesmos hashes desses materiais nas três candidatas. Glibc x64 não foi incluída por associação.

## Limite da conclusão

A rota de redistribuição dos textos de referência foi revisada. A ancestralidade exata de cada tradução Zig e a cobertura completa dos inputs efetivamente retidos continuam questões separadas da auditoria por artefato. Os registros permanecem sem aprovação integral; as condições ISO/W3C, os headers Apple, a entrega permanente de fontes e o aceite final continuam com seus gates.
