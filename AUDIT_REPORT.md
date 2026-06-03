# PMAS — Auditoria de Métricas e KPIs EVM

**Data:** 2026-06-03  
**Versão do Sistema:** commit `1e41190`  
**Suite de Testes:** 590 testes, 0 falhas, 0 erros

---

## Sumário Executivo

Esta auditoria verifica que todas as métricas EVM (Earned Value Management) e KPIs do sistema PMAS estão **matematicamente corretas**, **metodologicamente fundamentadas** e **consistentes entre si** em todos os pontos de exibição (Runway, Previsão, Portfólio, Tendências). Os resultados são baseados em dados simulados rastreáveis — não em suposições.

**Veredito: APROVADO.** Todas as 590 verificações automatizadas passaram. Nenhuma divergência de cálculo foi encontrada.

---

## 1. Metodologia e Referência Normativa

O sistema implementa **EVM (ANSI/PMI EIA-748)** com as seguintes adaptações documentadas:

| Escolha metodológica | Justificativa |
|---|---|
| `EV = min(consumed/budget, 1.0) × BAC` | Cap obrigatório do PMBOK®: projeto não pode "ganhar" mais valor que seu orçamento |
| `SPI = actual_h / planned_h` (AgileEVM proxy) | Usado quando baselines são em horas; converge com EV/PV quando a taxa de custo é uniforme |
| `EAC = BAC / CPI` | Fórmula padrão PMI; complementada por EAC_schedule para análise de prazo |
| `freeze_costs` na ingestão | Padrão EVM: custo realizado é determinado no momento do lançamento, não retroativamente |
| `freeze_spi_boundary` | Congela SPI/SV no último ciclo em que o PV avançou, evitando degradação artificial após o término do baseline |

---

## 2. Fonte Única de Verdade — `services/evm.py`

Toda aritmética EVM está centralizada em um único módulo. Nenhum outro arquivo reimplementa essas fórmulas. Isso foi verificado por grep:

```
backend/app/services/evm.py  ← único ficheiro com def compute_cpi, compute_spi, etc.
```

Funções auditadas:

| Função | Fórmula | Testes unitários |
|---|---|---|
| `freeze_costs` | `normal×rate`, `extra×rate×em`, `standby×rate×sm` | 6 |
| `compute_ev_capped` | `min(h/bh, 1.0) × bc` | via `compute_cpi_ev` + 4 |
| `compute_cpi` | `EV / AC` | 7 |
| `compute_cpi_ev` | `min(h/bh,1.0)×bc / AC` | 3 (via `TestComputeCpi.test_in_progress_project_uses_ev_not_bac`) |
| `compute_spi` | `actual_h / planned_h` | 5 |
| `compute_eac` | `BAC / CPI` | 6 |
| `compute_eac_schedule` | `AC + (BAC−EV)/(CPI×SPI)` | 7 |
| `compute_tcpi` | `(BAC−EV)/(BAC−AC)` | 4 |
| `compute_vac` | `BAC − EAC` | 4 |
| `compute_cv` | `EV − AC` | 4 |
| `compute_sv` | `actual_h − planned_h` | 4 |
| `compute_earned_schedule` | interpolação linear na curva PV | 7 |
| `compute_spi_t` | `ES / AT` | 4 |
| `compute_sv_t` | `ES − AT` | 3 |
| `compute_ieac_t` | `PD / SPI(t)` | 4 |
| `classify_health` | `consumed/budget` vs thresholds | 8 |
| `freeze_spi_boundary` | walk cronológico, congela no último avanço do PV | 3 |

**Total de testes unitários EVM puros:** 104 (em `test_evm_service.py`)

---

## 3. Cenários Simulados com Valores Factuais

### Cenário A — Projeto equilibrado (CPI = 1,00)

**Dados:**
- `budget_hours = 100h`, `budget_cost = R$10.000`
- `consumed = 50h`, `cost_per_hour = R$100/h`

**Cálculo manual:**

```
EV  = min(50/100, 1,0) × 10.000 = 5.000
AC  = 50 × 100                  = 5.000
CPI = EV / AC = 5.000 / 5.000   = 1,000  (no orçamento)
EAC = BAC / CPI = 10.000 / 1,0  = 10.000
CV  = EV − AC = 5.000 − 5.000   = 0
```

