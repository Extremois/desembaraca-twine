# Glibc: cruzamento de objetos retidos com fontes observadas

Revisão local dos relatórios nativos preservados; não executa ELF, não
recompila motores e não altera os pacotes existentes.

| Arquitetura | Objetos vinculados | Bytes alocados | Bytes executáveis | Fontes com a frase adicional de link |
| --- | ---: | ---: | ---: | ---: |
| x86_64 | 3 | 262 | 182 | 4 de 5 |
| aarch64 | 3 | 224 | 192 | 3 de 5 |

Os objetos são `crt1.o`, `elf-init-2.33.o` e `fstat-2.32.o` nas duas
arquiteturas. O cruzamento exige mesmo executável, mesmo input por SHA-256 e
membro único dentro do arquivo estático. As seis fontes distintas e seus
prefixos foram novamente comparados aos bytes do SDK fixado. Os recibos
originais e seus hashes permanecem referenciados em `summary.json`.

Correção da revisão: a fonte `sysdeps/aarch64/start-2.33.S` não contém a
mesma frase de exceção do startup x64. `csu/init.c` também não a contém,
em ambas as arquiteturas. A presença textual é registrada por fonte;
não representa aprovação de uma licença nem interpretação de seus efeitos.

`crt1.o` reúne mais de uma unidade fonte. Nenhuma linha de seu mapa retido
usa `.rodata`; não se conclui apenas daí que `init.c` deixou de contribuir
para todo o executável. O objeto local antigo disponível no WSL tem hash
diferente do objeto nativo e foi excluído dessa conclusão. O runtime Zig
ARM64 é listado como input fora do escopo deste cruzamento.

Para reproduzir, obtenha o SDK x64 fixado em
`tools/runtime/REBUILD-SOURCES.md` e execute na raiz do projeto:

```powershell
python specs/003-add-cross-platform-support/evidence/glibc-retained-source-review-2026-10-20/verify.py --sdk-archive CAMINHO/zig-x86_64-linux-0.15.2.tar.xz
```

O script confere o hash do SDK antes de ler fontes, não extrai arquivos e
compara o resultado com o recibo existente sem sobrescrevê-lo. Os cinco
testes em `tests/unit/test_glibc_retention.py` cobrem identidade de executável,
inputs/membros, ambiguidade, integridade de avisos e os limites de atribuição
por fonte. T030 permanece aberta para a auditoria completa dos quatro builds.

A suíte `python tests/run_foundation.py` passou com **241 testes em cada
Python local (3.12 e 3.14), oito skips por execução**. Isso inclui os cinco
testes novos; não é uma nova execução CI nem qualificação nativa POSIX.
O reprodutor também confere os campos novos por arquitetura em
`tools/runtime/licenses/linux.json` contra os fatos do cruzamento.
