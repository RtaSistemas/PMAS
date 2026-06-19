# PMAS — Relatório de UX e Estética

**Data:** 2026-06-19  
**Versão analisada:** 2.0.3_PMAS  
**Escopo:** Toda a camada de apresentação — `frontend/style.css` (1 600 linhas), `frontend/index.html` (1 956 linhas), `frontend/app.js` (730 linhas), `tabs/*.js`, `charts/*.js`, `multiselect.js`

---

## Sumário Executivo

O PMAS apresenta uma interface de **dark dashboard profissional** fortemente alinhada ao design de ferramentas de analytics SaaS modernas (Vercel, Linear, Grafana). A linguagem visual é coesa: paleta navy/sky-blue, tipografia system-ui, densidade ajustável e ECharts extensivamente configurado. Os pontos mais fortes são o sistema de tokens CSS bem estruturado, a hierarquia de z-index documentada e o suporte real a acessibilidade de teclado. Os principais pontos de atenção são a dispersão de tamanhos de fonte (20+ valores distintos), a ausência de dark/light toggle, variáveis de tema duplicadas na camada JavaScript e o uso de valores `style.setProperty` que criam uma tensão entre o sistema de tokens do CSS e o sistema de tema dinâmico.

---

## 1. Identidade Visual

### 1.1 Nome e marca

O aplicativo se chama **PMAS** (*Project Management Assistant System*). A marca é exibida como logotipo textual (`<span class="header-name">`) e como bloco de ícone SVG na tela de login. Não há imagem bitmap — a marca é puramente tipográfica e vetorial, o que garante nitidez em qualquer DPI.

O nome pode ser customizado via `GlobalConfig.app_name`, refletido dinamicamente no `<title>` e em todos os elementos `[data-app-name]`.

### 1.2 Tema base

O tema *hard-coded* no CSS é **navy profundo + Sky Blue + Cyan accent + Emerald**, conforme declarado no próprio comentário de cabeçalho de `style.css`:

```
Paleta: Navy profundo + Sky Blue + Cyan accent + Emerald
```

É um dark theme exclusivo — não há modo claro (*light mode*) implementado.

---

## 2. Sistema de Cores

### 2.1 Tokens de cor (`:root`)

Todos os valores cromáticos são definidos como custom properties CSS, formando um design token system bem estruturado:

| Token | Valor | Uso semântico |
|---|---|---|
| `--bg` | `#060e1c` | Fundo da página (camada mais escura) |
| `--surface` | `#0b1829` | Superfície intermediária (inputs, sidebar) |
| `--card` | `#0e2038` | Cards e painéis principais |
| `--card-alt` | `#0a1a30` | Cards secundários, fundo de sub-navs |
| `--border` | `#172f4e` | Bordas sutis |
| `--border-hi` | `#1d4068` | Bordas de ênfase (inputs com foco, cards destacados) |
| `--text` / `--text-1` | `#ddeeff` | Texto primário (alto contraste sobre navy) |
| `--text-2` | `#7ba0c0` | Texto secundário / labels |
| `--text-3` | `#7aadcc` | Texto de dica / placeholders |
| `--primary` | `#0ea5e9` | Azul sky — cor de ação principal |
| `--primary-d` | `#0284c7` | Azul sky escuro — hover/pressed |
| `--primary-g` | `linear-gradient(135deg, #0ea5e9 → #06b6d4)` | Gradiente primário (botões CTA, logo accent) |
| `--primary-light` | `#38bdf8` | Azul claro — links, ênfase suave |
| `--cyan` | `#22d3ee` | Accent cyan — borda ativa de sub-tabs |
| `--green` | `#10d98a` | Status positivo / CPI ≥ 1 |
| `--amber` | `#f59e0b` | Alerta / atenção |
| `--red` | `#f04040` | Erro / orçamento estourado |
| `--violet` | `#a78bfa` | Destaque especial (ex.: EAC Schedule) |

### 2.2 Paleta extendida (tokens auxiliares)

Para casos específicos que não se encaixam no sistema de tokens principais:

| Token | Valor | Contexto |
|---|---|---|
| `--card-ingest` | `#1e293b` | Painel de resultado de upload + tooltip EVM |
| `--border-ingest` | `#334155` | Bordas do painel de ingestão |
| `--error-text` | `#f87171` | Mensagens de erro inline em formulários |
| `--very-dark` | `#0f172a` | Detalhe expandido de sessão de importação |
| `--info-text` | `#93c5fd` | Texto informativo em listas de sessão |
| `--warn-text` | `#fcd34d` | Texto de aviso em listas de sessão |
| `--input-overlay` | `#e2e8f0` | Texto do widget de moeda no header |

### 2.3 Semântica de cor no domínio

A aplicação usa cor para comunicar saúde financeira de projetos:

