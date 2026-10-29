# Guia de validação da implementação

**Escopo aprovado pelo usuário em 2026-10-28:** validação obrigatória por ABI, arquitetura e Python no GitHub Actions: 7 alvos/14 slots. Linux: glibc/musl × x64/ARM64 × Python 3.12/3.14; macOS: Intel/ARM64 × os dois Pythons; Windows x64 × os dois Pythons. As 69 células anteriores são declarações de compatibilidade, sem obrigação de ensaio individual e sem afirmação de validação por distribuição. Assinatura Developer ID e notarização macOS são opcionais e não bloqueiam aceite ou encerramento; não exigem credenciais Apple. Continuam obrigatórios integridade, licenças/fontes, funcionamento, instalação, corpus, offline e recuperação. Nenhuma proteção do sistema é desativada. Sem VMs e sem testes nativos adicionais. A política substitui os critérios anteriores conflitantes.

**Política de validação atualizada por instrução do usuário (2026-10-27):** validar exclusivamente pelo GitHub Actions, diretamente nos runners hospedados e em contêineres quando necessários. Não exigir teste nativo, hardware dedicado, runner próprio, kernel específico ou VM; não criar nem iniciar VMs, inclusive dentro do CI. Esta decisão substitui exigências anteriores desses ambientes e suas pendências históricas. Conservar hashes, integridade, instalação, corpus, recuperação e o ambiente efetivamente exercitado nos logs; não inventar cobertura. Resultados de VMs anteriores são somente histórico e não são gates de aceite.


**Estado**: sete alvos ABI/14 slots qualificados; catálogo público completo, 42 instalações externas e fontes/notices revisados. Resultados em [qualification/summary.json](evidence/final-paired-review-2026-10-28/qualification/summary.json). Testes exclusivamente no GitHub Actions, sem VMs.

## Pré-requisitos e registro

O [procedimento Linux](evidence/linux-prerequisites.md) registra os quatro alvos
ABI glibc/musl em x64/ARM64. Os ensaios usam CPython 3.12 e 3.14 no GitHub Actions,
em venvs externas, sem substituir o Python do SO. Registrar imagem/digest,
SO/kernel/CPU observados, versão/origem do Python, revisão e artefato.
Os dois slots precisam satisfazer a mesma ABI e seus mínimos; não precisam
compartilhar kernel ou imagem. As 69 declarações de distribuição e os snapshots
rolling não exigem execuções individuais. Resultados antigos em WSL/VMs são histórico.

Para a etapa visual, siga [REVIEW-TWINE.md](REVIEW-TWINE.md). Ela usa as seis
saídas prontas do Actions e mantém a revisão no Twine separada dos testes de ABI.

Ter diretórios de usuário com escrita/execução, acesso HTTPS para instalação/preparo, espaço livre suficiente para download/expansão/gerações (manter orientação conservadora de 2 GiB inicialmente) e Twine para revisão. Não instalar Graphviz global. Build dos componentes é responsabilidade do projeto, não do usuário. Usar conta sem privilégios administrativos; macOS sob proteções normais.

## 1. Instalar a candidata, sem checkout obrigatório

A URL imutável abaixo e no README contém a revisão pública
`53fb2aba47d78b5cb4a6679cafaaef5fc5e52c29`, com comando `desembaraca-twine`
e o catálogo completo da spec 003. A preparação, o corpus e o reuso offline
foram aceitos em Linux/macOS/Windows nas duas versões de Python.
A branch `feat/003-add-cross-platform-support` não é URL imutável nem release.

Em shell POSIX, usar `python3.12` ou `python3.14` conforme o ensaio:

```sh
python3.12 -m venv "$HOME/.venvs/desembaraca-twine"
"$HOME/.venvs/desembaraca-twine/bin/python" -m pip install "https://github.com/Extremois/desembaraca-twine/archive/53fb2aba47d78b5cb4a6679cafaaef5fc5e52c29.zip"
"$HOME/.venvs/desembaraca-twine/bin/desembaraca-twine" --help
"$HOME/.venvs/desembaraca-twine/bin/python" -m twine_edge_overlap --help
```

Esse fluxo dispensa ativação/PATH, Git e Graphviz global. Para usar 3.14, trocar
o interpretador no primeiro comando. Não reaproveitar uma venv de outra versão.
Instalação requer HTTPS ao GitHub e ao índice Python; help não adquire o motor.
O workflow `documented-installation.yml` executa instalação e as três chamadas de
help em venv externa, com PATH contendo somente a venv e sem runtime preparado.
Esse é teste dos comandos documentados, não qualificação de célula ou motor.