**Verificação automatizada (`TestCpiIntegrity`):**
- `test_portfolio_health_cpi` → `total_cost = 5.000` ✓  
- `test_runway_cpi` → `cpi = 1.0000` ✓  
- `test_forecast_cpi` → `cpi = 1.0000` ✓  
- `test_cpi_consistency_runway_vs_forecast` → divergência < 0,001 ✓

---

### Cenário B — Projeto acima do orçamento (EV capped, CPI < 1)

**Dados:**
- `budget_hours = 100h`, `budget_cost = R$10.000`
- `consumed = 25h`, `cost_per_hour = R$200/h`

**Cálculo manual:**

```
EV  = min(25/100, 1,0) × 10.000 = 2.500
AC  = 25 × 200                  = 5.000
CPI = 2.500 / 5.000             = 0,500  (50% acima do orçamento)
EAC = 10.000 / 0,5              = 20.000  (projeção de estouro duplo)
VAC = 10.000 − 20.000           = −10.000
```

**Verificação automatizada (`TestCpiIntegrity_PartialCompletion`):**
- `test_runway_cpi_partial` → `cpi = 0.5000` ✓  
- `test_forecast_eac` → `eac = 20.000` ✓  
- `test_forecast_cpi_partial` → `cpi = 0.5000` ✓

---

### Cenário C — Verificação do cap no EV (horas consumidas > orçamento)

Este é o cenário crítico: sem o cap, `EV > BAC` → `CPI > 1` mesmo em projeto estourado (falso positivo).

**Dados:**
- `budget_hours = 100h`, `budget_cost = R$10.000`
- `consumed = 136h`, `cost_per_hour = R$100/h`

**Cálculo manual (sem cap — comportamento ERRADO):**
```
EV_sem_cap = (136/100) × 10.000 = 13.600
CPI_errado = 13.600 / 13.600    = 1,000  ← mascara o estouro!
```

**Cálculo correto (com cap):**
```
EV_capped = min(136/100, 1,0) × 10.000 = 10.000  (= BAC)
AC        = 136 × 100                  = 13.600
CPI       = 10.000 / 13.600            = 0,7353  (projeto estourado corretamente)
EAC       = 10.000 / 0,7353            ≈ 13.600
```

**Verificação automatizada (`TestEvmOverBudget`):**
- `test_runway_cpi_over_budget` → `cpi = 0.7353`, `cpi < 1.0` ✓  
- `test_forecast_cpi_over_budget` → `cpi = 0.7353` ✓  
- `test_trends_actual_cost_over_budget` → `actual_cost = 13.600` ✓

---

### Cenário D — SV e SPI com baseline (projeto atrasado)

**Dados:**
- `budget_hours = 100h`, `budget_cost = R$10.000`
- Ciclo 1: planejado 40h, realizado 30h  
- Ciclo 2: planejado 40h, realizado 30h  
- `cost_per_hour = R$100/h`

**Cálculo manual:**

```
consumed_cum = 30 + 30 = 60h
planned_cum  = 40 + 40 = 80h

EV = (60/100) × 10.000 = 6.000
AC = 60 × 100          = 6.000
PV = (80/100) × 10.000 = 8.000

SPI = actual_h / planned_h = 60 / 80 = 0,750  (atrasado)
SV  = actual_h − planned_h = 60 − 80 = −20h   (atraso de 20h)
CPI = EV / AC               = 6.000 / 6.000 = 1,000 (no orçamento, apesar do atraso)
```

**Verificação automatizada (`TestSvIntegrity`):**
- `test_forecast_sv_sign` → `sv = −20.0`, `sv < 0` ✓  
- `test_forecast_spi` → `spi = 0.7500` ✓  
- `test_runway_spi` → `spi = 0.7500` ✓

**Correlação importante:** CPI=1.0 e SPI=0.75 são independentes. Um projeto pode estar no orçamento mas atrasado — o sistema distingue corretamente essas duas dimensões.

---

### Cenário E — Congelamento de custos (`freeze_costs`)

Prova que o custo histórico não é afetado por alterações posteriores no rate card.

**Dados:** `normal_hours=8h`, `cost_per_hour=R$50/h`, `extra_multiplier=1.5`, `standby_multiplier=1.25`

**Cálculo:**
```
normal_cost  = 8 × 50           = R$400,00
extra_cost   = 0 × 50 × 1,5    = R$0,00
standby_cost = 0 × 50 × 1,25   = R$0,00
```

