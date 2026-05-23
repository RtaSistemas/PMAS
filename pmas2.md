# PMAS 2 — Plano de Refatoração Arquitetural

## Visão Geral

O PMAS 2 é uma refatoração completa do PMAS v1, mantendo toda a lógica de negócio existente (EVM, regras de validação, quarentena, ACL, auditoria) e introduzindo uma nova estrutura de navegação centrada em **projetos** e **portfólio**, com painéis dedicados por entidade.

**Stack (sem mudanças):** Python 3.11+ · FastAPI · SQLAlchemy · SQLite · Vanilla JS · Apache ECharts 5  
**UI:** Português (pt-BR)  
**Ponto de partida:** cópia limpa do PMAS v1 em `/home/user/PMAS2`

---

## Nova Estrutura de Abas (7 tabs)

### 1. Portfólio
Visão consolidada de todos os projetos do portfólio.

- Semáforo macro (verde/amarelo/vermelho/cinza) por PEP
- Treemap de horas ou R$ consumidos vs. orçamento
- Bullet chart EVM por projeto
- Indicadores agregados: CPI médio, SPI médio, total de horas, total de custo
- Filtros: período (data_from / data_to), colaborador, PEP

### 2. Projeto
Painel aprofundado de um único projeto selecionado.

- Seletor de PEP no topo
- Curva S: horas/custo planejados vs. realizados por ciclo
- Tabela de indicadores EVM: PV, EV, AC, CPI, SPI, CV, SV, EAC, VAC, TCPI
- Histórico de uploads que afetaram o projeto
- Colaboradores que trabalharam no projeto (horas por colaborador)
- Alertas de orçamento e desvios

### 3. Equipe
Gestão e visualização de colaboradores.

- Tabela de colaboradores com nível de senioridade e rate card vigente
- CRUD de níveis de senioridade
- CRUD de rate cards (com intervalo de vigência)
- Gráfico de horas por colaborador (agrupado por ciclo ou PEP)
- Atribuição de senioridade por colaborador

### 4. Tendências
Análise temporal do portfólio.

- Linha de horas totais por ciclo (realizadas vs. planejadas)
- Linha de custo por ciclo (AC vs. PV)
- Barras de horas por PEP agrupadas por ciclo
- Filtros: período, colaborador, PEP

### 5. Dados
Central de upload e gestão de dados brutos.

- Upload de timesheet (CSV/XLSX) com feedback de resultado por fase
- Histórico de uploads (sessões) com status e contadores de linhas
- Fila de quarentena: listagem, aprovação, rejeição, deleção
- Motor de regras de validação: CRUD, toggle, reordenação
- Exportação de dados: timesheets por ciclo, projetos, ciclos

### 6. Cadastros
Tabelas de referência do sistema.

- Ciclos: CRUD + importação/exportação CSV
- Projetos (PEPs): CRUD + importação/exportação CSV + badges de alerta de orçamento
- Configurações globais: tema da UI, logo, preferências

### 7. Admin
Visível apenas para usuários com `role=admin`.

- Gestão de usuários: CRUD, alteração de senha, atribuição de papel
- ACL por projeto: whitelist de PEPs por usuário
- Log de auditoria: tabela paginada com filtros
- Configuração do motor de regras de validação
- Visão global de quarentena
- Histórico global de uploads

---

## Diferenças Estruturais em Relação ao PMAS v1

| Aspecto | PMAS v1 | PMAS 2 |
|---|---|---|
| Tabs de nível superior | 6 (Dashboard, Ciclos, Projetos, Equipe, Minha Área, Admin) | 7 (Portfólio, Projeto, Equipe, Tendências, Dados, Cadastros, Admin) |
| Dashboard | Tab único com 3 sub-tabs de analytics | Substituído por Portfólio (macro) + Projeto (micro) |
| Ciclos / Projetos | Tabs separadas | Unificadas em Cadastros |
| Minha Área | Tab dedicada | Fundida em Dados (histórico pessoal) e Equipe |
| Tendências | Sub-tab de Dashboard | Tab própria de nível superior |
| Curva S / Previsão | Sub-tab de Dashboard | Movida para tab Projeto |
| Motor de validação | Seção do Admin | Movido para Dados |
| Quarentena | Seção do Admin (global) | Duplicada: Dados (pessoal) + Admin (global) |

