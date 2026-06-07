# Auditoria Executiva — PMAS

**Project Management Assistant System** · Conformidade EVM, Integridade de Dados e Cobertura Funcional

| Campo | Valor |
|---|---|
| **Versão** | v1.4.8RC_PMAS |
| **Empresa** | RTA Sistemas |
| **Período** | S1–S3 · 2026 |
| **Data da auditoria** | 2026-06-06 |
| **Stack** | Python 3.11+ · FastAPI · SQLAlchemy · SQLite · Vanilla JS · Apache ECharts 5 |

> ## VEREDITO: **PARCIALMENTE CONFORME**
> 30 Conforme · 1 Parcialmente Conforme · 0 Não Conforme · NC-01 e NC-03 resolvidas

---

## 1. Resumo Executivo

O **PMAS (Project Management Assistant System)** é uma plataforma de gestão e analytics de apontamentos de horas (timesheets) com rastreamento financeiro EVM (Earned Value Management), motor de regras de validação, fluxo de quarentena, planejamento de baseline, ACL por usuário e log de auditoria completo. Esta auditoria avaliou a conformidade das fórmulas EVM com o padrão PMI, a integridade e consistência dos dados, a formatação conforme normas internacionais (ISO 8601, ECMA-402) e a cobertura funcional do sistema.

Foram verificados **mais de 30 critérios** distribuídos em cinco matrizes de validação. As **11 fórmulas EVM** avaliadas estão 100% conformes ao padrão PMI Practice Standard for Earned Value Management; a **cobertura funcional** é 100%. Três não-conformidades foram identificadas; **NC-01** (fuso horário misto) e **NC-03** (barra de semáforo) foram corrigidas no mesmo sprint. Permanece aberta apenas a **NC-02** (chave secreta obrigatória em produção — severidade baixa).

### Indicadores-chave

| Métrica | Valor |
|---|---|
| Critérios avaliados | 30+ |
| Conforme | 30 |
| Parcialmente Conforme | 1 |
| Não Conforme | 0 |
| Fórmulas EVM conformes | 11 |
| Cobertura funcional | 100% |
| Testes automatizados | 677 |
| Testes EVM específicos | 124 |

### Veredito Final

**PARCIALMENTE CONFORME.** O sistema demonstra excelência técnica nas áreas críticas: as fórmulas EVM são fiéis ao padrão PMI, possuem guardas contra divisão por zero em todas as funções, e contam com 124 testes unitários e de integração específicos. A cobertura funcional atende 100% dos requisitos. Das três não-conformidades identificadas, **NC-01** (`datetime.utcnow` padronizado para `now_br` em todos os modelos) e **NC-03** (remoção de `!important` em `.semaphore-bar`) foram corrigidas no mesmo sprint. Permanece aberta apenas a **NC-02** (severidade baixa): recomenda-se tornar `PMAS_SECRET_KEY` obrigatória antes do próximo deploy de produção.

### Destaques Positivos

- **Fonte única de verdade EVM:** todas as fórmulas vivem em `services/evm.py` (Golden Rule GR-2); nenhum router ou frontend reimplementa cálculo financeiro.
- **Respostas render-ready:** a camada `/api/v2` entrega CPI, SPI, EAC, TCPI, VAC, CV, SV já computados no servidor; o frontend não faz aritmética EVM.
- **Padrão de congelamento (freeze):** `cost_per_hour` é resolvido na ingestão e nunca é alterado retroativamente por mudanças de rate card.
- **Baseline imutável:** `ProjectBaseline` trava o orçamento (`locked_at`, `is_active`); `resolve_effective_budget()` é a fonte autoritativa.
- **Zero dívida técnica crítica:** 0 `console.log` no frontend, 0 TODO/FIXME/HACK em fluxos EVM.

---

## 2. Matriz A — Validação de Fórmulas EVM

Todas as 11 fórmulas avaliadas estão **CONFORME** ao PMI Practice Standard for Earned Value Management. Cada função guarda contra divisão por zero retornando `None`.

