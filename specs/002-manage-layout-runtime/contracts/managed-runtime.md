# Contrato do runtime gerenciado

## Origem e confiança

Usar o ZIP oficial completo Graphviz 16.1.0 win32 e manifesto conforme [data-model.md](../data-model.md). O hash deve ser literal, obtido e conferido no desenvolvimento, sem consulta a `latest` ou checksum remoto na execução. Manifesto ausente/inválido impede download e execução. Incluir manifesto e avisos em checkout, wheel e sdist; testar instalação fora da pasta do checkout.

Download por `urllib.request`, HTTPS validado, URL fixa, até cinco redirecionamentos somente para hosts HTTPS exatos qualificados no manifesto. Não desativar verificação de certificados, não aceitar downgrade para HTTP ou dados/URLs indicados pelo arquivo Twine. Sem cookies/autenticação próprios. Aproveitar somente o comportamento padrão de proxy do Python, sem registrar credenciais.

Limites: 128 MiB recebidos, 512 MiB expandidos, 5.000 membros, timeout socket até 30s, orçamento cooperativo global de preparação de 300s. Verificar contagem de bytes realmente lidos/escritos, mesmo se Content-Length ou tamanhos declarados estiverem incorretos. Sondagens de até 10s cada e até 1 MiB de saída combinada. Sem retries ocultos ilimitados; nova invocação inicia nova tentativa.

## Cache e extração

Raiz privada do usuário definida no plano. Nenhum binário é obtido em Program Files, PATH, diretório de trabalho ou caminho fornecido em história. A aplicação não precisa de privilégios de administrador.

1. Validar plataforma/manifesto e procurar instalação exata. Se válida, retornar sem rede.
2. Se preparação necessária, adquirir lock via handle `msvcrt` com espera limitada e revalidar após o lock. O lock não é arquivo cuja mera existência indique processo ativo. No crash o SO libera o handle.
3. Criar staging exclusivo sob a raiz de cache e baixar para arquivo temporário. Conferir hash antes de extrair ou executar.
4. Validar membros antes e durante escrita: rejeitar caminhos absolutos, drive/UNC, `..`, ADS (`:`), nomes reservados Windows, componentes com ponto/espaço final, links/symlinks/reparse points, duplicatas ou colisões após normalização sem distinção de caixa e qualquer destino fora do staging. Rejeitar entradas especiais e limites excedidos. Não seguir links já presentes na raiz de cache.
5. Preservar árvore completa e verificar inventário/avisos. Copiar os avisos complementares do pacote da aplicação para `third-party-notices/` dentro da geração, verificando os hashes fixados no manifesto. Qualificar o caminho relativo real do executável na implementação; não presumir layout de instalação Program Files. Inventariar separadamente arquivos gerados e não aceitar executáveis extras.
6. Mover o staging para um diretório de geração exclusivo em seu caminho definitivo, no mesmo volume, ainda sem selecioná-lo para uso. Gerar configuração de plugins nesse caminho apenas se o pacote exigir. Sondar versão e layout `json0` com grafo sintético de dois nós; validar resultado e identidades. Usar executável absoluto, `shell=False`, cwd local ao runtime e ambiente por subprocesso. Ignorar variáveis herdadas que redirecionem Graphviz/plugins e caminhos de DLL externas; nenhum ajuste global é feito.
7. Após validar arquivos, avisos e sondagem no caminho definitivo, gravar o registro de prontidão e selecionar a geração mediante substituição atômica de `active.json` sob lock. Se outro processo já selecionou geração válida da mesma identidade, revalidar e reutilizar a vencedora no uso normal. Cache incompleto ou geração não selecionada nunca é retornado.

## Reparo e uso simultâneo

Cada preparação produz uma geração em diretório exclusivo: `<chave-do-artefato>/generations/<generation_id>/`. O arquivo `<chave-do-artefato>/active.json` identifica a geração ativa por identidade de artefato e identificador relativo, sem aceitar caminhos absolutos ou subida. A geração deve ser validada em seu caminho definitivo antes de ser selecionada para uso. Depois dessa validação, escrever um arquivo de seleção temporário exclusivo, descarregar e sincronizar seu conteúdo, fechá-lo e substituir `active.json` atomicamente com `os.replace` no mesmo volume, sob lock.

A geração anteriormente ativa permanece disponível, inclusive para processos que já receberam seu RuntimeHandle. Se o processo terminar antes da substituição de `active.json`, a próxima execução continua usando a anterior saudável sem rede. Se terminar depois, utiliza a nova geração validada sem rede. O arquivo de seleção é aberto, lido e fechado na resolução; o handle retornado aponta diretamente para a geração escolhida, sem novas consultas ao seletor durante o layout.

Gerações incompletas ou sem referência ativa não são consideradas prontas para nova resolução. Falha ou encerramento abrupto durante o reparo não remove a geração anteriormente ativa. Se a substituição de `active.json` falhar, manter a seleção anterior e orientar nova tentativa. Não renomear nem apagar uma geração em uso, nem encerrar processos alheios. As garantias de interrupção cobrem encerramento do processo; não constituem garantia adicional contra falha física do armazenamento ou perda de energia.

Limpeza só pode atingir staging e arquivos de seleção temporários da própria tentativa dentro da raiz canônica conferida. Não descartar gerações ativas, anteriores ou órfãs nesta entrega; coleta dessas gerações fica fora do escopo. Não fazer varredura/descarte de diretórios externos ou versões em uso. Processos consumidores não alteram binários; se possível, usam diretórios temporários próprios para DOT e saída.

## Resolução e execução

Interface interna planejada: `ensure_runtime(force_repair=False) -> RuntimeHandle`; sua falha gera erro de dependência. `graphviz.layout(document, deadline, runtime=handle)` usa somente o handle, sem rede ou descoberta de executável. O runner poderá aceitar `cwd` e `env` opcionais, conservando limites e encerramento do filho.

O handle só é emitido após validação e não elimina a possibilidade de falha posterior do SO ou mudança externa no cache. Uma falha entre validação e uso é tratada sem gerar saída incorreta, conforme a fronteira CLI documentada. Não há garantia de proteção contra outro processo malicioso com os mesmos direitos do usuário.

## Privacidade e licenças

Somente o pacote é transferido; histórias, conteúdo, nomes e caminhos não são enviados a serviços remotos. Não introduzir telemetria. Layout permanece local.

Antes de ativar o manifesto: identificar componentes e compatibilidade de uso, conservar os avisos presentes no ZIP e complementar textos/avisos exigidos que faltem no pacote a partir de fontes oficiais, incluindo referências às fontes correspondentes. Esses materiais devem estar acessíveis na distribuição da aplicação e junto ao runtime. Download direto não dispensa esse requisito. Falta de evidência de licença ou pré-requisito nativo não resolvido impede qualificação do artefato.

Para cada aviso complementar, o manifesto identifica origem relativa no pacote da aplicação, destino relativo sob `third-party-notices/` e SHA-256 esperado. A cópia e a verificação desses arquivos integram a prontidão e a reutilização offline. Aviso ausente ou alterado invalida a geração; avisos originais do fornecedor permanecem intactos na árvore extraída.
