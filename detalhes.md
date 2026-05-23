# PMAS — Detalhamento do Sistema

> Gerado em 2026-05-23 · Branch `claude/create-project-docs-qJaUo`

---

## 1. O que o sistema entrega de informação e como

### Fontes de entrada

O sistema recebe **planilhas de timesheet** (CSV/XLSX) com no mínimo 3 colunas: colaborador, data, horas. As demais (hora extra, sobreaviso, código PEP, descrição PEP) são opcionais mas enriquecem toda a análise. O restante — projetos, ciclos, taxas, planos — é cadastrado diretamente no sistema.

### O que é produzido

**Esforço humano** — quem fez o quê e quando:
- Horas por colaborador (normal / extra / sobreaviso)
- Drill-down por clique: timeline mensal + heatmap de atividade diária por colaborador
- Tendência de consumo mês a mês
- Matriz de alocação: cruzamento colaborador × PEP

**Saúde financeira dos projetos** — quanto custa e quanto sobrou:
- Custo real acumulado por projeto (AC), calculado com taxas congeladas no momento da ingestão
- Budget consumido vs planejado (bullet chart)
- Composição do custo: quanto é hora normal, extra, sobreaviso
- Concentração de risco: quais colaboradores dominam o custo de cada projeto

**Desempenho EVM** — se os projetos estão entregando valor pelo que gastam:
- CPI, SPI, EAC, VAC, TCPI, CV, SV por projeto
- Histórico de CPI e SPI ao longo dos ciclos (evolução do desempenho)
- Quadrante EVM: posição de cada projeto no espaço custo × prazo
- Forecast: quando vai terminar e quanto vai custar no final

**Governança e rastreabilidade:**
- Quarentena com workflow de revisão (pendente → aprovado/rejeitado)
- Histórico de uploads com contagem exata de linhas inseridas/ignoradas/quarentenadas
- Log de auditoria de todas as ações com snapshot antes/depois
- Controle de acesso por PEP por usuário

### Como entrega

Tudo calculado em tempo real a cada requisição — sem cache intermediário. Os filtros (ciclo, PEP, colaborador, período) são aplicados diretamente nas queries SQL com agregação no banco. Os gráficos são construídos no cliente via Apache ECharts 5. Exportação CSV disponível para esforço, planos, ciclos, projetos, taxa e quarentena.

---

## 2. Qual metodologia usa

### Base: EVM (Earned Value Management) — ANSI/PMI 19-006-2019

O sistema implementa EVM com adaptação para contexto de timesheet por ciclos mensais (próximo de AgileEVM, Sulaiman et al., 2006):

**Cálculo do EV (Valor Agregado):**
```
EV = min(horas_ponderadas_acumuladas / BAC_horas, 1.0) × BAC_custo
```

O uso de horas ponderadas (não físicas brutas) garante consistência dimensional com o AC:
```
horas_ponderadas = normal + extra × 1.5 + sobreaviso × 0.33
```

**Custo Real (AC):** congelado na ingestão via rate card × horas ponderadas. Imutável após o upload.

**BAC:** vem do `ProjectBaseline` ativo (snapshot aprovado) ou, se inexistente, do `budget_cost` do projeto.

### Indicadores derivados

| Sigla | Fórmula | Interpretação |
|---|---|---|
| **CPI** | EV / AC | < 1 = gastando mais do que entregando |
| **EAC** | BAC / CPI | estimativa de custo final |
| **CV** | EV − AC | positivo = abaixo do orçamento |
| **TCPI** | (BAC − EV) / (BAC − AC) | eficiência necessária para terminar dentro do BAC |
| **VAC** | BAC − EAC | sobra ou estouro projetado |
| **SPI** | EV / PV (congelado) | < 1 = atrasado vs plano |
| **SV** | EV − PV | variação de prazo em R$ |

### Decisões de design metodológico

- **SPI congelado:** travado no último ciclo em que o plano avançou — evita que projetos que ultrapassam o prazo tenham SPI artificialmente convergindo para 1.0
- **TCPI indefinido:** retorna `null` quando `AC > BAC` (matematicamente indefinido — o orçamento já foi extrapolado)
- **Forecast ajustado por SPI:** a velocidade de conclusão é multiplicada pelo SPI — projetos atrasados recebem projeção mais pessimista
- **Baseline imutável:** o `ProjectBaseline` congela o BAC no momento da aprovação formal; editar o orçamento do projeto não altera KPIs históricos