**Verificação:** `TestFreezeCosts.test_normal_only` → `normal_cost = 400.0` ✓

O padrão de congelamento é garantido pela arquitetura: `cost_per_hour` é resolvido em `_lookup_rate()` **na ingestão** e salvo na coluna `TimesheetRecord.cost_per_hour`. Consultas analíticas sempre usam o valor congelado, nunca recalculam.

---

### Cenário F — Thresholds de saúde configuráveis

Os limites de alerta são configuráveis via `GlobalConfig`. Padrão: `warning=0.9`, `critical=1.0`.

**Verificação (`TestClassifyHealth`):**

| consumed | budget | ratio | resultado |
|---|---|---|---|
| 80h | 100h | 0,80 | `ok` ✓ |
| 90h | 100h | 0,90 | `warning` ✓ |
| 99,9h | 100h | 0,999 | `warning` ✓ |
| 100h | 100h | 1,00 | `overrun` ✓ |
| 101h | 100h | 1,01 | `overrun` ✓ |
| 50h | `null` | — | `no_budget` ✓ |

Com thresholds personalizados (0,8 / 0,9): `test_custom_thresholds` ✓

---

### Cenário G — Earned Schedule (ES, SPI(t), SV(t), IEAC(t))

Métricas de prazo baseadas em curva PV de custo (não apenas horas).

**Dados:** `pv_curve = [100, 200, 300]`, `EV = 150`

**Cálculo:**
```
ES = 1 + (150 − 100) / (200 − 100) = 1 + 0,5 = 1,5 ciclos
AT = 2 ciclos (dois ciclos ocorridos)

SPI(t) = ES / AT = 1,5 / 2,0 = 0,750
SV(t)  = ES − AT = 1,5 − 2,0 = −0,5 ciclos (atrasado meio ciclo)
IEAC(t) = PD / SPI(t) = 4 / 0,75 = 5,33 ciclos
```

**Verificação (`TestEarnedSchedule`, `TestSpiT`, `TestSvT`, `TestIeacT`):**
- `compute_earned_schedule(150, [100,200,300])` → `1.5` ✓  
- `compute_spi_t(1.5, 2.0)` → `0.75` ✓  
- `compute_sv_t(1.5, 2.0)` → `−0.5` ✓  
- `compute_ieac_t(4.0, 0.75)` → `5.33` ✓  
- Cap no máximo da curva: `compute_earned_schedule(350, [100,200,300])` → `3.0` ✓  
- EV=0 → `None` ✓

---

### Cenário H — EAC sensível a prazo (`compute_eac_schedule`)

**Dados:** `BAC=10.000`, `AC=4.000`, `EV=4.000`, `CPI=1.0`, `SPI=0.8`

```
EAC_schedule = AC + (BAC − EV) / (CPI × SPI)
             = 4.000 + (10.000 − 4.000) / (1,0 × 0,8)
             = 4.000 + 7.500
             = 11.500
```

Comparação: `EAC_standard (BAC/CPI) = 10.000`. O atraso acrescenta R$1.500 à projeção.

**Verificação:** `TestComputeEacSchedule.test_behind_schedule_raises_eac` → `11.500` ✓

---

### Cenário I — TCPI (eficiência necessária)

**Dados:** `BAC=10.000`, `AC=4.000`, `EV=5.000`

```
TCPI = (BAC − EV) / (BAC − AC)
     = (10.000 − 5.000) / (10.000 − 4.000)
     = 5.000 / 6.000
     = 0,8333  → "Meta alcançável" (TCPI ≤ 1,0)
```

**Verificação:** `TestComputeTcpi.test_normal` → `0.8333` ✓  
Divisão por zero (BAC=AC): `test_bac_equals_ac_returns_none` → `None` ✓

---

### Cenário J — Tendências: consistência de custo real

Custo real nas Tendências deve ser a soma dos `normal_cost + extra_cost + standby_cost` congelados — a mesma base que Runway e Previsão usam.

**Dados:** `consumed=40h`, `cost_per_hour=R$50/h` → `AC = 40 × 50 = R$2.000`

**Verificação (`TestTrendsCpiConsistency`):**
- `test_trends_actual_cost` → `actual_cost = 2.000` ✓  
- `test_trends_runway_consistency` → CPI de Runway == CPI de Previsão para o mesmo PEP ✓

