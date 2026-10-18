# Matriz proposta e política de versões

**Referência de manutenção**: 2026-10-17. Esta tabela é escopo de qualificação, não anúncio de suporte entregue. Todas as células Linux/macOS começam **pendentes**. Cada versão listada expande para cada arquitetura/variante indicada; cada célula contém dois slots de ensaio, CPython 3.12 e 3.14 nativos. Registrar o patch do SO/Python, imagem, hash e data nos ensaios. Os interpretadores não criam identidades independentes de célula.

## Alvos nomeados

| Distribuição/sistema | Versões elegíveis no recorte | Arquiteturas alvo | Condições e fonte oficial |
|---|---|---|---|
| Windows | 11 | x64 | Regressão do MVP; evidência local anterior não conclui aceitação em Windows limpo nem revisão visual. [Registro](../002-manage-layout-runtime/validation.md) |
| macOS | 15 | Intel x64; Apple Silicon ARM64 | Execução nativa sem Rosetta; qualificar distribuição assinada/notarizada. [Apple](https://developer.apple.com/developer-id/) |
| Ubuntu | 22.04, 24.04, 26.04, 26.10 | x64, ARM64 | Manutenção padrão. [Ciclo](https://ubuntu.com/about/release-cycle), [26.10](https://documentation.ubuntu.com/release-notes/26.10/) |
| Ubuntu | 18.04, 20.04 | x64, ARM64 | ESM via Ubuntu Pro gratuito para usuários elegíveis; conta/adesão necessária. Não presumir direito gratuito de toda organização. [Pro](https://ubuntu.com/pro/docs/), [ciclo](https://ubuntu.com/about/release-cycle) |
| Debian | 12, 13 | amd64, arm64 | 12 inclui LTS; não excluir manutenção somente de segurança. [Releases](https://www.debian.org/releases/index.en.html), [LTS](https://wiki.debian.org/LTS/) |
| Fedora | 43, 44 | x86_64, aarch64 | Somente releases estáveis mantidos; 45 em desenvolvimento não conta como lançado. [44](https://fedoramagazine.org/announcing-fedora-linux-44/), [imagens](https://torrent.fedoraproject.org/index.html) |
| RHEL | 8.10, 9.8, 10.2 | x86_64, aarch64 | Programa Developer Individual gratuito condicionado à elegibilidade/termos; não presume autorização para CI organizacional. [Datas](https://access.redhat.com/articles/red-hat-enterprise-linux-release-dates), [termos](https://developers.redhat.com/terms-and-conditions) |
| Rocky Linux | 8.10, 9.8, 10.2 | x86_64, aarch64 | Último minor mantido por major; x86_64 do major 10 exige CPU v3. [Releases](https://docs.rockylinux.org/latest/releases/) |
| AlmaLinux | 8.10, 9.8, 10.2 | x86_64, aarch64 | Último minor mantido por major; registrar variante x86_64/v2 quando aplicável, sem ocultar requisito de CPU da imagem. [Notas](https://wiki.almalinux.org/release-notes/) |
| openSUSE Leap | 16.0 | x86_64, aarch64 | x86 exige CPU v2; 16.1 ainda não é release estável na referência. [16.0](https://get.opensuse.org/leap/16.0/), [RC](https://news.opensuse.org/2026/09/24/leap-rc/) |
| openSUSE Tumbleweed | Rolling estável, snapshot datado | x86_64, aarch64 | Registrar ID real do snapshot e digest por arquitetura; não inventar uma série fixa. [Notícias oficiais](https://forums.opensuse.org/tag/tumbleweed-news) |
| Arch Linux | Rolling atualizado, snapshot datado | x86_64 | Port principal x86_64. [ArchWiki](https://wiki.archlinux.org/title/Arch_Linux?useskinversion=1) |
| Arch Linux ARM | Rolling atualizado, snapshot datado | aarch64 | Projeto separado explicitamente nomeado; imagem/dispositivo e kernel registrados. [Projeto](https://archlinuxarm.org/about) |
| Manjaro | Rolling Stable atualizado, snapshot datado | x86_64; ARM64 condicionado à imagem mantida | Imagens x86 oficiais; alvo ARM não é removido: identificação de imagem ARM atual e manutenção é gate pendente de qualificação. [x86](https://manjaro.org/products/download/x86/), [ARM](https://manjaro.org/products/download/arm/) |
| Alpine | 3.21, 3.22, 3.23, 3.24 | x86_64, aarch64 | Último patch disponível por série; anteriores à 3.24 mantêm main, não community. Não depender do Graphviz community do sistema. [Releases](https://alpinelinux.org/releases/), [imagens](https://www.alpinelinux.org/downloads/) |
| postmarketOS | v26.06 | Generic x86_64 EFI; ARM64 conforme imagem/dispositivo publicado | Derivado Alpine nomeado. Downloads comprovam host genérico x64 e dispositivos ARM; qualificar alvo ARM concreto sem prometer interface móvel/drivers. Pendência de ambiente ARM não elimina compromisso. [Downloads](https://postmarketos.org/download/) |
| Linux Mint | 21, 21.1, 21.2, 21.3; 22, 22.1, 22.2, 22.3; LMDE 7 | x64 | Tabela upstream mantém minors nomeados; não colapsar automaticamente. ARM64 não consta como arquitetura publicada dessa distribuição no recorte. [Versões](https://linuxmint.com/download_all.php) |

Os derivados de referência escolhidos são Rocky, AlmaLinux, Linux Mint, Arch Linux ARM e postmarketOS. Não se promete validar todas as distribuições derivadas. Pop!_OS, Gentoo, NixOS e outras não nomeadas permanecem melhor esforço tecnicamente compatível; não herdam qualificação Ubuntu/glibc.

## Exclusões verificáveis

| Caso | Motivo |
|---|---|
| Ubuntu 14.04/16.04 | Manutenção remanescente Legacy paga; não integra obrigação gratuita. [Ciclo](https://ubuntu.com/about/release-cycle) |
| Ubuntu 25.10 e intermediárias anteriores encerradas | Fora de manutenção na referência; 25.10 encerrou em 2026-07-09. [Aviso](https://lists.ubuntu.com/archives/ubuntu-announce/2026-July/000325.html) |
| Debian 11 e anteriores | 11 encerrou LTS em 2026-08-31; ELTS externo não equivale à manutenção oficial gratuita Debian. [LTS](https://wiki.debian.org/LTS/) |
| openSUSE Leap 15.6 e anteriores | 15.6 encerrou em 2026-04-30. [Calendário](https://calendar.opensuse.org/teams/product-schedule/events/leap-15-6-eol) |
| Alpine 3.20 e anteriores | Prazo regular encerrado; correções eventuais “on request” após EOL não são série regularmente mantida. Reavaliar se houver programa oficial de manutenção ativo identificável. [Política](https://alpinelinux.org/releases/) |
| Minors RHEL antigos com EUS exclusivamente pago | Não assumir elegibilidade gratuita; usar minor atual da série mantida. [Política](https://access.redhat.com/support/policy/updates/errata) |
| Imagem ARM64 não publicada por uma distribuição | Não inventar célula inexistente; comprovar ausência antes de classificá-la como não aplicável. Manjaro/postmarketOS ARM ainda são pendências, não exclusões consumadas. |

## Expansão e estados

Identidade de célula: distribuição/SO/versão/canal/arquitetura/variante de CPU, mais snapshot_id para rolling. Python é uma qualificação filha, com exatamente dois slots obrigatórios (3.12/3.14), e não parte da identidade do alvo. Para rolling, snapshot_id deriva de ID/versão/build/canal/arquitetura/kernel e inventário canônico completo de pacotes; data, label e imagem são metadados de evidência. Para Alpine, registrar série e patch separadamente. Para RHEL/Ubuntu ESM, registrar programa de manutenção e elegibilidade gratuita sem armazenar credenciais.

`pendente → em qualificação → validada` somente com ambos os slots Python e gates comuns completos, conforme o [contrato](contracts/support-policy.md). Falha de slot/gate impede aprovação agregada e registra motivo. Uma release pode promover células completas; as demais permanecem visíveis. Não atribuir um único estado “Linux suportado” à família inteira.

O reconhecimento rolling é local/offline pelo [contrato de snapshot](contracts/support-policy.md#reconhecimento-de-rolling). Coleta desconhecida, inventário diferente ou kernel/canal alterado não herda aprovação; o uso permanece possível com aviso de melhor esforço quando a ABI for comprovadamente compatível. Não incluir fingerprints inventados para snapshots ainda não ensaiados.

Rever fontes antes de cada publicação: novos lançamentos não herdam aprovação, snapshots futuros não estão cobertos automaticamente e EOL posterior deve ser registrado sem apagar o histórico/compromisso deste recorte. Escolher uma data fixa evita um escopo móvel durante a implementação.
