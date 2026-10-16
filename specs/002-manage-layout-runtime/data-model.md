# Data Model: runtime de layout gerenciado

## RuntimeArtifact — configuração confiável da aplicação

Um registro aprovado em `runtime-manifest.json`, incluído no checkout, wheel e sdist:

| Campo | Regra |
| --- | --- |
| schema_version | Inteiro de versão do contrato; rejeitar versão desconhecida |
| engine / version | `graphviz` / `16.1.0` |
| platform / artifact_arch | `windows` / `win32`; matriz de host Windows 11 AMD64 |
| url / allowed_redirect_hosts | URL HTTPS fixa do ZIP oficial; hosts exatos de origem/redirecionamento qualificados, sem aceitar destinos arbitrários |
| archive_sha256 | 64 caracteres hexadecimais, valor literal verificado antes da entrega |
| archive_bytes_limit / expanded_bytes_limit / entry_limit | 128 MiB / 512 MiB / 5.000 |
| executable_relative_path | Caminho relativo real do `dot.exe` dentro da árvore; sem caminho absoluto ou subida |
| files | Inventário do ZIP qualificado: caminho normalizado, tamanho e SHA-256 por arquivo |
| generated_files | Caminhos permitidos e validação de configuração criada pela aplicação, quando necessária; nunca executáveis |
| notices / source_references | Textos e avisos locais e URLs de fontes por componente, verificados antes de ativação |
| notices[].package_source / destination / sha256 | Origem relativa no pacote da aplicação, destino relativo sob `third-party-notices/` na geração e SHA-256 esperado de 64 caracteres hexadecimais para cada aviso complementar; rejeitar caminho absoluto, subida ou destino duplicado |

Identidade: engine + version + platform + artifact_arch + archive_sha256. O digest faz parte da chave de cache; mudar arquivo exige novo manifesto e qualificação, não substituição silenciosa. Campos de integridade vazios ou placeholders tornam o manifesto inválido antes de qualquer download/execução.

## RuntimeInstallation — estado persistido local

- `root`: caminho absoluto da geração sob `<chave-do-artefato>/generations/<generation_id>/`, dentro da raiz de cache gerenciada.
- `generation_id`: identificador único por tentativa, usado como um único componente relativo de caminho; não aceitar caminho absoluto, separadores ou subida.
- `artifact_identity`: referência à configuração confiável.
- `ready`: registro escrito pela aplicação somente após verificações; não é fonte de confiança independente.
- `files`: a árvore completa do fornecedor, incluindo bibliotecas, plugins e avisos, com caminhos relativos preservados.
- `third-party-notices/`: avisos complementares copiados do pacote da aplicação, com destinos e hashes conferidos pelo manifesto, disponíveis offline.
- `generated_configuration`: configuração de plugins produzida localmente, se necessária, restrita à própria árvore.
- `active.json`: seletor separado das gerações, com `artifact_identity` e `generation_id`; validar contra o manifesto e a raiz canônica antes de usar. Seleciona somente geração pronta e validada; não contém caminho absoluto fornecido externamente.

Para reutilizar: ler e fechar `active.json`, conferir identidade e todos os arquivos do inventário, incluindo avisos complementares, sem seguir links/reparse points para fora da raiz; rejeitar arquivos extras executáveis/DLLs e alterações inesperadas. Arquivos locais gerados são tratados separadamente. Sondar versão e `json0` em subprocesso com contexto local controlado. Nenhuma checagem envolve a rede. Gerações sem referência ativa não são selecionadas automaticamente, mesmo que contenham ready; handles existentes continuam usando sua geração anterior preservada.

## PreparationAttempt — estado transitório

`attempt_id`, identidade do artefato, `generation_id` exclusivo, staging, ZIP temporário, arquivo de seleção temporário, instante inicial, prazo, bytes recebidos/extraídos e lock de preparação. Não contém dados de histórias. Staging, geração e seletor ficam no mesmo volume.

Transições:

```text
ausente/inválido -> lock -> download -> hash conferido -> extração/avisos validados
                 -> geração no caminho definitivo -> configuração/sondagem -> ready
                 -> seleção atômica em active.json -> pronto para resolução
geração ativa -> validação local -> uso offline
preparação sem seleção -> erro/cancelamento -> geração não selecionada
reparo -> nova geração validada -> seleção atômica -> nova ativa, anterior preservada
```

Um arquivo `ready` sozinho nunca promove uma tentativa. Escrever, descarregar/sincronizar e fechar o seletor temporário antes de substituir `active.json` com `os.replace` sob lock. Encerramento abrupto antes da substituição conserva a anterior saudável para uso offline; depois, a próxima execução usa a nova geração validada offline. Se a substituição falhar, a seleção anterior permanece. Não renomear/remover gerações ativas ou anteriores, nem coletar órfãs nesta entrega. Outras execuções esperam até 10s pelo lock e depois falham com orientação para tentar novamente. A garantia cobre interrupção do processo, sem promessa adicional para falha física de armazenamento ou perda de energia.

## RuntimeHandle — valor em memória

Identidade do artefato, `generation_id`, raiz validada, caminho absoluto do executável, cwd e alterações de ambiente estritamente locais ao subprocesso. É passado da aplicação ao adaptador, nunca ao domínio geométrico. Fixa a geração resolvida durante a execução, sem reler o seletor. Não tem descoberta de PATH, download implícito em `layout` ou alteração do ambiente global.

## RuntimePreparationError — contrato de falha

Categoria de dependência existente com motivo identificável: plataforma não suportada, manifesto inválido, rede/TLS/HTTP, limite de transferência, integridade, arquivo inseguro, espaço/permissão, lock ocupado, sondagem ou publicação. Campos de apresentação: causa conhecida, impacto e ação sugerida. Não expor dados de histórias, credenciais de proxy ou traceback no fluxo normal.

## Dados Twine preservados

Nenhuma entidade do formato ou do domínio precisa mudar. Entrada, nós, conexões, contagens e resultado mantêm os [contratos anteriores](../001-reduce-edge-overlap/contracts/format-profile.md). RuntimeArtifact e PreparationAttempt não recebem conteúdo, títulos ou caminhos de histórias para transferência externa. Download leva somente requisições do pacote; layout continua local com IDs sintéticos e geometria.