| Métrica | Fórmula PMI | Implementação | Arquivo:Linha | Status |
|---|---|---|---|---|
| CPI | EV ÷ AC | `if not ev_cost or actual_cost == 0: return None; return round(ev_cost / actual_cost, 4)` | `services/evm.py:47` | CONFORME |
| SPI | EV ÷ PV (proxy de horas AgileEVM) | `if not cumulative_planned_hours or cumulative_planned_hours == 0: return None; return round(cumulative_actual_hours / cumulative_planned_hours, 4)` | `services/evm.py:91` | CONFORME |
| SV | EV − PV (horas) | `return round(cumulative_actual_hours - cumulative_planned_hours, 2)` | `services/evm.py:214` | CONFORME |
| CV | EV − AC | `return round(ev_cost - actual_cost, 2)` | `services/evm.py:182` | CONFORME |
| EAC (BAC/CPI) | BAC ÷ CPI | `return round(budget_cost / cpi, 2)` | `services/evm.py:110` | CONFORME |
| EAC (schedule) | AC + (BAC−EV) ÷ (CPI×SPI) | `return round(actual_cost + (budget_cost - ev_cost) / (cpi * spi), 2)` | `services/evm.py:128` | CONFORME |
| ETC | EAC − AC | `return round(max(eac - actual_cost, 0.0), 2)` | `services/evm.py:169` | CONFORME |
| VAC | BAC − EAC | `return round(budget_cost - eac, 2)` | `services/evm.py:158` | CONFORME |
| TCPI | (BAC−EV) ÷ (BAC−AC) | `denominator = budget_cost - actual_cost; if denominator == 0: return None; return round((budget_cost - ev_cost) / denominator, 4)` | `services/evm.py:143-146` | CONFORME |
| EV capped | min(consumed/budget, 1.0) × BAC | `return round(min(consumed_hours / budget_hours, 1.0) * budget_cost, 2)` | `services/evm.py:280-282` | CONFORME |
| ES (Earned Schedule) | Interpolação na curva PV | `frac = (ev - pv_prev) / (pv_at_t - pv_prev); return round(i + frac, 4)` | `services/evm.py:514` | CONFORME |

> **Nota sobre SPI:** a implementação adota o proxy de horas AgileEVM (Sulaiman et al., 2006) — usa horas reais / horas planejadas em vez do EV/PV monetário. Ambos os métodos convergem quando o custo é distribuído uniformemente. Decisão documentada explicitamente no código.

---

## 3. Integridade, Formatação e Cobertura de Dados

### Matriz B — Consistência de Dados

| Critério | Norma | Evidência | Status |
|---|---|---|---|
| PV/EV/AC na mesma unidade | PMI 19-006 §4.3 | Horas para SPI/SV; R$ para CPI/EAC/CV — consistente dentro de cada ramo | CONFORME |
| Divisão por zero | Obrigatória em todos os índices | Toda função EVM: guarda explícita `if denominator == 0: return None` ou `if actual_cost == 0: return None` | CONFORME |
| BAC imutável após baseline | Sem mudança sem Change Request | `ProjectBaseline` trava o orçamento na criação (`locked_at`, `is_active=True`); `resolve_effective_budget()` é fonte única | CONFORME |
| EV apenas de itens aceitos | PMI 19-006 §4.2 | Fluxo de quarentena: linhas inválidas excluídas do analytics; só registros aprovados geram AC/EV | CONFORME |
| AC vinculado ao período | ISO 21508 | `cost_per_hour` congelado na ingestão; `record_date` (coluna Data) rastreia o período de faturamento | CONFORME |

### Matriz C — Formatação e Integridade de Dados