### Motor de validação de dados

Regras configuráveis avaliadas row-by-row na ingestão:

| Campo | Operadores | Ações |
|---|---|---|
| horas_individuais, hora_extra_horas, hora_sobreaviso_horas | gt, gte, lt, lte, eq, neq | quarentena, descarte, warning, info |
| soma_diaria, soma_semanal | gt, gte, lt, lte | info, warning (apenas) |
| dia_semana | eq, neq, in_lista | quarentena, descarte, warning, info |
| pep_wbs | contem, nao_contem, vazio, nao_vazio | quarentena, descarte, warning, info |

Regras de sistema (🔒) não podem ser removidas, apenas desativadas.

### Custo congelado na ingestão

`cost_per_hour` é resolvido uma única vez por `_lookup_rate()` durante o upload:
1. Busca a senioridade atual do colaborador
2. Encontra o `RateCard` válido para a data do registro
3. Armazena o valor no `TimesheetRecord` — imutável depois disso

Mudanças de taxa após ingestão não afetam registros históricos.

---

## 3. Como foi pensada a UX — o que faz bem e o que pode melhorar

### O que funciona bem

**Contextualização permanente:** o semáforo no cabeçalho mostra o estado do portfólio em qualquer aba — verde/amarelo/vermelho por projeto, com contagem. O gestor nunca perde o estado macro ao navegar.

**Filtros globais com atalhos temporais:** os botões "Último mês", "Último trimestre", "Este ano" cobrem 90% dos casos de uso sem o usuário precisar digitar datas. Os multiselects cascadeados para PEP e colaborador reduzem o espaço de seleção progressivamente.

**Curva de aprendizado suave nos KPIs EVM:** todos os indicadores (CPI, EAC, TCPI, etc.) têm tooltip com nome completo em PT-BR, descrição e fórmula ao hover. Isso torna o sistema acessível a quem não tem formação formal em EVM.

**Congelamento transparente:** o banner na aba Previsão deixa explícito se o BAC está usando um baseline congelado ou o orçamento atual. O gestor sabe exatamente contra o que está medindo.

**Quarentena com rastreabilidade:** nada é descartado silenciosamente. Dados inválidos ficam com motivo, quem enviou, quando e qual regra foi violada.

**Drill-down no esforço:** clicar em um colaborador no gráfico abre painel com timeline mensal + heatmap de atividade diária — sem trocar de tela.

**Bilíngue com toggle:** toda a interface alterna entre PT-BR e EN em tempo real, sem recarregar a página.

**Layout personalizável:** o usuário pode reordenar os painéis da aba por arrastar-e-soltar, e a preferência é salva por usuário no servidor.

### O que pode melhorar

**Descoberta dos gráficos secundários é ruim:** o gráfico de IDC por PEP, a composição de custo, o bullet chart e o quadrante EVM estão escondidos atrás de toggles ou rolagem. Um usuário novo não sabe que existem. Painéis colapsáveis com título sempre visível resolveriam isso.

**A aba Previsão é manual demais:** o usuário precisa selecionar manualmente o PEP no dropdown. O sistema poderia sugerir automaticamente o projeto mais crítico (menor CPI ou mais próximo do orçamento) como padrão.

**Não há alertas proativos:** o sistema só mostra problemas quando o usuário navega até eles. Não existe notificação de "CPI caiu abaixo de 0.9 neste mês" ou "projeto X ultrapassou o orçamento esta semana". Os alertas de budget existem mas são apenas badges na tabela de projetos.

**O scatter CPI × SPI não tem rótulos nos quadrantes:** os 4 quadrantes têm cores mas não têm texto explicando o que cada um significa ("no prazo, abaixo do custo", etc.). Quem não conhece EVM não sabe o que o posicionamento significa.

**Sem comparação temporal:** não é possível ver "CPI em março vs CPI em abril" para o mesmo projeto num card comparativo. O gráfico de linhas IDC por PEP faz isso ao longo do tempo, mas não há visão de "delta do período".

**Runway e Concentração de Risco estão subutilizados:** são painéis muito úteis (ciclos restantes por projeto, dominância de colaboradores) mas ficam escondidos na sub-aba de Portfólio sem destaque. Deveriam ter pelo menos um card-resumo visível por padrão.

