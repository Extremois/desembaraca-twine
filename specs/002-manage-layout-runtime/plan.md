# Implementation Plan: Uso sem instalação separada do Graphviz

**Branch**: `main` (branch Git efetiva; identificador da feature: `002-manage-layout-runtime`) | **Date**: 2026-10-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-manage-layout-runtime/spec.md`

## Summary

Manter Graphviz `dot` 16.1.0 e obter automaticamente seu ZIP oficial completo na primeira preparação. Guardar o runtime em diretório privado do usuário, validar integridade e capacidade de layout antes de usá-lo e reutilizá-lo sem rede. O comando existente continua suficiente: `python run.py CAMINHO`. A aplicação assume o gerenciamento sem instalação global, alteração de PATH ou seleção manual de executável.

A mudança se concentra na preparação do motor e sua integração. Leitor, geração DOT geométrica, avaliador dos arcos Twine, seleção sem regressão e publicação da cópia mantêm seus contratos. A escolha e suas alternativas estão em [research.md](research.md).

## Technical Context

**Language/Version**: `requires-python >=3.12` permanece como restrição mínima do código e dos metadados do pacote. As versões oficialmente suportadas nesta entrega serão CPython 3.12 x64 e CPython 3.14 x64, após validação completa de ambas; outras versões não integram essa matriz. Ambiente observado nesta sessão: CPython 3.14.6 x64, Windows build 26200, AMD64.

**Primary Dependencies**: Biblioteca padrão Python; Graphviz 16.1.0 ZIP oficial win32 executado como processo externo, mesma arquitetura do runtime anteriormente inventariado. Não introduzir wrapper Graphviz, Node, ELK, compilador ou gerenciador de pacotes sistêmico.

**Storage**: Arquivos `.twee`; cache em `%LOCALAPPDATA%\DesembaracaTwine\runtimes\graphviz\`, ou `Path.home()/AppData/Local/DesembaracaTwine/runtimes/graphviz` se LOCALAPPDATA estiver ausente. Subdiretório por versão, plataforma e hash integral do artefato, com `generations/<generation_id>/` e seletor `active.json`; staging e seletor temporário no mesmo volume. Cada geração inclui `third-party-notices/`. Nenhum banco; gerações anteriores/órfãs não são coletadas nesta entrega.

**Testing**: unittest; novos testes unitários de manifesto, transferência, extração e cache, contratos CLI e integração real em ambiente limpo e sem rede. Reutilizar os testes e os seis casos `known_resolvable` de `tests/fixtures/cases.json`.

**Target Platform**: A matriz oficialmente suportada nesta entrega é Windows 11 x64 com CPython 3.12 x64 ou CPython 3.14 x64. Ambas as combinações exigem validação completa de instalação limpa, processamento e uso offline antes da entrega. O requisito `requires-python >=3.12` é o mínimo do código/metadados, não uma promessa de suporte oficial às demais versões. O filho Graphviz win32 executa como processo separado. Windows 10, Windows x86, ARM64, Linux e macOS não integram a matriz desta entrega.

**Project Type**: CLI local, executável pelo checkout; instalação do pacote continua alternativa e exige validação própria.

**Performance Goals**: Preservar até 10 MiB por entrada, 100 nós, 300 links, cabeçalhos até 8 KiB, 60s de trabalho de processamento e 30s por chamada do motor, com até 8 MiB de saída combinada. Preparação tem orçamento separado de 300s, com timeout de conexão/leitura de até 30s e sondagens de até 10s cada; limites cooperativos não garantem interrupção imediata de DNS/I/O do SO.

**Constraints**: Sem administração, PATH global, instalações sistêmicas, atualização automática de versão ou rede com cache saudável. Download HTTPS de origem fixada, hash fixado no projeto antes da execução e extração contida. Limites iniciais: ZIP de até 128 MiB, total extraído até 512 MiB, até 5.000 entradas, espera de lock até 10s. Conferir adequação ao pacote real antes de ativar o manifesto, sem elevar limites silenciosamente.

**Scale/Scope**: Um arquivo por execução e um runtime fixado por versão da aplicação; não criar serviço de atualização, interface gráfica, instalador autônomo ou nova solução de layout.

## Constitution Check

*GATE: avaliação antes da pesquisa e novamente após o desenho.*

| Princípio | Antes da pesquisa | Após o desenho |
| --- | --- | --- |
| I. Open source | Atendido: preservar fontes, licença e documentação públicas | Atendido: instruções PT/EN e inventário fazem parte da entrega |
| II. Clareza | Atendido: mudança restrita à preparação | Atendido: gerenciador coeso com funções separadas, sem novo framework |
| III. Responsabilidades | Atendido: domínio e formato permanecem independentes | Atendido: runtime cuida de rede/cache; motor recebe caminho resolvido; aplicação coordena |
| IV. Integridade | Atendido: manter invariantes existentes | Atendido: preparação falha antes da publicação; saída continua verificada sem sobrescrita |
| V. Qualidade | Atendido: validação proporcional planejada | Atendido: cache, falhas, pacote real, corpus, ambiente limpo e offline com evidências exigidas |
| VI. Decisões justificadas | Atendido: alternativas existentes serão avaliadas | Atendido: comparação registrada em research.md; nenhum algoritmo novo |
| Distribuição e licenças | Atendido nesta fase: nenhum componente incorporado | Atendido pelo desenho: proveniência e avisos exigidos antes de ativar o manifesto; não dispensados pelo download direto |

Nenhuma exceção constitucional. A implementação deve obter hash oficial, inspecionar o ZIP e completar avisos por componente antes de ativar o runtime. Isso é trabalho de qualificação da entrega, não aprovação já obtida nem autorização para incluir componente incompatível.

## Project Structure

### Documentation (this feature)

```text
specs/002-manage-layout-runtime/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   └── managed-runtime.md
└── checklists/requirements.md
```

`tasks.md` será gerado por `$speckit-tasks`, fora desta fase.

### Source Code (repository root)

```text
src/twine_edge_overlap/
├── application.py                 # Preparar uma vez e passar o runtime ao motor
├── cli.py                         # Opção de reparo e progresso em stderr
├── errors.py                      # Erros de dependência com causa/recuperação
├── runtime.py                     # Novo: cache, download, validação, lock e preparação
├── runtime-manifest.json          # Novo: origem/hash/estrutura aprovada
├── engines/graphviz.py            # Usar executável resolvido, sem nova descoberta
├── engines/process.py             # Reutilizar runner limitado; ambiente/cwd por chamada
├── formats/profile.py             # Contrato preservado
└── domain/                        # Geometria e seleção preservadas

