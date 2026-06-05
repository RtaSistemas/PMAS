# Relatório de Integridade — Gráfica · Stack · Propósito
## PMAS (Project Management Assistant System)

> **Dimensões avaliadas:** Integridade Gráfica · Aproveitamento da Stack · Cumprimento de Propósito
> **Stack detectada:** Python 3.11 · FastAPI · SQLAlchemy · SQLite · Vanilla JS · Apache ECharts 5 · SortableJS · pandas
> **Data:** 2026-06-05

---

## SUMÁRIO EXECUTIVO

**Integridade Gráfica: 7,5/10 — O design system existe e é sofisticado, mas ainda escorrega em pontos críticos de consistência.** O sistema de tokens CSS está bem definido (46 variáveis) e é genuinamente usado; os gráficos ECharts respeitam o sistema cromático via `_cssVar()`. O problema central não é ausência de tokens — é que há dois regimes coexistindo: os tokens do design system e o CSS extendido (slate/Tailwind-inspired hardcoded fora de `:root`) que aparece principalmente em badges de quarentena e em dois gráficos do `app.js` (Tendências e Distribuição de Custo) que hardcodam `#94a3b8` em vez de `_cssVar('--text-2')`. A mixagem de `var(--token)` com literais hexadecimais em componentes funcionalmente equivalentes é o principal gap gráfico.

**Aproveitamento da Stack: 7,0/10 — Cada biblioteca está sendo usada para o que foi escolhida, mas com profundidades muito diferentes.** Apache ECharts é a biblioteca com maior gap de utilização: o sistema usa scatter, treemap, bar, line, radar, heatmap/calendar e timeline — mas omite visualMap, parallel, gauge, dataView completo e o registro de tema global (`echarts.registerTheme`), obrigando cada gráfico a repetir boilerplate de `backgroundColor/textStyle/axisLine`. SortableJS é usado exatamente para o que foi projetado, mas só com os callbacks `onEnd`. O `utils.js` exporta funções ES Module que não são importadas em lugar nenhum — é código morto presente no repositório.

**Cumprimento de Propósito: 8,5/10 — Para um sistema de timesheet + EVM, a cobertura funcional é notavelmente alta.** O ciclo completo de upload → validação → quarentena → aprovação → analytics está implementado e testado. EVM completo (CPI, SPI, EAC, TCPI, VAC, CV, SV, Earned Schedule, IEAC(t), Monte Carlo, What-If) está presente. Os dois gaps genuínos de propósito são: (1) ausência de entrada manual de horas — o sistema só ingere via CSV/XLSX, não há formulário de lançamento individual; e (2) ausência de notificações proativas — alertas de orçamento existem como badges na tela, mas não há envio de e-mail, webhook ou qualquer notificação push quando CPI/SPI cruzam thresholds configurados.

---

## 1. INTEGRIDADE GRÁFICA

### 1.1 Sistema de Design — Estado Atual

| Elemento | Status | Evidência |
|---|---|---|
| Paleta cromática | Sistematizado | 46 tokens em `:root` cobrindo bg/surface/card/border/text/primary/cyan/green/amber/red/violet + extended palette (`--text-hint`, `--text-faint`, etc.) |
| Tipografia | Parcialmente sistematizado | `--font-family: 'Inter', system-ui` definido e aplicado. Sem token para tamanho de fonte base ou escala tipográfica. A fonte Inter não é carregada por CDN — depende do sistema ou do cache do navegador |
| Espaçamento | Parcialmente sistematizado | `--radius`, `--radius-lg`, `--density-spacing` existem; não há escala de espaçamento (--space-sm / --space-md / --space-lg) — padding/margin são usados como literais `0.6rem`, `0.85rem`, `1.25rem`, etc. |
| Sombras | Sistematizado | `--shadow`, `--shadow-sm`, `--glow` definidos e usados |
| Ícones | Não sistematizado | Unicode emoji e caracteres especiais usados inline (⚠, ✓, ≥, ↑, ↗) |
| Animações | Parcialmente sistematizado | 3 `@keyframes` definidos (spin, pmas-shimmer, btn-pulse); transições usam literais de tempo (0.15s, 0.12s, 0.2s) — sem token `--transition-fast` / `--transition-base` |
| Tema ECharts | Sistematizado via `_cssVar()` | A maioria dos gráficos usa `_cssVar('--card')`, `_cssVar('--border')`, etc.; exceto duas funções em `app.js` que hardcodam `#94a3b8` |
| Responsividade | Presente | 3 breakpoints (`@media max-width: 800px, 768px, 480px`) + `@media print` + `ResizeObserver` nos charts |
| Dark mode | Hard-coded | O sistema é dark-only; `color-scheme: dark` declarado; não há modo claro |
| Tema customizável | Implementado | `GlobalConfig.ui_theme` (JSON) + `ThemePreset` no banco permitem customizar via Admin, mas os tokens `--theme-*` são usados apenas no preset "classic_navy" carregado por `_loadTheme()` |