| Cor | Significado EVM / orçamento |
|---|---|
| Verde (`--green`) | Saudável — consumo < 90% do orçamento; CPI/SPI ≥ 1,0 |
| Âmbar (`--amber`) | Atenção — consumo entre 90–99%; CPI/SPI ≥ 0,85 |
| Vermelho (`--red`) | Crítico — orçamento estourado; CPI/SPI < 0,85 |
| Cinza (texto mudo) | Indefinido — sem orçamento cadastrado |

Esse mesmo esquema de 4 estados é aplicado consistentemente nos badges de status, na barra de semáforo do header, nos cards KPI e nos tooltips EVM.

### 2.4 Tema dinâmico (admin customizável)

O sistema permite override completo da paleta via painel Admin → Tema. Os tokens são aplicados em runtime por `_loadTheme()` em `app.js`, que sobrescreve as variáveis CSS via `root.style.setProperty()`.

**Tokens customizáveis pelo admin:**

| Campo | Token CSS mapeado |
|---|---|
| `color_primary` | `--primary`, `--primary-d`, `--primary-g` |
| `color_background` | `--bg`, `--card-alt` |
| `color_surface` | `--surface`, `--card` |
| `color_accent` | `--cyan` |
| `color_success` | `--green` |
| `color_warning` | `--amber` |
| `color_danger` | `--red` |
| `color_text` | `--text`, `--text-1` |
| `color_text_muted` | `--text-2`, `--text-3` |
| `font_family` | `--font-family` |
| `border_radius` | `--radius`, `--radius-lg` |
| `density` | `--density-spacing`, `--density-font-size` |
| `chart_palette` | `window._CHART_PALETTE` |

**Ponto de atenção:** A função `_loadTheme()` mantém dois sistemas de aliases paralelos — `--color-*` (novo) e `--theme-*` (aliases) e as variáveis legacy (`--bg`, `--surface`, etc.) — resultando em 27 `setProperty()` calls para cada carregamento de tema. Esse schema duplo existe para manter compatibilidade com o CSS existente, mas cria uma camada de indireção desnecessária.

### 2.5 Paleta de gráficos (ECharts)

A paleta padrão de séries, definida em `_getPalette()`:

```
['#4f8ef7', '#e94560', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
```

Azul · Vermelho/rosa · Verde · Laranja · Roxo · Teal — 6 cores distintas para séries de dados. Pode ser completamente substituída pelo admin. Por Golden Rule GR-3, nenhum arquivo de chart pode usar hex literals hardcoded — todas as cores de série passam por `_getPalette()` e status/semânticas por `_cssVar()`.

---

## 3. Tipografia

### 3.1 Família de fontes

```css
--font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
```

Stack system-font — sem dependência de font-face externo, garantindo carregamento instantâneo. Monospace é usado somente em contextos específicos:

```css
font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
```
(Aplicado em: campos de formulário tipo código, audit log, valores numéricos críticos)

### 3.2 Escala de tamanhos

O sistema usa um range extenso de tamanhos — 20+ valores distintos foram identificados:

| Categoria | Tamanho | Contexto de uso |
|---|---|---|
| Micro | `0.58rem` (≈ 9.3px) | Badge de contagem no tab (`.tab-badge`) |
| Micro+ | `0.60rem` | Bordas de badge |
| Tiny | `0.62rem` | Label do stat card (`.stat-card .lbl`) |
| XS | `0.67rem` | Cabeçalho de coluna de tabela (th) |
| XS+ | `0.68–0.72rem` | Labels de categorias, chip labels |
| Small | `0.75–0.80rem` | Card title (`.card > h2`), labels de filtro |
| Body-sm | `0.82rem` | Texto de botão (`.btn`) |
| Body | `0.875rem` | Texto padrão (densidade normal), input |
| Body+ | `0.90–0.95rem` | Descrições, body relaxado |
| Base | `1rem` | Nomes de colaboradores, valores prominentes |
| Medium | `1.1–1.2rem` | Títulos de seção dentro de tab |
| Large | `1.35rem` | Valor de stat card (`.stat-card .val`) |
| XL | `1.7rem` | (raramente usado — hero numbers) |

**Observação:** A granularidade excessiva (20+ valores) dificulta a manutenção. Um sistema de escala modular (ex.: 8-step com razão 1.25) reduziria a variação para 8–10 valores sem perda expressiva.

### 3.3 Pesos de fonte

| Peso | Uso |
|---|---|
| 400 (normal) | Texto corrido, células de tabela |
| 500 | Botões de tab, labels de filtro |
| 600 | Cabeçalhos de tabela, labels de formulário, chip labels |
| 700 | Títulos de card, valores numéricos de destaque |
| 800 | (raramente — hero text) |

### 3.4 Line-height e legibilidade

- Texto corrido: `1.5–1.6` — adequado
- Tabelas: `1.3` — compacto, mas aceitável em contexto de dados
- Tooltips/badges: `1` — sem interlinhas

