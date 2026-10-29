# Modelo de dados e estados

**Escopo aprovado pelo usuário em 2026-10-28:** validação obrigatória por ABI, arquitetura e Python no GitHub Actions: 7 alvos/14 slots. Linux: glibc/musl × x64/ARM64 × Python 3.12/3.14; macOS: Intel/ARM64 × os dois Pythons; Windows x64 × os dois Pythons. As 69 células anteriores são declarações de compatibilidade, sem obrigação de ensaio individual e sem afirmação de validação por distribuição. Assinatura Developer ID e notarização macOS são opcionais e não bloqueiam aceite ou encerramento; não exigem credenciais Apple. Continuam obrigatórios integridade, licenças/fontes, funcionamento, instalação, corpus, offline e recuperação. Nenhuma proteção do sistema é desativada. Sem VMs e sem testes nativos adicionais. A política substitui os critérios anteriores conflitantes.

**Política de validação atualizada por instrução do usuário (2026-10-27):** validar exclusivamente pelo GitHub Actions, diretamente nos runners hospedados e em contêineres quando necessários. Não exigir teste nativo, hardware dedicado, runner próprio, kernel específico ou VM; não criar nem iniciar VMs, inclusive dentro do CI. Esta decisão substitui exigências anteriores desses ambientes e suas pendências históricas. Conservar hashes, integridade, instalação, corpus, recuperação e o ambiente efetivamente exercitado nos logs; não inventar cobertura. Resultados de VMs anteriores são somente histórico e não são gates de aceite.


Modelo proposto, não schema já implementado. Sem banco: metadados confiáveis empacotados e registros locais de runtime. Histórias continuam no modelo vigente da feature [001](../001-reduce-edge-overlap/spec.md).

## HostEnvironment

Campos: `os`, `os_version`, `native_arch`, `python_implementation`, `python_version`, `distribution_id`, `distribution_version`, `channel`, `snapshot_id`, `snapshot_state`, `libc_family`, `libc_version`, `loader`, `cpu_features`, `kernel_version`. `snapshot_state` é `known` ou `unknown`; snapshot só é obrigatório para reconhecer oficialmente um alvo rolling. Desconhecer snapshot não comprova incompatibilidade ABI.

Na implementação, `cpu_variant` registra uma variante de imagem reconhecida ou
string vazia quando desconhecida. Se há variantes distintas da mesma série/arch,
desconhecimento não herda a célula padrão. Em AlmaLinux 10 x86_64, consultar apenas
ARCH/VERSION do pacote almalinux-release, com argv fixa, 1 s/64 KiB e sem rede;
comparar a versão com os-release. CPU flags não identificam a imagem instalada.
Essa observação é parte da classificação no orçamento existente, não atestado
de integridade dos arquivos do SO. O caminho do cache não repete essa consulta.

Normalizar amd64/x86_64 para x86_64 e arm64/aarch64 para aarch64 internamente; conservar nomes públicos de cada SO. Detectar arquitetura do interpretador/processo e host, rejeitando execução que dependa de tradução. Linux lê os-release como dados; nunca executa comandos encontrados nesse arquivo. `ID_LIKE` auxilia diagnóstico, não concede suporte nem prova compatibilidade. Falha em identificar requisito necessário impede escolher artefato por adivinhação.

## SupportTarget, PythonQualification e QualificationEvidence

`SupportTarget`: `id`, `reference_date`, distribuição/SO, versão/série/canal, `snapshot_id` quando rolling, arquitetura, variante CPU, `required_python_minors` fixado em `["3.12", "3.14"]`, `application_revision`, `artifact_id`, `maintenance_state`, `free_eligibility`, `maintenance_sources`, `status`, `python_qualifications`, `evidence_ids`, `pending_reason`.

**Identidade da célula**: distribuição/SO + versão/série/canal + arquitetura + variante CPU + snapshot_id para rolling. A versão Python não integra essa identidade. O estado publicado refere-se à revisão da aplicação/artefato qualificada; não se transfere automaticamente a outra revisão. Versões não rolling registram patch/imagem nas evidências, mantendo a série explicitamente nomeada na matriz.

`PythonQualification`: `target_id`, `python_minor` (`3.12` ou `3.14`), `status`, `application_revision`, `artifact_id`, `evidence_ids`, `pending_reason`. Unicidade por `(target_id, python_minor)` no registro da revisão qualificada; `python_patch`, origem e arquitetura reais ficam em QualificationEvidence. Cada entrada só pode apontar para evidência da mesma célula, revisão da aplicação, artefato e snapshot. Coletar ambos os interpretadores no mesmo baseline do ambiente; mudança no snapshot exige nova célula rolling, não mistura de ensaios antigos/novos.

