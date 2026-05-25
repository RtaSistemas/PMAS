# Proposta: EVM Tempo-Faseado com Fallback por Horas

**Data:** 2026-05-25  
**Contexto:** Divergência identificada entre CPI do bullet chart e runway. Corrigida com `compute_cpi_ev` (horas como proxy de progresso). Este documento propõe a evolução para EVM tempo-faseado quando baseline de custo existe.

---

## 1. Situação Atual

### Como o CPI é calculado hoje

```
EV = min(horas_consumidas / horas_orçadas, 1.0) × budget_cost
CPI = EV / actual_cost
```

**Por que horas e não custos?** Em EVM, usar custo para medir desempenho de custo é raciocínio circular — o índice sempre resultaria próximo de 1,0, perdendo seu valor diagnóstico. Horas consumidas funcionam como medida de progresso físico independente do custo.

### Limitação do método atual

O proxy por horas assume que **1 hora planejada entrega exatamente o mesmo valor em qualquer ponto do projeto**. Isso ignora o cronograma: um projeto com 80% das horas consumidas nos primeiros 3 meses de um projeto de 12 meses aparece com "80% concluído" mesmo que o plano previsse apenas 30% para esse período.

---

## 2. Alternativa: EVM Tempo-Faseado

### Conceito

Com um baseline de custo por ciclo (`ProjectCyclePlan.planned_cost`), é possível calcular:

| Métrica | Definição | Fonte |
|---|---|---|
| **BAC** | Budget at Completion — orçamento total | `Project.budget_cost` ou `ProjectBaseline.budget_cost` |
| **PV** | Planned Value — custo planejado acumulado até o ciclo de referência | `SUM(ProjectCyclePlan.planned_cost)` até o ciclo atual |
| **AC** | Actual Cost — custo real acumulado | `SUM(TimesheetRecord.{normal,extra,standby}_cost)` |
| **EV** | Earned Value — `min(PV / BAC, 1.0) × BAC` | Calculado em runtime |
| **CPI** | `EV / AC` | Calculado em runtime |
| **SPI** | `EV / PV` | Calculado em runtime |

### Fórmula

```
PV_acumulado = SUM(planned_cost dos ciclos já encerrados até hoje)
EV = min(PV_acumulado / BAC, 1.0) × BAC
CPI = EV / AC
SPI = EV / PV_acumulado   (quando PV > 0)
```

**Por que isso é mais preciso:**  
O valor agregado (EV) passa a refletir o cronograma previsto, não apenas o total de horas. Um projeto onde o plano previa gastar R$ 30.000 até agora, mas já gastou R$ 50.000, mostra CPI = 0,6 — mesmo que as horas estejam no ritmo esperado.

---

## 3. Comparação de Resultados

### Cenário exemplo

| Dado | Valor |
|---|---|
| `budget_cost` | R$ 100.000 |
| `budget_hours` | 1.000 h |
| `planned_cost` acumulado até hoje | R$ 40.000 |
| `consumed_hours` | 500 h (50% das horas totais) |
| `actual_cost` | R$ 60.000 |

| Método | EV | CPI | Interpretação |
|---|---|---|---|
| **Atual (horas)** | `min(500/1000, 1.0) × 100.000 = R$ 50.000` | `50.000/60.000 = 0,83` | 17% acima do orçamento |
| **Tempo-faseado** | `min(40.000/100.000, 1.0) × 100.000 = R$ 40.000` | `40.000/60.000 = 0,67` | 33% acima do orçamento |
| **Errado (BAC proxy)** | `R$ 100.000` | `100.000/60.000 = 1,67` | 67% abaixo do orçamento ✗ |

O método tempo-faseado revela que o projeto gastou R$ 60.000 para entregar o valor que custaria R$ 40.000 segundo o plano — diagnóstico mais preciso.

---

## 4. Regras de Prioridade (Fallback)

A proposta mantém compatibilidade total: projetos sem baseline de custo continuam funcionando com o método por horas.

