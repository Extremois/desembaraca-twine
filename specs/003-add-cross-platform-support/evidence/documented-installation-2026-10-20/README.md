# Instalação remota do código atual

O workflow [39513702063](https://github.com/Extremois/desembaraca-twine/actions/runs/39513702063),
na revisão `752b6c35a9fbc09247c8a956878c8d3ce69c24e9`, passou nas dez
combinações de Ubuntu 24.04 x64/ARM64, macOS 15 Intel/Apple Silicon e Windows
hospedado × CPython 3.12/3.14. Cada job instalou o ZIP público imutável
`d90b5671cba0477649e71a52b0d94704cce81c4e` em venv nova, fora do checkout,
com perfil isolado e PATH contendo somente a venv.

Os dez recibos conferem os mesmos 53 arquivos Python/dados/avisos e LICENSE/NOTICE,
importação do pacote instalado, origem SHA-256 registrada pelo pip e três
entrypoints de help: console, módulo do pacote e módulo CLI. Todos registram
ausência de Git/Graphviz no PATH e ausência de preparo do motor. Os hashes
das fontes Python e LICENSE/NOTICE do checkout são comparados com LF, conforme
armazenado no arquivo GitHub; JSON e avisos de terceiros conservam os bytes.

O ZIP remoto teve SHA-256
`c76d9051339b184ececdbb45a357b02fd5ac1f1a40d5f6460fedcc6254b6833c`
em todos os jobs. `summary.json` vincula relatórios, artefatos baixados e jobs.
O README PT/EN e quickstart agora usam essa mesma URL. Os recibos anteriores
de 2026-10-19 permanecem preservados com a revisão anterior.

`foundation.json` preserva os seis jobs de regressão do workflow `39513702103`,
todos aprovados com 242 testes por job na revisão `752b6c3`. Os skips específicos
de sistema estão registrados; o job de aceite Windows foi pulado e não constitui
aceite limpo em Windows 11.

Este é um ensaio de instalação do código de desenvolvimento e seus comandos
de help. Não prepara nem distribui motor POSIX, não qualifica célula, assinatura,
licença ou suporte oficial; o catálogo continua Windows. T078 permanece parcial.
O runner Windows hospedado não substitui o aceite limpo em Windows 11.
As ferramentas de build foram obtidas pelo pip no ambiente efêmero do job;
esse percurso remoto exige acesso HTTPS ao GitHub e ao índice Python.
