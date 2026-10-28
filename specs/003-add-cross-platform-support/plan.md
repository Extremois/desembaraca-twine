# Implementation Plan: Uso em Linux e macOS

**Escopo aprovado pelo usuário em 2026-10-28:** validação obrigatória por ABI, arquitetura e Python no GitHub Actions: 7 alvos/14 slots. Linux: glibc/musl × x64/ARM64 × Python 3.12/3.14; macOS: Intel/ARM64 × os dois Pythons; Windows x64 × os dois Pythons. As 69 células anteriores são declarações de compatibilidade, sem obrigação de ensaio individual e sem afirmação de validação por distribuição. Assinatura Developer ID e notarização macOS são opcionais e não bloqueiam aceite ou encerramento; não exigem credenciais Apple. Continuam obrigatórios integridade, licenças/fontes, funcionamento, instalação, corpus, offline e recuperação. Nenhuma proteção do sistema é desativada. Sem VMs e sem testes nativos adicionais. A política substitui os critérios anteriores conflitantes.

**Política de validação atualizada por instrução do usuário (2026-10-27):** validar exclusivamente pelo GitHub Actions, diretamente nos runners hospedados e em contêineres quando necessários. Não exigir teste nativo, hardware dedicado, runner próprio, kernel específico ou VM; não criar nem iniciar VMs, inclusive dentro do CI. Esta decisão substitui exigências anteriores desses ambientes e suas pendências históricas. Conservar hashes, integridade, instalação, corpus, recuperação e o ambiente efetivamente exercitado nos logs; não inventar cobertura. Resultados de VMs anteriores são somente histórico e não são gates de aceite.


**Feature**: `003-add-cross-platform-support` | **Data**: 2026-10-17 | **Spec**: [spec.md](spec.md)

**Branch Git atual**: `feat/002-manage-layout-runtime`. O identificador da feature não representa uma branch criada. Este planejamento não altera branches nem publica releases.

## Summary

Estender `desembaraca-twine` a Linux x64/ARM64 e macOS 15 Intel/Apple Silicon, mantendo preparação automática, processamento local/offline, integridade e regressão Windows. Separar compatibilidade do componente nativo de qualificação de cada distribuição/versão/arquitetura. A [matriz](support-matrix.md) fixa o recorte em 2026-10-17 e permite entrega incremental sem eliminar alvos restantes.

Manter Graphviz 16.1.0 e o ZIP original Windows. Construir seis variantes POSIX: Linux glibc e musl, cada uma em x86_64/aarch64, e Darwin x86_64/arm64. Adaptar cache, locks, permissões e seleção de componentes; conservar algoritmo e contratos de I/O. Esses bundles POSIX ainda não são entregáveis qualificados do projeto: build, licenças e evidência do GitHub Actions são trabalho obrigatório futuro; assinatura/notarização macOS são opcionais.

## Technical Context

**Language/Version**: CPython 3.12 e 3.14 no GitHub Actions, registrando patch por ensaio; metadados `>=3.12` não ampliam o suporte.

**Primary Dependencies**: biblioteca padrão Python; Graphviz 16.1.0 privado; pytest no desenvolvimento. Compilador/CMake e assinatura somente na produção dos bundles, nunca no uso normal.

**Storage**: arquivos locais, catálogo/inventários JSON empacotados, cache por usuário, gerações imutáveis e seletor atômico. Sem banco ou serviço remoto.

