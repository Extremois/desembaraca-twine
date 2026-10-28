# Contrato de qualificação e entrega incremental

**Política de validação atualizada por instrução do usuário (2026-10-27):** validar exclusivamente pelo GitHub Actions, diretamente nos runners hospedados e em contêineres quando necessários. Não exigir teste nativo, hardware dedicado, runner próprio, kernel específico ou VM; não criar nem iniciar VMs, inclusive dentro do CI. Esta decisão substitui exigências anteriores desses ambientes e suas pendências históricas. Conservar hashes, integridade, instalação, corpus, recuperação e o ambiente efetivamente exercitado nos logs; não inventar cobertura. Resultados de VMs anteriores são somente histórico e não são gates de aceite.


A [matriz](../support-matrix.md) é o registro do escopo, com data, fontes de manutenção e condições gratuitas. A célula de suporte é por distribuição/SO, versão/canal/snapshot, arquitetura e variante CPU; contém duas qualificações Python, não duas células independentes. Um artefato glibc compartilhado não valida distribuições automaticamente.

## Agregação das qualificações Python

Cada SupportTarget tem exatamente dois slots PythonQualification, para 3.12 e 3.14. Aprovar um slot não aprova o outro nem o alvo agregado. O alvo só é `validada` quando ambos os slots e gates comuns têm evidência completa do GitHub Actions da mesma célula, revisão da aplicação e artefato; em rolling, também do mesmo snapshot_id. Registrar patch/origem do interpretador em cada evidência, sem impor igualdade de patch entre séries diferentes. Não basta executar a mesma versão Python duas vezes ou misturar registros de snapshots distintos.

Slots faltantes ou inválidos impedem promoção oficial daquela célula. Não bloqueiam a qualificação ou proposta de outra célula completa, conforme a independência entre artefatos de I1. Duplicatas de `(target_id, python_minor)` na mesma revisão são erro de dados; status agregado é calculado, não editado para contornar gates.

## Reconhecimento de rolling