---

## 4. Sistema de Espaçamento e Densidade

### 4.1 Densidade ajustável

Um dos recursos mais sofisticados do sistema: 3 modos de densidade, selecionáveis pelo admin e/ou usuário:

| Modo | `--density-spacing` | `--density-font-size` | Uso |
|---|---|---|---|
| `compact` | `0.45rem` | `0.78rem` | Exibir muitos dados em tela pequena |
| `normal` | `0.875rem` | `0.875rem` | **Padrão** |
| `relaxed` | `1.35rem` | `1rem` | Apresentações, monitores grandes |

O padding de tabelas, cards e labels usa `calc(var(--density-spacing) * multiplicador)`, tornando toda a densidade responsiva a um único token.

### 4.2 Escala de espaçamento (utilitários)

```css
.mb-0: margin-bottom: 0
.mb-1: margin-bottom: 0.5rem
.mb-2: margin-bottom: 1rem
.mb-3: margin-bottom: 1.5rem
.mb-4: margin-bottom: 2rem
.mt-2: margin-top: 1rem
```

O sistema de gap utilitário: `.gap-xs` (0.35rem) · `.gap-sm` (0.5rem) · `.gap-md` (0.85rem) · `.gap-lg` (1.25rem) · `.gap-xl` (1.75rem).

### 4.3 Border radius

| Token | Valor (padrão) | Alternativas via tema |
|---|---|---|
| `--radius` | `0.6rem` (9.6px) | `sharp: 2px`, `normal: 8px`, `rounded: 16px` |
| `--radius-lg` | `0.875rem` (14px) | `sharp: 4px`, `normal: 12px`, `rounded: 24px` |

Os raios são aplicados consistentemente em cards, inputs, botões, badges e modais. Apenas `border-radius: 9999px` (full-pill) é usado para badges de status e contagem — e de forma intencional.

---

## 5. Layout e Grade

### 5.1 Estrutura de página

```
┌─────────────────────────────────────────────────────┐
│  HEADER (fixed, z-100)                              │
│  Logo · Breadcrumb · Semaphore · Actions            │
├─────────────────────────────────────────────────────┤
│  NAV TABS (sticky, z-90)                            │
│  Dashboard · Projetos · Ciclos · Equipe · Minha Área │
├─────────────────────────────────────────────────────┤
│  MAIN (max-width 1480px, auto margins)              │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ TAB CONTENT (role="tabpanel")                 │  │
│  │                                               │  │
│  │  [Filter Card — collapsible]                  │  │
│  │  [Analytics Sub-tabs — sticky at 3.25rem]     │  │
│  │  [Chart Panels]                               │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 5.2 Grid de filtros

```css
grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
gap: 0.85rem;
```

Grid auto-responsivo: em telas largas, até 6 colunas (ciclo, PEP código, PEP descrição, colaborador, data início, data fim + botões). Em mobile, colapsa para 1 coluna.

### 5.3 Grid de KPIs / stat cards

```css
grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
gap: 0.75rem;
```

Permite de 3 a 8+ cards por linha dependendo do viewport.

### 5.4 Navegação em abas (dois níveis)

**Nível 1 — Abas principais** (`.tab-btn`):
- 6 abas fixas no topo (Dashboard, Projetos, Ciclos, Equipe, Minha Área, Admin)
- Tab ativa: `border-bottom: 2px solid var(--primary)` + cor de texto `var(--text)`
- Tab inativa: `border-bottom: transparent` + cor `var(--text-3)`
- Ícone: badge de contagem vermelho para quarentena pendente

**Nível 2 — Abas de analytics** (`.atab-btn`):
- 3 sub-abas no Dashboard (Esforço da Equipe, Saúde do Portfólio, Previsão EVM)
- Comportamento sticky: `position: sticky; top: 3.25rem; z-index: var(--z-sticky)` — flutua abaixo do header ao rolar
- Tab ativa: `border-bottom: 2px solid var(--cyan)` — diferencia visualmente do nível 1

---

## 6. Componentes de Interface

### 6.1 Botões

**Anatomia base (`.btn`):**
- Height: `2.25rem` — altura fixa, não depende de padding vertical
- Border-radius: `var(--radius)`
- Font-size: `0.82rem`
- Padding: `0 1.1rem`
- Display: `inline-flex; align-items: center; gap: 0.4rem`

**Variantes:**

| Classe | Aparência | Uso |
|---|---|---|
| `.btn-primary` | Gradiente azul, texto branco, sombra glow | CTA principal (Carregar, Salvar, Entrar) |
| `.btn-secondary` | Transparente, borda `--border-hi`, texto `--text-2` | Ações secundárias (Limpar, Cancelar) |
| `.btn-danger` | Transparente, borda vermelha 40% opacity, texto `--red` | Ações destrutivas (Excluir, Rejeitar) |
| `.btn-warning` | Transparente, borda âmbar, texto `--amber` | Aprovação de quarentena |
| `.btn-ghost` | Sem borda, sem fundo | Ações sutis (Print, Export) |
| `.btn-sm` | Height `1.875rem`, font `0.76rem`, padding `0 0.75rem` | Ações em linhas de tabela |
| `.btn:disabled` | `opacity: 0.4; cursor: not-allowed` | Estado inativo |

**Estado de filtros sujos (`.btn-dirty`):**
O botão "Carregar" recebe `animation: btn-pulse` + borda primária quando filtros foram alterados mas não aplicados — feedback visual sutil e efetivo.

### 6.2 Cards

**Card base:**
```css
background: var(--card);
border: 1px solid var(--border);
border-radius: var(--radius-lg);
padding: calc(var(--density-spacing) * 1.7);
box-shadow: var(--shadow-sm);
```

**Card header** — sempre uppercase, 0.7rem, weight 700, cor `--text-2`, letter-spacing 0.09em. O estilo "subtítulo apagado" acima do conteúdo é consistente em todos os cards.

**Card de ingestão** — variante com `--card-ingest` (#1e293b) e `--border-ingest` (#334155) para o painel de resultado de upload. Diferenciação clara do restante da UI.

### 6.3 Tabelas de dados

**Estrutura (`.data-table`):**
- Cabeçalho: `0.67rem`, uppercase, weight 700, `--text-2`, `border-bottom` sólida
- Células: `0.875rem` (density), `#c8dff0`, `border-bottom` semitransparente (50% opacity)
- Hover: fundo `rgba(14,165,233, 0.04)` — highlight primário muito sutil
- Ordenação: ícones ↕/▲/▼ via JS (`_makeSortable`, `_applySort`)