**Sem exportação do dashboard completo:** não é possível gerar um PDF ou pacote de relatório com todos os gráficos de um projeto. Cada gráfico tem o botão de salvar como PNG individualmente, mas não há visão consolidada exportável.

**Baseline apenas por projeto:** o congelamento existe para o BAC (orçamento), mas não para o plano de horas por ciclo (`ProjectCyclePlan`). Editar o plano muda PV, SPI e SV retroativamente. Um `PlanBaseline` seria o próximo nível de proteção.

---

## 4. O que cada gráfico conta individualmente

### Esforço da Equipe (barra horizontal empilhada)

> *"Quem carrega o portfólio — e com que tipo de hora?"*

O comprimento total da barra é o volume de trabalho. A cor divide entre normal (produtivo padrão), extra (sobrecarga) e sobreaviso (disponibilidade de baixa intensidade). Quando a fatia extra é grande num único colaborador, é sinal de risco de burnout ou gargalo. Quando sobreaviso domina num projeto, o custo real pode estar inflado sem entrega proporcional.

---

### Tendências por Ciclo (barras + linha de CPI)

> *"O ritmo de trabalho está crescendo, estável ou esgotando?"*

O eixo do tempo conta a história da aceleração ou desaceleração do portfólio. Um pico isolado pode ser sprint final de entrega; crescimento contínuo pode ser expansão de escopo. A linha de CPI sobreposta (quando ativada) mostra se esse ritmo está sendo eficiente — é possível ter muito volume e CPI baixo ao mesmo tempo.

---

### IDC por PEP — CPI × IDP ao longo dos ciclos (linhas)

> *"Cada projeto está ficando mais ou menos eficiente com o tempo?"*

É o gráfico de saúde longitudinal. Uma linha CPI começando em 1.2 e descendo ciclo a ciclo conta uma história de degradação — o projeto foi bem no início e perdeu o controle. Uma linha estável acima de 1.0 é sinal de execução consistente. A linha IDP tracejada ao lado mostra se o atraso (SPI < 1) e o custo excessivo (CPI < 1) andam juntos ou separados — divergência entre elas é o sinal mais importante.

---

### Treemap (portfólio)

> *"Onde está concentrado o esforço do portfólio — e quais projetos estão saudáveis?"*

O tamanho do bloco é o peso relativo do projeto (horas ou custo). A cor é o estado: verde = dentro do orçamento, amarelo = atenção, vermelho = estourado, cinza = sem budget definido. Um portfólio saudável tem blocos grandes e verdes. Quando um bloco grande está vermelho, é ali que a atenção gerencial deve ir primeiro.

---

### Bullet Chart — Orçado vs Realizado

> *"Cada projeto está dentro do orçamento, e por quanto?"*

A barra de fundo é o budget total. A barra colorida é o quanto foi consumido. Os marcadores de threshold (90% e 100%) criam zonas visuais de alerta. O CPI no tooltip adiciona a dimensão de eficiência: um projeto pode ter consumido 80% do budget mas ter CPI 0.7 — significa que vai ultrapassar o orçamento mesmo ainda estando abaixo. É o gráfico mais direto para uma reunião de status.

---

### Quadrante EVM — CPI × SPI (scatter)

> *"Quais projetos têm problema simultâneo de custo e prazo?"*

É o gráfico de triagem executiva. Os 4 quadrantes têm significados claros:

| Quadrante | CPI | SPI | Diagnóstico |
|---|---|---|---|
| Superior-direito (verde) | ≥ 1 | ≥ 1 | No prazo e dentro do custo |
| Superior-esquerdo (âmbar) | ≥ 1 | < 1 | Dentro do custo mas atrasado |
| Inferior-direito (azul) | < 1 | ≥ 1 | No prazo mas acima do custo |
| Inferior-esquerdo (vermelho) | < 1 | < 1 | Atrasado e acima do custo — intervenção |

Projetos no canto inferior-esquerdo muito distantes da origem são candidatos a rebaseamento ou encerramento.

---

### Curva S — Previsão de Conclusão

> *"Quando o projeto vai terminar e o que falta gastar?"*