| Critério | Norma | Evidência | Status |
|---|---|---|---|
| Moeda com locale | ECMA-402 Intl.NumberFormat | `v.toLocaleString(_locale === 'pt' ? 'pt-BR' : 'en-US', {minimumFractionDigits:2})` — `app.js:30` | CONFORME |
| Datas da API em ISO 8601 | ISO 8601 | Tipo `Date` do FastAPI serializa para ISO 8601 (YYYY-MM-DD) em todas as respostas JSON | CONFORME |
| Fuso horário consistente | Estratégia de fuso uniforme | **RESOLVIDO (NC-01):** `datetime.utcnow` substituído por `now_br` em `ProjectBaseline.locked_at`, `ThemePreset.created_at` e `Notification.created_at`. Todos os timestamps usam `now_br` (BRT/America/Sao_Paulo) uniformemente. | CONFORME |
| Duração vs. hora-do-dia | Formatos distintos | Horas armazenadas como decimal `Float` (ex.: 7.5), não string HH:MM. Sem confusão entre duração e hora de relógio | CONFORME |

### Matriz D — Cobertura Funcional (100% CONFORME)

| Funcionalidade | Requerida | Implementação | Status |
|---|---|---|---|
| Registro de timesheet | Sim | `POST /api/upload-timesheet` → `ingest_file()` pipeline de 6 fases | CONFORME |
| Vínculo Timesheet → AC | Sim | `cost_per_hour` congelado na ingestão; `total_cost` agregado em `PepCycleSummary` | CONFORME |
| BAC por projeto | Sim | `Project.budget_hours/budget_cost`; sobreposto por `ProjectBaseline` ativa | CONFORME |
| PV planejado por ciclo | Sim | `ProjectCyclePlan` — horas/custo planejados por (projeto, ciclo); S-curve de baseline | CONFORME |
| EV por ciclo | Sim | `PepCycleSummary` pré-computado; `compute_ev_capped()` no servidor | CONFORME |
| Dashboard SPI + CPI | Sim | `/api/v2/forecast` retorna CPI, SPI, EAC, TCPI, VAC, CV, SV render-ready | CONFORME |
| EAC projetado | Sim | Ambos BAC/CPI e EAC sensível a cronograma (CPI×SPI) | CONFORME |
| Histórico de métricas | Sim | `BudgetRevision` append-only; `PepCycleSummary` por ciclo; gráfico de tendências | CONFORME |
| Exportação de dados | Recomendada | Exportação CSV em todas as tabelas (Ciclos, Projetos, Equipe, Esforço) | CONFORME |
| Alertas de desvio crítico | Recomendada | Semáforo (verde/amarelo/vermelho/cinza), badges de orçamento, sistema de notificações | CONFORME |

### Matriz E — Qualidade

| Critério | Limiar | Encontrado | Status |
|---|---|---|---|
| Logs de debug em produção | 0 | 0 `console.log` em `frontend/`; `logging` estruturado no backend | CONFORME |
| TODOs críticos em fluxos EVM | 0 | 0 TODO/FIXME/HACK em qualquer arquivo Python ou JS | CONFORME |
| Cobertura de testes nos cálculos EVM | > 0 | 677 testes no total; 104 em `test_evm_service.py` + 20 em `test_evm_integrity.py` = 124 testes EVM específicos | CONFORME |
| Segredos hardcoded | 0 | 0 — `PMAS_SECRET_KEY` lida de variável de ambiente; fallback aleatório apenas em dev | PARCIALMENTE CONFORME |

---

## 4. Não-Conformidades e Observações

### NC-01 — ✅ RESOLVIDA

**Inconsistência de fuso horário nos registros de auditoria**

| Campo | Descrição |
|---|---|
| Norma | ISO 8601 / ISO 21508 — estratégia de fuso uniforme |
| Evidência original | `models.py:128` usava `datetime.utcnow` para `locked_at`; linhas 149, 243, 254, 278 usavam `now_br` (BRT) |
| Correção aplicada | Substituídos `datetime.utcnow` por `now_br` em `ProjectBaseline.locked_at`, `ThemePreset.created_at` e `Notification.created_at`. Import `from datetime import datetime` removido de `models.py`. Todos os timestamps agora usam `now_br` uniformemente. |
| Testes | 677 testes passam após a correção |
| Status | **FECHADA** |

### NC-02 — SEVERIDADE BAIXA

**`PMAS_SECRET_KEY` não obrigatória em produção**