**Busca inline nas tabelas:**
- `.table-search-input` — input de busca com ícone à esquerda, filtro client-side em tempo real

**Paginação:**
- `.pagination-bar` com `.pagination-label` + botões prev/next
- Controle de `limit` (10/25/50/100 registros por página)

### 6.4 Modais

**Backdrop:** `rgba(0,0,0,0.72)` + `backdrop-filter: blur(3px)` — desfoque real do conteúdo ao fundo.

**Caixa modal:**
- `max-width: 560px` (padrão), `max-height: calc(100vh - 2rem)`
- `border: 1px solid var(--border-hi)` + `box-shadow: var(--shadow), var(--glow)` — glow primário sutil
- Estrutura: `modal-header` (título + botão ✕) + corpo com `overflow-y: auto` + `modal-footer`

**Acessibilidade de modal:**
- `role="dialog"`, `aria-modal="true"`
- Focus trap via Tab — cicla entre elementos focáveis dentro do modal
- Escape fecha o modal
- Retorno de foco ao elemento disparador ao fechar

### 6.5 Inputs e formulários

```css
height: 2.35rem;
border: 1px solid var(--border-hi);
background: var(--surface);
border-radius: var(--radius);
padding: 0 0.85rem;
transition: border-color 0.15s, box-shadow 0.15s;
```

**Foco:** `border-color: var(--primary)` + `box-shadow: 0 0 0 3px rgba(14,165,233,0.15)` — anel de foco com glow, mas sutil.

**Placeholder:** `color: var(--text-3)` — cinza médio, legível sem conflito com texto real.

**Select:** mesma aparência dos inputs — consistência visual preservada apesar da dificuldade de estilizar o elemento nativo.

### 6.6 MultiSelect (componente customizado)

Componente `MultiSelect` implementado do zero (sem dependência externa), em `multiselect.js`.

**Aparência:**
- Toggle button: aparência de select nativo, seta `▼` à direita
- Dropdown: `max-height: 260px; overflow-y: auto` — scrollável
- Opção: checkbox `accent-color: var(--primary)` + label, `font-size: 0.79rem`
- Hover em opção: `rgba(14,165,233,0.1)` — consistente com hover de tabela
- "Selecionar todos": item especial `.ms-all` com separador

**Acessibilidade:**
- `role="combobox"` + `aria-haspopup="listbox"` + `aria-expanded`
- `role="listbox"` + `aria-multiselectable="true"` no painel
- `aria-activedescendant` para rastrear item focado
- Navegação completa por teclado: ↑/↓, Enter/Space, Escape, Tab

### 6.7 Badges de status

`.badge-status` — pill compacta (padding `0.15rem 0.6rem`, font `0.67rem`, `border-radius: 9999px`, uppercase, weight 700).

**Variantes de status:**

| Classe | Visual | Contexto |
|---|---|---|
| `.ativo` | Verde suave | Projeto/ciclo ativo |
| `.encerrado` | Cinza | Projeto/ciclo encerrado |
| `.suspenso` | Âmbar | Projeto suspenso |
| `.quarantine` | Âmbar | Ciclo de quarentena |
| `.warnings` | Âmbar | Com avisos |
| `.rejected` | Vermelho | Rejeitado na revisão |