`QualificationEvidence`: `id`, `target_id`, `python_minor` quando o ensaio depende de interpretador, commit da aplicação/receita, artifact_id e SHA, imagem/digest, SO/kernel/CPU/arquitetura, snapshot_id/inventário quando rolling, patch Python e origem, data, tipo de ambiente (nativo/container/emulado/simulado), comandos, resultados, hashes de originais/saídas, três métricas, rede observada, ensaios de falha/concorrência, reabertura Twine e revisor. Evidência comum como auditoria de licença pode ser referenciada pelos dois ensaios, sem duplicação fictícia. Não conter histórias privadas, caminhos pessoais desnecessários ou credenciais.

Relação: várias células podem usar um artefato; cada célula tem exatamente dois slots de qualificação Python e suas próprias evidências. Slots e alvo usam `pendente → em_qualificacao → validada`; falha de ensaio invalida o respectivo slot e registra motivo. O estado do alvo é derivado: `validada` somente com os dois slots validados e todos os gates comuns completos; `em_qualificacao` enquanto houver progresso sem conclusão integral; `pendente` se nenhum ensaio qualificado foi iniciado. Gate comum falho impede validação mesmo com os dois slots completos. Não permitir atribuir `validada` manualmente sem evidência. Nova imagem/versão não herda aprovação. Componentes existentes podem permitir execução em melhor esforço antes da qualificação oficial da célula, com aviso explícito.

Os registros de implementação usam `checks` somente para gates observados:
verdadeiro significa aprovado e falso significa falha conhecida. Etapas ainda não
executadas ficam em `pending_checks`, não em falso. Somente licenças e revisão
Twine podem ser comuns aos dois slots; ensaios de instalação, primeiro uso,
offline, preservação, recuperação/interrupção/crash/concorrência dependem de Python.
Auditoria comum de artefato pode referenciar os mesmos logs licenciados sem inventar
uma execução de outro SO. Mantém o vínculo lógico de alvo/revisão/artefato/snapshot,
mas não fornece gate de execução. Os hashes reabertos no Twine devem identificar
as saídas verificadas do corpus. Formatos de pacote distintos podem ter SHAs
distintos para a mesma revisão; imagem/kernel/artefato dos ensaios permanecem consistentes.

## EnvironmentSnapshot — identidade rolling offline

`EnvironmentSnapshot`: `schema` (`rolling-host-v1`), `distribution_id` exato, `version_id`, `build_id`, `channel`, `native_arch`, `kernel_release`, `inventory_schema` (`package-inventory-v1`), `manager`, `inventory_sha256`, `snapshot_id`, `label`, `image_digest`, `captured_at`, `evidence_ids`. Campos os-release opcionais ausentes são `null`; identidade/canal não reconhecidos tornam a coleta desconhecida. `label`, imagem e data são metadados de qualificação, não prova de igualdade nem entrada obrigatória fornecida pelo usuário. O label é recuperado do registro empacotado após correspondência do fingerprint.

O inventário é a lista completa de pacotes instalados consultada localmente: pacman produz `[nome, versao_completa]`; rpm produz `[nome, epoch_decimal, versao, release, arquitetura]`. Preservar epoch/release; no rpm normalizar epoch numérico para decimal sem zeros à esquerda. Rejeitar campos vazios, controles, UTF-8 inválido, linhas incompletas ou tuplas idênticas duplicadas; versões RPM diferentes do mesmo pacote são registros distintos. Ordenar tuplas lexicograficamente pelos bytes UTF-8 dos campos, sem locale.

`inventory_sha256` é SHA-256 do JSON `{schema, manager, records}`, serializado UTF-8 com `sort_keys=True`, `ensure_ascii=False`, separadores `(',', ':')` e sem newline final. `snapshot_id` é SHA-256 da serialização canônica das chaves `schema`, `distribution_id`, `version_id`, `build_id`, `channel`, `native_arch`, `kernel_release`, `inventory_schema`, `manager`, `inventory_sha256`; não incluir o próprio hash nem label/imagem/data/evidências no payload. Não incluir histórias, caminhos de entrada, hostname ou usuário.

