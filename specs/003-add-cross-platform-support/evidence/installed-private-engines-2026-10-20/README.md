# Motores privados executados pelos pacotes instalados

Checkpoint enviado: `d90b5671cba0477649e71a52b0d94704cce81c4e`.
Os três workflows passaram e os relatórios foram baixados e conferidos:

| Escopo | Instalações wheel/sdist | Casos do corpus explícito | Referências com três métricas zeradas |
| --- | ---: | ---: | ---: |
| Ubuntu hospedado x64/ARM64 × Python 3.12/3.14 | 8 | 104 | 48 |
| macOS 15 ARM64/Intel × Python 3.12/3.14 | 8 | 104 | 48 |
| Total com motor privado | 16 | 208 | 96 |

O [recibo de runtime](runtime/summary.json) vincula os oito relatórios à revisão,
ao verificador e aos quatro motores reais anteriores, sem recompilá-los. Cada
formato também passou nos três entrypoints, somando 48 verificações de help.
Primeiro uso automático, preparo explícito, probe no destino final antes de
`ready.json`, modos 0755/0700, caminhos Unicode, cache offline e preservação
foram exercitados pelo gerenciador e pelo motor reais. O driver conferiu a
semântica das saídas e os bytes dos originais; os hashes de entrada foram
reconferidos contra os arquivos públicos da revisão Git.

Cada instalação é externa e isolada. O driver recebe apenas auxiliares,
fixtures públicas e o inspetor Mach-O; não recebe `src/`. A aplicação é
importada do venv instalado e os 53 arquivos de pacote são conferidos antes
do ensaio. A obtenção do bundle usa transporte controlado: não é download
da futura candidata distribuída nem ativação de catálogo.

As [vinte instalações básicas](packages/summary.json) também passaram no
mesmo checkpoint, nos dez slots hospedados anteriores, incluindo Windows.
A [fundação](foundation.json) passou nos seis jobs com 242 testes cada,
seis skips POSIX e oito Windows. Localmente foram 247 testes por Python;
os cinco testes glibc de revisão anterior permanecem locais e não entraram
neste checkpoint.

## Reprodução

Use um CPython completo e um bundle privado da mesma arquitetura/SO:

```sh
python tools/validation/check-built-packages.py --dist-dir PACOTES --wheelhouse WHEELS_DE_BUILD --engine-artifact ARTEFATO_BAIXADO --engine-id linux-glibc-x86_64 --report RELATORIO_NOVO.json
```

O diretório do artefato deve conter um único `candidate.json`, seu ZIP,
inventário e proveniência cujo hash corresponda ao descritor. O preparo
recusa divergências antes de criar a cópia privada. `--engine-artifact` e
`--engine-id` são opcionais e devem ser usados juntos. Sem eles, continua
disponível o smoke de instalação/help sem motor. O relatório não é sobrescrito.

## Limites de aceite

O bloqueio de rede deste ensaio é apenas Python; não substitui um trace de
syscalls nativas desses slots instalados. Os rótulos hospedados não substituem
imagens imutáveis/elegibilidade de todas as células da spec. Licenças,
assinatura, candidata final remota e reabertura visual no Twine continuam
pendentes nas tarefas próprias.

No macOS, as oito instalações (quatro slots × dois formatos) registraram Gatekeeper habilitado e
SIP já desabilitado na imagem hospedada, antes e depois. Nenhuma proteção foi
alterada. Esses resultados não aprovam Developer ID/notarização nem aceitação
de executável distribuído com quarentena.

Os índices parciais são [Ubuntu 24.04](../linux-ubuntu-24.04.json),
[macOS](../macos.json) e [instalação](../package-installation.json).
T036/T048/T056/T078 permanecem abertas; catálogo só Windows e total 57/84.
Recibos finais locais, sem commit adicional após o checkpoint necessário.
