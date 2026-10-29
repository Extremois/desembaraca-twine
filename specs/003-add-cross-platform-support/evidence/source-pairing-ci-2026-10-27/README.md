# Pareamento Linux conferido no CI — 2026-10-27

Checkpoint corrigido: `a825f0d80bd7892de0e307656d28070885a9d1ed`.
Os cinco workflows terminaram com sucesso:

| Workflow | Execução |
| --- | --- |
| Fundação Windows/Linux/macOS, Python 3.12/3.14 | [40565098533](https://github.com/Extremois/desembaraca-twine/actions/runs/40565098533) |
| Linux glibc x64 | [40565098269](https://github.com/Extremois/desembaraca-twine/actions/runs/40565098269) |
| Linux glibc ARM64 | [40565098572](https://github.com/Extremois/desembaraca-twine/actions/runs/40565098572) |
| macOS Intel/Apple Silicon | [40565098360](https://github.com/Extremois/desembaraca-twine/actions/runs/40565098360) |
| Linux musl x64/ARM64 e compatibilidade Alpine 3.21–3.24 | [40565098367](https://github.com/Extremois/desembaraca-twine/actions/runs/40565098367) |

Os seis jobs de fundação executaram 274 testes cada. Windows registra oito
skips por job; Linux/macOS registram seis. A aceitação Windows 11 limpa é
um job separado e continua skipped; não recebe aprovação por esses resultados.
Os oito jobs Alpine cobrem cada versão/CPU com ambos os interpretadores;
permanecem testes de userland em contêiner, sem qualificação nativa Alpine.

A [primeira tentativa](attempt-1.json), no checkpoint `a1acb47`, passou em
fundação/glibc/macOS e falhou em musl nas duas CPUs. Os logs preservados mostram
`PermissionError` ao ler no host o pacote privado criado pelo usuário do
contêiner. O ajuste executa o pareamento dentro do mesmo contêiner e exporta
recibos legíveis nos dois conjuntos de evidência, sem abrir os diretórios
privados. A segunda tentativa usa os mesmos controles de acesso.

[capture.py](capture.py) é o coletor offline da revisão: recebe recibos de
downloads do checkpoint, confere hashes dos arquivos de Actions, inventários
binários/notices e os quatro pacotes de fontes. Exige recibos de pareamento
idênticos em ambos os artefatos e repete a conferência com os dois arquivos
locais. O manifesto completo das fontes e a proveniência embutida são
confrontados com os bytes e o build binário. Os pacotes ficam em `.tmp`;
somente recibos e logs de revisão são preservados aqui.

A [consolidação conferida](summary.json) registra quatro pares Linux, com
1.953 membros binários/notices e 72.912 membros de fontes verificados. Cada
pacote de fontes contém 18.228 membros, dos quais 18.102 pertencem ao SDK.
Os recibos nativos dos dois conjuntos coincidiram em bytes, e os quatro
resultados locais coincidiram integralmente com os emitidos nos runners.
O manifesto completo e a proveniência embutida passaram em todas as variantes.
Os dois bundles macOS também passaram na auditoria de inventário/notices;
somando as seis variantes, são 2.419 membros e 2.407 payloads de notices.

| Linux | Membros binários/notices | Membros nas fontes |
| --- | ---: | ---: |
| glibc x64 | 480 | 18.228 |
| glibc ARM64 | 573 | 18.228 |
| musl x64 | 450 | 18.228 |
| musl ARM64 | 450 | 18.228 |

Os seis logs de fundação ficam em `foundation/`, com hashes dos bytes originais
na consolidação. Os executáveis Linux preservam os hashes históricos medidos;
essa igualdade não transfere aprovação de notices/cache, fonte ou célula para
um ZIP diferente. O índice de distribuição referencia esta revisão separadamente.

Os artefatos temporários de Actions não constituem entrega pública permanente
de fontes. Os bundles macOS continuam sem aprovação de assinatura/notarização;
o fluxo de pareamento integrado nesta rodada é Linux. Completude das fontes,
distribuição final, revisão Twine, Windows limpo e qualificação de toda a matriz
continuam com seus gates. T030/T066 permanecem abertas; nenhum catálogo ou
alvo de suporte foi promovido.
