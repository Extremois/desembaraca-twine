# Fechamento T080: mecanismos de limites, privacidade e escrita

A T080 pede a auditoria dos mecanismos da aplicação enumerados no seu texto.
A revisão atual cobre esses mecanismos; os ensaios de pacotes finais e por
célula permanecem nas tarefas T066, T076, T078, T082 e nas tarefas de plataforma.
Nenhuma delas foi marcada como concluída por esta auditoria.

O resultado consolidado está em [security-limits.json](../security-limits.json).
A versão anterior foi preservada em `previous-security-limits.json`, com seu
hash no novo registro. O estado anterior aguardava também pacotes finais;
este fechamento distingue a auditoria dos mecanismos do aceite desses pacotes,
sem alterar o texto da T080 ou os critérios de entrega da spec.

| Execução nova | Casos | Registros de skip | Resultado |
| --- | ---: | ---: | --- |
| Windows atual, CPython 3.12 | 59 | 4 | PASS |
| Windows atual, CPython 3.14 | 59 | 4 | PASS |
| WSL existente, CPython 3.14 | 59 | 6 | PASS |

Os quatro skips Windows são de permissões/symlinks POSIX. No WSL, cinco
subtestes de junction Windows pertencem a dois casos; o sexto skip é o caso
de byte-range lock Windows. Esses registros não contam como passes. O coletor
foi corrigido para comparar identidades de casos pais, em vez de equiparar
quantidade de eventos de skip à quantidade de casos. A primeira tentativa WSL
parou na validação do coletor; não produziu recibo nem falha da aplicação.
Os dois recibos Windows anteriores à correção estão preservados como `runner-v1-*`.

Todos os recibos atuais incluem hashes das 21 fontes Python da aplicação, dos
11 módulos de contratos e do coletor, além dos resultados individuais. Os
arquivos permaneceram iguais durante os testes; ambiente e diretório do
processo pai foram restaurados. Os blobs Git das fontes e contratos existentes,
mais três auxiliares, correspondem ao commit `58f69b0` do CI preservado: seis
jobs aprovados em Windows, Ubuntu e macOS, com 236 testes por job. Isso vincula
os testes POSIX anteriores ao mesmo código, sem transformar WSL em célula nativa.

## Cobertura revisada

| Mecanismo | Código/contratos conferidos |
| --- | --- |
| Preparação 300 s; download 30 s/128 MiB; redirects HTTPS | `runtime.py`, `test_security_limits`, `test_runtime_archives`; prazo cooperativo, timeout restante, contador real de bytes e origem final |
| Probe 10 s/1 MiB; lock 10 s | `RuntimeManager.probe`, `runtime_platform.preparation_lock`; mínimo com prazo restante, descritor OS e concorrência isolada |
| Processamento 60 s; motor 30 s/8 MiB | `application.py`, `engines/graphviz.py`, `engines/process.py`, `test_runtime_budget`; leitura/classificação debitadas, preparação separada, filhos CPython reais para saída/prazo |
| Expansão 512 MiB/5.000 entradas | `RuntimeManager.extract`, contratos de ZIP/POSIX; inventário, contadores reais, nomes/links/modos e hashes |
| Rolling 5 s/8 MiB agregados/100.000 registros por leitura | `runtime_snapshot.py`, seus contratos e `test_security_limits`; duas leituras iguais, argv fixo, sem persistência/rede, fallback limitado |
| Identidade 64 KiB; entrada 10 MiB/100 nós/300 links/cabeçalho 8 KiB | `runtime_platform.py`, `files.py`, `formats/profile.py`, `domain/model.py` e contratos de perfil |
| Privacidade | GET do manifesto sem história; DOT só com IDs gerados/geometria/arestas; ambiente de filhos permitido explicitamente; inventário local e diagnósticos sem seus dados |
| Ausência de alterações globais | Escritas da aplicação limitadas a cópia selecionada, temporários e cache por usuário; permissões apenas nos descendentes criados/extraídos; testes com sentinelas externas e restauração de umask/ambiente |

Para repetir os contratos, na raiz do projeto:

```powershell
python tests/run_security_audit.py --report CAMINHO_NOVO/security-audit.json
```

O comando recusa sobrescrever recibos. Não instala componentes nem executa
Graphviz: transportes/probes são controlados, e os testes de limite de processo
usam filhos CPython. A revisão de escrita combina inspeção de código e testes
isolados; não afirma monitoramento exaustivo do filesystem, contenção de árvores
arbitrárias de processos ou proteção contra todo ataque concorrente do mesmo
usuário. Os prazos são cooperativos, com até dois segundos de limpeza do
processo direto. Auditorias de licenças, assinatura, artefatos e matriz nativa
continuam abertas nas respectivas tarefas. Nenhum catálogo foi promovido.