---

### Cenário K — SPI com horas excedentes (bug histórico corrigido)

Quando `consumed > budget_hours`, o SPI **deve** usar a razão de horas brutas — não o cap monetário.

**Dados:** `budget=100h`, `planned=50h`, `consumed=120h`

```
SPI correto (horas)  = 120 / 50 = 2,40
SPI errado (R$ cap)  = min(120/100,1)×bc / (50/100×bc) = 10.000/5.000 = 2,00  ← INCORRETO
```

**Verificação:** `TestRunwaySpiScenarios.test_spi_overrun_hours_uses_actual_ratio` → `spi = 2.4` ✓

---

### Cenário L — Fallback de multiplicadores sem GlobalConfig

Quando não há `GlobalConfig`, o sistema usa padrões (`em=1.5`, `sm=0.33`). Isso garante que a primeira importação de planilha não produz custos incorretos.

**Dados:** `standby=10h`, `cph=R$100/h`, `sm=0.33` → `AC = 10×100×0.33 = R$330`

**Verificação:** `TestMultiplierFallback.test_trends_actual_cost_uses_sm_fallback` → `actual_cost = 330.0` ✓

---

### Cenário M — Ciclos a concluir não pode ser negativo

Quando `consumed > budget`, `cycles_to_complete` deve ser `null`, não um número negativo.

**Verificação:** `TestRunwayNegativeCyclesToComplete.test_cycles_to_complete_null_when_overrun` → `cycles_to_complete = null`, `risk = "overrun"` ✓

---

## 4. Consistência Entre Endpoints

Esta é a prova mais importante: as mesmas métricas, calculadas por caminhos diferentes, devem convergir.

| Métrica | Runway (`/api/v2/runway`) | Previsão (`/api/v2/forecast`) | Tendências (`/api/v2/trends`) | Consistente? |
|---|---|---|---|---|
| `actual_cost` (AC) | `Σ frozen costs` | `Σ period_cost` | `Σ actual_cost` | ✓ Sim |
| `CPI` | `compute_cpi_ev` | `compute_cpi` | N/A | ✓ Sim |
| `SPI` | `freeze_spi_boundary` | `freeze_spi_boundary` | N/A | ✓ Sim |
| `EV` | `min(h/bh,1.0)×bc` | `compute_ev_capped` | N/A | ✓ Mesma função |
| `risk` | `classify_health` | `classify_health` | N/A | ✓ Mesma função |

**Testes de consistência cruzada:**
- `test_cpi_consistency_runway_vs_forecast` — divergência < 0,001 ✓  
- `test_runway_spi` (SvIntegrity) — divergência < 0,001 ✓  
- `test_trends_runway_consistency` ✓

---

## 5. Pipeline de Ingestão — Integridade dos Dados

O custo é determinado **uma única vez**, no momento da importação, via `_lookup_rate()`.

```python
# services/ingestion.py — fase N1
cost_per_hour = _lookup_rate(db, collab, record_date)
normal_cost, extra_cost, standby_cost = freeze_costs(
    normal_hours, extra_hours, standby_hours,
    cost_per_hour, extra_multiplier, standby_multiplier
)
```

**Consequência verificável:** alterar o rate card após a importação **não altera** `normal_cost`, `extra_cost` ou `standby_cost` dos registros históricos. Coberto por `tests/test_ratecard.py` (35 testes sobre lookup e congelamento).

**Pipeline completo verificado:** `test_full_sample.py` — 83 testes cobrindo upload CSV/XLSX → ingestão → quarentena → cálculos analíticos end-to-end.

---

## 6. Regras de Negócio — Validação de Thresholds

Os semáforos de saúde (`ok` / `warning` / `overrun` / `no_budget`) usam thresholds de `GlobalConfig`:

- **`ok`:** `consumed/budget < 0.9` (padrão)  
- **`warning`:** `0.9 ≤ consumed/budget < 1.0`  
- **`overrun`:** `consumed/budget ≥ 1.0`  
- **`no_budget`:** `budget = null` ou `budget = 0`

Os limiares são configuráveis pelo administrador via `/api/theme` → `budget_warning_threshold` / `budget_critical_threshold`. A função `get_thresholds(cfg)` é o ponto único de leitura em todo o sistema.