```
SE projeto tem ProjectCyclePlan com planned_cost preenchido
  E existe pelo menos um ciclo planejado no passado
→ usar EVM tempo-faseado

SENÃO SE projeto tem budget_hours > 0 e budget_cost > 0
→ usar EVM por horas (comportamento atual)

SENÃO
→ CPI = None (sem dados suficientes)
```

---

## 5. Impacto por Componente

### Backend

| Arquivo | Mudança |
|---|---|
| `backend/app/services/evm.py` | Adicionar `compute_cpi_timephased(plans, cutoff_date, bac, actual_cost)` |
| `backend/app/routers/v2/portfolio.py` | Substituir `compute_cpi_ev` por chamada com fallback; consultar `ProjectCyclePlan` por PEP |
| `backend/app/routers/v2/runway.py` | Idem — usar tempo-faseado quando disponível |
| `backend/app/routers/v2/forecast.py` | Já usa lógica similar — verificar consistência |

#### Novo query necessário em portfolio.py

```python
# Para cada pep_wbs que tem projeto registrado:
plans = (
    db.query(ProjectCyclePlan)
    .join(Cycle, ProjectCyclePlan.cycle_id == Cycle.id)
    .filter(
        ProjectCyclePlan.project_id == proj.id,
        ProjectCyclePlan.planned_cost.isnot(None),
        Cycle.end_date <= date.today(),   # apenas ciclos encerrados
    )
    .all()
)
pv_accumulated = sum(p.planned_cost for p in plans)
```

**Custo de performance:** Uma query adicional por PEP que tem projeto registrado. Com índice em `(project_id, cycle_id)` já existente, o impacto é mínimo. Para o endpoint de portfolio agregado (sem filtro por ciclo), essa query pode ser feita em batch com `project_id.in_(proj_ids)`.

### Frontend

Sem mudanças necessárias. O campo `cpi` na resposta da API já é consumido pelo bullet chart e runway — a melhoria é transparente para o frontend.

### Testes

| Arquivo | O que testar |
|---|---|
| `tests/test_analytics.py` | Adicionar cenário: projeto com baseline de custo → CPI tempo-faseado |
| `tests/test_analytics.py` | Cenário sem baseline → fallback para horas (comportamento atual preservado) |
| `tests/test_analytics.py` | Cenário sem baseline e sem budget_hours → CPI = None |

---

## 6. Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|---|---|---|
| Projetos com `planned_cost = 0` em todos os ciclos ativam o tempo-faseado incorretamente | Média | Verificar `pv_accumulated > 0` antes de usar o método |
| Ciclos futuros no baseline inflam o PV | Baixa | Filtrar apenas ciclos com `end_date <= today` |
| Baseline parcial (só alguns ciclos com custo) dá PV sub-estimado | Alta | Documentar: o método só é ativado se ≥ 1 ciclo passado tem `planned_cost` preenchido; caso contrário, fallback |
| Projetos recém-criados sem histórico de baseline | Alta | Tratada pelo fallback — sem baseline → horas |

---

## 7. O Que NÃO Muda

- O campo `cpi` na resposta da API mantém o mesmo nome e tipo — **sem breaking change**
- A aba Previsão (S-curve) já usa lógica tempo-faseada para seu próprio cálculo — não é afetada
- Projetos sem baseline continuam funcionando exatamente como hoje
- O cálculo de SPI no runway (baseado em `ProjectCyclePlan.planned_hours`) não é alterado

---

## 8. Decisão Necessária

Antes de implementar, confirmar:

1. **Corte temporal do PV**: usar apenas ciclos com `end_date <= hoje`, ou com `start_date <= hoje`? (Recomendação: `end_date`, pois um ciclo só está "realizado" quando encerrado)

2. **Ciclos futuros no baseline**: devem ser ignorados no cálculo de PV? (Recomendação: sim — PV acumulado só inclui o passado)

3. **Baseline parcial**: se apenas 5 dos 12 ciclos têm `planned_cost`, usar tempo-faseado mesmo assim? (Recomendação: sim, desde que `pv_accumulated > 0`)

4. **Exibir o método usado**: adicionar campo `cpi_method: "timephased" | "hours_proxy"` na resposta da API para fins de transparência na UI? (Opcional — útil para debugging)