Fazer duas coletas consecutivas iguais dos metadados/inventário, sob orçamento agregado de 5 s/8 MiB de saída stdout+stderr e até 100.000 registros por leitura, conforme [contrato](contracts/support-policy.md#reconhecimento-de-rolling). Não truncar inventário para obter correspondência. Falha, limite ou divergência resulta em `unknown`. Não persistir resultado de classificação entre execuções sem nova coleta; atualização de qualquer pacote/canal/kernel pode retirar a correspondência oficial sem impedir uso tecnicamente compatível.

Correspondência oficial exige snapshot_id exato num único SupportTarget validado, arquitetura/canal/variante compatíveis e Python corrente em um dos slots obrigatórios validados. Não aceitar somente data, nome da ISO, VERSION_ID, BUILD_ID ou parentesco ID_LIKE. Match de inventário não é prova de integridade dos arquivos do SO nem promove sozinho uma célula. Não publicar hashes ou labels fictícios para alvos ainda pendentes; referências futuras podem ter snapshot_id nulo até captura real, sem serem elegíveis a validação.

## RuntimeCatalog e ArtifactDescriptor

Catálogo schema 2 proposto: `schema_version`, `engine`, `engine_version`, `artifacts` ordenados deterministicamente. Arquivo empacotado; não baixar catálogo mutável ou procurar “latest” durante execução.

`ArtifactDescriptor`: `id`, `os`, `arch`, `abi`, `minimum_os`, `minimum_libc`, `minimum_kernel`, `cpu_requirements`, `build_variant`, `manifest_path`, `manifest_sha256`, `qualification_evidence`, `priority`. Requisitos só são fixados após medição/qualificação. Resolver exatamente um candidato compatível, por prioridade explícita e identidade estável; empate ambíguo é erro de catálogo. Não selecionar pelo nome da distribuição isoladamente.

Manifesto por artefato: versão do schema, identidade do motor/build, URL HTTPS imutável e hosts permitidos, SHA-256/tamanho do ZIP, raiz interna, executável relativo, inventário de arquivos com caminho/tamanho/SHA/modo, bibliotecas aprovadas, notices e hashes, fontes correspondentes e hashes/receita/proveniência, requisitos ABI e identificação de assinatura quando aplicável. Sem hash/URL fictício ou licença pendente em catálogo ativo.

Validação: paths relativos normalizados, sem travessia, nomes duplicados/colisões na plataforma, links, arquivos especiais ou hierarquias contraditórias; limites de volume e contagem aplicados antes e durante extração. Modos POSIX somente de uma lista aprovada (arquivos comuns 0644, executáveis 0755, diretórios privados apropriados), nunca setuid/setgid ou escrita de terceiros. Hash não comprova licença nem ABI: ambos têm gates separados.

Compatibilidade Windows: adaptador lê manifesto schema 1 existente, conserva identidade/cache, ZIP original e avisos; não reinterpreta `win32` como Linux x86 nem troca o artefato por causa do novo schema. A primeira atualização com cache Windows íntegro não deve baixar novamente.

## RuntimeGeneration, ActiveSelector e RuntimeHandle

`RuntimeGeneration`: identidade do artefato incluindo OS/arch/ABI/build/hash, UUID da geração, diretório privado, inventário instalado, notices, `ready` com identidade e resumo de verificação. Windows conserva namespace legado; novas identidades nunca colidem entre ABI/arquiteturas.

`ActiveSelector`: identidade e geração prontas. Escrever registro temporário, flush/fsync, fechar e substituir atomicamente somente após validar/probar a geração no caminho definitivo. Leitores não aceitam staging como pronto.

`RuntimeHandle`: identidade/geração, raiz, executável absoluto, cwd, ambiente privado. Resolvido uma vez antes do baseline; permanece válido durante todo o processamento. Reparação concorrente não altera o handle nem apaga sua geração.

Estados: `ausente/alterado → staging → extraido → verificado → instalado → probado → pronto → ativo`. Falha/interrupção remove somente staging/pendências próprias e mantém seletor anterior. Crash pode deixar geração órfã imutável, nunca ativa sem commit; não implementar coleta de gerações nesta feature. Cache saudável toma caminho offline; preparação/reparo mutáveis usam lock do SO com prazo.

## InputStory, PublishedCopy e OperationResult

Entrada preservada byte a byte; conteúdo, IDs, metadados, direção/multiplicidade de links conservados fora das alterações visuais autorizadas. Saída integral verificada antes de publicação atômica sem sobrescrita, ao lado da entrada. Métricas: conflitos de arestas, sobreposições de nós e travessias de nós alheios; todas não aumentam, seis referências terminam (0,0,0).

Resultado: status, código existente, caminho absoluto quando há cópia válida, três contagens antes/depois e limitações/diagnóstico. Preparação não produz resultado geométrico; erro de dependência não se transforma em sucesso parcial. Aviso de melhor esforço é independente do status de processamento.
