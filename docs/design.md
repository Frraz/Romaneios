# Interface e identidade visual

Como as telas são montadas e onde ficam cores, fontes e componentes. O comportamento das telas de relatório está em [relatorios.md](relatorios.md).

## Bibliotecas

Todas carregadas por CDN em `templates/base.html`, sem etapa de build nem `npm`:

| Biblioteca | Versão | Uso |
|---|---|---|
| Bootstrap (CSS e JS bundle) | 5.3.0 | Grade, componentes, menu lateral do celular |
| Font Awesome | 6.4.0 | Ícones |
| jQuery | 3.7.0 | Formulário de romaneio e inicialização do Select2 |
| Select2 + tema Bootstrap 5 | 4.1.0-rc.0 / 1.3.0 | Caixas de seleção com busca (classe `select2`) |
| Inter (Google Fonts) | — | Fonte da interface |

Sem internet no navegador do operador, a interface perde estilos e as caixas de seleção com busca. `django-widget-tweaks` está instalado e é usado só em `cadastros/cliente_form.html`; os demais formulários definem as classes nos widgets do `forms.py`.

## Estrutura das páginas

- `templates/base.html`: esqueleto de todas as telas, com navbar, mensagens, conteúdo e rodapé.
- **Desktop** (a partir de `lg`): barra superior fixa com menus Dashboard, Cadastros, Romaneios, Financeiro e Relatórios, mais o menu do usuário.
- **Celular** (abaixo de `lg`): barra compacta e menu lateral (offcanvas `#mobileMenu`) com os mesmos itens. Um item de menu novo precisa entrar nos dois lugares.
- O item **Operadores** só aparece para usuários staff.
- Mensagens do Django aparecem como alertas do Bootstrap (`MESSAGE_TAGS` em `config/settings.py`).
- Rodapé com os créditos e contatos do desenvolvedor.
- Login e redefinição de senha (`templates/registration/`) têm layout próprio, com o logo do cliente (`/media/image.png`).
- Ícone da aba: emoji 🌲 em SVG embutido, sem arquivo.

## Cores e medidas

Definidas como variáveis CSS no início de `static/css/base.css`:

| Variável | Valor | Papel |
|---|---|---|
| `--primary-color` | `#2d5a3d` | Verde-floresta: navbar, botões principais |
| `--primary-dark` / `--primary-light` | `#1e3d29` / `#3d7a51` | Variações do verde |
| `--secondary-color` | `#8b7355` | Marrom (madeira) |
| `--accent-color` | `#d4af37` | Dourado de destaque |
| `--success-color` / `--danger-color` | `#28a745` / `#dc3545` | Saldo positivo e negativo |

Também ficam ali raios de borda, sombras, transições e camadas (`z-index`). Novas cores entram como variável nesse bloco, não soltas no CSS.

Há só o tema claro. O `base.css` é referenciado com `?v=1.1`: ao mudar o arquivo, aumente esse número em `base.html` para forçar o navegador a baixar a versão nova.

## Convenções das telas

- **Números no padrão brasileiro:** milhar com `.` e decimal com `,` (`USE_THOUSAND_SEPARATOR` e `pt-br`). Nos templates, use `floatformat` (o `intcomma`, do `django.contrib.humanize`, também está disponível). Use `unlocalize` onde o número não pode ganhar separador, como anos e valores de `<input>`.
- **Saldos coloridos:** verde para crédito, vermelho para dívida, cinza para zero.
- **Listas** com filtros no topo, totais do período e paginação que preserva os filtros.
- **Exclusão** sempre passa por uma tela de confirmação (`*_confirm_delete.html`), que mostra os vínculos do registro quando existem.
- **Formulário de romaneio:** os campos de unidades só aparecem no modo detalhado; o valor por m³ é somente leitura; m³ e totais são recalculados na tela enquanto o operador digita.
- **PDFs** têm templates próprios (`apps/relatorios/templates/relatorios/*_pdf.html`), com CSS embutido e pensados para impressão em A4.