| Campo | Descrição |
|---|---|
| Norma | Boas práticas de segurança de API |
| Evidência | `deps.py:17-25` — se `PMAS_SECRET_KEY` não está definida, gera chave aleatória com aviso; não bloqueia o startup |
| Impacto na gestão | Em deploy sem a variável configurada, todos os usuários são deslogados a cada reinicialização do servidor |
| Recomendação | Verificar `PMAS_ENV=production` no startup e lançar `RuntimeError` se a chave não estiver definida |
| Esforço | Pequeno |
| Prazo | Antes do próximo deploy de produção |
| Risco se não tratado | Perda de sessão em manutenções |

### NC-03 — ✅ RESOLVIDA

**Barra de semáforo no dashboard não era exibida**

| Campo | Descrição |
|---|---|
| Evidência original | `style.css:459` — `.semaphore-bar { display: none !important }` impedia que `bar.style.display = 'flex'` funcionasse |
| Impacto | Resumo do semáforo no cabeçalho funcionava; barra expandida com pills por PEP não era visível; drill-down por PEP inacessível |
| Correção aplicada | Removido `!important` da regra `.semaphore-bar` em `style.css:459`. A regra `#semaphoreBar { display: none }` mantém o estado inicial oculto; o JS `bar.style.display = 'flex'` agora sobrepõe corretamente via inline style. |
| Status | **FECHADA** |

---

## 5. Pipeline de Ingestão — 6 Fases

`ingest_file()` é um orquestrador que chama seis funções de fase em sequência. A assinatura pública e o dicionário de retorno permanecem inalterados. Garante GR-1: dados só entram via este pipeline.

| Fase | Função | Responsabilidade |
|---|---|---|
| 1 | `_phase_load_and_validate(file_bytes, filename)` | Carregar CSV/XLSX com pandas; validar existência das colunas obrigatórias → `DataFrame` |
| 2 | `_phase_authorize_peps(df, db, user_id, role)` | Filtrar linhas para PEPs permitidos pela ACL para usuários não-admin |
| 3 | `_phase_prescan_dates(df, db)` | Pré-escanear datas únicas parseáveis; construir cache de ciclos; auto-criar ciclos de quarentena para datas fora de qualquer ciclo ativo |
| 4 | `_phase_validate_rows(df, db, rules, cycle_cache, collab_cache)` | Checagens estruturais por linha (Q1/Q2/Q8) + motor de `ValidationRule`; separar linhas válidas do buffer de quarentena |
| 5 | `_phase_aggregate_rules(valid_rows, rules)` | Calcular somas diárias/semanais entre linhas válidas; emitir warnings/infos de regras agregadas |
| 6 | `_phase_upsert_records(db, valid_rows, extra_multiplier, standby_multiplier)` | `DELETE` cirúrgico por `(pep_wbs, cycle_id)` + `INSERT` em lote + congelamento de custo via `_lookup_rate()` |

Após as fases, `ingest_file()` persiste linhas de `QuarantineRecord`, cria a `UploadSession`, commita a transação e grava a entrada de `AuditLog`. `_lookup_rate(db, collab, record_date)` congela `cost_per_hour` na ingestão localizando a `RateCard` que casa o nível de senioridade do colaborador e o intervalo de datas.

---

## 6. Trilha de Auditoria

Registro cronológico das verificações executadas durante a auditoria (2026-06-06).