### 1.2 Componentes — Consistência

**Consistentes:**
- Botões: 4 variantes bem definidas (`btn-primary`, `btn-secondary`, `btn-danger`, `btn-sm`) usadas uniformemente via classes CSS
- Modais: padrão único com focus trap + Escape + aria-label via `openModal()`/`closeModal()`
- Tabelas: skeleton loader animado + estado vazio padronizado via `_renderEmptyState()`
- Paginação: componente `_makePaginator()` reutilizável com controles uniformes
- Badges de status do projeto: `badge-status.ativo/encerrado/suspenso` com paleta consistente via `color-mix()`

**Inconsistentes:**
- Badges de quarentena (`.badge-structural`, `.badge-rule`, `.badge-reviewed`, `.badge-pending`): usam hexadecimais literais (`#422006`, `#fcd34d`, `#1e1b4b`) em vez de tokens
- Badge `.badge-status.warnings`: usa `color: #fb923c` literal em vez de `var(--amber)`
- Badge `.badge-baseline.active`: usa `color: #7eb3ff` literal em vez de um token
- Dois sub-tabs com classes distintas para a mesma função: `.my-tab-btn`, `.atab-btn` e `.tab-btn` — três nomes de classe para o conceito "sub-aba"
- Botões com modificadores de ordem inconsistente: `btn btn-sm btn-secondary` e `btn btn-secondary btn-sm` coexistem no HTML

### 1.3 Apontamentos Gráficos

**GR-01 — Dois gráficos hardcodam `#94a3b8` em vez de `_cssVar('--text-2')`**
- Localização: `app.js`, linha 1021 (legenda do gráfico de tendências), linhas 1038–1039 (eixos do gráfico de composição de custo)
- Código: `textStyle: { color: '#94a3b8', fontSize: 11 }` / `axisLabel: { color: '#94a3b8', ...}`
- Impacto: quando o usuário customiza o tema via Admin, esses dois gráficos não respondem — os eixos permanecem com a cor padrão do slate enquanto os demais se adaptam
- Recomendação: substituir `'#94a3b8'` por `_cssVar('--text-2')` nas linhas 1021, 1038, 1039

**GR-02 — Inter não é carregada por CDN — dependência silenciosa do sistema**
- Localização: `style.css` linha 52: `--font-family: 'Inter', system-ui, ...`
- Impacto: em sistemas sem a fonte Inter instalada, o fallback cai para `system-ui` sem aviso. O sistema visual foi desenhado para Inter (proporções, letter-spacing). A degradação é silenciosa
- Recomendação: adicionar `<link rel="preconnect" href="https://fonts.googleapis.com">` + `@import` para Inter no topo de `style.css`

**GR-03 — Badges de quarentena com paleta paralela ao design system**
- Localização: `style.css`, linhas 929–932
- Código: `.badge-structural { background: #422006; color: #fcd34d; border: 1px solid #92400e; }`
- Impacto: os 4 badges de quarentena usam uma paleta Tailwind amber/purple/green/stone completamente fora do vocabulário do design system. Um tema customizado não os alcança
- Recomendação: remapear para `color-mix(in srgb, var(--amber) 12%, transparent)` / `var(--amber)` seguindo o padrão das demais badges

**GR-04 — `utils.js` exporta ES Modules que não são importados**
- Localização: `/home/user/PMAS/frontend/utils.js` — contém `export function escHtml`, `export function fmtDateBR`, etc.
- Nenhum `<script type="module">` no `index.html`; `app.js` redefine `escHtml` localmente na linha 4324
- Impacto: `utils.js` não é carregado em `index.html` — é código morto. A duplicação de `escHtml` entre `utils.js` e `app.js` é um risco de divergência silenciosa
- Recomendação: ou converter o frontend para ES modules (adicionando `type="module"` e `import`) ou remover as declarações `export` de `utils.js` e carregá-lo como script global

**GR-05 — `--primary-light` referenciado em CSS mas não definido em `:root`**
- Localização: `style.css` linha 694: `.alloc-total { color: var(--primary-light); }`
- O token `--primary-light` não existe em `:root` — sem valor de fallback, resulta em `color: (vazio)` e o texto `.alloc-total` fica invisível
- Recomendação: definir `--primary-light: #38bdf8;` em `:root` ou substituir por `var(--cyan)`

