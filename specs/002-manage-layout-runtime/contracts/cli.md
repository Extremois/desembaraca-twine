# Contrato CLI: preparação automática

Este é o contrato a implementar. Não anuncia comandos novos como já disponíveis.

## Invocações

```powershell
python run.py 'C:\Grafos\história.twee'
python run.py --prepare-runtime
python run.py --repair-runtime
python run.py --help
python run.py --version
```

Depois da instalação do pacote, o comando `twine-edge-overlap` aceita os mesmos argumentos. `--prepare-runtime` e `--repair-runtime` são mutuamente exclusivos entre si e com o caminho. As opções de ajuda e versão não preparam componentes nem acessam rede. Ausência de argumento/ação, múltiplos caminhos ou combinações inválidas falham com código 1 e orientação de ajuda.

## Uso normal

1. Validar localmente caminho, acesso e perfil. Entrada inválida não inicia download.
2. Resolver/validar runtime gerenciado. Se necessário, preparar automaticamente, exibindo mensagem breve em stderr: preparação em andamento e eventual necessidade de internet. Não solicitar Graphviz, PATH ou variável de ambiente.
3. Com runtime pronto, executar o fluxo existente. O adaptador recebe seu executável absoluto uma vez; não redescobre componentes.
4. Em stdout, manter estado, razão, caminho absoluto da cópia e as três contagens antes/depois. Progresso de preparação fica em stderr e não se confunde com sucesso.

Uma instalação global incompatível ou `TWINE_GRAPHVIZ_DOT` herdada não muda a seleção gerenciada. A variável anterior deixa de selecionar executáveis neste fluxo; registrar essa migração na documentação, sem editar o ambiente do usuário.

## Preparação e reparo

- `--prepare-runtime`: garante runtime pronto, valida cache existente sem rede e informa sua disponibilidade. Se precisar obter o pacote, usa internet. Não lê histórias ou gera `.twee`.
- `--repair-runtime`: força nova preparação da versão fixada e troca somente após validação completa. Exige internet para obter novamente o ZIP, mesmo se houver instalação anterior saudável; avisa esse requisito. Falha mantém a anterior utilizável. Cada reparo cria uma geração e seleciona a substituta validada por troca atômica de `active.json`; a anterior permanece disponível para handles em uso. Após encerramento abrupto antes/depois da seleção, nova execução usa offline a anterior saudável/nova validada, respectivamente. Não troca para versão mais recente.
- Cache ausente/inválido no uso normal tenta preparação uma vez; sem repetição infinita. Uma nova execução retoma a preparação do início com staging novo; não confia em download parcial.

## Códigos e falhas

| Código | Condição |
| --- | --- |
| 0 | Processamento com sucesso completo, ou ação de preparação/reparo concluída |
| 2 | Cópia válida com limitações, conforme contrato anterior |
| 1 | Falha de entrada, dependência/preparação, integridade ou escrita, sem cópia válida anunciada |
| 130 | Cancelamento pelo usuário |

Falha de preparação é `DependencyError` antes do fallback e não gera cópia, mesmo para história já sem conflitos. Depois de prontidão e baseline válidas, falha de execução do motor mantém o fallback anterior quando sua integridade pode ser garantida. Nunca classificar indisponibilidade como sucesso completo.

Mensagem de dependência em português deve informar motivo conhecido, impacto e recuperação concreta. Exemplos de conteúdo, sem fixar texto literal:

- Rede ausente: não foi possível obter o componente; nenhuma cópia gerada; restabeleça acesso e repita o mesmo comando.
- Hash divergente: pacote não passou na verificação e não foi executado; repita `--repair-runtime`; se persistir, relate a falha com versão da aplicação.
- Cache inválido/bloqueado: explique causa conhecida; libere espaço ou acesso, ou encerre outras execuções quando necessário, e use `--repair-runtime`.
- Plataforma não suportada: apresente a matriz de suporte e impeça preparação incompatível.

Não instruir a desativar segurança/TLS nem pedir credenciais de proxy. Erros de sistema sem causa específica identificável devem declarar a incerteza e remeter ao procedimento do projeto.

## Orçamentos

Preparação separada até 300s cooperativos; espera de lock até 10s incluída. Processamento mantém seu orçamento de 60s sem contar preparação, mas contando leitura/parse e trabalho posterior. Motor continua limitado a 30s e 8 MiB de saída. Não alegar prazo absoluto de interrupção para chamadas de I/O do SO. Cancelamento preserva original e não anuncia saída parcial.

## Compatibilidade dos resultados

Continuam válidos os [contratos de formato](../../001-reduce-edge-overlap/contracts/format-profile.md) e de [publicação/CLI](../../001-reduce-edge-overlap/contracts/cli.md), exceto a descoberta/instalação manual de Graphviz, substituída aqui. Nome `.layout.twee`/`.layout-N.twee`, não sobrescrita e significado dos resultados permanecem.
