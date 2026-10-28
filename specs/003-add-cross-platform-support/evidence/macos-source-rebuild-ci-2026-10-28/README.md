# Reconstrução macOS a partir das fontes exportadas

Intel e ARM passaram no GitHub Actions, revisão `fed01cc58e7a51625ce8b6da43b526dbc55c80a0`.
Cada arquitetura exportou 127 arquivos, com todos os hashes conferidos, incluindo
o tarball Graphviz fixado, as receitas e a proveniência vinculada ao binário.
Nenhuma árvore do SDK Apple foi incluída no arquivo de fontes.

O workflow extraiu esse material em uma pasta nova e executou seus próprios
scripts de preparo/compilação, usando Xcode instalado no runner. Os motores
reconstruídos passaram 13 casos e seis referências zeradas com cada Python:
52 casos e 24 referências nas quatro combinações. Os relatórios originais,
as proveniências e os logs de reconstrução estão nas pastas de cada arquitetura.

Não se afirma reconstrução binária idêntica, completude das fontes transitivas,
aprovação de licenças, publicação permanente ou promoção de suporte. Os campos
`obligations` dos recibos descrevem itens da revisão; não são resultados de
ensaios. Auditoria por componente e entrega pública continuam pendentes.
