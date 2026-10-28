# Especificação de Vinculação e Entrega de Fontes Correspondentes

Este documento formaliza os requisitos de vinculação e o esquema de recibo para
a entrega de fontes correspondentes (*corresponding source code*) ao lado de cada
binário distribuído, atendendo conjuntamente à LGPL 2.1 §6(d), à EPL-2.0 §3.1 e
às políticas de integridade de distribuição do Desembaraça Twine.

## 1. Fundamentos contratuais e legais

### 1.1 LGPL 2.1, Seções 6(a) e 6(d)

A rota LGPL 2.1 §6(a)/§6(d) foi estabelecida em [SOURCE-DELIVERY-REVIEW.md](SOURCE-DELIVERY-REVIEW.md)
e comprovada tecnicamente no checkpoint `bead45d` (relink com libc modificada e
instruções completas em [REBUILD-SOURCES.md](../REBUILD-SOURCES.md)).

- **LGPL 2.1 §6(a)**: A distribuição em fontes completas do trabalho e das bibliotecas
  atende à permissão de modificação e relink do programa sem obrigar a entrega de
  arquivos-objeto intermediários quando o material em fontes é suficiente e
  acompanhado de receitas/scripts de compilação reproduzíveis.
- **LGPL 2.1 §6(d)**: Se a distribuição do executável/biblioteca for feita mediante
  oferta de acesso para cópia em local designado, deve-se oferecer acesso equivalente
  para cópia dos materiais de fontes correspondentes *a partir do mesmo local*.
  Não é permitido exigir que o usuário baixe ambos compulsoriamente nem postergar
  o fornecimento das fontes para momento posterior à disponibilidade do binário.

### 1.2 EPL-2.0, Seção 3.1

O Graphviz é licenciado sob Eclipse Public License 2.0 (EPL-2.0). A seção 3.1(a)
exige que o programa distribuído seja acompanhado do código fonte ou de oferta
expressa de como obtê-lo sob termos conformes à EPL-2.0, mantendo todas as
declarações de direitos autorais e licenças acessíveis offline no pacote.

### 1.3 Apache-2.0 e componentes de terceiros

O Desembaraça Twine é distribuído sob Apache-2.0. A entrada de um componente
no catálogo exige revisão de compatibilidade e obrigações por artefato.
ColorBrewer, musl, Go e materiais W3C/ISO mantêm seus termos individuais;
não se atribui uma licença homogênea a arquivos com permissões distintas.
Avisos e fontes exigidos devem ser conferidos nos materiais efetivamente
distribuídos. Pareamento de hashes não concede aprovação de licença.

## 2. Invariantes do par vinculador de entrega

Para cada artefato executável (`artifact_id`) qualificado para distribuição, deve
existir exatamente um par vinculador imutável composto por:

1. **Arquivo binário candidato (`candidate.zip`)**:
   - Pacote ZIP empacotado por `tools/runtime/pack-candidate.py`.
   - Contém o executável `dot`, bibliotecas relocáveis privadas, arquivos de
     licenças integrais, avisos offline e `SOURCE-REFERENCES.txt`.
   - Identificado por `archive_sha256`, `archive_bytes`, `executable_sha256`,
     `inventory_sha256` e `provenance_sha256`.

2. **Arquivo de fontes correspondentes (`sources.tar.gz`)**:
   - Tarball comprimido USTAR empacotado por `tools/runtime/pack-sources.py`.
   - Contém o tarball oficial fixado do Graphviz (`graphviz.tar.gz`), a árvore
     completa `lib/` e `LICENSE` do SDK Zig fixado nos alvos Linux, todas as receitas/scripts
     de build em `tools/runtime/`, dependências internas do projeto,
     `candidate-provenance.json` e `manifest.json`.
   - Identificado por `archive_sha256`, `archive_bytes`, `executable_sha256`,
     `provenance_sha256` e `manifest_sha256`.

   O material de revisão macOS contém Graphviz, receitas e proveniência,
   sem redistribuir um arquivo completo do SDK Apple. `sdk_files` conta os membros
   extraídos do SDK Linux e permanece zero no macOS. Quando o preparo declara
   headers selecionados, `--header-review` é obrigatório. No escopo
   `observed-apsl-headers-v1`, o preparo seleciona todos os headers observados
   com declaração explícita APSL 1.1 ou 2.0, preserva seus caminhos relativos
   ao Xcode sob `header-review/` e inclui os textos integrais aplicáveis e
   `notice-review.json`. O exportador exige correspondência exata de caminhos,
   quantidade e hashes entre fontes, observações e proveniência; omissões são
   rejeitadas. Os dois headers inicialmente fixados continuam conferidos pelos
   hashes revisados. Recibos históricos sem esse escopo conservam o conjunto
   original de dois headers. `selected_sdk_header_files` registra o total de
   inputs selecionados separadamente. Aplicação dos termos
   de headers/runtime do SDK e completude das fontes correspondentes continuam
   pendentes de auditoria própria. Reconstrução no Actions é evidência técnica
   separada, sem afirmar identidade binária, licença ou oferta pública aprovada.

