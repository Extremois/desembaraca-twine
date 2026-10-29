# Revisão dos demais headers macOS

O [workflow de coleta](https://github.com/Extremois/desembaraca-twine/actions/runs/40784211220) leu o acordo instalado no Xcode 16.4, build 16F6, nos dois runners macOS. O RTF tem o mesmo hash nas duas arquiteturas, identifica `EA1879` e conserva a data literal `06/10/2024`. O original e sua conversão para texto estão preservados em gzip por arquitetura; o [resumo](summary.json) fixa seus hashes. A página pública atual de termos Apple não foi tratada como cópia histórica desse arquivo.

A [revisão estruturada](header-findings.json) vincula os 67 headers não APSL restantes aos hashes e avisos observados nas candidatas `6279d6f`:

| Bloco/rota identificada | Intel | ARM64 |
|---|---:|---:|
| Declaração explícita Apache-2.0 WITH LLVM-exception | 24 | 24 |
| Blocos BSD de quatro condições | 5 | 7 |
| Prefixo apenas de copyright; uso como input do SDK | 2 | 5 |

Os headers LLVM têm declaração SPDX própria e o texto integral de referência permanece no runtime. A exceção para trechos incorporados em forma objeto e os avisos preservados fundamentam a rota de headers compilados; não há necessidade de obter o código do executável Apple Clang para esse fim. A [política oficial LLVM](https://llvm.org/docs/DeveloperPolicy.html) documenta essa exceção.

Os blocos BSD preservam copyright, condições, disclaimer, reconhecimento e proibição de endosso. O reconhecimento Berkeley foi acrescentado a README/NOTICE e registrado no plano de entrega para os materiais de divulgação pertinentes. Não se presumiu revogação da cláusula de publicidade nem se atribuiu BSD a todas as partes Apple/NeXT dos arquivos.

Para os inputs do SDK, as seções 2.2 A(ii) e 2.4 do acordo instalado tratam do desenvolvimento e da distribuição de aplicações/bibliotecas macOS sem contrato separado, sujeitos aos seus termos. As seções 2.5–2.7 preservam restrições do SDK e distinguem a aplicação do software Apple. Essa rota permite tratar esses arquivos como inputs de compilação; não concede redistribuição geral dos headers proprietários ou das bibliotecas do SDK. Os termos explícitos dos componentes abertos continuam separados. A [página oficial Apple](https://www.apple.com/legal/sla/docs/xcode.pdf) serve como referência do fornecedor; a conclusão aqui usa a cópia instalada identificada por hash.

Os cinco arquivos com prefixo apenas de copyright foram lidos por hash nos runners, com contagens léxicas limitadas. Seus corpos não foram copiados para a evidência. As contagens não demonstram ausência de contribuições protegidas. Os tarballs candidatos contêm as fontes selecionadas com APSL; os ZIPs de runtime têm somente o motor e avisos, sem bibliotecas do SDK. Nenhum SDK completo foi redistribuído, nenhuma licença foi aceita automaticamente e não houve build ou teste de motor nessa coleta.

Esta revisão fecha a classificação dos termos dos demais headers, com as condições descritas. Não aprova integralmente os bundles. Permanecem a conclusão W3C/ISO e dos demais componentes/fontes, a correção do NOTICE no kit de fontes, a entrega permanente e o aceite final. Os [seis jobs de fundação](foundation.json) passaram com 307 testes cada; os [quatro workflows da revisão](workflows.json) passaram. Não há requisito de credenciais Apple, assinatura/notarização ou nova revisão visual.
