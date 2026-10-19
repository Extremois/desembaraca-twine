# Reconstrução da candidata Linux glibc x64

O artefato `linux-glibc-x86_64-source-review-*` contém `sources.tar.gz` e um
recibo SHA-256. É material para revisão, ainda sem aprovação de oferta completa
de fontes ou publicação permanente. Não é necessário para usar o runtime.

O arquivo reúne o tarball Graphviz original, a árvore `lib/` completa do Zig
0.15.2 (fontes, headers, dados e avisos), a licença raiz do SDK, scripts,
receitas, os módulos Python auxiliares do build com sua licença Apache e
referências de licença do mantenedor. O compilador Zig não está
incluído. `manifest.json` relaciona tamanho/hash de cada entrada e vincula o
material ao executável e à proveniência da candidata. A árvore SDK inclui
material de outras plataformas; sua inclusão não declara que foi ligado ao dot.

Use Linux x86_64 glibc, filesystem POSIX e diretórios novos. São necessários
Python 3.12 ou 3.14, CMake, make, Bison, Flex e readelf. As versões/hashes usados
originalmente estão em `candidate-provenance.json`, em `sdk.facts.host_tools`;
a imagem do runner também está registrada. A imagem hospedada pode mudar, e
estes passos não prometem reprodução byte a byte ou compatibilidade com o SO
mínimo. O teste hospedado reconstrói a partir das fontes exportadas.

Confira o SHA-256 do arquivo contra o recibo antes de extrair em pasta vazia.
Execute os comandos a partir dessa pasta. `prepare-linux-ci.py` baixa e verifica
os arquivos Graphviz e SDK fixados, criando ferramentas privadas; precisa de
rede somente nessa preparação. Nenhuma instalação global é feita pelo script.

```sh
python3 tools/runtime/prepare-linux-ci.py --work /tmp/twine-rebuild-sdk
cp -a sdk/lib/. /tmp/twine-rebuild-sdk/sdk/zig-x86_64-linux-0.15.2/lib/
python3 tools/runtime/build-common.py --artifact-id linux-glibc-x86_64 --source-archive graphviz.tar.gz --sdk-record /tmp/twine-rebuild-sdk/sdk-record.json --output /tmp/twine-rebuild-output --execute
```

O resultado está em `/tmp/twine-rebuild-output/candidate/bin/dot`. O CMake refaz
as tabelas e parsers a partir das fontes Graphviz; o Zig recompila os objetos
de biblioteca usando a árvore `lib/` copiada e seu cache privado novo. Preserve
o log e a nova proveniência. Para experimentar alterações privadas nas fontes
glibc, edite a cópia do SDK antes de executar `build-common.py`; o compilador
continua conferido pelo hash, mas as auditorias da candidata original devem
recusar essas fontes modificadas. Alterações não recebem aprovação automática.

O corpus público e o observador de rede exigem também o checkout de testes e
`src/` da revisão correspondente do projeto, mais `strace`. Esses arquivos da
aplicação, além dos auxiliares do build, não fazem parte deste pacote. A reconstrução no
workflow usa o checkout da própria execução para verificar 13 casos novamente.
Revisão das obrigações por arquivo, disponibilidade permanente das fontes,
baseline antigo e qualificação de instalação continuam pendentes.