**Badges de orçamento:**
- `.badge-budget.critical` — "Estourado" em vermelho
- `.badge-budget.warning` — "Atenção ≥90%" em âmbar

### 6.8 Stat cards (KPIs)

**Estrutura:**
```
┌──────────────────────┐
│         1.234h       │  ← .val (1.35rem, bold)
│        HORAS TOTAIS  │  ← .lbl (0.62rem, uppercase, --text-3)
└──────────────────────┘
```

**Variantes de cor (`.val` colorido):**
- `.blue` → `--primary`
- `.amber` → `--amber`
- `.violet` → `--violet`
- `.green` → `--green`
- `.neutral` → `--text-2`
- `.red` → `--red`

### 6.9 Notificações toast

- **Posição:** `fixed; top: 3.75rem; right: 1.25rem` — canto superior direito, abaixo do header
- **Sistema de fila** (`_notifQueue`) — mensagens não se sobreposem; a próxima entra após a atual fechar
- **Duração:** 5 000 ms (info/sucesso), 12 000 ms (erro)
- **Variantes:** `.success` (verde), `.error` (vermelho), `.info` (azul) — fundo semitransparente + borda colorida + `backdrop-filter: blur(8px)`
- **Close manual:** botão ✕ independente do timer

### 6.10 Painel de notificações (sino)

- **Bell icon** com badge de contagem no header
- **Dropdown panel** ao clicar — lista de notificações com scroll
- **Por item:** mensagem + data relativa + botão ✕ (deletar) + marca como lido ao clicar
- **Estado não lido:** fundo levemente diferenciado (`.notif-item.unread`)
- **Polling:** atualiza a cada 60 segundos automaticamente

### 6.11 Barra de semáforo (header)

Posicionada entre o logo e as ações do header, a barra de semáforo (`#headerSemaphore`) exibe todos os projetos como *pills* coloridas:

```
● PROJ-01  ● PROJ-02  ● PROJ-03  ⬜ PROJ-04
  (verde)    (âmbar)    (vermelho)  (cinza)
```

- Clique em qualquer pill → navega para o tab Portfolio filtrando aquele PEP
- Tooltip (hover) mostra % horas e % custo consumidos
- Carregado via `/api/v2/portfolio` — atualizado a cada carregamento de página

---

## 7. Hierarquia Visual e Z-Index

O sistema de z-index é documentado explicitamente nos tokens CSS com comentários, o que é raro e valioso:

| Camada | Z-index | Elementos |
|---|---|---|
| Base | `1` | Elementos de layout inerte |
| Raised | `2` | Cards levemente elevados |
| Sticky | `90` | Sub-nav de analytics |
| Header | `100` | Header fixo |
| Dropdown | `200` | Multiselect, menus de ação de linha |
| Overlay | `400` | Backdrops de modal |
| Notification | `8 000` | Toasts |
| Modal | `9 999` | Modais / overlay de login |
| Tooltip | `10 000` | Tooltips EVM (acima de modais) |

A hierarquia é bem pensada: tooltips EVM são posicionados acima de modais (caso o usuário abra um modal com dados EVM), e notificações toast ficam acima de overlays para garantir feedback de ação mesmo com modal aberto.

---

## 8. Visualizações de Dados (ECharts)

### 8.1 Inventário de gráficos

| Gráfico | Arquivo | Tipo ECharts | Contexto |
|---|---|---|---|
| `effortChart` | `charts/effort.js` | Bar (horizontal, stacked/grouped) | Horas por colaborador |
| `trendsChart` | `charts/effort.js` | Line (dupla: horas + custo) | Tendência por ciclo |
| `pepCpiChart` | `charts/effort.js` | Bar (horizontal) | CPI por PEP (condicional) |
| `costCompositionChart` | `charts/effort.js` | Pie / donut | Composição de custo |
| `collabInlineTimelineChart` | `charts/effort.js` | Bar (timeline) | Timeline de colaborador |
| `collabCalendarChart` | `charts/effort.js` | Calendar heatmap | Calendário de atividade |
| `treemapChart` | `charts/portfolio.js` | Treemap | Portfólio por horas/R$ |
| `bulletChart` | `charts/portfolio.js` | Bar com marcas | Bullet chart de orçamento |
| `scatterChart` | `charts/portfolio.js` | Scatter (bubble) | Quadrante EVM CPI × SPI |
| `forecastChart` | `charts/forecast.js` | Line (S-curve) | EVM: realizado vs projetado |
| `burnUpChart` | `charts/forecast.js` | Line | Burn-up de custo |
| `whatIfBurnUpChart` | `charts/forecast.js` | Line | Cenário What-If |
| `mcHistogramChart` | `charts/forecast.js` | Bar | Histograma Monte Carlo |
| `velocitySparklineChart` | `charts/forecast.js` | Line (mini) | Sparkline de velocidade |