A linha de histórico é o que aconteceu (horas acumuladas reais). A projeção tracejada é o que o ritmo atual sugere. A linha de budget é o teto. A linha de VP (valor planejado) é onde o projeto deveria estar segundo o plano original. Quando a projeção cruza o budget antes do fim, o projeto vai estourar. Quando a curva real fica muito abaixo do VP, o projeto está atrasado. A combinação das quatro linhas conta a história completa de execução.

---

### Composição de Custo por Tipo de Hora (barras empilhadas)

> *"O custo está sendo gerado por trabalho regular ou por sobrecarga?"*

Cada barra é um ciclo. A fatia azul é custo regular, a âmbar é hora extra (com multiplicador 1.5×), a vermelha é sobreaviso. Quando a fatia extra cresce num ciclo específico, houve pressão naquele período. Quando o sobreaviso domina um projeto inteiro, o modelo de trabalho desse time é fundamentalmente diferente — e isso explica comportamentos de CPI que parecem anômalos quando olhados só em horas.

---

### Runway (tabela)

> *"Quanto tempo cada projeto ainda tem antes de esgotar o orçamento?"*

É a visão operacional de sobrevida. Ciclos restantes, velocidade média, SPI e status (no prazo / em risco / atrasado / sem baseline) numa tabela ordenável. Um projeto com 2 ciclos restantes e SPI de 0.7 vai terminar em 2 ÷ 0.7 ≈ 2.9 ciclos reais — o sistema faz esse ajuste automaticamente na coluna de conclusão estimada.

---

### Concentração de Risco (cards)

> *"Qual é o risco de perder uma pessoa-chave em cada projeto?"*

Mostra quantos colaboradores concentram mais de 60% das horas (ou custo) de cada projeto. Se um único colaborador representa 70% de um projeto, a ausência dele para esse projeto. É um indicador de *bus factor* — baixíssima redundância de conhecimento. Útil para decisões de onboarding ou realocação preventiva.

---

### Heatmap de Atividade Diária (por colaborador)

> *"Quando essa pessoa trabalha — e há padrões de concentração?"*

Cada célula é um dia, a intensidade é o volume de horas. Um colaborador que concentra horas apenas nas sextas-feiras pode estar lançando retroativamente. Dias com horas muito acima da média são candidatos a revisão pela engine de validação. É o único gráfico que expõe comportamento individual ao longo do tempo calendário.

---

## Apêndice — Arquitetura resumida

### Stack
- **Backend:** Python 3.11+ · FastAPI · SQLAlchemy · SQLite
- **Frontend:** HTML + Vanilla JS · Apache ECharts 5 · SortableJS
- **Idioma da UI:** PT-BR (com toggle EN)

### Endpoints analytics principais

| Endpoint | Agrega por | Principais campos retornados |
|---|---|---|
| `GET /api/portfolio-health` | PEP | consumed_hours, actual_cost, budget_hours, budget_cost, cpi |
| `GET /api/trends` | Ciclo | normal_hours, extra_hours, standby_hours, actual_cost, normal_cost, extra_cost, standby_cost |
| `GET /api/allocation` | Colaborador × PEP | total_hours, actual_cost |
| `GET /api/forecast` | PEP (único) | cpi, spi, eac, vac, tcpi, cv, sv, remaining_hours, remaining_cost, history[], using_baseline |
| `GET /api/portfolio-runway` | PEP | pct_consumed, cycles_to_complete, spi, cpi, schedule_status, risk |
| `GET /api/portfolio-concentration` | PEP | top_contributors[], top1_pct, risk |
| `GET /api/dashboard` | Colaborador | normal_hours, extra_hours, standby_hours |

### Filtros globais disponíveis

Todos os endpoints analytics aceitam combinação de:
- `cycle_id[]` — seleção de ciclos
- `pep_wbs[]` e `pep_description[]` — filtro por PEP (código ou descrição)
- `collaborator_id[]` — filtro por colaborador
- `date_from` e `date_to` — intervalo de datas

### Fluxo de dados resumido

```
Upload CSV/XLSX
    ↓ validação estrutural (Q1-Q8)
    ↓ engine de regras configuráveis
    ↓ _lookup_rate() → congela cost_per_hour
    ↓ DELETE por (pep_wbs, cycle_id) + INSERT TimesheetRecord
    ↓ QuarantineRecord (se falhou)
    ↓ UploadSession + AuditLog
         ↓
    Queries de analytics (tempo real)
         ↓
    ECharts 5 (cliente)
```