tests/
├── unit/test_runtime.py           # Novo: integridade, extração, estados e limites
├── contract/test_cli_runtime.py   # Novo: mensagens, preparação e reparo
├── integration/test_runtime.py    # Novo: runtime real, offline e recuperação
├── integration/test_reference_layouts.py
└── fixtures/

docs/third-party.md                # Atualizar inventário/avisos e fonte correspondente
README.md                         # Instalação e uso PT/EN
CONTRIBUTING.md                    # Execução de testes e qualificação do manifesto
pyproject.toml                    # Incluir manifesto/avisos no pacote e sdist
```

**Structure Decision**: Expandir a organização atual. Um módulo de runtime com funções delimitadas basta inicialmente; não criar arquitetura de plugins nem abstração de múltiplos motores. Manifesto e avisos devem ser encontrados tanto pelo checkout como pelo pacote instalado.

## Phase 0 — Pesquisa concluída

Alternativas, fontes primárias e decisões em [research.md](research.md). Selecionado download direto do ZIP fixado, não redistribuição de binários no repositório. Não há escolhas técnicas pendentes nesta fase. O hash e a lista de arquivos reais são dados de qualificação a registrar na implementação, nunca placeholders aceitos em produção.

## Phase 1 — Desenho

1. Validar entrada e perfil antes de acessar a rede, evitando preparar componentes para caminho inválido. Suspender a contagem do orçamento de processamento durante a preparação; leitura, parse e trabalho posterior continuam consumindo o mesmo orçamento de 60s. O orçamento de preparação é separado.
2. Resolver somente o runtime gerenciado. Substituir a busca atual por PATH, Program Files e `TWINE_GRAPHVIZ_DOT`; a variável antiga deixa de selecionar executáveis. Documentar a migração. Não remover nem alterar instalações do usuário.
3. Usar cache saudável sem rede; conferir arquivos do inventário fixado e sondar versão/`json0`. Preparar automaticamente se ausente/inválido. Detalhes em [managed-runtime.md](contracts/managed-runtime.md).
   Cada tentativa produz geração exclusiva e copia/verifica os avisos complementares por origem, destino e hash fixados. Configuração e sondagem ocorrem no caminho definitivo antes da escrita de ready e seleção atômica via `active.json`. Interrupção antes da seleção mantém a geração anterior saudável acessível offline; depois da seleção, a nova geração é usada offline. Handles existentes continuam apontando à anterior preservada; não coletar gerações nesta entrega.
4. Passar o executável validado e seu contexto ao adaptador Graphviz; não chamar uma segunda descoberta dentro de `layout`. Ajustar testes com motor falso para injetar explicitamente um runtime/provedor falso, sem rede acidental.
5. Preservar a fronteira de falhas atual: preparação impossível gera `DependencyError`, código 1 e nenhuma cópia, inclusive entrada limpa. Depois da preparação e baseline íntegra, erros do motor conservam o fallback existente com limitações. Cancelamento continua 130.
6. Acrescentar `--prepare-runtime` e `--repair-runtime`, mutuamente exclusivos e sem caminho de história, para preparação antecipada e recuperação; o uso normal continua automático. Não acrescentar configurações de caminho ao usuário.
7. Publicar documentação real somente junto à implementação validada. O quickstart desta fase descreve o contrato futuro e identifica comandos ainda não implementados.

## Validation Strategy

| Requisitos | Evidência exigida na implementação |
| --- | --- |
| FR-001–003; SC-001 | Máquina/VM Windows 11 x64 limpa, sem instalação global, sem variável legada, cache vazio; Python 3.12 e 3.14; primeiro processamento com melhoria |
| FR-004–006; SC-002–003/006 | Suíte existente, seis referências zeradas, dados preservados, colisões, falhas e reabertura Twine |
| FR-007–008/010; SC-004 | Rede negada/cache ausente, pacote errado, hash divergente, extração hostil, falta de espaço/permissão, interrupção antes/depois da seleção atômica, próxima execução offline com geração correta, reparo e concorrência |
| FR-009; SC-005 | Revisor segue README PT/EN desde ambiente limpo; requisitos e conexão explícitos |
| FR-010; SC-007 | Seis referências com rede desabilitada e cache pronto; nenhum acesso de rede tentado no teste automatizado |
| FR-011 | Hash/estrutura/arquivo de origem qualificados, inventário nativo e avisos completos; wheel/sdist preservam manifesto e avisos; cada runtime preparado contém avisos complementares sob third-party-notices/ com hashes conferidos, inclusive offline |

Não considerar cópia intacta sem tentativa de layout como prova do primeiro uso. Testes locais com mocks não substituem execução do ZIP real nem ambiente limpo. Inspecionar dependências nativas e eventuais runtimes Microsoft sem presumir que a instalação global existente os forneça: a feature só é aceita se a aplicação gerenciar tudo que for necessário. Uma necessidade externa não atendida bloqueia a entrega, em vez de criar instrução para instalação manual do Graphviz.

## Status de validação deste plano

Foram lidos código, contratos e fixtures e consultadas fontes oficiais. O ZIP não foi baixado ou executado nesta fase; portabilidade, hash e licenças transitivas não são apresentados como validados. Não houve alteração de código de produção nem execução da suíte para alegar entrega. Branch Git observada: `main`; nenhum hook de branch foi configurado.