### 8.2 Padrões de configuração dos gráficos

**Tema registrado:**
```javascript
echarts.registerTheme('pmas', {
  backgroundColor: 'transparent',
  textStyle:  { color: _cssVar('--text-1') },
  axisLabel:  { color: _cssVar('--text-2') },
  splitLine:  { lineStyle: { color: _cssVar('--border') } },
});
```
Todos os gráficos herdam esse tema, garantindo integração visual com a UI.

**Padrões recorrentes:**
- Tooltip: `trigger: 'axis'` com formatador customizado, fundo `--card-ingest`, borda `--border-ingest`
- Legenda: posicionada no topo, fonte `0.72rem`, `--text-2`
- Data zoom: slider exibido automaticamente quando > 15 itens
- Resize: único `ResizeObserver` no `<main>` para todos os gráficos — eficiente
- Lifecycle: `dispose()` ao sair da sub-tab, `getOrCreateChart()` ao entrar — sem leaks de memória

### 8.3 Quadrante EVM (scatter chart)

O gráfico mais sofisticado: CPI × SPI com bolhas proporcionais ao custo.

**Quadrantes:**
```
     CPI
  1.0 ──────────────────────────────────
      │ Atrasado,   │ No prazo,         │
      │ dentro do   │ dentro do         │
      │ orçamento   │ orçamento         │
      │  (âmbar)   │   (verde)         │
SPI ──┼─────────────┼──────────────────►
  1.0 │ Atrasado,   │ No prazo,         │
      │ acima do    │ acima do          │
      │ orçamento   │ orçamento         │
      │  (vermelho) │   (azul)          │
```

Inclui suporte a seleção por brush rect (highlight interativo de múltiplos projetos) e linhas de trajetória histórica opcionais.

### 8.4 Gerenciamento de lifecycle de gráficos

```javascript
const CHARTS_PER_TAB = {
  effort:    ['effortChart', 'trendsChart', 'pepCpiChart', ...],
  portfolio: ['treemapChart', 'bulletChart', 'scatterChart'],
  forecast:  ['forecastChart', 'burnUpChart', 'whatIfBurnUpChart', ...],
};
```

`_disposeTabCharts(tab)` destrói instâncias ao sair. `_getOrCreateChart(id)` reutiliza ou cria. O `ResizeObserver` em `<main>` chama `.resize()` em todos os gráficos vivos.

---

## 9. Acessibilidade

### 9.1 O que está implementado

| Recurso | Implementação |
|---|---|
| Focus ring | `outline: 2px solid var(--primary)` apenas em `:focus-visible` (não em clique de mouse) |
| Screen reader only | `.sr-only` com clip pattern clássico |
| ARIA em tabs | `role="tablist"`, `role="tab"`, `aria-selected`, `aria-controls`, `role="tabpanel"` |
| ARIA em modais | `role="dialog"`, `aria-modal="true"`, focus trap, Escape para fechar |
| ARIA em multiselect | `role="combobox"`, `aria-haspopup`, `aria-expanded`, `role="listbox"`, `aria-multiselectable` |
| ARIA em notificações | `role="alert"`, `aria-live="assertive"` |
| Checkbox accent | `accent-color: var(--primary)` — nativo, acessível |
| Teclado em modal | Focus trap com Tab / Shift+Tab, retorno de foco ao disparador |
| Lang no HTML | `<html lang="pt-BR">` (inferido da localização pt-BR default) |

### 9.2 Pontos de atenção em acessibilidade

- **Contraste de texto-2 e texto-3 sobre fundo card:** `#7ba0c0` e `#7aadcc` sobre `#0e2038` produzem razão de contraste ~3.5:1 — abaixo do mínimo WCAG AA (4.5:1) para texto pequeno. Aceitável para texto não-essencial (labels de tabela, placeholders), mas crítico para elementos informativos como labels de formulário.
- **Ícones sem texto alternativo:** Vários botões de ação em linhas de tabela usam apenas ícone (✕, ✎) sem `aria-label` consistente.
- **Tabelas de dados:** Não foi verificada a presença de `<caption>` ou `scope` em todas as tabelas.

---

## 10. Responsividade

### 10.1 Breakpoints definidos

| Breakpoint | Tipo | Adaptações principais |
|---|---|---|
| `> 768px` | Desktop (base) | Layout completo |
| `≤ 768px` | Tablet/Mobile | Nav com scroll horizontal, grid de filtros 1 col, altura de charts reduzida (260px) |
| `≤ 480px` | Mobile pequeno | Padding mínimo, modais full-width, tabelas com min-width 420px (scroll horizontal), charts 200px |

### 10.2 Print media