**GR-06 — SortableJS carregado via CDN externo com SRI mas sem fallback local**
- Localização: `index.html` linha 13: CDN jsdelivr com `integrity` e `crossorigin`
- Impacto: se o CDN estiver offline ou bloqueado por firewall corporativo, toda funcionalidade de drag-and-drop falha silenciosamente. ECharts é servido localmente; SortableJS deveria seguir o mesmo padrão
- Recomendação: mover `sortable.min.js` (já presente em `/frontend/`) para ser servido localmente, removendo a dependência CDN

---

## 2. APROVEITAMENTO DA STACK

### 2.1 Mapa de Aproveitamento

```
Criticidade × Utilização

                    ┌────────────────────────────────────────────┐
              Alta  │         ECharts(5)    FastAPI               │
     Crítico  para  │                    SQLAlchemy               │
              o     │    pandas  python-jose/JWT  SortableJS      │
              sist. │                                             │
              Baixa │    bcrypt   slowapi   openpyxl              │
                    └────────────────────────────────────────────┘
                       Subutilizado     Bem usado     Profundo
```

| Biblioteca | Propósito declarado | % utilização estimado | Notas |
|---|---|---|---|
| Apache ECharts 5 | Visualização interativa | 55% | 7 tipos de gráfico usados; tema global ausente; visualMap/parallel/gauge ignorados |
| SortableJS 1.15.6 | Drag-and-drop | 35% | Só `animation` + `handle` + `onEnd`; swap, multiDrag, AutoScroll, grupos ignorados |
| FastAPI | API REST | 75% | Routers/Depends/HTTPException/response_model usados; BackgroundTasks/WebSocket ausentes |
| SQLAlchemy | ORM | 70% | Relationships/FK/cascades bem usados; raw `text()` para PRAGMAs (justificável); sem async |
| pandas | Ingestão CSV/XLSX | 40% | Usado apenas para `read_csv`/`read_excel` + `pd.to_datetime`/`pd.isna`; nenhum `groupby`, `merge`, `agg`, `pivot` |
| python-jose / JWT | Autenticação | 80% | `jwt.encode`/`jwt.decode` com HS256 e expiração; sem refresh tokens |
| bcrypt | Hash de senhas | 100% | Usado corretamente para hash e verificação |
| slowapi | Rate limiting | 60% | Aplicado como middleware global; sem rate limits por rota específica |
| openpyxl | Parse XLSX | 100% | Usado via pandas `read_excel` como engine |

### 2.2 Análise por Biblioteca

#### Apache ECharts 5 — 55%

**O que usa bem:**
- `scatter` (quadrante EVM CPI×SPI com brush + markArea + markLine + bolhas proporcional ao custo)
- `treemap` (portfolio com agrupamento de saúde + timeline animado por ciclo)
- `bar` (esforço stacked + bullet chart sobreposto + histograma Monte Carlo)
- `line` (tendências + forecast S-curve com banda de incerteza + burn-up)
- `radar` (perfil de colaborador: volume/extra/standby/regularidade/presença)
- `heatmap` com `coordinateSystem: 'calendar'` (atividade mensal do colaborador)
- `toolbox` com saveAsImage + dataView + magicType + brush
- `dataZoom` slider + inside no gráfico de esforço
- `timeline` no treemap por ciclo

**O que não usa:**
- `echarts.registerTheme()` — cada gráfico repete 5–8 linhas de boilerplate (`backgroundColor`, `textStyle`, `tooltip.backgroundColor`, `axisLine.lineStyle.color`, `splitLine.lineStyle.color`). Um tema registrado eliminaria ~80 linhas de código redundante
- `visualMap` — seria natural para codificar gradiente de CPI/SPI no treemap (hoje usa cor categórica: verde/amarelo/vermelho)
- `graphic` — texto e anotações personalizadas no canvas
- `parallel` — coordenadas paralelas para comparação multi-dimensão de projetos

**Anti-padrão identificado (GR-01):**
```js
// app.js linha 1021 — hardcoded, não responde a tema customizado
legend: { top: 0, textStyle: { color: '#94a3b8', fontSize: 11 } }

// Correto — todos os outros gráficos fazem assim:
legend: { top: 0, textStyle: { color: _cssVar('--text-2'), fontSize: 11 } }
```

#### SortableJS 1.15.6 — 35%

**O que usa:**
- `Sortable.create()` com `animation` e `handle` em 3 contextos: layout de abas, painéis por aba, lista de regras de validação
- `onEnd` callback para persistir ordem de validações via API

