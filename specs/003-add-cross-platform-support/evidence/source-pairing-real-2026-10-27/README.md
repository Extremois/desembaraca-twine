# Pareamento sobre quatro pares históricos reais — 2026-10-27

O [resumo](summary.json) registra a revalidação offline das quatro variantes
Linux glibc/musl x64/ARM64 do commit histórico
`47844106ff072cad005a8a1c795153c658b2bc89`. Os arquivos de Actions e os pacotes
de fontes já estavam preservados em `.tmp`; não houve download ou execução
de motor/compilador nesta medição.

| Variante | Arquivos binários/notices | Arquivos no pacote de fontes | ZIP reproduzido |
| --- | ---: | ---: | --- |
| glibc x64 | 480 | 18.175 | Idêntico |
| glibc ARM64 | 544 | 18.175 | Idêntico |
| musl x64 | 421 | 18.175 | Idêntico |
| musl ARM64 | 421 | 18.175 | Idêntico |
| Total | 1.866 | 72.700 | 4/4 |

[capture.py](capture.py) confere o hash de cada arquivo de Actions contra seu
recibo histórico, o inventário binário completo, bytes/tamanhos/modos ZIP e o
índice offline de origens dos notices. Reconstitui somente os membros validados
em uma árvore nova dentro de `.tmp`, sem `extractall`, e executa o empacotador
atual. Exige que SHA-256 e tamanho do novo ZIP coincidam com o candidato antigo.
O recibo novo inclui o hash do executável; o recibo original permanece intacto
e ambos ficam identificados por seus hashes na evidência.

Cada pacote de fontes teve todos os membros confrontados com seu manifesto,
incluindo proveniência embutida idêntica à do binário. O verificador de
pareamento leu ambos os arquivos reais e emitiu os quatro recibos. Alterar a
proveniência declarada das fontes foi recusado em cada variante.

O modo POSIX é conferido no ZIP/inventário histórico; não se declara medição
de permissões POSIX no Windows (`source_modes_checked: false`). O procedimento
não altera os arquivos originais nem os recibos históricos. Uma nova execução
precisa de novos diretórios de evidência e scratch; o script recusa sobrescrita.

Esses são candidatos históricos de desenvolvimento. Os avisos e arquivos
posteriores têm seus próprios hashes e não recebem esta prova por associação.
O teste não revisa novamente a completude ou licenças das fontes, não executa
novos ensaios nativos, não estabelece URLs públicas permanentes e não promove
catálogo ou suporte. T030/T066 continuam abertas para os pacotes finais e a
entrega correspondente.
