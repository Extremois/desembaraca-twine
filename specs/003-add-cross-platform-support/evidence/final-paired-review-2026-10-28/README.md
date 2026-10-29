**Atualiza??o ap?s autoriza??o:** a [pr?-release](https://github.com/Extremois/desembaraca-twine/releases/tag/graphviz-16.1.0-posix-46d111d) foi publicada com os 12 arquivos. Todos os downloads p?blicos, inclusive fontes, tiveram tamanho/SHA-256 conferidos sem autentica??o. Os seis manifestos foram integrados para o aceite final; a promo??o dos alvos aguarda esse resultado. [Recibo p?blico](public-download-verification.json).

**Encerrado em 2026-10-29:** [84/84 tarefas e revisão constitucional](closeout.json), [sete alvos/14 slots promovidos](qualification/summary.json), [42 instalações finais](../package-installation.json), [14 comandos documentados](../quickstart.json). [Runtime e fontes publicados](https://github.com/Extremois/desembaraca-twine/releases/tag/graphviz-16.1.0-posix-46d111d), com [hashes públicos verificados](public-download-verification.json). As condições pendentes nas auditorias originais abaixo descrevem o instante da revisão; publicação e aceite foram cumpridos e estão vinculados no encerramento, sem reescrever os recibos originais.


# Pares POSIX revisados e preparados para entrega

**T030 concluída; 77/84 tasks.** A auditoria técnica dos quatro pares Linux
está concluída. Os dois macOS também têm revisão técnica aprovada; T052 inclui
ainda a entrega pública e o catálogo, que continuam pendentes. Os resultados
não são uma aprovação genérica dos registros históricos.

Os [seis registros de auditoria](summary.json) identificam os dois hashes de
cada par, a proveniência e os notices exatos. As [decisões por componente](audits/DECISIONS.md)
resolvem a rota das entidades, os demais dados/notices, glibc, LLVM/Zig/musl e
os inputs macOS. Os 262 inputs estáticos Linux estão mapeados sem transferir
inventários entre arquiteturas. Aprovação técnica não autoriza publicar.

## Verificações executadas no GitHub Actions

- [Oito slots glibc/macOS instalados](https://github.com/Extremois/desembaraca-twine/actions/runs/40805216885): inspeção nativa com os registros aprovados, wheel/sdist em venv externa, corpus, integridade, uso offline e recuperação.
- [Quatro slots musl e dois Windows](https://github.com/Extremois/desembaraca-twine/actions/runs/40805217225): musl em userland Alpine fixada e usuário sem privilégios; notices/cache, corpus/recuperação e os dois formatos. Windows usa a aquisição oficial fixada.
- [Oito slots de notices glibc/macOS](https://github.com/Extremois/desembaraca-twine/actions/runs/40804473185): leitura independente dos avisos no cache, antes/depois, sem rede no reaproveitamento íntegro; corrupção recusada e restauração conferida.
- [Fundação corrigida](https://github.com/Extremois/desembaraca-twine/actions/runs/40805520908): seis jobs de 310 testes, com skips explícitos.

São 12 inspeções auditadas POSIX, 12 slots POSIX de execução instalada e
14 slots de notices/cache, todos nos dois Pythons. As instalações dos dois
formatos foram exercitadas fora do checkout. Os códigos/dados empacotados do
aplicativo são idênticos entre as revisões de coleta; os patches intermediários
alteraram a auditoria e um dado sintético de teste. Os recibos originais e seus
hashes ficam em `acceptance/`, separados por revisão; as tentativas falhas não
foram convertidas em sucesso. O timeout do serviço de artefatos macOS exigiu
repetição do job antes da captura final.

As provas de fontes completas, reconstrução, relink glibc modificado e saídas
Twine idênticas continuam vinculadas aos [mesmos seis pares](../entity-integration-ci-2026-10-28/README.md).
Nenhum teste, gerador ou motor foi executado localmente nesta conclusão. A
conferência local leu somente arquivos, recibos e hashes.

## Entrega concreta preparada

O [plano da release](release-plan.json), o [inventário dos 12 arquivos](upload-inventory.json),
os [SHA-256](SHA256SUMS) e as [notas propostas](DRAFT-RELEASE.md) estão prontos.
Total: 390.122.923 bytes; seis ZIPs e seis kits completos, com nomes por hash.
Os arquivos estão em `.tmp/publish-posix-46d111d/`. As propostas de manifestos
estão separadas do catálogo ativo. Não foi criado release, feito upload ou
alegada disponibilidade das URLs propostas.

Destino proposto: `Extremois/desembaraca-twine`, pré-release
`graphviz-16.1.0-posix-46d111d`. O [preflight somente de leitura](release-preflight.json)
confirmou repositório público, acesso de escrita e ausência de release com esse
nome. A entrega deve disponibilizar os dois arquivos de cada par juntos, com
acesso equivalente às fontes. O estado preparatório nos recibos não constitui
uma oferta pública já executada.

## Único passo externo pendente

Autorizar a publicação dos 12 arquivos e das notas desta pré-release. Em seguida,
conferir os downloads públicos por hash, integrar os seis manifestos, repetir o
aceite remoto dos pacotes finais, promover os sete alvos ABI e registrar o
encerramento. T031/T052/T066/T078/T082/T083/T084 continuam abertas até esses gates.
Assinatura Apple, VMs e nova revisão visual não são exigidas.