**O que não usa:**
- `group` (conexão entre listas) — seria útil para arrastar regras entre listas ativo/inativo
- `filter` (elementos não arrastáveis dinamicamente) — hoje usa CSS para desabilitar; Sortable tem suporte nativo
- `ghostClass`, `chosenClass`, `dragClass` — feedback visual durante drag está ausente (o cursor muda mas não há destaque)

#### FastAPI — 75%

**O que usa bem:**
- `APIRouter` com `prefix` e `tags` em todos os módulos
- `Depends` para autenticação (`get_current_user`, `require_admin`)
- `HTTPException` com status codes
- `response_model` para serialização Pydantic
- `lifespan` (startup hook para `init_db`)
- `CORSMiddleware` + `SlowAPIMiddleware`
- `StreamingResponse` para exports CSV

**O que não usa:**
- `BackgroundTasks` — o upload de timesheet (que pode ser lento em arquivos grandes) é síncrono; uma task assíncrona pós-resposta melhoraria a UX
- `WebSocket` — não há real-time
- `Query`/`Path` com validators (min/max, regex) — parâmetros de query chegam como `Optional[str]` sem validação declarativa

#### SQLAlchemy — 70%

**O que usa bem:**
- ORM com `relationship`, `back_populates`, `cascade`
- `ForeignKey` com `ondelete`
- `UniqueConstraint`, `Index` compostos
- `joinedload` em quarantine queries
- Transações explícitas via `db.commit()`/`db.rollback()`

**Uso de `text()` (aceitável):**
- `database.py` usa `text("PRAGMA table_info(...)")` para migrations manuais — justificável dado que SQLAlchemy Alembic não está no projeto
- `dashboard.py` usa `sa_text()` em uma query de aggregação

**O que não usa:**
- `async` SQLAlchemy — o projeto é síncrono; em uploads grandes isso bloqueia o event loop do uvicorn
- `hybrid_property` ou `column_property` para campos derivados
- Alembic para migrations — as migrations manuais em `_migrate_columns()` escalam mal

#### pandas — 40%

**O que usa:**
- `pd.read_csv()` + `pd.read_excel()` para parsing multi-formato
- `pd.to_datetime()` para parse de datas com `dayfirst=True`
- `pd.isna()` para checagem de nulos

**O que não usa (mas poderia simplificar `ingestion.py`):**
- `df.groupby()` — a fase 3 (aggregate rules) faz loops manuais que pandas faria em 2–3 linhas
- `df.apply()` — a validação por linha usa iterrows implicitamente em vez de apply vetorial
- `df.merge()` — joins com tabelas de lookup são feitos via dicionários Python construídos manualmente

#### python-jose / JWT — 80%

**Uso adequado:** `jwt.encode`/`jwt.decode` com `SECRET_KEY` e `ALGORITHM=HS256`, expiração em payload. Bom.

**Gap:** sem refresh tokens — o token expira e o usuário é deslogado sem aviso; sem rotação de chave.

---

## 3. CUMPRIMENTO DE PROPÓSITO

### 3.1 Mapa de Funcionalidades

