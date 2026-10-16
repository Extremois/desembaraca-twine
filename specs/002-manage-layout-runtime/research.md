# Research: runtime de layout gerenciado

Data: 2026-10-16. Pesquisa documental e inspeção do código; não é validação do binário.

## 1. Forma de disponibilização

**Decision**: Obter automaticamente o ZIP oficial completo Graphviz 16.1.0 win32 em cache privado do usuário. Manter `dot` como processo externo e a transformação atual limitada às posições.

**Rationale**: A [página oficial de downloads](https://graphviz.org/download/) oferece ZIPs 16.1.0 de 32 e 64 bits com ferramentas e bibliotecas e links de SHA-256. O runtime anteriormente exercitado e inventariado no projeto é win32; mantê-lo reduz a mudança experimental. A escolha de download gerenciado é uma conclusão deste plano: não significa que o ZIP já tenha sido exercitado em ambiente limpo.

Artefato selecionado: [ZIP win32 16.1.0](https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/16.1.0/windows_10_cmake_Release_Graphviz-16.1.0-win32.zip). [Checksum oficial](https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/16.1.0/windows_10_cmake_Release_Graphviz-16.1.0-win32.zip.sha256). O navegador de pesquisa não renderizou o checksum, servido como conteúdo binário; nenhum valor foi inventado. Durante a implementação, obter o ZIP e o checksum, comparar o SHA-256 calculado e registrar o valor literal e o inventário de arquivos no manifesto versionado. A aplicação nunca baixa o checksum para decidir em quem confiar na mesma execução.

**Alternatives considered**:

| Alternativa | Resultado |
| --- | --- |
| Incluir o runtime completo na entrega | Dispensa download específico no primeiro uso, mas aumenta o artefato e o trabalho de distribuição/avisos; não é exigida instalação inicial offline |
| Download oficial gerenciado | Escolhida: mantém o checkout leve e o motor já comparado; exige tratamento de rede somente na preparação/recuperação |
| Instalar via EXE ou gerenciador sistêmico | Rejeitada: amplia dependência de permissões, ferramentas externas e estado global |
| Trocar por ELK.js, outro motor ou WASM | Rejeitada nesta feature: reabre comparação de qualidade e integração, sem necessidade para remover configuração manual |
| Algoritmo próprio | Rejeitada: não há evidência de necessidade; aumenta risco geométrico e custo de manutenção |

Usar a [comparação existente](../001-reduce-edge-overlap/research.md) como evidência local da seleção de motor, não como prova do novo modo de distribuição. O inventário de 97 executáveis/DLLs existente descreve outra instalação: não substitui inventário do ZIP escolhido.

## 2. Integridade, extração e prontidão

**Decision**: Manifesto confiável incluído no código/pacote, HTTPS com validação de certificado, hash fixado antes da extração, staging privado e validação funcional antes da publicação. Nenhum instalador ou script do ZIP é executado.

**Rationale**: A biblioteca padrão fornece transferência e leitura de ZIP, evitando dependência Python nova. A [documentação urllib.request para Python 3.12](https://docs.python.org/3.12/library/urllib.request.html) descreve HTTPS, timeout e mecanismos de proxy; o desenho usa verificação TLS padrão e não modifica credenciais/configurações do usuário. A [documentação zipfile para Python 3.12](https://docs.python.org/3.12/library/zipfile.html) alerta para inspeção de arquivos não confiáveis. O projeto adotará validação própria dos membros e limites, em vez de presumir que uma chamada a `extractall` seja suficiente.

**Alternatives considered**: confiar só no nome do arquivo, no CRC do ZIP, em `dot -V` ou num marcador `ready` é insuficiente. O desenho verifica hash do download, inventário extraído e uma chamada `-Tjson0` com grafo sintético. Preservar a árvore completa evita assumir que apenas `dot.exe` basta. Se o pacote exigir configuração de plugins, executar `dot -c` somente pela aplicação em staging e validar novamente; nunca pedir essa etapa ao usuário. O [contrato oficial da CLI Graphviz](https://graphviz.org/doc/info/command.html) é a referência para essas opções.

## 3. Cache, offline e concorrência

**Decision**: Cache local por versão, plataforma e hash integral, sem consultas de atualização. Lock de arquivo Windows mantido pelo SO durante preparação/publicação. Staging exclusivo por tentativa. Reutilizar cache íntegro sem rede; reparo é explícito ou automático para cache ausente/inválido.

**Rationale**: Atende à resposta do usuário sobre funcionamento sem internet e isola Graphviz global incompatível. Um lock baseado em handle, via `msvcrt`, é liberado ao terminar o processo e evita inferir expiração apenas por um arquivo antigo. Cada tentativa produz geração exclusiva. Configuração e sondagem ocorrem no caminho definitivo, e a seleção usa substituição atômica de `active.json` no mesmo volume após validação. A geração anterior é preservada, inclusive após a troca; interrupção antes/depois da seleção permite nova execução offline com a anterior saudável/nova validada, respectivamente. Não coletar gerações nesta entrega.

**Alternatives considered**: cache compartilhado em Program Files exigiria permissões; pasta do checkout pode não ser gravável; atualizações em toda execução prejudicam offline; escolha do primeiro `dot` em PATH reintroduz dependência do ambiente.

## 4. Integração e falhas

**Decision**: Preparar uma única vez por operação, depois da validação local da entrada e fora do orçamento de processamento. Injetar o runtime resolvido em `engines.graphviz.layout`. Manter erros de dependência fora do fallback que gera cópia com limitações.

**Rationale**: Hoje `application.run` chama `locate` antes de medir a baseline e `layout` volta a chamar `locate`. Uma substituição ingênua acrescentaria rede dentro dos 60s e duplicaria a resolução. Suspender somente o relógio de processamento durante a preparação preserva o orçamento já consumido por leitura/parse. O contrato de erros já distingue dependência ausente de falha do motor após baseline válida.

**Alternatives considered**: preparar antes de validar o caminho provocaria download para entradas inválidas; aceitar cópia sem melhoria para provar instalação limpa esconderia a falta do componente; manter variável de caminho como recuperação violaria o objetivo desta feature.

## 5. Plataforma e dependências nativas

**Decision**: A matriz oficial desta entrega é Windows 11 x64 com CPython 3.12 x64 ou CPython 3.14 x64, ambas sujeitas à qualificação completa. Preservar `requires-python >=3.12` como mínimo de código/metadados, sem incluí-lo como promessa de suporte às demais versões. Usar pacote win32 como processo filho, sem importação de DLL por Python. Não afirmar validação em Windows 10, ARM64, Linux ou macOS.

**Rationale**: O código e os documentos anteriores só evidenciam execução no Windows. A sessão atual informa AMD64, Windows build 26200 e Python 3.14.6 x64. A seleção de matriz é uma delimitação de validação da entrega, não comprovação de portabilidade do ZIP. Fontes oficiais não substituem ensaio em máquina sem instalação Graphviz e sem runtimes nativos herdados.

**Alternatives considered**: adotar win64 simultaneamente duplicaria qualificação sem exigência atual; anunciar todos os Windows com base no nome do arquivo seria uma inferência sem ensaio. Se o ZIP não for autossuficiente, identificar e gerenciar automaticamente o pré-requisito adicional antes da aceitação; nenhuma instalação manual de Graphviz será adicionada ao quickstart.

## 6. Licenças e proveniência

**Decision**: Manter o código autoral Apache-2.0 e identificar separadamente os componentes obtidos, conservar avisos e disponibilizar as referências de fontes correspondentes. Atualizar `docs/third-party.md` antes de ativar o manifesto. Fixar origem no pacote, destino relativo e SHA-256 de cada aviso complementar; copiá-lo para `third-party-notices/` em cada geração e verificá-lo antes da prontidão e no uso offline.

**Rationale**: O [LICENSE da tag Graphviz 16.1.0](https://gitlab.com/graphviz/graphviz/-/raw/16.1.0/LICENSE) declara EPL-2.0. Essa evidência não determina licenças das DLLs transitivas. O download direto não será usado como justificativa para dispensar FR-011 ou a constituição. A inclusão de cada componente requer identificação, compatibilidade e textos/avisos aplicáveis; lacunas impedem ativação.

**Alternatives considered**: atribuir EPL-2.0 à árvore inteira, copiar a instalação atual sem revisar componentes ou supor que uma URL de download satisfaça todos os avisos foram rejeitados. Nenhum parecer de compatibilidade universal é presumido.

## Saída da pesquisa

As escolhas de arquitetura estão resolvidas. Os seguintes itens são qualificações executáveis da implementação: obter e fixar hash/estrutura real; inventariar licenças; executar o pacote em ambiente limpo; testar plugins e eventuais pré-requisitos nativos; executar corpus offline e reabertura. Não são resultados já obtidos. A pesquisa não alterou produção nem incorporou binários.