Implementação robusta de `@media print`:
- Oculta: header, navegação, filtros, botões de ação, inputs de busca
- Exibe: apenas conteúdo da sub-tab ativa
- Tamanho de página: A4 landscape, margem 12mm
- Tabelas: fonte 9pt, texto preto sobre fundo branco
- Charts: altura fixa 320px, impressão exata com `print-color-adjust: exact`

---

## 11. Animações e Transições

### 11.1 Transições de UI

| Duração | Uso |
|---|---|
| `0.12s` | Hover de linhas de tabela, chips |
| `0.15s` | Botões, inputs (border-color, box-shadow), tabs, dropdown |
| `0.20s` | Collapsibles (filtro expansível) |
| `0.25s` | Transições de modal, notificação |

### 11.2 Keyframe animations

```css
@keyframes spin
/* Usado em: loading spinners */

@keyframes pmas-shimmer
/* background-position slide: efeito skeleton loading */

@keyframes btn-pulse
/* box-shadow ring pulsante: botão "Carregar" com filtros sujos */
```

### 11.3 Preferências de movimento

**Não identificada implementação de `@media (prefers-reduced-motion)`**. Usuários com sensibilidade a movimento não têm as animações `btn-pulse` e `shimmer` desativadas automaticamente — ponto de melhoria.

---

## 12. Internacionalização (i18n)

### 12.1 Suporte a idiomas

Dois idiomas implementados: **Português Brasil (pt-BR)** e **Inglês (en)**. Seleção via botão EN/PT no header (`#langToggleBtn`), persistida em `localStorage`.

### 12.2 Estrutura

```
frontend/lang/
  pt.js  — objeto com todas as chaves em pt-BR (idioma padrão)
  en.js  — objeto com todas as chaves em inglês
```

Função `_t('chave')` retorna a string do idioma ativo. Componentes como `MultiSelect` recebem o placeholder via parâmetro (já traduzido), não hardcoded.

### 12.3 Moeda

Widget de moeda no header permite alternar entre BRL (R$) e USD ($). A formatação numérica usa `Intl.NumberFormat` com locale `pt-BR` ou `en-US` conforme seleção do usuário.

---

## 13. Fluxos de UX Principais

### 13.1 Login

```
Tela de login (overlay fixo z-9999)
  └── Formulário centrado (max-width 380px)
       ├── Logo + nome do app
       ├── Divisor decorativo
       ├── Input usuário (autocomplete="username")
       ├── Input senha (autocomplete="current-password")
       ├── Botão "Entrar" (btn-primary full-width)
       └── Mensagem de erro inline (#loginError)
```

Após login bem-sucedido: overlay se oculta, app shell aparece, `_bootApp()` inicializa tabs e headers.

### 13.2 Upload de timesheet

```
Minha Área → Upload
  └── Input file (CSV/XLSX)
       ├── Preview de arquivo selecionado
       ├── Botão "Importar"
       └── Painel de resultado (#ingestResultPanel)
            ├── Contadores (aprovados/quarentena/erros)
            ├── Lista de avisos (collapsível)
            └── Botão "Ver detalhes" → modal de sessão
```

### 13.3 Dashboard — filtros cascata

```
Filtros (collapsível):
  Ciclo → PEP Código → PEP Descrição → Colaborador
  (cada seleção restringe as opções das subsequentes)

  Date pickers: Data início / Data fim
  Shortcuts: "Últ. mês", "Últ. trimestre", "Este ano"

  → Botão "Carregar" (pulsa quando filtros mudam)
  → Botão "Limpar"
```

### 13.4 Feedback de estado vazio

Quando não há dados: mensagens "empty state" em texto descritivo (ex.: "Nenhum dado encontrado para os filtros selecionados.") dentro dos containers de chart/tabela. Não há ilustrações decorativas — texto puro.

---

## 14. Pontos Fortes da UX

| # | Ponto forte | Evidência |
|---|---|---|
| 1 | **Token system consistente** | 36 custom properties em `:root`, todas com uso semântico documentado em comentário |
| 2 | **Z-index documentado** | Camadas nomeadas e comentadas — manutenção simples |
| 3 | **Densidade adaptável** | 3 modos (compact/normal/relaxed) com tokens que escalam toda a UI |
| 4 | **Acessibilidade de teclado real** | Focus trap em modais, keyboard nav completo em MultiSelect, `role` ARIA em todas as estruturas interativas |
| 5 | **ECharts lifecycle gerenciado** | Dispose/create por sub-tab, ResizeObserver centralizado — sem leaks |
| 6 | **Tema customizável pelo admin** | 13 variáveis de cor + família de fonte + raio de borda + paleta de gráficos |
| 7 | **Print media robusto** | Oculta UI, imprime só conteúdo relevante, A4 landscape |
| 8 | **Feedback de filtros sujos** | Botão "Carregar" pulsa quando há mudanças não aplicadas — previne confusão |
| 9 | **Sem dependência de fonte externa** | System font stack — zero FOUT, carregamento instantâneo |
| 10 | **Semáforo de saúde no header** | Visibilidade macro de todos os projetos a qualquer momento |