```
PMAS — Promessas de um Sistema Timesheet + EVM

Registro de Tempo
  ✅ Upload CSV/XLSX (multi-formato)
  ✅ Validação multi-fase com rule engine
  ✅ Quarentena com workflow de revisão
  ✅ Ciclos de faturamento com controle de status
  ✅ Colaboradores + senioridade + rate card
  ❌ Entrada manual de horas (sem upload)
  ❌ Edição de registro individual pós-ingesta

Gestão de Projetos
  ✅ CRUD de projetos (PEP/WBS)
  ✅ Budget por horas e custo
  ✅ Baselines bloqueados com ativação
  ✅ Histórico de revisões de orçamento
  ✅ Planejamento por ciclo (S-curve baseline)
  ✅ ACL por usuário por projeto
  ⚠️ Status de projeto (ativo/encerrado/suspenso) existe mas sem fluxo de encerramento automático

Métricas EVM
  ✅ CPI (IDC) — Índice de Desempenho de Custo
  ✅ SPI (IDP) — Proxy AgileEVM em horas
  ✅ EAC (EPT) — com e sem SPI*CPI
  ✅ ETC (EPC) — via remaining_cost = EAC - AC
  ✅ VAC (VNT) — Variação no Término
  ✅ TCPI (IDC-PC) — Performance necessária
  ✅ CV (VC) — Variação de Custo
  ✅ SV (VS) — Variação de Prazo
  ✅ Earned Schedule (ES/SPI(t)/SV(t)/IEAC(t))
  ✅ EV capped at BAC (não superestima)
  ✅ Freeze de custo na ingesta (sem retroatividade)
  ⚠️ PV (VP) requer baseline configurado — sem baseline, SPI não é calculado

Análise e Visualização
  ✅ Treemap portfolio (horas/R$, saúde EVM)
  ✅ Timeline por ciclo (treemap animado)
  ✅ Bullet chart orçamento vs. realizado
  ✅ Quadrante EVM (CPI × SPI bubble chart)
  ✅ Esforço da equipe (stacked bar por colaborador)
  ✅ Tendências por ciclo (linha com custo)
  ✅ Forecast S-curve (planejado vs. realizado + projeção)
  ✅ What-If / Simular (multiplicador de velocidade)
  ✅ Monte Carlo P10/P50/P90 + histograma
  ✅ Runway (ciclos restantes por PEP)
  ✅ Concentração (risco de dependência de colaborador)
  ✅ Over-allocation (capacidade por colaborador)
  ✅ Perfil de colaborador (radar + heatmap calendário + timeline inline)
  ⚠️ Semáforo macro existe mas não tem drill-down direto nos gráficos (só filtra a aba portfolio)

Operações e Administração
  ✅ Usuários com roles (admin/user)
  ✅ Audit log estruturado
  ✅ Upload history com transparência
  ✅ Tema global customizável + presets
  ✅ Export CSV de todos os dados principais
  ✅ Import CSV para ciclos, projetos, rate cards, planos
  ✅ Preferências por usuário (drag-to-reorder de painéis)
  ✅ i18n pt-BR/en completo
  ❌ Notificações por email/webhook
  ❌ Relatório exportável consolidado (PDF/XLSX com múltiplos gráficos)
  ❌ Entrada manual de lançamento de horas
```

### 3.2 Tabela de Cumprimento

| Funcionalidade | Status | Arquivo(s) de Evidência |
|---|---|---|
| Upload CSV/XLSX | ✅ Implementado | `services/ingestion.py`, `routers/upload.py` |
| Validação configurable | ✅ Implementado | `services/rule_engine.py`, `routers/validation_rules.py` |
| Quarentena + workflow | ✅ Implementado | `models.py:QuarantineRecord`, `routers/quarantine.py` |
| Ciclos de faturamento | ✅ Implementado | `models.py:Cycle`, `routers/cycles.py` |
| Gestão de projetos | ✅ Implementado | `models.py:Project`, `routers/projects.py` |
| EVM completo (9 métricas) | ✅ Implementado | `services/evm.py` (39 funções), `routers/v2/forecast.py` |
| Earned Schedule (ES/SPI(t)) | ✅ Implementado | `services/evm.py:compute_earned_schedule`, `compute_spi_t` |
| Monte Carlo P10/P50/P90 | ✅ Implementado | `routers/v2/monte_carlo.py` |
| What-If / Simulation | ✅ Implementado | `routers/v2/simulate.py` |
| Baselines + freeze | ✅ Implementado | `models.py:ProjectBaseline`, `routers/baselines.py` |
| S-curve planejada | ✅ Implementado | `models.py:ProjectCyclePlan`, `routers/plans.py` |
| ACL por projeto | ✅ Implementado | `models.py:UserProjectAccess`, `routers/acl.py` |
| Audit log | ✅ Implementado | `models.py:AuditLog`, `routers/auditlog.py` |
| Rate card com freeze | ✅ Implementado | `models.py:RateCard`, `services/ingestion.py:_lookup_rate` |
| Tema customizável | ✅ Implementado | `models.py:GlobalConfig.ui_theme`, `routers/theme.py` |
| i18n pt-BR/en | ✅ Implementado | `frontend/lang/pt.js`, `frontend/lang/en.js` (498 linhas cada) |
| Over-allocation | ✅ Implementado | `routers/v2/over_allocation.py` |
| Concentração de risco | ✅ Implementado | `routers/v2/concentration.py` |
| Perfil de colaborador | ✅ Implementado | `app.js` linhas 2629–2917 (radar + calendar heatmap + inline timeline) |
| Export CSV (múltiplos) | ✅ Implementado | `ratecard.py`, `plans.py`, `my.py`, client-side em `app.js` |
| Entrada manual de horas | ❌ Ausente | Sem formulário POST para `TimesheetRecord` individual |
| Edição de registro individual | ❌ Ausente | Sem `PUT /api/timesheet-records/{id}` |
| Notificações por email | ❌ Ausente | Zero referências a `smtp`, `email`, `sendgrid` |
| Notificações webhook | ❌ Ausente | Sem `httpx` ou `requests` para callbacks externos |
| Relatório consolidado (PDF) | ❌ Ausente | Sem `reportlab`, `weasyprint`, `puppeteer` |
| Refresh tokens JWT | ❌ Ausente | Token único sem rotação |

