# Revisão visual no Twine

Esta revisão fecha a parte visual de T063/T065. Os testes de execução continuam
exclusivos do GitHub Actions. Você só precisa do Twine para abrir as saídas prontas.

## Passo a passo

1. Extraia [abi-review-all.zip](evidence/abi-review-all.zip) e entre em `review-by-hash`.
   São seis arquivos `.twee`; não precisa abrir os relatórios JSON/GZ.
2. Abra o [Twine online](https://twinery.org/2/) em uma janela privativa ou use
   uma biblioteca de testes vazia no Twine instalado. Anote a versão do Twine,
   o sistema operacional e, na versão online, o navegador.
3. Na biblioteca, escolha **Library → Import** (Biblioteca → Importar) e selecione
   um arquivo `.twee`. Abra a história `Synthetic ...` que foi importada.
   [Procedimento oficial](https://twinery.org/reference/en/story-library/creating.html).
4. Confira o mapa conforme a tabela abaixo. Ajuste apenas o zoom; não arraste
   passagens nem aplique organização automática antes da conferência.
   Os blocos devem estar separados e as setas não devem cruzar outros blocos
   nem outras setas. A história `isolated_overlap` não possui setas.
5. Abra as passagens com duplo clique e confira o texto `Synthetic passage.` e
   os links indicados na tabela. Feche o editor sem modificar o conteúdo.
6. Repita com os seis arquivos. Eles compartilham um identificador de teste:
   importe um por vez; se houver aviso de conflito, substitua somente uma
   história `Synthetic ...` criada por você nesta revisão. Não substitua uma
   história pessoal. Se houver erro de importação ou formato ausente, anote
   a mensagem e informe o arquivo afetado.
7. Envie o resultado pelo modelo ao final. Não é necessário calcular hashes:
   os arquivos já foram vinculados por SHA-256 às 28 instalações no Actions.

## O que esperar

| Arquivo | Blocos | Setas esperadas |
|---|---|---|
| `crossing-aa821f1611a9.twee` | P0, P1, P2, P3 | P0 → P3; P1 → P2 |
| `coincident-8644eeb34040.twee` | P0, P1, P2, P3 | P0 → P1; P2 → P3 |
| `isolated_overlap-bef1e0132bce.twee` | P0, P1 | Nenhuma |
| `connected_overlap-137e849cfdf0.twee` | P0, P1, P2 | P0 → P2; P1 → P2 |
| `through_isolated-f2460867ce13.twee` | P0, P1, P2 | P0 → P1; P2 isolado |
| `through_connected-8c13ace7ce2f.twee` | P0, P1, P2, P3 | P0 → P1; P2 → P3 |

As seis saídas distintas correspondem aos mesmos bytes gerados nas sete ABIs,
nos dois Pythons e nos formatos wheel/sdist. O [índice](evidence/abi-recovery-ci-canonical/summary.json)
registra cada correspondência. Isso evita repetir a leitura visual dos mesmos
168 resultados e não constitui aprovação automática.

## Resposta para registrar o aceite

```text
Revisor: seu nome ou identificador
Twine: versão
Ambiente: sistema operacional; navegador e versão, se online
crossing: OK ou problema encontrado
coincident: OK ou problema encontrado
isolated_overlap: OK ou problema encontrado
connected_overlap: OK ou problema encontrado
through_isolated: OK ou problema encontrado
through_connected: OK ou problema encontrado
```

Se todos estiverem corretos, pode resumir as seis linhas como `6/6 OK`.
O aceite visual não aprova licenças, publicação ou promoção de suporte.
