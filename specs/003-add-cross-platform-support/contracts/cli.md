# Contrato público da CLI multiplataforma

**Escopo aprovado pelo usuário em 2026-10-28:** validação obrigatória por ABI, arquitetura e Python no GitHub Actions: 7 alvos/14 slots. Linux: glibc/musl × x64/ARM64 × Python 3.12/3.14; macOS: Intel/ARM64 × os dois Pythons; Windows x64 × os dois Pythons. As 69 células anteriores são declarações de compatibilidade, sem obrigação de ensaio individual e sem afirmação de validação por distribuição. Assinatura Developer ID e notarização macOS são opcionais e não bloqueiam aceite ou encerramento; não exigem credenciais Apple. Continuam obrigatórios integridade, licenças/fontes, funcionamento, instalação, corpus, offline e recuperação. Nenhuma proteção do sistema é desativada. Sem VMs e sem testes nativos adicionais. A política substitui os critérios anteriores conflitantes.

**Política de validação atualizada por instrução do usuário (2026-10-27):** validar exclusivamente pelo GitHub Actions, diretamente nos runners hospedados e em contêineres quando necessários. Não exigir teste nativo, hardware dedicado, runner próprio, kernel específico ou VM; não criar nem iniciar VMs, inclusive dentro do CI. Esta decisão substitui exigências anteriores desses ambientes e suas pendências históricas. Conservar hashes, integridade, instalação, corpus, recuperação e o ambiente efetivamente exercitado nos logs; não inventar cobertura. Resultados de VMs anteriores são somente histórico e não são gates de aceite.


Contrato alvo; Linux/macOS ainda não implementados. Mantém [CLI anterior](../../002-manage-layout-runtime/contracts/cli.md) e perfil de arquivos vigente.

```text
desembaraca-twine CAMINHO.twee
desembaraca-twine --prepare-runtime
desembaraca-twine --repair-runtime
desembaraca-twine --help
```

- Mesmo comando em Windows/Linux/macOS, um arquivo por execução; opções de preparo/reparo não recebem história. Caminhos relativos são relativos ao cwd do usuário; não ao checkout, cache ou executável.
- Console script é instalado pelo pacote. Após ativar o venv funciona de qualquer pasta; alternativa sem alterar PATH: caminho absoluto ao console script do venv ou ao seu Python seguido de `-m twine_edge_overlap`.
- Pré-requisito é CPython 3.12 ou 3.14 da arquitetura nativa com venv/pip disponíveis; origem e instalação do interpretador documentadas por alvo. Não requer Graphviz, compilador, Git, administrador ou mudança global para uso normal. Instalação remota por ZIP real de commit/release não exige checkout.
- Instalação e primeira preparação exigem conexão; entrada inválida é rejeitada antes de adquirir runtime. Cache saudável permite processamento e preparação idempotente sem tentativa de rede. Reparo explicitamente solicita nova preparação e pode exigir rede; falha conserva geração saudável anterior.
- Mensagens em português, inclusive macOS/Linux. Diagnósticos explicam causa conhecida, impacto e ação aplicável ao SO; não receitam PATH do motor, instalação manual de Graphviz, sudo, remoção de quarentena ou desativação de proteções.
- Se Linux tem ABI compatível, mas célula não validada/fora da matriz, avisar em stderr que o ambiente não foi validado e o uso é de melhor esforço. Prosseguir mantendo todos os controles. Ausência de ABI/componente compatível é erro e impede execução, não simples aviso.
- Em rolling, comparar a identidade local conforme [support-policy.md](support-policy.md#reconhecimento-de-rolling), sem rede. Pacote/canal/kernel alterado ou coleta indisponível gera aviso de ambiente não validado quando ABI compatível; não exigir label da ISO, instalação de gerenciador ou reversão de atualizações. Help não consulta inventário. A execução corrente usa um Python, mas anunciar suporte oficial do ambiente exige os dois slots 3.12/3.14 aprovados.

## Resultado e códigos

| Código | Contrato |
|---|---|
| 0 | Operação concluída conforme contrato existente; processamento só anuncia sucesso completo com três métricas zeradas e demais garantias satisfeitas |
| 2 | Cópia válida com limitações, conforme contrato anterior; nunca mascara indisponibilidade do motor |
| 1 | Falha conhecida, inclusive preparo, ABI, integridade, acesso ou publicação; nenhuma cópia parcial anunciada |
| 130 | Interrupção pelo usuário; preservar originais, arquivos existentes e runtime anterior |

Quando uma cópia válida é publicada, stdout informa caminho absoluto e três contagens antes/depois, além de limitações aplicáveis; diagnóstico/aviso vai para stderr. Preparação/reparo anunciam prontidão somente depois da verificação completa, sem métricas fictícias. Não se altera o significado de códigos anteriores nesta feature.

Originais e destinos ocupados nunca são sobrescritos. Falhas conhecidas de noexec, espaço, permissões, segurança macOS e concorrência devem orientar corrigir a condição e repetir. Não alegar causa específica sem evidência do SO; preservar detalhes úteis sem revelar dados de história em logs.