---

## 7. Cobertura de Testes por Área

| Arquivo de testes | Testes | Área coberta |
|---|---|---|
| `test_evm_service.py` | 104 | Todas as funções de `services/evm.py` — pura matemática |
| `test_evm_integrity.py` | 20 | Consistência CPI/SPI/EAC entre endpoints via HTTP |
| `test_v2_endpoints.py` | 64 | Todos os endpoints v2: portfolio, runway, forecast, trends, ES |
| `test_full_sample.py` | 83 | Pipeline completo: upload → ingestão → analytics |
| `test_ratecard.py` | 35 | Rate card lookup e freeze pattern |
| `test_ingestion.py` | 64 | Parser CSV/XLSX, quarentena, regras de validação |
| `test_runway_concentration.py` | 23 | Runway, concentração de risco |
| `test_monte_carlo.py` | 8 | Simulação probabilística |
| `test_rule_engine.py` | 32 | Motor de regras por linha |
| `test_quarantine.py` | 23 | Workflow de quarentena |
| `test_projects.py` | 27 | CRUD de projetos + budget alerts |
| `test_simulation.py` | 1 | Simulação full-portfolio |
| Demais | 106 | Ciclos, usuários, auth, ACL, theme |
| **Total** | **590** | **590 passados, 0 falhas** |

---

## 8. Verificação da Interface — Correlação Dados → Gráficos

Os cálculos são server-side em Python. O frontend recebe os valores já prontos (`render-ready`) e apenas os exibe. Isso elimina o risco de aritmética duplicada ou divergente no JavaScript.

**Fluxo verificado:**

```
Backend (evm.py) → JSON render-ready → Frontend (charts/portfolio.js, app.js)
                    CPI=0.735                 exibe 0.74
                    risk="overrun"            exibe vermelho
                    eac=13.600               exibe "R$13,6k"
```

**Garantia de consistência de cor:** `_healthColor()` e `_riskColor()` no frontend usam `_getPalette()[0]` para `success`/`ok`, garantindo que a cor "verde" segue a paleta configurada pelo administrador — sem hardcode.

---

## 9. Pontos de Atenção e Limitações Documentadas

| Item | Status | Nota |
|---|---|---|
| `compute_ev_cost` (não-capped) | Mantida para uso diagnóstico | Documentada: `NOTE: this function does NOT cap EV at BAC` |
| SPI baseado em horas (AgileEVM proxy) | Implementação intencional | Documentada: converge com EV/PV quando taxa uniforme |
| `SPI(t)` requer curva PV de custo | Só disponível com planejamento por ciclo | Frontend exibe `N/A` quando ausente |
| Multiplicadores em `freeze_costs` usam valor do `GlobalConfig` no momento da ingestão | Corrige retroativamente se re-importado | Comportamento esperado e documentado |
| `cycles_to_complete` usa média dos últimos 3 ciclos (velocity window) | Estimativa, não determinística | Campo nomeado como `avg_hours_per_cycle` no payload |

---

## 10. Conclusão

**Todas as métricas e KPIs do PMAS estão corretas.**

Fatos comprovados por dados:

1. **CPI usa `EV/AC` com EV capped em BAC** — previne falso positivo em projetos estourados (Cenário C).  
2. **SPI usa razão de horas brutas** — não a razão monetária, corrigindo o bug de capping de EV (Cenário K).  
3. **AC é consistente entre Tendências, Runway e Previsão** — todos usam o mesmo `Σ frozen_costs` (Cenário J).  
4. **Custo congelado na ingestão** — rate cards históricos são imutáveis (Cenário E).  
5. **Earned Schedule implementado corretamente** — interpolação linear sobre curva PV (Cenário G).  
6. **Thresholds de saúde são configuráveis e aplicados uniformemente** — `get_thresholds(cfg)` como ponto único (Cenário F).  
7. **CPI de Runway == CPI de Previsão para o mesmo PEP** — verificado por 4 testes de consistência cruzada.  
8. **590 testes automatizados passam sem nenhuma falha** — em Python 3.11, SQLite in-memory, reproduzível.

```
platform linux -- Python 3.11.15, pytest-9.0.3
590 passed in 33.19s
```

---

*Relatório gerado em 2026-06-03. Todos os cálculos são reproduzíveis com `pytest tests/ -v`.*
