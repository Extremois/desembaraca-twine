# Fontes Graphviz e glibc: rota de distribuição

Revisão de implementação em 2026-10-20 para T030/T052/T066. Este documento
define as obrigações que o empacotamento deve atender; não aprova os bundles
nem substitui a revisão dos demais componentes.

## Graphviz, EPL-2.0

A [EPL-2.0, seção 3.1(a)](https://www.eclipse.org/org/documents/epl-2.0/EPL-2.0.html)
exige disponibilizar o código fonte e acompanhar o programa de uma declaração
da licença aplicável e de como obter as fontes. As seções 3.2/3.3 exigem a
licença e a preservação dos avisos. Não basta incluir somente a URL do tarball
sem identificar os direitos sobre o código fonte.

`SOURCE-REFERENCES.txt` passa a declarar EPL-2.0, apontar para
`Graphviz-COPYING.txt` e identificar URL, revisão e SHA-256 do Graphviz.
Linux e macOS recebem a mesma declaração. O arquivo continua coberto pelo
índice offline de origens. Subcomponentes preservam suas próprias condições.

A fonte original está fixada em `source-lock.json`; as fontes/receitas
específicas do build precisam acompanhar a entrega final. A recuperação pública
e as reconstruções já registradas são evidências técnicas aproveitáveis,
mas não autorizam ignorar alterações, arquivos gerados ou termos de terceiros.
Não se presume licença secundária GPL pelo simples texto do Exhibit A da EPL.

## Glibc, LGPL-2.1-ou-posterior

O [texto LGPL-2.1 distribuído pela glibc](https://raw.githubusercontent.com/bminor/glibc/master/COPYING.LESSERv2)
foi confrontado com as seções 0, 4 e 6 do texto integral local
`lgpl-2.1-COPYING.txt`, fixado em `material-source-lock.json`.

As observações de objetos retidos demonstram código startup/nonshared nos dois
executáveis glibc. Algumas fontes não têm a exceção adicional de link:
`csu/init.c` nas duas arquiteturas e `sysdeps/aarch64/start-2.33.S` em ARM64.
Por isso, a rota escolhida cobre conservadoramente todo esse código pela LGPL,
sem depender de provar o descarte de cada unidade ou de estender uma exceção.
O uso dinâmico da libc do sistema não elimina o código já copiado no executável.

| Obrigação | Implementação/evidência | Pendência concreta |
| --- | --- | --- |
| Aviso de uso da biblioteca e licença, seção 6 | `SOURCE-REFERENCES.txt` identifica GNU C Library, startup/nonshared e LGPL-2.1-ou-posterior; o texto integral e os prefixos individuais já integram os avisos | Conferir esse aviso atualizado nos novos pacotes nativos |
| Modificação para uso próprio e engenharia reversa para depuração, seção 6 | O aviso identifica expressamente essa condição para os termos da distribuição | Conferir os termos finais; não adicionar uma proibição incompatível |
| Fontes da biblioteca, seções 0/4/6(a) | Exportação preserva a árvore `lib/` completa do SDK fixado, incluindo fontes/headers glibc e avisos; recibos conferem os bytes | Vincular a exportação exata ao bundle final e revisar modificações/geradores necessários |
| Trabalho que usa a biblioteca, seção 6(a) | Fonte Graphviz completa, receitas, dados e utilitários exportados; reconstruções funcionais já executadas | Demonstrar também relink com uma alteração controlada na biblioteca e entregar instruções correspondentes |
| Acesso equivalente, seção 6(d) | Rota escolhida: fontes completas junto ao binário no local de distribuição, sem exigir que o usuário baixe ambas | Preparar o par binário/fontes final com hashes e acesso equivalente; publicação depende da autorização existente para esse destino |

O texto 6(a) admite o trabalho que usa a biblioteca em código objeto **e/ou
código fonte**. Não é obrigatório acrescentar objetos Graphviz se a entrega
completa em fontes realmente permite recompilar e relinkar. A exportação ampla
do SDK permite cobrir as fontes observadas sem depender de uma atribuição
exaustiva de instruções a cada arquivo para excluir material.

A alternativa 6(c) é uma oferta escrita válida por pelo menos três anos.
Ela não foi escolhida nem emitida. Portanto, não tratamos esse prazo como uma
exigência universal de qualquer distribuição LGPL. Na rota 6(d), o acesso às
fontes deve acompanhar a disponibilidade do binário. Artefatos temporários de
Actions, isoladamente, não estabelecem a entrega final. Também não basta apontar
somente para o tarball Graphviz e o SDK sem as receitas específicas do build.

## Limite da decisão

A ausência de exceção não é, por si só, uma incompatibilidade insolúvel: há uma
rota de cumprimento identificada na própria LGPL. O estado continua parcial
porque falta executar/entregar essa rota para os pacotes finais e concluir os
demais componentes, em especial as condições ISO dos dados de entidades.
Assinatura macOS e qualificação das células continuam com suas tarefas próprias;
não são pré-requisitos para analisar a licença da glibc nem motivo para deixar
essa análise indefinida.