### 3.3 Gaps de Propósito

**GP-01 — Entrada manual de horas ausente**
- Impacto no usuário: colaboradores sem acesso ao sistema de ponto digital (prestadores, consultores) não têm como lançar horas diretamente. O PM precisa manter uma planilha auxiliar e fazer upload periódico, quebrando a rastreabilidade em tempo real
- Estado atual: `POST /api/upload-timesheet` aceita apenas arquivo CSV/XLSX; não há rota `POST /api/timesheet-records` para um único lançamento
- Caminho de implementação: adicionar `POST /api/timesheet-records` com validação de ciclo ativo + quarentena opcional + audit log. Frontend: modal de lançamento no Dashboard (colaborador + data + PEP + horas). O pipeline de validação já está abstraído em `rule_engine.py`
- Esforço estimado: Médio (2–3 dias de backend + 1 dia de frontend)
- Prioridade: Alta — é a funcionalidade mais óbvia que um usuário de timesheet espera

**GP-02 — Notificações proativas ausentes**
- Impacto no usuário: CPI < 0.8 ou orçamento > 95% acontece sem que ninguém seja avisado até que o PM abra a tela. Em portfólios com 10+ projetos, problemas passam despercebidos por semanas
- Estado atual: os thresholds existem em `GlobalConfig.budget_warning_threshold/critical_threshold` e `classify_health()` já classifica saúde. O alerta existe só como badge visual na tela. Não há email, webhook, ou notificação in-app persistente
- Caminho de implementação: usando apenas a stack atual, criar uma tabela `Notification` (já caberia no padrão de `AuditLog`) e uma flag de "notificado" por (user_id, pep_wbs, threshold_event). FastAPI `BackgroundTasks` (já disponível, não usado) acionaria a geração de notificações após cada upload. A entrega poderia ser in-app (badge de sino no header) sem necessitar de SMTP
- Esforço estimado: Médio (1–2 dias para notificação in-app; adicionar SMTP é +1 dia)
- Prioridade: Média-Alta

**GP-03 — Edição de registro individual pós-ingesta ausente**
- Impacto no usuário: erro em uma linha de uma planilha exige re-upload de toda a planilha. O workflow de quarentena permite aprovar/rejeitar linhas problemáticas, mas não permite corrigir o valor de uma linha já importada sem re-fazer o upload
- Estado atual: sem `PUT /api/timesheet-records/{id}`. O sistema usa delete-by-pep+cycle + insert na fase 4 da ingesta, o que torna uma edição granular viável tecnicamente (bastaria replicar esse padrão para um único registro)
- Caminho de implementação: `PATCH /api/timesheet-records/{id}` com campos editáveis (horas_normal, horas_extra, horas_sobreaviso), re-freeze de custo e registro em `AuditLog`. Backend: ~50 linhas. Frontend: botão de edição inline na tabela de registros
- Esforço estimado: Baixo-médio (1 dia)
- Prioridade: Média

**GP-04 — Relatório exportável consolidado ausente**
- Impacto no usuário: para apresentações ao cliente ou reuniões de steering, o PM precisa copiar prints individuais de cada gráfico. O `toolbox.saveAsImage` do ECharts salva gráficos um a um; não há "exportar relatório completo"
- Estado atual: export CSV existe para dados tabulares; ECharts tem `saveAsImage` por gráfico; sem consolidação
- Caminho de implementação sem novas dependências: o `toolbox.dataView` do ECharts permite abrir dados brutos; scripts de exportação client-side poderiam montar um HTML printável via `window.print()` com todos os gráficos como SVG exportado. Alternativa backend: `StreamingResponse` com HTML+CSS gerado com dados do `/api/v2` (sem necessidade de headless browser)
- Esforço estimado: Médio (2 dias para versão print-CSS; mais para PDF server-side)
- Prioridade: Baixa-média

---

## 4. INTERSEÇÕES — ONDE AS TRÊS DIMENSÕES SE ENCONTRAM

### INT-01 — ECharts sem tema global: gap gráfico + stack + propósito simultaneamente

Este é o problema mais genuinamente tridimensional do sistema.

