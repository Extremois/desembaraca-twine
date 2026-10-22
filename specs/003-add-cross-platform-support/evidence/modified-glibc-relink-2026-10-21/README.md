# Glibc: comprovação de reconstrução e relink de biblioteca modificada sob LGPL 2.1 §6

Este diretório contém as evidências autênticas da comprovação técnica da rota
LGPL 2.1 seções 6(a) e 6(d) para o runtime/startup glibc (`crt1.o` e membros de
`libc_nonshared.a`) em `linux-glibc-x86_64` e `linux-glibc-aarch64`.

A comprovação atesta que os usuários podem modificar as fontes do runtime glibc,
recompilar os objetos da biblioteca e relinkar o binário `dot` contra os objetos
compilados do Graphviz existentes, obtendo um motor funcional e diferente sem
recompilar o Graphviz ou depender de código de terceiros não fornecido.

## Resultados dos runners nativos (commit `bead45d`)

| Dimensão | `linux-glibc-x86_64` | `linux-glibc-aarch64` |
| --- | --- | --- |
| Workflow Run ID | `39707588053` | `39707588112` |
| URL do Job | [Run 39707588053](https://github.com/Extremois/desembaraca-twine/actions/runs/39707588053) | [Run 39707588112](https://github.com/Extremois/desembaraca-twine/actions/runs/39707588112) |
| ID do Artefato | `12396056020` | `12396220847` |
| SHA-256 executável baseline | `e712acb3f95800ba373096c21611e299b819daf67ae9b0981cb59ed6b9cb8ff6` | `e5cca07b6a9a80b7ba9d58910baf25be550a62dbbb54e498f5f3da83103967bb` |
| SHA-256 executável modificado | `e4aac65b8657d424501321c609f8292634e9d0dc19da9902364427236e6f79e3` | `10892040441e8c9c0d381c81ef40742f36f6e5e8e788647c2317fc04ef9eb21c` |
| Proveniência build-pai Graphviz | `1af947d403442f1668db333cd48e61902b62c40bb260d306509cd6b7485d1ff8` | `463052e4ad857b3e989d09df28bbc1ffc40eb0024411d00bfcdefc82776b48b4` |
| Inputs de link Graphviz | 59 preservados (100% idênticos) | 59 preservados (100% idênticos) |
| Seções alocadas Graphviz | 620 preservadas (100% idênticas) | 645 preservadas (100% idênticas) |
| Rejeição pelo audit SDK fixado | Confirmada (`ValueError`) | Confirmada (`ValueError`) |
| Inclusão de `.rodata` em `crt1.o` | Sim (124 -> 128 bytes alocados) | Sim (88 -> 96 bytes alocados) |
| Aumento total de `libc_nonshared.a` | Sim (138 -> 139 bytes alocados) | Sim (136 -> 156 bytes alocados) |
| Chamadas de rede no corpus (`strace`) | 0 (zero) | 0 (zero) |
| Controle positivo de processo filho | Detectado | Detectado |
| Casos do corpus / referências limpas | 13 casos / 6 referências limpas | 13 casos / 6 referências limpas |
| Relocação em diretório Unicode/espaço | Aprovada | Aprovada |

## Procedimento técnico de reprodução

O procedimento completo, determinístico e auditado para modificar o SDK,
recompilar os stubs e relinkar o binário está documentado em
[REBUILD-SOURCES.md](../../../tools/runtime/REBUILD-SOURCES.md). A ferramenta
de verificação automatizada é [verify-modified-glibc-relink.py](../../../tools/runtime/verify-modified-glibc-relink.py).

## Limitações e escopo

1. A comprovação atesta exclusivamente a separação técnica entre objetos da
   aplicação Graphviz e objetos da biblioteca glibc, satisfazendo os requisitos
   de relink das seções 6(a) e 6(d) da LGPL 2.1.
2. Não constitui aconselhamento jurídico nem aprovação final de distribuição.
3. A vinculação de empacotamento da oferta de fontes correspondentes aos
   artefatos distribuídos e as análises de compatibilidade de entidades ISO
   permanecem tarefas em andamento.
