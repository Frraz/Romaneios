# Documentação do Romaneios

Índice da documentação técnica. Para o que é o sistema e como rodá-lo, comece pelo [README da raiz](../README.md).

| Se você quer… | Leia |
|---|---|
| Entender como o sistema é organizado, as rotas e o modelo de dados | [arquitetura.md](arquitetura.md) |
| Conhecer os termos, fórmulas, validações e permissões | [regras-de-negocio.md](regras-de-negocio.md) |
| Saber o que cada relatório mostra, filtra e exporta | [relatorios.md](relatorios.md) |
| Montar o ambiente, rodar os testes e seguir as convenções | [desenvolvimento.md](desenvolvimento.md) |
| Publicar, reverter, ver logs, fazer backup | [operacao.md](operacao.md) |
| Saber por que algo foi decidido | [decisoes.md](decisoes.md) |
| Mexer na interface, cores e componentes | [design.md](design.md) |
| Ver o que está pronto, os defeitos conhecidos e o que falta | [../ROADMAP.md](../ROADMAP.md) |
| Saber o que mudou e quando | [../CHANGELOG.md](../CHANGELOG.md) |

## Como manter

- A documentação muda no mesmo commit que o código que a tornou falsa.
- Mudou um cálculo, uma validação ou uma permissão? Atualize [regras-de-negocio.md](regras-de-negocio.md).
- Mudou um relatório, filtro ou exportação? Atualize [relatorios.md](relatorios.md).
- Rota, app ou modelo novo? Atualize [arquitetura.md](arquitetura.md) (o catálogo de rotas está lá).
- Variável de ambiente nova? Atualize o `.env.example` e a tabela do [README](../README.md#configuração).
- Mudou o deploy, o servidor ou o workflow? Atualize [operacao.md](operacao.md).
- Toda mudança que o usuário percebe entra no [CHANGELOG](../CHANGELOG.md), em `[Não lançado]`, e passa a ter data ao ser publicada. Migração nova leva "Ação necessária na atualização".
- Resolveu um débito (`DT-xx`) ou uma pendência (`P-xx`)? Marque no [ROADMAP](../ROADMAP.md) com a data; não apague o item.
- O número de testes só aparece em [desenvolvimento.md](desenvolvimento.md#estado-da-suíte).
- Nada de domínio, IP, caminho do servidor, senha ou dado de cliente nos documentos. Use `app.exemplo.com.br` e `/srv/romaneios`. Os valores reais ficam num arquivo local fora do Git (`docs/ambiente.local.md`, listado em `.git/info/exclude`).
- Quando a documentação e o código divergirem, o código é a verdade sobre o que o sistema faz. Se o errado for o código, registre um `DT` no roteiro.

## Desvios do padrão de documentação

O projeto segue o padrão geral de documentação no nível **Padrão** (`docs/` plano), com estas exceções:

- `relatorios.md` existe além dos arquivos-base, porque os relatórios são o módulo mais extenso.
- Os débitos técnicos ficam numa seção do `ROADMAP.md`, com identificadores estáveis, em vez de um documento próprio.