A revisão acima já contém os manifestos qualificados e usa os artefatos públicos.
Os percursos 2–4 descrevem a preparação, o processamento e a recuperação cobertos
pelos recibos finais. Falhas deliberadas usam apenas caches temporários do CI.

Em PowerShell, usar o Python nativo selecionado e chamar diretamente a venv, sem mudar política de execução:

```powershell
python -m venv "$HOME\.venvs\desembaraca-twine"
& "$HOME\.venvs\desembaraca-twine\Scripts\python.exe" -m pip install "https://github.com/Extremois/desembaraca-twine/archive/53fb2aba47d78b5cb4a6679cafaaef5fc5e52c29.zip"
& "$HOME\.venvs\desembaraca-twine\Scripts\desembaraca-twine.exe" --help
```

Esperado: instalação sem Git/checkout, compilação de Graphviz, sudo, `--break-system-packages` ou configuração do motor. Help não precisa preparar runtime. Com venv ativada, console script funciona de qualquer pasta. Alternativa sem PATH/ativação em POSIX:

```sh
"$HOME/.venvs/desembaraca-twine/bin/python" -m twine_edge_overlap --help
```

Repetir instalação de wheel e sdist construídos do mesmo commit, em venvs novas **fora do checkout**. No GitHub Actions, com dependências de desenvolvimento disponíveis (não executar testes locais):

```sh
python -m pip install '.[dev]' build
python -m build
python -m pytest
```

Registrar wheel/sdist reais gerados em dist/, seus SHA-256, instalações e importações externas. A suíte portátil já condiciona imports específicos de SO. `python tests/run_foundation.py` exercita essa fundação; não equivale a aceitar um bundle ou uma célula nativa.

O coletor `python tools/runtime/qualify-target.py --help` documenta o percurso de
pacote local instalado em venv externa, com os dois interpretadores disponíveis.
Informar alvo, revisão e hashes reais. Acrescentar `--review-output CAMINHO_NOVO`
para preservar as seis saídas públicas e seu manifesto de hashes antes de remover
a venv temporária. O diretório deve ser novo; a exportação não conclui a revisão.
Reabrir os arquivos numa biblioteca de teste isolada do Twine e registrar versão,
revisor e hashes correspondentes. As referências compartilham IFID, portanto não
devem ser importadas sobre histórias de uma biblioteca pessoal.

## 2. Primeira preparação e caminho externo

Em cache inicialmente vazio, com rede, executar:

```sh
desembaraca-twine --prepare-runtime
```

Esperado: artefato nativo compatível, hashes/notices íntegros e geração pronta. Registrar origem/hash real; conferir ausência de alterações globais. Repetir o comando com cache íntegro e verificar ausência de tentativa de conexão.

Em uma segunda conta/cache inicial limpo, validar também preparação **automática** pelo primeiro arquivo válido, sem rodar prepare antes. Entrada inválida deve falhar sem iniciar download.

Definir `CHECKOUT` como caminho absoluto do checkout de teste. Em diretório temporário novo e vazio:

```sh
TEST_ROOT=$(mktemp -d)
mkdir "$TEST_ROOT/histórias com espaços"
cp "$CHECKOUT/tests/fixtures/crossing.twee" "$TEST_ROOT/histórias com espaços/entrada.twee"
cd "$TEST_ROOT"
desembaraca-twine 'histórias com espaços/entrada.twee'
```

Repetir com caminho absoluto; usar fixture nova/cópia em cada ensaio, sem apagar saídas existentes. Esperado: cópia ao lado da entrada, caminho absoluto e três contagens antes/depois; crossing termina (0,0,0). Original conserva hash. Testar de modo equivalente em PowerShell e repetir em filesystem case-sensitive/case-insensitive quando aplicável.

## 3. Corpus e offline real

Referências conhecidas em tests/fixtures/cases.json: crossing, coincident, isolated_overlap, connected_overlap, through_isolated e through_connected. Copiar as seis entradas para área de teste e registrar hashes antes:

```sh
for case in crossing coincident isolated_overlap connected_overlap through_isolated through_connected; do
  cp "$CHECKOUT/tests/fixtures/$case.twee" "$TEST_ROOT/histórias com espaços/$case.twee"
done
```

Bloquear rede com mecanismo do ambiente de ensaio e observar tentativas de conexão (apenas desligar a rede não prova ausência de tentativas). Então executar:

```sh
for case in crossing coincident isolated_overlap connected_overlap through_isolated through_connected; do
  desembaraca-twine "$TEST_ROOT/histórias com espaços/$case.twee"
done
```