**Dimensão gráfica:** dois gráficos não respondem à customização de tema do Admin porque hardcodam `'#94a3b8'` em vez de `_cssVar('--text-2')`. O Admin pode mudar o tema visual mas a coerência gráfica quebra exatamente nos charts de Tendências e Distribuição de Custo.

**Dimensão de stack:** ECharts 5 tem `echarts.registerTheme(name, themeConfig)` + `echarts.init(el, themeName)` precisamente para resolver isso. Sem o tema registrado, cada gráfico repete manualmente `backgroundColor`, `textStyle`, `tooltip.backgroundColor`, `axisLine`, `splitLine` — boilerplate que `_chartDefaults()` (em `ui-helpers.js`) captura parcialmente mas não elimina (apenas 3 dos 7 campos repetidos). Os dois charts problemáticos nem usam `_chartDefaults()`.

**Dimensão de propósito:** para um sistema de gestão de portfólio que anuncia "tema customizável via Admin", a incapacidade dos gráficos de Tendências de responder ao tema é um gap funcional — a promessa de customização não é totalmente cumprida.

**Solução transversal:** registrar um tema ECharts gerado dinamicamente via `_loadTheme()` e passar o nome do tema para todos os `echarts.init()`. Estima-se eliminar ~80 linhas de boilerplate e corrigir GR-01 simultaneamente.

### INT-02 — `utils.js` como módulo ES não integrado: gráfico + stack

`utils.js` exporta funções ES Module (`export function escHtml`, `export function formatCost`, `export function riskColor`) mas não é carregado em `index.html` e não tem `<script type="module">`. O `app.js` redefine `escHtml` localmente (linha 4324). O `frontend/charts/portfolio.js` e demais dependem do `escHtml` global de `app.js`.

**Gráfico:** código morto no repositório cria confusão sobre qual é a fonte canônica das funções utilitárias.

**Stack:** a coexistência de dois sistemas de módulo (global scripts + ES module não conectado) é um anti-padrão arquitetural. Se um desenvolvedor corrigir `escHtml` em `utils.js`, a correção não será visível no produto.

---

## 5. POTENCIAL DESBLOQUEÁVEL

O que o sistema poderia entregar **sem adicionar nenhuma nova dependência:**

```
Ações de alto impacto com stack existente
─────────────────────────────────────────
GP-01 + FastAPI BackgroundTasks → Notificação in-app de threshold
  ↓ usa: FastAPI (já presente) + AuditLog pattern (já existe)
  ↑ entrega: alertas proativos sem SMTP

ECharts.registerTheme → Eliminar boilerplate + corrigir GR-01
  ↓ usa: ECharts (já presente) + _loadTheme() (já existe)
  ↑ entrega: tema verdadeiramente coerente + -80 linhas de código

pandas.groupby/agg na ingestion.py → Simplificar fases 2-3
  ↓ usa: pandas (já presente) + lógica existente
  ↑ entrega: código mais idiomático + melhor performance em arquivos grandes

utils.js integrado como módulo → Eliminar código duplicado
  ↓ usa: ES Modules (nativo no browser) sem npm build
  ↑ entrega: fonte única de verdade para helpers

SortableJS ghostClass/chosenClass → Feedback visual no drag
  ↓ usa: SortableJS (já presente) + CSS tokens (já existem)
  ↑ entrega: UX de reordenação mais clara sem código novo
```

| Ação | Impacto Estimado | Esforço | Score Desbloqueado |
|---|---|---|---|
| `echarts.registerTheme()` global | Alto gráfico | 2h | +0.5 GR |
| Corrigir `#94a3b8` → `_cssVar` (GR-01) | Alto gráfico | 30min | +0.3 GR |
| Definir `--primary-light` (GR-05) | Baixo gráfico | 5min | +0.1 GR |
| Notificação in-app via BackgroundTasks | Alto propósito | 1 dia | +0.3 GP |
| Entrada manual de horas (GP-01) | Alto propósito | 3 dias | +0.5 GP |
| Integrar `utils.js` como módulo real | Médio stack | 2h | +0.2 ST |
| `SortableJS ghostClass` | Baixo gráfico | 30min | +0.1 GR |
| Inter via Google Fonts (GR-02) | Médio gráfico | 10min | +0.2 GR |
| **Total desbloqueável** | | ~5 dias | **+2.2 pts** |

---

## 6. PLANO DE EVOLUÇÃO

### Fase 1 — Fundação (Semana 1) — Score esperado: 8.5 / 7.5 / 9.0

Corrigir todos os gaps que não exigem novo código, apenas ajustes:

