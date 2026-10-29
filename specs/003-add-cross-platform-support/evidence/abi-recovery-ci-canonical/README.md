# Aceite de recuperação por ABI

T076 concluída no GitHub Actions: sete ABIs, 14 slots Python e 28 instalações
wheel/sdist. Foram conferidos 53 arquivos instalados por formato contra o commit,
364 execuções do corpus, 168 referências zeradas, 112 cenários de reparo e
112 cenários de crash/concorrência. Os recibos originais estão em `*.json.gz`;
`summary.json` registra os hashes e os cinco workflows aprovados.

Aquisição, falta de espaço e certos erros são injetados explicitamente. No
Windows, EACCES é injetado; nos POSIX, a recusa de execução usa permissões reais.
Saídas de processo, liberação de locks e concorrência são reais. O bloqueio de
rede observa chamadas Python, sem alegar rastreio de syscalls.

`review-by-hash/` contém as seis saídas distintas. Cada SHA-256 corresponde aos
mesmos bytes produzidos pelas 28 instalações; o índice mantém esse vínculo.
Revisão visual no Twine continua pendente. Não há aprovação automática de
licenças, distribuição ou suporte, nem certificação de versões do Windows.