Resultado: 6/6 com (0,0,0), nenhuma tentativa de conexão, hashes dos originais intactos e integridade semântica comprovada. Rodar também o corpus restante: nenhuma das três métricas pode aumentar. Coordenadas podem diferir entre plataformas. Guardar relatórios/códigos por arquivo, não apenas o último código do loop.

Reabrir as seis saídas no Twine do ambiente, conferir dados/conexões/layout e registrar versão/evidência de revisão. Parser ou screenshot isolado não conclui essa etapa.

## 4. Reparo, concorrência e falhas

Com geração saudável, executar com rede:

```sh
desembaraca-twine --repair-runtime
```

Usar cenários isolados de teste para interromper preparo, bloquear download, provocar checksum incorreto, falta de espaço, diretório sem escrita/execução e incompatibilidade. Não corromper o cache pessoal saudável: usar usuário/raiz temporária controlada no harness. Esperado: causa/impacto/recuperação em português, sem bypass de segurança, e nenhum anúncio de runtime/saída parcial.

Depois de reparo falho, bloquear rede e processar novamente com a geração saudável anterior. Concorrer dois preparos; concorrer reparo e processamento longo; matar escritor durante staging/promoção. Verificar lock limitado, seletor íntegro, handles antigos utilizáveis e ausência de remoção de recursos alheios.

Provocar colisão de nome de saída, cancelamento e falha na publicação: originais/destinos existentes mantêm hashes; códigos 0/2/1/130 correspondem ao resultado real. Linux com ABI qualificada recebe suporte por ABI, sem certificação individual de distribuição; ABI ainda não qualificada funciona em melhor esforço quando compatível; componente incompatível deve ser rejeitado. Mac distribuído passa execução real; assinatura/notarização são opcionais, sem remoção de quarentena ou desativação de Gatekeeper.

## 5. Critério de conclusão

Preencher [QualificationEvidence](data-model.md) e aplicar [support-policy.md](contracts/support-policy.md) para cada célula. Registrar nativo/container/emulado/simulado e pendências de forma explícita. Não converter o baseline Windows em aceitação limpa/revisão visual já concluída.

### Agregação dos dois interpretadores

Com registros de ensaio isolados, verificar que somente Python 3.12 completo deixa o alvo sem aprovação; executar 3.12 duas vezes também não substitui 3.14. Combinar evidência de outro artefato, revisão ou snapshot deve ser rejeitado. Somente os dois slots válidos e gates comuns completos permitem proposta de validação. Esses são cenários de dados no harness, sem simular aprovação nativa.

### Reconhecimento de snapshots rolling

Em Arch/Arch ARM/Manjaro/Tumbleweed, a consulta inicial de referência pode ser inspecionada pelos comandos locais abaixo; o harness usa argv fixa sem shell e calcula a canonicalização do [contrato](contracts/support-policy.md#reconhecimento-de-rolling). Rodar somente o comando correspondente ao gerenciador já presente, sem instalar outro:

```sh
/usr/bin/pacman --query --color never
/usr/bin/rpm --query --all --queryformat '%{NAME}\t%{EPOCHNUM}\t%{VERSION}\t%{RELEASE}\t%{ARCH}\n'
```

Os procedimentos de snapshots são ferramentas de diagnóstico históricas; o suporte atual é qualificado por ABI. Um inventário de distribuição não concede certificação individual. Registrar inventário canônico/snapshot_id reais apenas quando esse diagnóstico for exercitado; rótulo/data/imagem são metadados. Alterar pacotes/canal/snapshot muda a identidade diagnóstica, mas não retira, por si só, a qualificação ABI. Arquitetura, libc, kernel e demais mínimos do artefato continuam obrigatórios; uma incompatibilidade deve impedir o uso. Exercitar essas diferenças somente em fixtures ou ambientes temporários do GitHub Actions, sem alterar o computador pessoal.

Exercitar gerenciador ausente, Branch Manjaro ausente/duplicado, coleta instável, timeout agregado 5 s, saída agregada acima de 8 MiB e mais de 100.000 registros por leitura; nunca aceitar inventário truncado. Resultado esperado: identidade desconhecida, diagnóstico de melhor esforço e nenhuma tentativa de conexão. ABI incompatível continua sendo erro. Medir o custo dentro dos orçamentos existentes. Não modificar pacotes do computador pessoal; fixtures simuladas não aprovam snapshots reais nem encerram ensaios no GitHub Actions pendentes.

Somente promover células com todos os gates, ambos os Pythons e links de evidência. Publicar parcialmente exige listar o restante pendente. Encerrar a feature exige a matriz completa; este guia e o planejamento, sozinhos, não demonstram suporte entregue.