- **GR-01**: substituir `'#94a3b8'` por `_cssVar('--text-2')` em `app.js` linhas 1021, 1038, 1039
- **GR-02**: adicionar `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap')` no topo de `style.css`
- **GR-05**: definir `--primary-light: #38bdf8` em `:root` de `style.css`
- **GR-03**: remap dos badges de quarentena para `color-mix(in srgb, var(--amber)...)`
- **GR-04**: mover SortableJS para servir localmente (o arquivo já existe em `frontend/sortable.min.js`)
- **GR-06**: implementar `echarts.registerTheme('pmas', ...)` chamado em `_loadTheme()` e passar o nome para `echarts.init(el, 'pmas')`
- **Stack**: integrar `utils.js` como script global (remover `export`, adicionar ao `index.html` antes de `app.js`, remover definição local em `app.js` linha 4324)

### Fase 2 — Funcionalidades de Propósito (Semanas 2–3) — Score esperado: 8.5 / 7.5 / 9.5

- **GP-01**: `POST /api/timesheet-records` — endpoint de entrada manual com validação + audit log
- **GP-02**: notificação in-app via `BackgroundTasks` — tabela `Notification` + badge no header
- **GP-03**: `PATCH /api/timesheet-records/{id}` — edição granular com re-freeze de custo

### Fase 3 — Excelência Técnica (Semana 4+) — Score esperado: 9.0 / 8.5 / 9.5

- **Stack pandas**: refatorar fases 2–3 da ingesta para usar `groupby`/`agg` vetorial
- **Stack FastAPI**: adicionar `Query` validators com limites declarativos em parâmetros numéricos
- **Stack SQLAlchemy**: avaliar migração para Alembic (substitui `_migrate_columns()` manual)
- **GP-04**: página de relatório HTML/CSS printável com todos os charts como SVG exportado

---

## APPENDIX A — STACK DETECTADA

| Pacote | Versão (requirements.txt) | Uso |
|---|---|---|
| fastapi | >=0.111.0 | Framework API REST principal |
| uvicorn[standard] | >=0.29.0 | Servidor ASGI |
| sqlalchemy | >=2.0.0 | ORM + migrations manuais |
| pandas | >=2.0.0 | Parsing CSV/XLSX na ingesta |
| python-multipart | >=0.0.9 | Upload de arquivos multipart |
| openpyxl | >=3.1.0 | Engine XLSX para pandas |
| python-jose | >=3.3.0 | JWT (HS256) para autenticação |
| bcrypt | >=4.0.0 | Hash de senhas |
| slowapi | >=0.1.9 | Rate limiting como middleware |
| echarts.min.js | 5.x (local) | Todos os gráficos |
| sortable.min.js | 1.15.6 (CDN + local) | Drag-and-drop reordenação |

---

## APPENDIX B — ARQUIVOS AVALIADOS

| Arquivo | Linhas | Papel |
|---|---|---|
| `/home/user/PMAS/frontend/style.css` | 1.251 | Design system, tokens, componentes |
| `/home/user/PMAS/frontend/app.js` | 5.953 | Toda a lógica frontend |
| `/home/user/PMAS/frontend/ui-helpers.js` | 182 | Helpers de componente reutilizáveis |
| `/home/user/PMAS/frontend/utils.js` | ~65 | Utilitários (ES Module, não integrado) |
| `/home/user/PMAS/frontend/charts/portfolio.js` | 473 | Scatter, Treemap, Timeline, Bullet |
| `/home/user/PMAS/frontend/charts/effort.js` | 270 | Stacked bar, dataZoom |
| `/home/user/PMAS/frontend/charts/forecast.js` | 369 | S-curve, burn-up, projeção |
| `/home/user/PMAS/frontend/evm-glossary.js` | 350 | Glossário EVM bilíngue + tooltips |
| `/home/user/PMAS/frontend/lang/pt.js` | 498 | Traduções pt-BR |
| `/home/user/PMAS/frontend/lang/en.js` | 498 | Traduções en |
| `/home/user/PMAS/frontend/index.html` | 1.684 | Estrutura HTML + 154 inline styles |
| `/home/user/PMAS/backend/app/services/evm.py` | 545 | 39 funções EVM (fonte única de verdade) |
| `/home/user/PMAS/backend/app/models.py` | 370 | 20 modelos ORM |
| `/home/user/PMAS/backend/app/services/ingestion.py` | 670 | Pipeline de ingesta 6-fases |
| `/home/user/PMAS/backend/app/routers/v2/forecast.py` | ~380 | Endpoint EVM render-ready |
| `/home/user/PMAS/requirements.txt` | 9 | Dependências Python |
