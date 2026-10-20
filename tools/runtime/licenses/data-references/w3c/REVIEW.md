# Revisão das referências W3C e das declarações de entidades

Material coletado em 2026-10-20. A auditoria de aplicabilidade e compatibilidade
dos bundles permanece aberta. Os arquivos gzip preservam os bytes recebidos;
`sources.json` fixa origem, destino observado, codificação, tamanho e hashes.
As páginas históricas são as versões servidas hoje pela W3C, sem afirmação de
que seus bytes sejam idênticos aos de 1999 ou 2011.

HTML 4.01 identifica copyright de 1997–1999, seu status de Recommendation e
links explícitos para as políticas de [documentos de 1999](https://www.w3.org/Consortium/Legal/copyright-documents-19990405)
e [software de 1998](https://www.w3.org/Consortium/Legal/copyright-software-19980720).
A política de documentos distingue software/DTDs e não concede por si só
direito geral de modificar documentos. A política de software contém condições
de preservação do aviso, atribuições e indicação de alterações. Esses regimes
não são intercambiáveis.

O cabeçalho de [SVG 1.1, Second Edition](https://www.w3.org/TR/2011/REC-SVG11-20110816/)
identifica copyright de 2011 e seu status de Recommendation. Seu link genérico
de uso de documentos hoje redireciona à política de 2023. A política de 2002
e a atual de 2023 foram preservadas separadamente para a revisão histórica;
o preparador não atribui automaticamente uma delas ao material de 2011.

Há também três avisos de partes atribuídas à ISO dentro das declarações SGML
do [capítulo de entidades HTML](https://www.w3.org/TR/1999/REC-html401-19991224/sgml/entities.html).
Os três comentários, incluindo suas condições, correspondem aos encontrados
em `lib/common/entities.html` do tarball Graphviz 16.1.0 fixado. Eles não são
substituídos pelos avisos gerais W3C. A condição referente a sistemas/aplicações
SGML conformes precisa ser avaliada; este registro não afirma conformidade do
Graphviz nem conclui a compatibilidade dessa distribuição.

Foi consultada também a [resposta pública W3C anexada ao NETBEANS-853](https://issues.apache.org/jira/secure/attachment/12929220/reply_w3.mbox),
referenciada no processo [LEGAL-386](https://issues.apache.org/jira/browse/LEGAL-386).
A resposta confirma que a W3C disponibiliza seus arquivos DTD/de entidades sob
a licença de software e não reivindica condições incompatíveis com Apache,
mas ressalva expressamente que não fala pelos termos da ISO. Assim, o registro
de outro projeto não é tratado como autorização ISO nem como aprovação do
Graphviz. O recibo local preserva URL/hash e a conclusão de escopo; não inclui
o conteúdo completo da mensagem nem seus dados de contato.

O preparo Linux, quando recebe evidência de dados do próprio build, agora gera
seis referências W3C em texto sem conteúdo HTML ativo, além de um arquivo com
os três avisos de declarações de entidades. O texto inclui URLs e hashes da
origem; o índice offline da candidata relaciona os sete materiais. Os arquivos
brutos permanecem nas fontes exportadas. Os capítulos de comparação existentes
e os ZIPs de candidatas anteriores não são alterados.

A correspondência dos 252 valores de entidades e das 147 cores SVG, e a
reprodução dos headers gerados, estabelecem relações técnicas com os inputs.
Elas não determinam sozinhas o regime de licença, a data/origem de cópias
históricas nem o atendimento às condições. A incorporação dos novos avisos em
um pacote nativo precisa ser confirmada no próximo CI; a auditoria final deve
resolver aplicabilidade/condições por componente antes da distribuição.