---

## 15. Pontos de Atenção e Oportunidades de Melhoria

| # | Problema | Severidade | Recomendação |
|---|---|---|---|
| UX-01 | **Escala de fonte com 20+ valores distintos** | Média | Consolidar para uma escala modular de 8–10 steps (ex.: 0.625 → 0.75 → 0.875 → 1 → 1.125 → 1.375rem) |
| UX-02 | **Contraste de `--text-2`/`--text-3` abaixo WCAG AA** | Alta | Clarear `#7ba0c0` → `#93b4cc` para atingir 4.5:1 sobre `--card` (#0e2038) |
| UX-03 | **Sem `prefers-reduced-motion`** | Média | Envolver `btn-pulse` e `pmas-shimmer` em `@media (prefers-reduced-motion: no-preference)` |
| UX-04 | **Tema dinâmico: 3 sistemas de alias paralelos** | Baixa | Unificar `--color-*`, `--theme-*` e variáveis legacy em um único set; deprecar aliases em versão futura |
| UX-05 | **Ausência de modo claro (light mode)** | Baixa | Não planejado, mas vale considerar `@media (prefers-color-scheme: light)` com token overrides |
| UX-06 | **Empty states sem ilustração** | Baixa | Adicionar SVG inline simples para estados vazios melhora percepção de polimento |
| UX-07 | **Botões de ação de linha com ícone sem `aria-label`** | Alta | Adicionar `aria-label="Editar registro"` etc. em botões icon-only |
| UX-08 | **Painel de filtros sem indicador de filtros ativos** | Média | Mostrar contagem/chips de filtros ativos no header colapsado do painel |
| UX-09 | **Scroll horizontal em tabelas mobile** | Baixa | As tabelas têm `min-width`, mas não há indicador visual de scroll (ex.: sombra lateral) |
| UX-10 | **Polling de notificações fixo em 60s** | Baixa | Considerar backoff ou WebSocket para reduzir requests desnecessários em sessões longas |

---

## 16. Inventário de Arquivos Frontend

| Arquivo | Tamanho (linhas) | Responsabilidade |
|---|---|---|
| `style.css` | 1 600 | Todos os estilos — design system completo |
| `index.html` | 1 956 | Estrutura HTML completa — todos os tabs, modais, formulários |
| `app.js` | 730 | Globals: auth, ECharts lifecycle, i18n, tema, modal, toast |
| `tabs/dashboard.js` | ~2 000+ | Tab Dashboard: filtros, 3 sub-tabs, todos os renders de analytics |
| `tabs/equipe.js` | ~800+ | Tab Equipe: seniority, rate cards, over-allocation |
| `tabs/admin.js` | ~1 000+ | Tab Admin: usuários, audit, validação, quarentena, Central de Alertas |
| `tabs/minha-area.js` | ~600+ | Minha Área: preferências, upload, histórico pessoal, alertas |
| `tabs/header.js` | 224 | Header: user info, semáforo, badges, sino de notificações |
| `charts/effort.js` | 271 | Gráficos de esforço: bar, trends, sparklines, calendar |
| `charts/portfolio.js` | ~300+ | Gráficos de portfólio: treemap, bullet, scatter EVM |
| `charts/forecast.js` | ~400+ | Gráficos de previsão: S-curve, burn-up, MC histograma |
| `multiselect.js` | ~180 | Componente MultiSelect acessível e auto-contido |
| `evm-glossary.js` | ~100 | Textos de tooltip do glossário EVM (i18n) |
| `crud/cycles.js` | ~200 | CRUD inline de ciclos |
| `crud/projects.js` | ~200 | CRUD inline de projetos |
| `lang/pt.js` | ~80 | Strings pt-BR |
| `lang/en.js` | ~80 | Strings en |
| `echarts.min.js` | — | ECharts 5 bundle (vendored) |
| `sortable.min.js` | — | SortableJS para drag-drop de layout (vendored) |

---

## 17. Conclusão

O PMAS apresenta uma UX **sólida e profissional** para uma aplicação de analytics B2B. O design é deliberadamente funcional — prioriza densidade de informação e clareza de dados sobre elementos decorativos. O sistema de tokens CSS é bem estruturado e o suporte a tema dinâmico é completo. A acessibilidade está acima da média para aplicações desta categoria (foco em teclado, ARIA real, não apenas simbólico).

As oportunidades de melhoria mais impactantes são: consolidar a escala tipográfica (UX-01), corrigir o contraste de texto secundário para conformidade WCAG AA (UX-02) e adicionar `prefers-reduced-motion` (UX-03). Todas são mudanças de baixo risco e alto impacto de qualidade percebida.

---

*Relatório gerado com base na análise estática completa de todos os arquivos frontend do PMAS v2.0.3_PMAS — 2026-06-19.*