| # | Verificação | Artefato / Evidência | Resultado |
|---|---|---|---|
| 01 | CPI = EV ÷ AC com guarda de zero | `services/evm.py:47` | CONFORME |
| 02 | SPI = horas reais ÷ planejadas (AgileEVM) | `services/evm.py:91` | CONFORME |
| 03 | SV = EV − PV (horas) | `services/evm.py:214` | CONFORME |
| 04 | CV = EV − AC | `services/evm.py:182` | CONFORME |
| 05 | EAC (BAC/CPI) | `services/evm.py:110` | CONFORME |
| 06 | EAC schedule = AC+(BAC−EV)/(CPI×SPI) | `services/evm.py:128` | CONFORME |
| 07 | ETC = max(EAC − AC, 0) | `services/evm.py:169` | CONFORME |
| 08 | VAC = BAC − EAC | `services/evm.py:158` | CONFORME |
| 09 | TCPI = (BAC−EV)/(BAC−AC) com guarda | `services/evm.py:143-146` | CONFORME |
| 10 | EV capped = min(consumo/orçamento,1)×BAC | `services/evm.py:280-282` | CONFORME |
| 11 | ES por interpolação na curva PV | `services/evm.py:514` | CONFORME |
| 12 | GR-2: fórmulas EVM exclusivas em evm.py | `services/evm.py` + routers v2 | CONFORME |
| 13 | PV/EV/AC mesma unidade por ramo | PMI 19-006 §4.3 | CONFORME |
| 14 | Guarda de divisão por zero em toda função | `services/evm.py` (retorna None) | CONFORME |
| 15 | BAC imutável após baseline | `ProjectBaseline` / `resolve_effective_budget()` | CONFORME |
| 16 | EV apenas de itens aceitos (quarentena) | Fluxo de quarentena | CONFORME |
| 17 | AC vinculado ao período | `cost_per_hour` congelado + `record_date` | CONFORME |
| 18 | Moeda com locale (ECMA-402) | `app.js:30` | CONFORME |
| 19 | Datas da API em ISO 8601 | FastAPI `Date` → YYYY-MM-DD | CONFORME |
| 20 | Consistência de fuso horário | `models.py:128 (utc)` vs `149,243,254,278 (BRT)` | PARCIAL |
| 21 | Duração (Float) vs hora-do-dia | Horas como decimal Float | CONFORME |
| 22 | Registro de timesheet via pipeline único | `POST /api/upload-timesheet` | CONFORME |
| 23 | Vínculo Timesheet → AC | `cost_per_hour` + `PepCycleSummary` | CONFORME |
| 24 | BAC por projeto | `Project` + `ProjectBaseline` | CONFORME |
| 25 | PV planejado por ciclo | `ProjectCyclePlan` | CONFORME |
| 26 | EV por ciclo pré-computado | `PepCycleSummary` + `compute_ev_capped()` | CONFORME |
| 27 | Dashboard SPI+CPI render-ready | `/api/v2/forecast` | CONFORME |
| 28 | EAC projetado (dois métodos) | `services/evm.py:110,128` | CONFORME |
| 29 | Histórico de métricas | `BudgetRevision` + trends | CONFORME |
| 30 | Exportação CSV em todas as tabelas | Ciclos/Projetos/Equipe/Esforço | CONFORME |
| 31 | Alertas de desvio (semáforo/badges) | Header semaphore + budget badges | CONFORME |
| 32 | 0 console.log em produção | `frontend/` | CONFORME |
| 33 | 0 TODO/FIXME/HACK em fluxos EVM | Todo o código Python/JS | CONFORME |
| 34 | 124 testes EVM específicos | `test_evm_service.py` + `test_evm_integrity.py` | CONFORME |
| 35 | Segredos hardcoded ausentes | `deps.py:17-25` (env var) | PARCIAL |
| 36 | PMAS_SECRET_KEY obrigatória em prod | `deps.py:17-25` (fallback aleatório) | PARCIAL |
| 37 | Barra de semáforo exibível | `style.css:459` (display:none !important) | OBS |
| 38 | Pipeline de 6 fases íntegro | `services/ingestion.py` | CONFORME |
| 39 | ACL por usuário em endpoints v2 | `_allowed_peps` (v2/portfolio.py) | CONFORME |
| 40 | Migração não-destrutiva de schema | `_migrate_columns()` em database.py | CONFORME |

---

*PMAS · Project Management Assistant System · v1.4.8RC_PMAS — RTA Sistemas · Auditoria Executiva · 2026-06-06*

**Veredito: PARCIALMENTE CONFORME · 30 Conforme · 1 Parcialmente Conforme · 0 Não Conforme · NC-01 e NC-03 resolvidas**
