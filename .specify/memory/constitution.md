<!--
Sync Impact Report — material temporário de revisão; remover antes do commit.
Versão: 1.0.0 → 1.0.1 (pendência de licença resolvida por escolha explícita do mantenedor).
Princípios modificados: nenhum; os seis princípios e seus títulos foram preservados.
Seções adicionadas/removidas: nenhuma.
Atualização: restrições de distribuição agora identificam Apache-2.0 e LICENSE.
Pendências de governança: nenhuma. Revisar inventário e avisos antes de distribuir.
-->
# TwineEdgeOverlap Constitution

## Core Principles

### I. Desenvolvimento open source

O código-fonte, a documentação de uso e as instruções de contribuição DEVEM permanecer
acessíveis publicamente. O projeto DEVE declarar explicitamente uma licença de código
aberto, disponibilizar seu texto e indicar onde encontrá-lo. As instruções de contribuição
DEVEM explicar como preparar o ambiente, executar as verificações e propor alterações.
Esses requisitos permitem uso, inspeção e colaboração sob condições conhecidas.

### II. Clareza e manutenção

O código DEVE aplicar Clean Code e boas práticas de engenharia: nomes que expressem
intenção, responsabilidades bem definidas e soluções simples para as necessidades atuais.
As alterações DEVEM seguir os padrões já adotados no projeto. Novas abstrações,
dependências ou desvios desses padrões DEVEM ter justificativa registrada na revisão.
Duplicação e complexidade desnecessárias DEVEM ser eliminadas quando afetarem a mudança.
A clareza DEVE permitir que outra pessoa compreenda e mantenha o comportamento.

### III. Separação de responsabilidades

A leitura e a escrita de arquivos, o processamento de grafos e a interface de uso DEVEM
ter responsabilidades separadas e contratos explícitos. O processamento de grafos NÃO
DEVE depender da interface de uso nem acessar arquivos diretamente. A leitura e a escrita
DEVEM poder ser exercitadas separadamente do algoritmo. A interface DEVE coordenar essas
operações e apresentar resultados e erros, sem concentrar as regras de transformação.
Essa separação DEVE permitir evolução e testes independentes de cada responsabilidade.

### IV. Correção e integridade

As transformações DEVEM preservar o conteúdo dos nós e das arestas, seus identificadores,
atributos e relações, exceto pelas mudanças explicitamente previstas no contrato da operação.
Dados não abrangidos por uma transformação NÃO DEVEM ser descartados silenciosamente.
Cada operação DEVE definir suas alterações permitidas e invariantes de preservação.
Entradas inválidas, formatos não suportados e limites de processamento DEVEM produzir
mensagens claras sobre o problema e, quando possível, como corrigi-lo. Uma falha NÃO DEVE
ser apresentada como sucesso nem deixar uma saída incompleta identificada como válida.

### V. Qualidade verificável

As alterações de comportamento DEVEM ser validadas com testes proporcionais ao risco.
Leitura e escrita de arquivos DEVEM ter cobertura para entradas válidas, entradas inválidas
e preservação dos dados em ciclos de leitura e escrita. O processamento das arestas DEVE
ser verificado quanto aos resultados esperados e à preservação das relações do grafo.
Casos-limite e regressões conhecidos DEVEM ser incluídos quando afetarem a alteração.
Os testes DEVEM observar contratos e resultados, evitando acoplamento desnecessário à
implementação. A revisão DEVE registrar as verificações executadas e eventuais lacunas;
mudanças com risco de perda de dados NÃO DEVEM ser integradas sem evidência de preservação.

### VI. Decisões justificadas

Antes de criar um algoritmo próprio, a equipe DEVE avaliar soluções existentes e registrar
a conclusão. A avaliação DEVE considerar adequação ao problema, correção, complexidade
computacional e de integração, manutenção e compatibilidade de licenças. A escolha de uma
implementação própria DEVE explicar por que as alternativas avaliadas não atendem ao caso.
A adoção de uma dependência DEVE justificar seu benefício e seu custo de manutenção.
O registro DEVE ter detalhe proporcional ao impacto da decisão e ficar acessível no
repositório ou na revisão correspondente.

## Restrições de distribuição e dependências

A distribuição do projeto DEVE incluir a licença declarada e os avisos exigidos pelas
dependências incorporadas. Dependências e código reutilizado DEVEM ter origem e licença
identificadas, com compatibilidade verificada antes de sua inclusão. Uma incompatibilidade
não resolvida DEVE impedir a inclusão do componente.

A licença selecionada explicitamente pelo mantenedor é Apache License, Version 2.0,
identificada como `Apache-2.0`, com texto integral em `LICENSE` na raiz do projeto.
As distribuições DEVEM incluir esse texto e os avisos aplicáveis. Essa escolha não altera
as licenças de dependências externas nem autoriza omitir suas condições em redistribuições.

## Fluxo de desenvolvimento e revisão

Toda proposta de alteração DEVE identificar o comportamento esperado, as responsabilidades
afetadas e os riscos para a integridade dos dados. O planejamento DEVE explicitar os
contratos de entrada e saída e as invariantes relevantes à transformação.

Antes da integração, a revisão DEVE verificar a conformidade com os seis princípios,
examinar as evidências de validação e confirmar a atualização da documentação afetada.
Decisões sobre algoritmos ou dependências DEVEM apresentar a avaliação exigida pelo
princípio VI. A profundidade do registro e da validação DEVE acompanhar o risco da mudança.

## Governance

Esta constituição prevalece sobre práticas e decisões locais conflitantes. Especificações,
planos, tarefas e revisões DEVEM verificar sua conformidade com os princípios aplicáveis.
Conflitos DEVEM ser resolvidos antes da integração, por adequação da proposta ou por uma
emenda aprovada; exceções implícitas não são permitidas.

Emendas DEVEM registrar a motivação, o texto proposto, os impactos e, quando necessário,
um plano de transição. Os mantenedores DEVEM aprovar a emenda antes de sua integração.
A alteração DEVE atualizar a versão e a data da última emenda, preservando a data original
de ratificação. Os artefatos dependentes afetados DEVEM ser identificados na revisão e
adequados no fluxo de trabalho correspondente.

O versionamento DEVE seguir MAJOR.MINOR.PATCH: MAJOR para remoções ou redefinições
incompatíveis de princípios ou regras de governança; MINOR para novos princípios, novas
seções ou ampliação material de orientações; PATCH para esclarecimentos e correções sem
mudança de significado. A versão 1.0.0 representa a primeira adoção desta constituição.

**Version**: 1.0.1 | **Ratified**: 2026-10-16 | **Last Amended**: 2026-10-16