Aplicável a Arch Linux, Arch Linux ARM, Manjaro e Tumbleweed. Não acrescenta consulta remota nem instalação de gerenciador de pacotes. A implementação futura deve coletar EnvironmentSnapshot e calcular os hashes canônicos de [data-model.md](../data-model.md#environmentsnapshot--identidade-rolling-offline).

| Dado | Fonte local e regra |
|---|---|
| Distribuição/versão/build | Ler /etc/os-release como dados; somente se ausente usar /usr/lib/os-release. ID exato; VERSION_ID/BUILD_ID ausentes são null; ID_LIKE não concede suporte |
| Arquitetura/kernel | Arquitetura normalizada do host/processo nativo e release do kernel em execução, não apenas o pacote de kernel instalado |
| Canal Arch/Arch ARM | Valor canônico `rolling` do adaptador para o ID/arquitetura nominalmente cadastrados; o inventário exato limita o estado reconhecido, sem promessa sobre repositórios/atualizações futuras |
| Canal Tumbleweed | Valor canônico `tumbleweed` somente para o ID próprio cadastrado; não inferir Slowroll/Leap por parentesco |
| Canal Manjaro | Ler /etc/pacman-mirrors.conf; exigir uma atribuição ativa Branch com valor stable, testing, unstable ou stable-staging. Ausente, duplicada ou desconhecida resulta em unknown, sem presumir stable. A matriz oficial desta feature qualifica Stable; canal sozinho não prova sincronização dos pacotes |
| Pacotes Arch/Arch ARM/Manjaro | argv fixa `/usr/bin/pacman --query --color never`, sem nomes/filtros/quiet; interpretar todas as linhas nome + versão completa |
| Pacotes Tumbleweed | argv fixa `/usr/bin/rpm --query --all --queryformat '%{NAME}\t%{EPOCHNUM}\t%{VERSION}\t%{RELEASE}\t%{ARCH}\n'`; o argumento contém TAB/newline reais após construção pelo código, sem shell intermediário |

Caminhos de executáveis são absolutos e aprovados pelo adaptador do SO, nunca procurados no cwd/PATH do usuário. `shell=False`, stdin fechado e ambiente mínimo com `LC_ALL=C`; não executar pacman-mirrors, sync, refresh, upgrade, instalação, scripts de pacotes ou conteúdo da história. Limitar leitura de cada arquivo de identidade/configuração a 64 KiB; erro/limite torna a identidade desconhecida. Não descobrir IDs ou comandos arbitrários a partir de conteúdo da configuração.

Duas leituras consecutivas devem produzir o mesmo payload canônico completo. Compartilhar prazo total de 5 s, teto agregado de 8 MiB de stdout+stderr e até 100.000 registros por leitura entre as consultas. Matar/recolher processo que exceder limite; não truncar, deduplicar silenciosamente ou aceitar coleta parcial. Esses são limites conservadores novos de classificação, contabilizados nos 60 s existentes de processamento, ou nos 300 s de preparação/reparo explícitos; não ampliar nenhum orçamento anterior. Help não faz coleta e entrada inválida é rejeitada antes dela.

Comparar snapshot_id com referências empacotadas reais de alvos validados e conferir ID/canal/arquitetura/variante, revisão/artefato e slot Python corrente. Impedir publicação de duas células distintas com o mesmo identificador completo e correspondência ambígua; rótulos alternativos da mesma captura são metadados de um só alvo. Data, label da ISO e fingerprint isolado sem alvo qualificado não bastam. O usuário não fornece label nem inventário para forçar aprovação.

| Resultado | Classificação e ação |
|---|---|
| Snapshot e alvo agregado validados, Python/variante correspondem | Oficial para o ambiente observado, mantendo demais verificações do motor/arquivos |
| Snapshot reconhecido, mas slots/gates do alvo incompletos | Pendente; uso de melhor esforço com aviso se ABI compatível |
| Pacote/canal/kernel alterado, snapshot sem referência ou coleta ausente/falha/instável/excedida | Ambiente não validado, com motivo; melhor esforço com aviso se ABI compatível |
| Requisito ABI/arquitetura necessário não comprovado ou incompatível | Recusa técnica, independentemente de snapshot/suporte |

Atualizar qualquer pacote, até sem relação com Graphviz, ou reiniciar com kernel diferente pode retirar a correspondência oficial. Não se exige reverter atualizações: continuar em melhor esforço compatível ou qualificar nova captura. O fingerprint reconhece versões declaradas pelo banco de pacotes, não autentica arquivos do SO nem resiste a administrador malicioso. Inventário de usuário permanece local, sem telemetria/upload; evidências publicadas contêm apenas inventário do ambiente de teste. Não reutilizar reconhecimento anterior para esconder mudança do host.

## Promoção de célula

Evidência ligada a commit/artefato/ambiente deve demonstrar:

1. Dois slots CPython 3.12 e 3.14 no GitHub Actions com evidência da mesma célula/revisão/artefato, instaláveis conforme instruções sem substituir o Python do SO; pacote remoto, wheel e sdist, fora do checkout, comando e alternativa sem PATH.
2. Primeira execução sem Graphviz global, preparação automática e explícita; seis referências com três métricas finais zero, corpus restante sem aumento de nenhuma métrica.
3. Original e arquivos existentes preservados byte a byte; conteúdo/IDs/metadados/direção/multiplicidade da cópia preservados; colisão/cancelamento/falha nunca publicam parcialmente.
4. Rede bloqueada após preparo: seis referências processadas, sem tentativa de conexão; notices disponíveis offline.
5. Reparo bem-sucedido e falho; corrupção/ausência, acesso, noexec quando aplicável, espaço, timeout, crash e concorrência exercitados. Reparo concorrente/falho não destrói geração saudável em uso.
6. Seis saídas realmente reabertas no Twine; registrar versão, ambiente e inspeção de dados/layout. Captura ou teste de parser sozinho não equivale à revisão visual.
7. Mensagens de causa/impacto/recuperação e README PT/EN correspondem ao ambiente. Mac distribuído funciona com segurança normal e assinatura/notarização qualificada.

Cada evidência registra o que executou, falhou, foi simulado ou não estava disponível. Jobs e contêineres executados pelo GitHub Actions constituem o ambiente de validação; não é exigido kernel dedicado ou execução em hardware separado. Skips não contam como aprovação. Pode-se reutilizar resultados de teste puro entre células, mas não substituir evidência específica de instalação/execução/arquitetura/arquivo por inferência.

## Publicação e encerramento

Somente células com todos os gates passam a oficialmente validadas. Células pendentes com artefato tecnicamente compatível podem executar com aviso de melhor esforço; ausência de componente compatível impede execução. A release lista validadas e pendentes, sem anunciar “todo Linux”.

Publicação externa, credenciais e criação de infraestrutura não são executadas pelo planejamento. A implementação prepara resultados revisáveis e mantém gates indisponíveis como pendentes. Não criar VM no sistema atual; usar runners hospedados do GitHub Actions conforme disponibilidade.

Entrega parcial é permitida. Concluir a feature requer FR-001–018 e SC-001–010 em toda a matriz acordada, incluindo versões antigas elegíveis, duas arquiteturas quando publicadas, ambos os interpretadores e regressão Windows. EOL ou dificuldade posterior não autoriza apagar silenciosamente uma obrigação; registrar alteração da condição e revisar escopo explicitamente.
