# Quickstart de validação: ambiente sem Graphviz

Este guia valida os comandos implementados `--prepare-runtime`, `--repair-runtime` e o processamento automático. Consulte [validation.md](validation.md) para distinguir os ensaios locais concluídos da aceitação ainda pendente em máquinas limpas. Sucesso com Graphviz global não é prova desta feature.

Por decisão do mantenedor em 2026-10-16, o trabalho atual prossegue no sistema
existente, sem criar VM. O percurso de primeiro uso, seis referências offline e
reparo foi executado com caches separados nas duas versões de Python; veja
[os resultados do host atual](current-host-results.json). Os pré-requisitos de
máquina limpa abaixo continuam específicos da aceitação de portabilidade adiada,
e não são exigência para executar a ferramenta no computador atual.

## Pré-requisitos

- VM ou máquina de teste Windows 11 x64, conta comum, com CPython 3.12 x64 ou CPython 3.14 x64. Essas são as duas combinações da matriz oficial desta entrega; executar e registrar a aceitação completa separadamente em ambas. `requires-python >=3.12` permanece como mínimo de código/metadados, sem promessa de suporte às demais versões.
- Checkout completo em pasta gravável, sem Graphviz instalado e sem cache DesembaracaTwine prévio. Usar VM/conta descartável para evitar apagar cache real.
- Internet para baixar o projeto e, na primeira preparação, o ZIP oficial fixado do Graphviz. O fluxo pelo checkout não exige instalar dependências Python de produção.
- Permissão e espaço para cache, temporários e cópia na pasta da entrada. Reservar pelo menos 2 GiB livres para preparação e eventual reparo com instalação anterior preservada; limites exatos estão no contrato.
- Manifesto qualificado com hash real, árvore, licenças/avisos e suporte `json0`, incluído na entrega. Nenhum caminho de executável ou variável de ambiente precisa ser configurado.

## 1. Primeiro uso real

Abra PowerShell na raiz do checkout e execute:

```powershell
python --version
Get-Command dot -ErrorAction SilentlyContinue
Get-Item Env:TWINE_GRAPHVIZ_DOT -ErrorAction SilentlyContinue
$taskSampleDir = Join-Path $env:TEMP ('twine-primeiro-uso-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $taskSampleDir | Out-Null
$taskInput = Join-Path $taskSampleDir 'história com espaços.twee'
Copy-Item -LiteralPath '.\tests\fixtures\crossing.twee' -Destination $taskInput
$taskOriginalHash = (Get-FileHash -LiteralPath $taskInput -Algorithm SHA256).Hash
python run.py $taskInput
$LASTEXITCODE
(Get-FileHash -LiteralPath $taskInput -Algorithm SHA256).Hash -eq $taskOriginalHash
Get-ChildItem -LiteralPath $taskSampleDir
```

Na VM limpa, a consulta de `dot` e da variável não encontra itens. São verificações do ensaio, não etapas de configuração do usuário. Esperado: a aplicação informa preparação, gera `história com espaços.layout.twee`, retorna 0, mostra caminho absoluto e três contagens finais zero. A comparação do hash retorna `True`. Reabrir a cópia no Twine e conferir história/conexões. O teste só passa com reorganização efetiva do exemplo, não com cópia intacta sem melhoria.

## 2. Uso sem internet após preparação

Desabilite a conexão nas configurações da VM de teste. Execute:

```powershell
python run.py --prepare-runtime
python run.py $taskInput
$LASTEXITCODE
python -m unittest discover -s tests -v
```

Esperado: preparação apenas valida cache e retorna 0 sem rede; novo processamento gera nome disponível `.layout-1.twee` e retorna 0. Os seis exemplos `known_resolvable` em `tests/fixtures/cases.json` ficam com três contagens zero. A suíte preserva contratos e integridade. Um teste automatizado deve também bloquear/interceptar abertura de conexões e falhar se qualquer chamada ocorrer com cache saudável; execução offline manual sozinha não demonstra ausência de tentativas de rede.

## 3. Preparação antecipada e recuperação

Em outra conta/VM limpa com internet:

```powershell
python run.py --prepare-runtime
$LASTEXITCODE
```

Esperado: prepara e valida o runtime, retorna 0 e não gera histórias. É alternativa para preparar antes de ficar sem conexão, sem ser obrigatória para o uso normal.

Sem internet e com cache vazio, tentar `python run.py $taskInput`: código 1, orientação para restabelecer conexão e repetir, nenhuma cópia nova. Restabelecida a conexão, repetir o mesmo comando deve funcionar. Não pedir instalação manual de Graphviz.

Para recuperação deliberada:

```powershell
python run.py --repair-runtime
$LASTEXITCODE
```

Esperado com internet: nova geração da mesma versão, validação no caminho definitivo e seleção atômica por `active.json`, com código 0. A geração anterior permanece disponível. Sem internet, retorna 1 com orientação e mantém a seleção anterior saudável. Repetir offline o processamento demonstra que o reparo falho não destruiu o cache utilizável.

No ensaio automatizado com processos reais e pacote controlado, encerrar o preparador imediatamente antes e depois da substituição de `active.json`. Iniciar outro processo sem rede: antes da troca, deve usar a geração anterior saudável; depois, a nova geração validada. Handles já resolvidos continuam usando a geração anterior. Gerações incompletas ou órfãs não são selecionadas, e nenhuma geração anterior é removida.

## 4. Casos adversos e regressões

Usar testes determinísticos com transporte e pacotes locais controlados para hash divergente, pacote truncado, caminhos inseguros, tamanho excedido, configuração/plugin ausente, bloqueio de cache, falta de permissão/espaço, cancelamento e duas preparações simultâneas. Não depender de indisponibilidade aleatória de um servidor real.

Validar em integração que Graphviz global incompatível e variável legada inválida não afetam a seleção gerenciada; testar cache sob perfil com espaços/acentos. Verificar que atraso de preparação não consome o orçamento de processamento. Conferir mensagem com causa, impacto e recuperação e ausência de saída parcial em cada falha.

Rodar verificações da implementação:

```powershell
python -m compileall -q src
python -m unittest discover -s tests -v
```

Testar também wheel e sdist instalados numa venv fora do checkout, verificando que manifesto e avisos estão presentes e que a CLI prepara o motor sem Graphviz global. Em cada distribuição, conferir os avisos complementares copiados para `third-party-notices/` da geração ativa: destinos e SHA-256 devem corresponder ao manifesto, e os textos devem permanecer acessíveis sem rede. Testar aviso ausente/alterado como geração inválida. Esse caminho pode exigir internet para ferramentas de build; não substituir o ensaio do procedimento recomendado pelo checkout.

## Registro de aceitação

Registrar versões/build/arquitetura do SO e Python, URL/hash do pacote, inventário e licenças, estado inicial sem Graphviz/cache, comandos/códigos, resultados dos seis exemplos, hashes de preservação, reabertura Twine e teste offline. Não registrar histórias privadas, credenciais ou conteúdo de proxy. A aceitação depende de todas essas evidências; as fontes e contratos de planejamento não as substituem.

Referências: [plano](plan.md), [CLI](contracts/cli.md), [runtime](contracts/managed-runtime.md) e [modelo de dados](data-model.md).
