# Revisão técnica dos pares POSIX 46d111d

Revisor: Codex, revisão de implementação. Escopo: exatamente os seis ZIPs e os
seis kits de fontes identificados nos JSONs desta pasta. Aprovação técnica dos
pares preparados não autoriza upload, publicação ou promoção de suporte.
O acesso público equivalente às fontes e o aceite remoto continuam gates
separados. Nenhum estado histórico de build é convertido em prova desses gates.

## Programa e dados Graphviz

O motor é um processo separado do aplicativo Apache-2.0. Graphviz e suas duas
modificações permanecem sujeitos à EPL-2.0 e aos termos próprios identificados
nos arquivos. A [EPL 2.0, seções 3.1–3.3](https://www.eclipse.org/org/documents/epl-2.0/EPL-2.0.txt)
é atendida pela licença integral, notices e entrega conjunta da árvore modificada
com receitas/dados. Os kits foram reconstruídos no Actions. Não se usa uma
licença secundária GPL nem se atribui Apache-2.0 ao motor.

Os grants Randomkit C/header, Rbtree, ColorBrewer, Bison e Flex foram examinados
na [revisão por componente](../../license-review-2026-10-28/COMPONENT-FINDINGS.md).
Os avisos integrais, os dois blocos Randomkit C, a exceção Bison 2.2 e o
reconhecimento ColorBrewer permanecem nos seis pares. Não há novo produto
endossado pelos autores, nem remoção das condições de publicidade/nome.

A tabela antiga de entidades não é distribuída. A alternativa fixa os inputs
WHATWG e W3C, os dois ajustes de compatibilidade e suas modificações datadas.
A [política WHATWG 7.1.1](https://whatwg.org/ipr-policy#copyright-license-for-whatwg-publications)
oferece BSD-3-Clause para as partes incorporadas a código; os seletores modernos
oferecem explicitamente a [licença W3C de software/documentos 2002](https://www.w3.org/copyright/software-license-2002/).
Os textos e disclaimers estão no runtime e os inputs completos nos kits.

SVG conserva os 147 pares nome/RGB da publicação, sem modificar os valores,
com origem e copyright/status preservados. A rota escolhida é reprodução da
porção de dados, em outro meio, da [licença documental W3C 2002](https://www.w3.org/copyright/document-license-2002/):
não é uma especificação SVG modificada nem uma relicença retroativa do documento.
Preservam-se URL, copyright, termos/disclaimers e o comentário de transformação.
As referências históricas/currentes permanecem separadas. Os valores X.Org e
seus ajustes Graphviz conservam ambos os grants Open Group/Oracle; não se
depende de provar uma cadeia histórica exclusiva para apagar outros avisos.

## Bibliotecas Linux

Cada input `.a`/`.o` observado pertence a exatamente um grupo identificado no
registro da arquitetura. Os grupos Graphviz contêm também os componentes acima;
isso não é atribuição de todos os símbolos a uma licença única.

glibc startup/nonshared segue a [LGPL 2.1, seções 0, 4 e 6(a)/(d)](https://raw.githubusercontent.com/bminor/glibc/master/COPYING.LESSERv2).
Não se estende a exceção de um arquivo a outro. Entregam-se fontes completas da
biblioteca, Graphviz, dados e receitas para modificação/relink; os dois relinks
com glibc modificada passaram no Actions. Os termos permitem modificação para
uso próprio e engenharia reversa para depuração. A rota exige manter fontes
disponíveis junto do binário, sem depender dos artefatos temporários do Actions;
não é uma oferta escrita de três anos.

LLVM libc++/libc++abi/libunwind preservam suas licenças integrais e os notices
por arquivo. A [exceção LLVM](https://llvm.org/docs/DeveloperPolicy.html#new-llvm-project-license-framework)
cobre as partes incorporadas em objeto; não implica publicar o compilador.
Zig e musl conservam MIT e todos os termos próprios do SDK exportado. Para as
portas matemáticas são preservados cumulativamente os avisos musl/Sun/FreeBSD e
o BSD Go histórico, conforme os hashes da [revisão das referências](../../license-review-2026-10-28/RUNTIME-REFERENCE-FINDINGS.md).
A árvore `lib/` inteira acompanha cada Linux. A aprovação não presume domínio
público para os quinze arquivos de referência sem comentário nem precisa de
uma alegação de ancestralidade exclusiva para eliminar avisos.

## Inputs macOS

Os kits contêm os 186 headers APSL Intel e 181 ARM64 observados, sem modificação,
com as licenças 1.1/2.0 próprias e hashes conferidos. A rota conservadora trata
eventuais contribuições como cobertas: manter notices e fornecer essas fontes
sob os termos próprios, identificando sua obtenção na entrega conjunta.
Aplicam-se APSL 1.1 2.1/2.2(d) e APSL 2.0 2.1/2.3/4; não se afirma que todos
os headers foram incorporados nem se herda uma versão de licença de outra.
Não há modificações Apple feitas pelo projeto que acionem os deveres específicos
de registrar/notificar modificações. Fontes e licenças permanecem intactas.

Os demais headers seguem a [classificação por arquivo](../../macos-sdk-terms-review-2026-10-28/README.md):
declarações LLVM com exceção, blocos BSD e inputs de compilação regidos pelas
seções 2.2 A(ii)/2.4 do acordo instalado Xcode EA1879. O reconhecimento Berkeley
está no README/NOTICE. O SDK proprietário e o compilador não são redistribuídos.
As dependências dinâmicas são somente libSystem e libc++ do sistema; mapas
nomeados e fontes vinculadas foram conferidos. Não há aprovação implícita de
redistribuição do SDK ou obrigação inventada de obter fontes do Apple Clang.

## Condições de entrega e aceite

Os JSONs vinculam proveniência, fonte, notices e os dois hashes do par exato.
`approved` aprova esta revisão técnica desses bytes e desta rota de entrega;
`qualified` permanece falso. A publicação deve disponibilizar ambos os arquivos
no mesmo release, sem autenticação extra para fontes e sem restrição adicional
aos direitos das licenças. URLs propostas não são declaradas disponíveis antes
da conferência remota. As anotações históricas de preparação nas proveniências
continuam históricas; o registro de distribuição final identificará os gates
efetivamente cumpridos. Nenhum catálogo pode ser ativado apenas com este texto.