3. **Invariantes criptográficos compartilhados**:
   - `artifact_id`: id idêntico em ambos os registros.
   - `executable_sha256`: hash idêntico do binário `dot`.
   - `provenance_sha256`: hash idêntico do registro de proveniência nativa.
   - `application_revision`: commit Git exato do repositório.
   - `recipe_revision`: hash SHA-256 da receita `tools/runtime/<artifact_id>.json`.

## 3. Esquema canônico do recibo de pareamento (`pairing.json`)

O recibo gerado por `tools/runtime/verify-source-pairing.py` segue o schema abaixo:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "schema_version": 1,
  "kind": "corresponding-source-delivery-pairing",
  "artifact_id": "linux-glibc-x86_64",
  "application_revision": "40-hex-digits",
  "executable_sha256": "64-hex-digits",
  "provenance_sha256": "64-hex-digits",
  "pairing_valid": true,
  "archive_verification": {
    "candidate": true,
    "sources": true
  },
  "candidate": {
    "archive": "candidate.zip",
    "sha256": "64-hex-digits",
    "bytes": 1234567,
    "inventory_sha256": "64-hex-digits",
    "file_count": 480
  },
  "sources": {
    "archive": "sources.tar.gz",
    "sha256": "64-hex-digits",
    "bytes": 68388251,
    "file_count": 18175,
    "sdk_files": 18102
  },
  "obligations": {
    "lgpl_2_1_section_6_d": "Acesso equivalente para download das fontes completas disponibilizado no mesmo endpoint da distribuição binária",
    "lgpl_2_1_section_6_a": "Fontes completas da biblioteca e do programa exportadas permitindo relink modificado sem dependência de objetos compilados",
    "epl_2_0_section_3_1": "Fontes completas do Graphviz acompanhadas de declaração expressa de licença e avisos preservados",
    "offline_notices": "Avisos SOURCE-REFERENCES.txt e textos integrais offline incorporados em ambos os arquivos"
  },
  "delivery_binding": {
    "status": "unpromoted_pending_authorized_distribution",
    "candidate_distribution_url": null,
    "sources_distribution_url": null,
    "active_catalog_promoted": false
  }
}
```

## 4. Gates de distribuição e limites invioláveis

1. **Artefatos temporários de CI não constituem distribuição pública**:
   Execuções no GitHub Actions produzem artefatos transitórios com prazo de
   retenção efêmero. Eles servem exclusivamente como evidência de qualificação
   técnica e não satisfazem a obrigação de disponibilidade contínua das fontes.

2. **Catálogo ativo permanece estritamente Windows**:
   O arquivo `src/twine_edge_overlap/runtime-catalog.json` só pode incorporar
   artefatos POSIX (Linux/macOS) após autorização humana formal, existência de
   URLs HTTPS públicas imutáveis para ambos os arquivos (`candidate.zip` e
   `sources.tar.gz`) e aprovação completa das células propostas. Outras células
   permanecem pendentes, conforme a entrega independente prevista no plano.

3. **Invariância de recibos passados**:
   Nenhuma revalidação ou empacotamento pode sobrescrever recibos históricos
   ou alterar hashes registrados de revisões anteriores. Cada nova revisão
   recebe seu próprio diretório de evidência datado.

## 5. Verificação técnica e integração

`pack-candidate.py` grava `executable_sha256` a partir da entrada executável do
inventário já validado contra a proveniência e os bytes copiados. Recibos antigos
que não contêm esse campo não devem ser alterados nem aceitos por inferência.

Os pipelines `linux-candidate.yml`, `linux-arm64-candidate.yml` e
`linux-musl-candidate.yml` executam `verify-source-pairing.py` depois dos dois
empacotadores, com ambos os arquivos em disco e o commit completo da execução.
Guardam o mesmo `source-pairing.json` junto à evidência binária e às fontes.
Isso cobre as quatro variantes Linux quando os workflows forem executados;
a integração não registra uma execução CI nem uma distribuição final.

`pairing_valid` significa que as identidades declaradas coincidem.
`archive_verification` registra separadamente se cada arquivo foi lido e seu
hash/tamanho conferidos. Sem argumentos de arquivo, a análise é só de recibos.
Mesmo com ambos os arquivos conferidos, a ferramenta não inspeciona a completude
de fontes, notices, reconstrução/relink, elegibilidade ou qualificação nativa.
Os campos `obligations` descrevem requisitos da revisão, não resultados desses
ensaios. A revisão da aplicação pode ser `null` quando não informada; o CI sempre
informa um hash completo de commit.

URLs são opcionais e apenas planejadas. Se informadas, exigem um par HTTPS
distinto no mesmo diretório de release, sem credenciais, query ou fragmento.
Esse teste sintático não prova imutabilidade, existência ou acesso equivalente;
o estado continua `unpromoted_pending_authorized_distribution` em todos os casos.
Não há consulta de rede, publicação nem alteração do catálogo por esta ferramenta.
