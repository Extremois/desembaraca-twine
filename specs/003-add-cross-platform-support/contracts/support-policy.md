# Contrato de qualificação por ABI

Escopo aprovado pelo usuário em 2026-10-28. O registro obrigatório é
`tools/runtime/abi-targets.json`: sete alvos e quatorze slots Python.
Linux glibc/musl em x64/ARM64, macOS em Intel/ARM64 e Windows x64, cada um
com CPython 3.12 e 3.14. Registrar patch, revisão, artefato, hashes e logs.

Os testes são executados exclusivamente no GitHub Actions, em runners
hospedados e contêineres quando necessários. Não exigir VM, hardware dedicado,
runner próprio, kernel exclusivo ou execução individual por distribuição.
Os dois Pythons podem usar imagens/kernels diferentes, desde que cada job
satisfaça a mesma ABI/arquitetura/baseline e revisão/artefato qualificados.

As 69 células de `support-targets.json` são declarações de compatibilidade;
não são gates individuais de encerramento nem certificação de distribuição.
Snapshots rolling permanecem como diagnóstico e histórico opcional.

## Gates mantidos

Exigir os dois slots e evidências reais de instalação remota/wheel/sdist em
venv externa, primeiro uso/preparo, corpus e seis referências zeradas, offline,
preservação, reparo/interrupção/crash/concorrência, integridade e avisos/fontes,
licenças aprovadas e revisão das saídas no Twine. Skips não aprovam testes.
Simulações validam contratos, sem substituir execução real do binário.

Conferir SO, arquitetura, libc/baseline e mínimo macOS. Não herdar glibc para
musl ou x64 para ARM64. Registrar o ambiente observado sem inventar cobertura.

## macOS

Developer ID, assinatura e notarização são opcionais. Não exigir conta Apple,
certificado, timestamp, ticket de notarização ou `spctl --assess` para aceite
ou encerramento. As ferramentas de assinatura permanecem opcionais.

Manter hashes, Mach-O/arquitetura, dependências permitidas, relocação e
execução normal. Não desativar Gatekeeper, SIP, quarentena ou outras políticas.
Uma falha de execução normal continua sendo falha. Identificar entregas sem
atestado Developer ID/notarização quando não houver assinatura Apple.

## Promoção

`promote-support.py` usa o registro ABI e prepara proposta sem publicar.
`support_status` exige ambos os slots e os gates comuns. A matriz empacotada
separa `abi_targets` das declarações históricas em `targets`.

Integrar artefatos ao catálogo somente após auditoria de licenças/fontes,
integridade, manifesto e URL HTTPS/hash reais. Retirar o gate Apple não
aprova automaticamente licenças, fontes, publicação ou suporte.
