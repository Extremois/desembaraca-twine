# Como contribuir

Consulte a [especificação](specs/001-reduce-edge-overlap/spec.md), o
[plano](specs/001-reduce-edge-overlap/plan.md), as
[tarefas](specs/001-reduce-edge-overlap/tasks.md) e a
[constituição](.specify/memory/constitution.md) antes de propor uma alteração.

## Ambiente de desenvolvimento

Use Python 3.12 ou posterior e siga a preparação no [README](README.md). No PowerShell,
na raiz deste projeto, verifique o fluxo por código-fonte e a sintaxe:

```powershell
python run.py --version
python -m compileall -q src tests run.py
```

Execute a suíte disponível, incluindo integração com Graphviz instalado:

```powershell
python -m unittest discover -s tests -v
```

A CLI é executável por `python run.py CAMINHO` sem instalar o pacote. Existem testes
funcionais de sucesso, limitações e falhas, e a reabertura dos seis exemplos foi confirmada
pelo usuário. O código autoral usa Apache-2.0. Versões diferentes das exercitadas e a
instalação editável ainda exigem validação própria.

## Propor uma alteração

1. Identifique a tarefa, o problema e o comportamento esperado. Para mudanças de escopo,
   atualize primeiro os artefatos correspondentes e registre decisões e impactos.
2. Faça uma alteração pequena e revisável, respeitando nomes claros e responsabilidades
   separadas entre arquivos, domínio geométrico, motor de layout e interface de terminal.
3. Para mudanças de comportamento, escreva testes proporcionais ao risco. Cubra preservação
   dos dados, casos-limite e regressões relevantes; testes devem observar resultados.
4. Execute as verificações disponíveis. Registre os comandos, resultados, versões e
   limitações na descrição da proposta. Não afirmar verificações que não foram executadas.
5. Atualize a documentação afetada e confira os princípios da constituição antes de integrar.
   Se houver repositório remoto configurado, envie a alteração por pull request com esse
   contexto; enquanto isso, uma alteração ou patch local deve conter as mesmas evidências.

Implementar somente o perfil `.twee` documentado e confirmado pelo usuário. T004–T011 exigem
uma amostra real, validação do perfil, contratos e desenho antes das histórias. Não marcar
tarefas concluídas sem evidência e não alterar marcadores dos checklists durante a implementação.

## Amostras e preservação

Para contribuir com uma amostra, indique sua origem e o aplicativo/versão quando conhecidos.
Confirme se pode ser incluída nos testes versionados. Caso seja privada, mantenha-a fora
do repositório e documente uma forma autorizada de aquisição local; uma amostra sintética
não substitui a confirmação do formato real.

Use cópias para os ensaios. O arquivo original deve permanecer idêntico byte a byte.
Mudanças visuais não podem alterar conteúdo, identificadores, metadados ou conexões.
Uma saída parcial nunca deve ser apresentada como válida. Não executar scripts ou macros
da história para extrair conexões.

## Dependências e licenças

Antes de propor um algoritmo próprio, avalie soluções existentes e registre adequação,
complexidade, manutenção e licenças. Registre dependências novas em
[docs/third-party.md](docs/third-party.md), incluindo versões e modo de integração.
O Graphviz é uma dependência externa escolhida, instalada separadamente.

O código autoral usa [Apache-2.0](LICENSE), com aviso em [NOTICE](NOTICE). Contribuições
devem manter esses avisos e identificar a origem e a licença de materiais incorporados.
Não incluir binários de motores ou amostras privadas sem autorização e avaliação próprias.
