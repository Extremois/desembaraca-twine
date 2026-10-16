# CLI

`twine-edge-overlap CAMINHO` ou `python -m twine_edge_overlap CAMINHO`.
Exatamente um caminho posicional existente, extensão `.twee` sem distinção de caixa,
com espaços e Unicode. `--help` e `--version` disponíveis. Sem seleção de destino,
lote, execução de scripts, interface gráfica ou acesso à rede.

Saída ao lado da entrada, nome `<stem>.layout.twee`, depois `<stem>.layout-2.twee`, etc.
Publicação Windows: temporário exclusivo no mesmo diretório, gravação completa, flush,
fsync, releitura/verificação e `os.rename` (falha se destino já existe no Windows).
Colisão repete outro nome sem sobrescrever. Em sistemas que substituem no rename,
usar hard-link exclusivo e remover temporário. A falha/cancelamento limpa temporários
que pertencem à execução, sem remover preexistentes. Sem caminho válido antes de terminar.

stdout: estado em português, caminho absoluto e três linhas de contagens antes → depois:
`Pares de arestas`, `Pares de nós`, `Pares aresta–nó`. Códigos: 0 sucesso completo,
2 limitações com cópia válida, 1 falha (inclui argumentos inválidos), 130 interrupção.
Falha vai para stderr com categoria e causa acionável, sem caminho anunciado como saída.
Nenhuma falha apresenta traceback como única mensagem. Limitações nunca afirmam
impossibilidade matemática. Sucesso em entrada limpa informa ausência de conflitos.

Graphviz: procurar `TWINE_GRAPHVIZ_DOT` (caminho de executável fornecido pelo operador),
PATH e instalações padrão Windows; executar diretamente sem shell. ELK não é runtime.
Dependência ausente é falha; erro/timeout de motor após baseline íntegra permite fallback
com causa explícita. Falha de escrita/integridade e cancelamento não retornam saída válida.