**Modelo histórico por distribuição (substituído pelo registro ABI em 2026-10-28)**: SupportTarget identifica ambiente/arquitetura/variante e snapshot rolling, sem Python na chave. Contém exatamente dois PythonQualification (3.12/3.14); estado oficial agregado depende dos dois e de gates comuns na mesma revisão/artefato. [Modelo normativo](data-model.md#supporttarget-pythonqualification-e-qualificationevidence).

**Identidade rolling (U1)**: hash canônico local de distribuição/canal/arquitetura/kernel e inventário instalado, coletado via consultas somente de leitura pacman/rpm em dois resultados iguais. Prazo agregado 5 s/8 MiB/100.000 registros por leitura, dentro dos orçamentos existentes. Falha ou diferença retira reconhecimento oficial, permitindo melhor esforço se ABI compatível; nenhuma rede. [Contrato](contracts/support-policy.md#reconhecimento-de-rolling).

**Testing**: testes unitários/contratuais existentes, integração multiprocesso e falhas reais, corpus, preservação de bytes, wheel/sdist fora do checkout, ensaios no GitHub Actions por célula e reabertura Twine.

**Target Platform**: [support-matrix.md](support-matrix.md): Windows 11 x64 como regressão; macOS 15 Intel/Apple Silicon; versões Linux elegíveis das distribuições nomeadas, x64/ARM64 quando publicadas. Derivadas não herdam suporte oficial.

**Project Type**: CLI instalada. Distribuição Python `twine-edge-overlap`, pacote `twine_edge_overlap`, comando `desembaraca-twine`.

**Performance Goals**: preservar processamento de 60 s; motor 30 s/8 MiB; preparação separada de até 300 s cooperativos, socket 30 s, probe 10 s/1 MiB, lock 10 s. Leitura/validação conta no processamento; aquisição não consome esse orçamento.

**Constraints**: entrada 10 MiB, 100 nós, 300 links, cabeçalho 8 KiB; download 128 MiB, expansão 512 MiB/5.000 entradas. Sem Graphviz global, administrador, mudanças globais ou desativação de proteções. Cache íntegro não tenta rede. Histórias/caminhos não são enviados. Preservar códigos 0/2/1/130.

**Scale/Scope**: um arquivo por execução; seis referências com (0,0,0), corpus restante sem regressão simultânea das três métricas; dois interpretadores por célula. Sem GUI, suporte móvel, executável autônomo, novos formatos/algoritmos ou compatibilidade universal prometida.

## Constitution Check

Constituição 1.0.1; gates avaliados antes da pesquisa e novamente após o design:

| Gate | Inicial | Após design |
|---|---|---|
| I — open source | PASS | PASS: Apache-2.0, receitas públicas e fontes/avisos dos bundles |
| II — manutenção | PASS | PASS: provedor existente, adaptadores locais de inventário com limites; sem framework de plugins/resolvedor de pacotes |
| III — separação | PASS | PASS: CLI coordena, runtime prepara uma vez, motor recebe handle, I/O publica |
| IV — integridade | PASS | PASS: invariantes, publicação sem sobrescrita e rollback explícitos |
| V — qualidade | PASS | PASS: dois slots por célula, revisão/artefato/snapshot consistentes; simulação/skip não aprova ambiente |
| VI — decisões | PASS | PASS: alternativas justificadas em research.md |
| Licenças/dependências | PASS: nenhuma incorporada nesta etapa | PASS de design: inclusão bloqueada até inventário, compatibilidade e fontes correspondentes verificadas |

Sem exceção constitucional. PASS de planejamento não autoriza incorporar binários sem qualificação. As [pendências Windows](../002-manage-layout-runtime/validation.md) não se tornam evidência concluída.

## Project Structure

### Documentation (this feature)

```text
specs/003-add-cross-platform-support/
  spec.md
  plan.md
  research.md
  support-matrix.md
  data-model.md
  quickstart.md
  contracts/
    cli.md
    managed-runtime.md
    support-policy.md
  checklists/requirements.md
```

`tasks.md` já contém 84 tarefas; esta revisão alinha somente referências de modelo/contrato a A1/U1, preservando IDs, progresso e independência por artefato de I1.

### Source Code (repository root)

Estrutura prevista; novos arquivos abaixo ainda não estão implementados:

```text
src/twine_edge_overlap/
  cli.py                         # interface e mensagens
  application.py                 # coordenação e um runtime por processamento
  runtime.py                     # aquisição, verificação, gerações
  runtime_platform.py            # novo: host, ABI, cache, locks, ambiente
  runtime_catalog.py             # novo: validação e seleção
  runtime_snapshot.py            # novo: consultas locais e fingerprint rolling
  runtime-catalog.json           # novo: artefatos qualificados
  support-matrix.json            # novo: classificação de suporte
  runtime_assets/                # novos manifestos POSIX
  runtime-manifest.json          # preservar schema 1 Windows
  third_party/graphviz-16.1.0/    # preservar avisos Windows e hashes
  engines/process.py
  engines/graphviz.py
  files.py
tools/runtime/                   # novo: receitas, inventário, proveniência
tests/unit/
tests/contract/
tests/integration/
tests/fixtures/
.github/workflows/               # novo: build/teste/qualificação
README.md
pyproject.toml
```

**Structure Decision**: manter um projeto Python. Extrair detalhes de plataforma hoje concentrados em runtime.py, sem reescrever parser/otimizador. Separar dados de suporte dos de aquisição; catálogo confiável empacotado, sem descoberta remota de versões.

## Phase 0 — Pesquisa concluída

[research.md](research.md) registra decisões, alternativas e fontes. [support-matrix.md](support-matrix.md) explicita séries elegíveis e condições gratuitas. Não há decisão de produto aguardando esclarecimento. Resultados ABI são gates de qualificação; imagens individuais de distribuições e credenciais Apple não são requisitos de aceite.

A revisão resolve A1 por agregação de dois ensaios Python por alvo e U1 por reconhecimento exato `rolling-host-v1`, com algoritmo, fontes locais, limites, falhas e cenários negativos definidos. Essas são decisões técnicas do projeto; os manuais primários justificam somente os dados disponíveis nas consultas. Não se inventa referência de snapshot nem validação Linux/macOS nesta etapa.

## Phase 1 — Design e sequência

1. Registrar baseline Windows e preservar alterações anteriores de comando/README. Adaptar testes presos a msvcrt/caminhos Windows e adicionar contratos de host, catálogo, permissões POSIX, locks e publicação.
2. Criar receitas Graphviz mínimas com dot, layout e json0; construir as seis variantes por pipelines independentes de artefato, cada um com fechamento de dependências, relocação e auditoria de licenças próprios. Uma variante pronta pode seguir para assinatura quando aplicável e inclusão no catálogo sem esperar builds de outras arquiteturas ou ABIs. A menor baseline glibc deve atender Ubuntu 18.04: medir símbolos/loader/CPU/kernel antes de fixá-los no catálogo. Se necessário, adicionar variante justificada sem retirar células.
3. Generalizar o provedor conforme [managed-runtime.md](contracts/managed-runtime.md), preservando cache Windows. Implementar classificação oficial/pendente/melhor esforço separada da ABI, agregação SupportTarget/PythonQualification e coleta rolling em runtime_snapshot.py. Consultar inventário sem rede nem mudança global, com os limites definidos; identidade desconhecida não é incompatibilidade ABI. Não ativar URL/hash/fingerprint fictícios.
4. Qualificar os sete alvos ABI nos dois Pythons pelo GitHub Actions; não exigir execução individual das 69 declarações. Cada célula pode avançar assim que seu próprio artefato estiver pronto; não há gate conjunto glibc/musl ou Intel/Apple Silicon. Ordem não elimina alvos difíceis nem altera as prioridades P1. Assinatura/notarização é opcional e não bloqueia a liberação macOS.
5. Executar [quickstart.md](quickstart.md), corpus, falhas, concorrência e reabertura Twine; atualizar README PT/EN e matriz com evidências. Liberar apenas células completas; feature permanece pendente até cobertura total.

### Ambientes

Usar runners hospedados x64/ARM64, máquinas existentes e CI. Não criar VM no sistema atual. Contêineres nos runners do GitHub Actions podem validar userland/ABI e os demais testes automatizados, sem exigir VM ou kernel exclusivo. Cada célula requer CPython 3.12 e 3.14 no GitHub Actions, origem e patch registrados. Falta de pacote Python padrão não permite excluir uma distribuição: qualificar instalação do interpretador no espaço do usuário; manter alvo pendente até isso ocorrer.

### Gates de entrega

- Artefato: build rastreável, licenças/fontes/notices, hashes/tamanhos/modos, dependências fechadas, relocação e execução normal; assinatura macOS opcional.
- Célula: instalação remota e wheel/sdist fora do checkout; caminhos com acentos/espaços; preparação/reparo; seis referências offline sem tentativa de rede; corpus sem regressão; bytes preservados; colisão, falha, interrupção, crash e concorrência; seis saídas reabertas no Twine; ambos os interpretadores.
- Classificação: impedir promoção com um slot ausente, Python duplicado ou evidências de revisões/artefatos/snapshots distintos; testar snapshot igual, pacote/canal/kernel alterado, gerenciador ausente, coleta instável/excedida e retorno ao melhor esforço compatível. Não confundir fingerprint com auditoria de integridade do SO.
- Release: somente artefatos reais e qualificados no catálogo, matriz coerente e links de evidência. Publicação não é executada nesta etapa. Skips não aprovam testes que não foram executados.
- Encerramento: FR-001–018 e SC-001–010 em todos os alvos ABI obrigatórios da data de referência. Mudanças posteriores de manutenção são registradas/revisadas, sem apagar silenciosamente compromissos.

## Complexity Tracking

Nenhuma violação constitucional. Seis builds são justificados por arquiteturas e glibc/musl; excluir bibliotecas opcionais apenas quando o corpus demonstrar adequação. O custo de validar versões antigas é explícito e exige entrega gradual.