---

## Plano de Fases

### Fase 0 — Setup e Migração de Base (sem novas features)
- [ ] Criar repositório PMAS2 com cópia limpa do v1
- [ ] Ajustar `index.html`: renomear os 7 tabs com IDs e estrutura HTML correta
- [ ] Mover lógica JS existente para os novos pontos de ancoragem
- [ ] Validar que os 406 testes continuam passando sem alterações

### Fase 1 — Tab Portfólio
- [ ] Migrar semáforo macro (já existe em v1)
- [ ] Migrar treemap e bullet chart (já existem em v1 como sub-tabs)
- [ ] Adicionar indicadores EVM agregados (CPI/SPI médios)
- [ ] Conectar filtros compartilhados (período, colaborador, PEP)

### Fase 2 — Tab Projeto
- [ ] Seletor de PEP + carga dinâmica
- [ ] Migrar curva S / previsão (já existe em v1)
- [ ] Tabela de KPIs EVM por projeto
- [ ] Histórico de uploads por projeto
- [ ] Lista de colaboradores por projeto

### Fase 3 — Tab Tendências
- [ ] Migrar gráfico de tendências (já existe em v1)
- [ ] Adicionar barras de horas por PEP por ciclo
- [ ] Conectar filtros compartilhados

### Fase 4 — Tab Equipe
- [ ] Migrar CRUD de senioridades e rate cards (já existe em v1)
- [ ] Adicionar gráfico de horas por colaborador
- [ ] Migrar atribuição de senioridade

### Fase 5 — Tab Dados
- [ ] Migrar upload de timesheet
- [ ] Migrar histórico de uploads (visão pessoal)
- [ ] Migrar quarentena (visão pessoal)
- [ ] Migrar motor de regras de validação

### Fase 6 — Tab Cadastros
- [ ] Migrar CRUD de ciclos + CSV import/export
- [ ] Migrar CRUD de projetos + badges de alerta
- [ ] Migrar configurações globais (tema, logo)

### Fase 7 — Tab Admin
- [ ] Migrar gestão de usuários
- [ ] Migrar ACL por projeto
- [ ] Migrar log de auditoria
- [ ] Migrar quarentena global
- [ ] Migrar histórico global de uploads

### Fase 8 — Refinamento e Testes
- [ ] Testes de regressão completos (406+ testes)
- [ ] Revisar responsividade e acessibilidade
- [ ] Documentação de usuário atualizada
- [ ] Performance: lazy loading de tabs pesadas

---

## Decisões Técnicas

### Backend
- **Sem alterações de routers** na Fase 0–2: toda a API REST permanece idêntica.
- Novos endpoints podem ser adicionados nas fases posteriores conforme necessidade (ex.: `/api/projects/{id}/evm-summary`).
- O padrão EVM freeze (`cost_per_hour` gravado na ingestão) permanece inalterado.

### Frontend
- Estrutura de arquivo: manter `index.html` + `app.js` + `style.css` + `multiselect.js` (sem build step).
- Inicialização: `_bootApp()` permanece o ponto central, adaptado para os 7 tabs.
- ECharts: manter `CHARTS_PER_TAB` + `_disposeTabCharts()` + `ResizeObserver` — apenas expandir o registro de tabs.
- Estado compartilhado: filtros de período, colaborador e PEP são globais e afetam todas as tabs de analytics.
- `_evmMode` boolean mantido para toggle Horas/R$.

### Migração de Dados
- `pmas.db` existente é 100% compatível — nenhuma mudança de schema no banco.
- `_migrate_columns()` em `database.py` continua sendo o mecanismo de evolução segura de schema.
- Dados de produção do PMAS v1 podem ser copiados diretamente para PMAS 2.

---

## Repositório de Origem

- **v1 (produção):** `RtaSistemas/PMAS` — branch `main`
- **v2 (novo):** `RtaSistemas/PMAS2` — branch `main` (cópia limpa, commit inicial do v1)
- **Este plano:** `RtaSistemas/PMAS` — branch `claude/create-project-docs-qJaUo` — arquivo `pmas2.md`

---

*Plano criado em 2026-05-23.*
