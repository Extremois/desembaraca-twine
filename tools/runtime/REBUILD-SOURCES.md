# Reconstrução das candidatas Linux glibc/musl x64/ARM64

Os artefatos `linux-{glibc,musl}-{x86_64,aarch64}-source-review-*`
contêm `sources.tar.gz` e um
recibo SHA-256. É material para revisão, ainda sem aprovação de oferta completa
de fontes ou publicação permanente. Não é necessário para usar o runtime.

## Recuperação das fontes por origens públicas

As receitas e os auxiliares usados nas candidatas da revisão `7d0476f` estão
no [arquivo público dessa revisão](https://github.com/Extremois/desembaraca-twine/archive/7d0476f3943e679ff1e151bf656f9992084209ba.zip),
acessível sem autenticação. O SHA-256 observado é
`c069987ed0ed6cd811c72aee1430a123b06e47d3659f0d2388ad2dd8fe14ade1`
(13.267.688 bytes), registrado em `public-recipe-source-lock.json`.
Graphviz está no [tarball 16.1.0 fixado](https://gitlab.com/graphviz/graphviz/-/archive/16.1.0/graphviz-16.1.0.tar.gz);
os SDKs completos estão em [Zig Linux x64](https://ziglang.org/download/0.15.2/zig-x86_64-linux-0.15.2.tar.xz)
e [Zig Linux ARM64](https://ziglang.org/download/0.15.2/zig-aarch64-linux-0.15.2.tar.xz).
Os tamanhos e hashes ficam em `source-lock.json` e `prepare-linux-ci.py`.
Essas origens permitem recuperar os bytes das fontes sem usar o armazenamento
temporário de Actions. Sua disponibilidade atual não garante hospedagem futura
nem aprova a oferta de fontes correspondente às licenças.

Para conferir uma exportação existente, baixe os três arquivos da arquitetura
correta e use o novo verificador do mantenedor:

```sh
python3 tools/runtime/verify-public-sources.py --source-package sources.tar.gz --receipt sources.json --project project-7d0476f.zip --graphviz graphviz-16.1.0.tar.gz --sdk zig-x86_64-linux-0.15.2.tar.xz --report public-source-review.json
```

O verificador roda offline, sem extrair arquivos nem executar compiladores.
Confere cada fonte exportada contra as origens fixadas, além do inventário,
dos hashes e do vínculo da receita com a candidata. Para ARM64, forneça o SDK
ARM64. `candidate-provenance.json` e `manifest.json` são metadados gerados,
explicitamente separados das fontes recuperáveis. Mudanças nos bytes dos
arquivos públicos reprovam a conferência; não substitua os hashes automaticamente.
O ZIP público fixado contém as receitas daquela revisão; o verificador novo
é uma ferramenta de revisão do checkout atual.

Para conferir outra revisão já publicada, forneça `--project-lock caminho.json`.
Esse arquivo deve ser revisado independentemente e conter `kind` igual a
`public-recipe-source-review-pin`, `approved: false`, o commit completo de 40
caracteres em `revision`, a URL HTTPS do arquivo desse commit neste repositório,
`root` igual a `desembaraca-twine-COMMIT`, `size` em bytes e `sha256` do ZIP
baixado. Não use nome de branch nem atualize o hash para contornar uma divergência.
O pin selecionado é preservado integralmente no relatório; a opção não altera
o pin padrão nem aprova licenças. Sem a opção, a revisão `7d0476f` continua fixada.
O arquivo de pin é limitado a 64 KiB e o ZIP público a 128 MiB.

A revisão atual `47844106ff072cad005a8a1c795153c658b2bc89` possui seu pin em
`specs/003-add-cross-platform-support/evidence/public-source-recovery-current-2026-10-20/project-pin.json`.
Use o ZIP público dessa revisão e a exportação de fontes correspondente ao
mesmo build, mantendo os arquivos Graphviz/SDK fixados acima:

```sh
python3 tools/runtime/verify-public-sources.py --project-lock specs/003-add-cross-platform-support/evidence/public-source-recovery-current-2026-10-20/project-pin.json --source-package sources.tar.gz --receipt sources.json --project project-4784410.zip --graphviz graphviz-16.1.0.tar.gz --sdk zig-x86_64-linux-0.15.2.tar.xz --report current-public-source-review.json
```

Para reconstruir diretamente das origens públicas, extraia o ZIP do projeto
conferido e, na raiz extraída, execute em Linux da CPU/ABI correspondente:

```sh
python3 tools/runtime/prepare-linux-ci.py --work /tmp/twine-public-sdk --arch x86_64 --libc glibc
python3 tools/runtime/build-common.py --artifact-id linux-glibc-x86_64 --source-archive /tmp/twine-public-sdk/graphviz.tar.gz --sdk-record /tmp/twine-public-sdk/sdk-record.json --output /tmp/twine-public-build --execute
```

O preparador baixa novamente e verifica Graphviz/SDK nos endereços fixados;
esse caminho não exige os artefatos de Actions. Em ARM64, troque `--arch` e
o sufixo do artifact-id por `aarch64`. Em userland musl, use `--libc musl` e
`linux-musl-ARCH`. Use pastas novas e os pré-requisitos de build abaixo. A
conferência dos arquivos públicos é uma prova de recuperação dos bytes; não
é uma nova execução dessas reconstruções nem uma promessa de binário idêntico.

## Reconstrução do pacote exportado

O arquivo reúne o tarball Graphviz original, a árvore `lib/` completa do Zig
0.15.2 (fontes, headers, dados e avisos), a licença raiz do SDK, scripts,
receitas, os módulos Python auxiliares do build/verificador ELF com sua licença Apache e
referências de licença do mantenedor. O compilador Zig não está
incluído. `manifest.json` relaciona tamanho/hash de cada entrada e vincula o
material ao executável e à proveniência da candidata. A árvore SDK inclui
material de outras plataformas; sua inclusão não declara que foi ligado ao dot.

Use Linux da arquitetura e ABI da candidata, filesystem POSIX e diretórios novos. São necessários
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

Para ARM64, em host Linux aarch64 nativo, use diretórios novos e os comandos:

```sh
python3 tools/runtime/prepare-linux-ci.py --work /tmp/twine-arm64-rebuild-sdk --arch aarch64
cp -a sdk/lib/. /tmp/twine-arm64-rebuild-sdk/sdk/zig-aarch64-linux-0.15.2/lib/
python3 tools/runtime/build-common.py --artifact-id linux-glibc-aarch64 --source-archive graphviz.tar.gz --sdk-record /tmp/twine-arm64-rebuild-sdk/sdk-record.json --output /tmp/twine-arm64-rebuild-output --execute
```

Para musl x64, em userland musl e CPU x86_64 correspondente:

```sh
python3 tools/runtime/prepare-linux-ci.py --work /tmp/twine-musl-rebuild-sdk --arch x86_64 --libc musl
cp -a sdk/lib/. /tmp/twine-musl-rebuild-sdk/sdk/zig-x86_64-linux-0.15.2/lib/
python3 tools/runtime/build-common.py --artifact-id linux-musl-x86_64 --source-archive graphviz.tar.gz --sdk-record /tmp/twine-musl-rebuild-sdk/sdk-record.json --output /tmp/twine-musl-rebuild-output --execute
```

Para musl ARM64, use `--arch aarch64`, `zig-aarch64-linux-0.15.2` e
`--artifact-id linux-musl-aarch64`, com novas pastas. O alvo é
`ARCH-linux.4.15-musl`, estático, com nova inspeção ELF. Nos containers CI,
acrescente `--environment-kind container` ao preparador: CPU correspondente e
userland musl sobre kernel Ubuntu não aprovam uma célula Alpine nativa.

O exportador seleciona e autentica o SDK específico da arquitetura e a receita
da proveniência. Os workflows glibc/musl x64 e ARM64 executam reconstruções em pastas
novas, copiando a árvore SDK exportada e usando cache de compilação privado novo.
Os testes do motor reconstruído usam o checkout público da mesma execução.

O resultado está em `/tmp/twine-rebuild-output/candidate/bin/dot`. O CMake refaz
as tabelas e parsers a partir das fontes Graphviz; o Zig recompila os objetos
de biblioteca usando a árvore `lib/` copiada e seu cache privado novo. Preserve
o log e a nova proveniência. Para experimentar alterações privadas nas fontes
glibc/musl, edite a cópia do SDK antes de executar `build-common.py`; o compilador
continua conferido pelo hash, mas as auditorias da candidata original devem
recusar essas fontes modificadas. Alterações não recebem aprovação automática.

O corpus público e o observador de rede exigem também o checkout de testes e
`src/` da revisão correspondente do projeto, mais `strace`. Esses arquivos da
aplicação, além dos auxiliares do build, não fazem parte deste pacote. A reconstrução no
workflow usa o checkout da própria execução para verificar 13 casos novamente.
Revisão das obrigações por arquivo, disponibilidade permanente das fontes,
baseline antigo e qualificação de instalação continuam pendentes.
