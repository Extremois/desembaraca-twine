# Contrato do runtime gerenciado

## Seleção e confiança

1. Identificar SO, arquitetura nativa, Python, distribuição e ABI/requisitos disponíveis.
2. Classificar suporte pela matriz empacotada, com SupportTarget agregado e PythonQualification corrente. Em rolling, coletar fingerprint local em runtime_snapshot.py conforme [support-policy.md](support-policy.md#reconhecimento-de-rolling), sem rede; identidade desconhecida ou sem alvo completo resulta em melhor esforço se ABI compatível. Classificação não substitui seleção técnica.
3. Selecionar artefato compatível do catálogo empacotado e validar manifesto. Sem candidato/condição comprovada: erro claro. Nunca fallback ao dot do PATH ou a outra arquitetura.
4. Reutilizar geração saudável verificada; esse caminho não abre conexão nem consulta atualização. Se ausente/alterada, preparar antes do baseline geométrico; executar uma única resolução por operação.

Schema 2 e adaptador Windows definidos em [data-model.md](../data-model.md). Dados de suporte não podem autorizar hash, origem ou execução não declarados no manifesto. Downloads usam HTTPS com origens/redirects aprovados, sem transmitir história/títulos/caminhos. Não executar scripts do arquivo baixado.

Coleta rolling tem limites próprios de 5 s/8 MiB agregados e 100.000 registros por leitura, sem modificar os limites de motor/probe/download. Contabilizá-la no orçamento já existente da operação. Não é aquisição nem autoriza rede em cache saudável; não altera o handle/identidade de artefato por ter mudado a classificação do ambiente.

## Cache por plataforma

| SO | Raiz |
|---|---|
| Windows | Manter `%LOCALAPPDATA%/DesembaracaTwine/runtimes/graphviz` e fallback/namespace existentes |
| Linux | `$XDG_CACHE_HOME/DesembaracaTwine/runtimes/graphviz` se absoluto; senão `~/.cache/DesembaracaTwine/runtimes/graphviz` |
| macOS | `~/Library/Caches/DesembaracaTwine/runtimes/graphviz` |

Canonicalizar base configurada legítima e restringir operações à raiz gerenciada. Rejeitar links/reparse points/componentes inesperados dentro da árvore gerenciada; não rejeitar indiscriminadamente aliases ancestrais legítimos do SO. Não seguir caminhos vindos de seletores/ZIP para fora da raiz. Diretórios e arquivos de controle POSIX privados, sem escrita de terceiros; conferir propriedade e modos quando necessário. Não prometer isolamento contra outro processo malicioso do mesmo usuário.

## Aquisição, integridade e permissões

Respeitar limites do [plano](../plan.md). Verificar hash/tamanho do arquivo e de cada arquivo expandido; contagem/tamanho reais são limitados durante streaming. ZIP só admite arquivos regulares/diretórios. Rejeitar travessia, caminhos absolutos, nomes reservados aplicáveis, entradas duplicadas, colisões/case aliases da plataforma, links e arquivos especiais. Não confiar em permissões contidas no ZIP: aplicar modos aprovados do inventário POSIX e validar executabilidade. Não aceitar setuid/setgid, escrita pública ou dependência não inventariada.

Preservar notices/fontes/origem acessíveis offline no ambiente preparado e na distribuição. Windows mantém hashes/bytes originais e identidade antiga. Novo manifesto/build requer nova identidade, não alteração da geração existente.

## Lock, promoção e recuperação

Windows conserva msvcrt; POSIX usa flock exclusivo não bloqueante com espera limitada a 10 s. Arquivo de lock persistente não significa lock detido: posse é do descritor do SO, liberada em crash. Escritores revalidam cache depois de adquirir lock. Leitores de geração saudável não dependem de reparo terminar.

Criar staging na mesma raiz/filesystem; extrair/verificar, mover a geração imutável para posição final, executar probe nesse caminho, escrever ready durável e só depois substituir seletor ativo atomicamente. Usar flush/fsync/fechamento e sincronização de diretório onde disponível; não afirmar durabilidade além das garantias do filesystem/SO. Não apagar geração ativa anterior nem gerações em uso. Reparo falho mantém seletor anterior. Cancelamento limpa somente recursos próprios; crash/órfãos não são prova de prontidão. Sem coleta automática nesta feature.

## Subprocesso e publicação

Executável absoluto, `shell=False`, cwd privado e ambiente construído sem mutação global. Preservar apenas variáveis necessárias do SO/locale/temp; não herdar redirecionamentos LD_/DYLD_/GV_ arbitrários. Usar bibliotecas relativas privadas e GVBINDIR controlado. Nenhuma execução do conteúdo da história. Timeout/cancelamento termina o motor e recolhe recursos sem atingir processos alheios; incluir filhos se o build vier a criá-los. Flags Windows não são passadas ao POSIX.

Publicação `.twee` mantém contrato de exclusão de destino: no Windows fluxo existente; POSIX link atômico do temporário validado para nome ainda inexistente e remoção do temporário. `os.replace` serve ao seletor do cache, não ao arquivo da história. Filesystem sem essa garantia falha claramente; não usar cópia parcial ou rename que sobrescreva como fallback. Testar colisões, diferenças de case e nomes Unicode no filesystem real.

## Qualificação do artefato

Build deve registrar revisão Graphviz, fontes correspondentes, receita, compilador/sysroot/imagem e hashes, dependências, SBOM/inventário, licenças e evidência de relocação/ABI. Não exigir recompilação pelo usuário. Não publicar componente com licença incompatível ou não verificada. Mac exige assinatura/notarização e execução nativa sob proteções normais, sem instrução de bypass. Todas as URLs/hashes precisam corresponder a bytes reais antes de entrar no catálogo ativo.
