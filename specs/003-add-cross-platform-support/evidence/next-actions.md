# Próximo incremento: Ubuntu 24.04 x86_64

O próximo objetivo é qualificar uma célula completa, com os dois Pythons, sem
esperar todas as distribuições ou alterar o escopo da matriz. A feature continua
parcial: 46/84 tarefas. A contagem não representa percentual de código restante.

Em 2026-10-19 o mantenedor autorizou usar GitHub Actions e enviar a branch. A
primeira execução usa runners hospedados para a regressão compartilhada. Isso
dispensa provisionar uma VM local; a aceitação do bundle Ubuntu continua exigindo
as etapas de auditoria/pacote/rede/revisão descritas abaixo.

## Runner disponível e pendências de aceite

O acesso ao runner Ubuntu 24.04 x64 hospedado está resolvido pelo GitHub Actions.
O workflow `linux-candidate.yml` prepara fonte/SDK privados e executa build e
corpus com os dois Pythons. Não é mais necessário o mantenedor fornecer outra
máquina Ubuntu para iniciar esse incremento. As condições abaixo continuam
descrevendo o ambiente e os gates para o aceite completo da célula.

Identificar uma máquina ou runner existente com Ubuntu 24.04 x86_64, CPU nativa
e kernel/imagem registrados. Pode ser um ambiente remoto; não será criada VM no
computador atual. WSL, container e emulação não satisfazem o aceite nativo da spec.

Informações necessárias para preparar a execução:

- Forma de acesso já configurada ou plataforma de CI/runner disponível.
- SO, arquitetura, kernel e identificador/digest da imagem de teste.
- Disponibilidade de CPython 3.12 e 3.14 nativos, com venv/pip, ou autorização
  específica para preparar interpretadores privados nesse runner.
- Diretório de teste com escrita/execução e acesso HTTPS para adquirir a candidata
  e seu runtime. Não é necessário Graphviz global ou alterar o Python do SO.
- Possibilidade de observar tentativas de rede em nível nativo no ensaio offline.
- Twine em ambiente de revisão para reabrir as seis saídas públicas e registrar
  versão/revisor/hashes. Essa revisão continua sendo um gate separado.

Nenhuma máquina/conta/credencial foi provisionada, nenhum job remoto disparado e
nenhum custo foi autorizado por este documento. O envio da branch e os testes
hospedados foram autorizados posteriormente; publicação de artefatos POSIX exige
seu próprio aceite e autorização. Ainda não há bundle POSIX qualificado com URL.

## Trabalho do projeto antes da aceitação

1. Encerrar a auditoria do bundle glibc x86_64: fontes correspondentes, dados e
   geradores Graphviz, componentes estáticos, notices e dependências do SO.
2. Medir/verificar o artefato e executar seu corpus/relocação no ambiente definido.
   As configurações de kernel/CPU do compilador não substituem essa execução.
3. Disponibilizar candidata com inventário/manifesto e URL/hash reais após a
   autorização de distribuição. O catálogo atual continua somente Windows.
4. Instalar wheel/sdist e candidata remota em venvs externas, nos dois Pythons.
5. Validar primeiro arquivo inválido sem aquisição, primeiro arquivo válido com
   preparação automática, prepare explícito idempotente e corpus offline com
   observação nativa de rede. O coletor agora inclui o primeiro desses ensaios.
6. Executar falhas/recuperação/concorrência, revisão Twine e combinar evidências
   dos dois slots antes de propor a promoção da célula.

Acesso ao runner não aprova o bundle ou suas licenças automaticamente. Há trabalho
de auditoria independente ainda aberto. As ferramentas já existentes devem ser
usadas para fechar o incremento; novos coletores só se justificam por uma lacuna
concreta que impeça esse fechamento.

## Recursos posteriores

ARM64 Linux exige executor ARM64 nativo. macOS 15 precisa de executores Intel e
Apple Silicon e identidade Developer ID/perfil de notarização autorizados no
ambiente de assinatura. Windows limpo e revisão visual permanecem pendentes.
Não é necessário disponibilizar tudo isso para iniciar a célula Ubuntu x86_64.
