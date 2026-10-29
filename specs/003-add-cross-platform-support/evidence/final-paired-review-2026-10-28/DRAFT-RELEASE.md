# Graphviz 16.1.0 ? runtimes POSIX do Desembara?a Twine

Rascunho local; aguarda autoriza??o para upload/publica??o.

Build de origem: `46d111de81038d6ae0e7e7772813693c5b0a2345`. Os seis motores privados foram ensaiados no GitHub Actions. O aplicativo Python mant?m Apache-2.0; Graphviz e componentes preservam os termos individuais dos arquivos.

## Bin?rios e fontes correspondentes

As fontes completas de Graphviz modificado est?o dispon?veis sob EPL-2.0. Os kits Linux incluem as fontes de bibliotecas/runtime e as receitas de reconstru??o/relink. Os kits macOS incluem os headers APSL 1.1/2.0 observados e suas licen?as, sob os termos pr?prios; o SDK propriet?rio e o compilador Apple n?o s?o distribu?dos.

A rota glibc ? LGPL 2.1 6(a)/6(d): download equivalente do bin?rio e das fontes no mesmo local. S?o permitidas modifica??o para uso pr?prio e engenharia reversa para depurar essas modifica??es. N?o h? oferta escrita alternativa de tr?s anos. As fontes devem continuar dispon?veis enquanto os bin?rios forem disponibilizados.

As anota??es de candidata/proveni?ncia nos arquivos descrevem o estado de prepara??o. Os pares exatos desta distribui??o e as obriga??es de disponibiliza??o s?o identificados nesta p?gina e no SHA256SUMS.

| Alvo | Bin?rio | Fontes completas |
|---|---|---|
| linux-glibc-aarch64 | [Download](https://github.com/Extremois/desembaraca-twine/releases/download/graphviz-16.1.0-posix-46d111d/graphviz-16.1.0-linux-glibc-aarch64-e4f8f852a3278edb8fb91b74330641c79693a13c367e9762fd119916b3c2f542.zip) | [Download](https://github.com/Extremois/desembaraca-twine/releases/download/graphviz-16.1.0-posix-46d111d/graphviz-16.1.0-linux-glibc-aarch64-d434a52573f3d29e6819300a33d4ede9ef8f4415a7e39befec68e5d0c9fbaadd-sources.tar.gz) |
| linux-glibc-x86_64 | [Download](https://github.com/Extremois/desembaraca-twine/releases/download/graphviz-16.1.0-posix-46d111d/graphviz-16.1.0-linux-glibc-x86_64-1403a2beae5a0bc7b616f68c772c954a6f66a4c44665619306ceac658f6a9871.zip) | [Download](https://github.com/Extremois/desembaraca-twine/releases/download/graphviz-16.1.0-posix-46d111d/graphviz-16.1.0-linux-glibc-x86_64-dfe53f2dc50f9c5837f4f86dc5af7f3151e450724e7cc65942bd98991c605059-sources.tar.gz) |
| macos-arm64 | [Download](https://github.com/Extremois/desembaraca-twine/releases/download/graphviz-16.1.0-posix-46d111d/graphviz-16.1.0-macos-arm64-3defe05ab35e63a73ec69faf44ecf382b63e9c0b7d46d19c7081ec0a7399a831.zip) | [Download](https://github.com/Extremois/desembaraca-twine/releases/download/graphviz-16.1.0-posix-46d111d/graphviz-16.1.0-macos-arm64-4beb91d4f42565ef94b0945ca464277661c57e1e1ad0a10efbb087a56d13d575-sources.tar.gz) |
| macos-x86_64 | [Download](https://github.com/Extremois/desembaraca-twine/releases/download/graphviz-16.1.0-posix-46d111d/graphviz-16.1.0-macos-x86_64-aa9ea80350aa63b269b9228da9b7e5b2812d7ef6ac3fa3c3a6205e9d1a7ad897.zip) | [Download](https://github.com/Extremois/desembaraca-twine/releases/download/graphviz-16.1.0-posix-46d111d/graphviz-16.1.0-macos-x86_64-96f093e56aab8f476fa7a792e0d7202bdeab2c3487853c4a86d8eab207078142-sources.tar.gz) |
| linux-musl-aarch64 | [Download](https://github.com/Extremois/desembaraca-twine/releases/download/graphviz-16.1.0-posix-46d111d/graphviz-16.1.0-linux-musl-aarch64-b342050b5f6a9ff861e4528bca1710298366938491db2b8c3cad0ba16b680df9.zip) | [Download](https://github.com/Extremois/desembaraca-twine/releases/download/graphviz-16.1.0-posix-46d111d/graphviz-16.1.0-linux-musl-aarch64-4a937f3371fab412c91a2cf9bc1d74100b1690053914c195d846368a8c4f9027-sources.tar.gz) |
| linux-musl-x86_64 | [Download](https://github.com/Extremois/desembaraca-twine/releases/download/graphviz-16.1.0-posix-46d111d/graphviz-16.1.0-linux-musl-x86_64-519ce6fa092c9e3bc5d0502cee3e5c86ac21e32e3c799df650249834da0224e1.zip) | [Download](https://github.com/Extremois/desembaraca-twine/releases/download/graphviz-16.1.0-posix-46d111d/graphviz-16.1.0-linux-musl-x86_64-f196f2e30a38a7414bcbc6ea00c56e609b71abd65b1d11b026883d1ed35fc859-sources.tar.gz) |

## Avisos e fontes

Os reconhecimentos ColorBrewer e Berkeley no NOTICE/README acompanham esta distribui??o. Nenhum autor ou entidade endossa este produto. As licen?as, copyrights, permiss?es e disclaimers completos permanecem nos ZIPs e kits; o texto desta p?gina n?o os substitui.

Os componentes Graphviz permanecem sob EPL-2.0; os termos permissivos das subpartes, as exce??es de Bison/Flex, as licen?as WHATWG/W3C da tabela substituta e os termos de bibliotecas/headers continuam pr?prios. N?o h? mudan?a nos direitos de qualquer componente.

A tabela de entidades usa a substitui??o revisada, com 252 nomes/valores e declara??es C equivalentes. Os seis resultados Twine mant?m os hashes aceitos. Assinatura/notariza??o macOS s?o opcionais; nenhuma prote??o do sistema deve ser desativada.

Esta release fornece os componentes. A ativa??o do cat?logo e a qualifica??o da distribui??o Python exigem a confer?ncia p?blica dos downloads e o aceite dos pacotes finais.
