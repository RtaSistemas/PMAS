# PMAS — Project Management Assistant System

<p align="center">
  <img src="docs/banner.png" alt="PMAS — Dashboard Analítico de Gestão de Projetos" width="520">
</p>

<p align="center">
  <strong>Dashboard analítico de timesheet para gestão de horas e custos por projeto, colaborador e ciclo.</strong><br>
  Importação CSV/XLSX · Análise EVM · Rate Card · Exportável como executável standalone
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/SQLite-embedded-003B57?style=flat-square&logo=sqlite" alt="SQLite"/>
  <img src="https://img.shields.io/badge/ECharts-5-AA344D?style=flat-square" alt="ECharts 5"/>
  <img src="https://img.shields.io/badge/testes-170%20passing-22c55e?style=flat-square" alt="170 testes"/>
</p>

---

## Visão geral

O PMAS transforma planilhas de horas em dashboards interativos. Gerentes de projeto importam exports de timesheet (CSV ou XLSX), definem ciclos de apuração e projetos com budget, e visualizam em tempo real:

- **Quem** está trabalhando em quê — esforço por colaborador e por PEP
- **Quanto** já foi consumido vs. o orçado — análise EVM com custo por hora congelado no momento da importação
- **Como** a equipe evolui ao longo dos ciclos — gráfico de tendências filtrado por PEP

<img width="1918" height="908" alt="image" src="https://github.com/user-attachments/assets/a858b592-858b-4c47-9418-917804b6d277" />


---

## Funcionalidades

### Dashboard analítico (3 visões)

| Visão | O que mostra | Controles |
|---|---|---|
| **Esforço da Equipe** | Barras horizontais: horas normais, extras e sobreaviso por colaborador. Cards de KPI. Radar de horas/custo por PEP. Gráfico orçado vs. realizado. | Empilhado/Agrupado · Exportar CSV |
| **Saúde do Portfólio** | Treemap com tamanho proporcional ao consumo (cinza = sem cadastro, laranja ≥75%, vermelho ≥100%). Bullet Chart com % de utilização. | Toggle Horas/R$ |
| **Tendências** | Linhas de horas normais, extras e custo real por ciclo (cronológico, quarentena excluída). | Filtro local por PEP |

### Importação de dados
- Suporta **CSV** e **XLSX/XLS** (planilhas Excel)
- Deduplicação automática por colaborador + data + PEP + tipo de hora + horário de início
- Datas fora de qualquer ciclo cadastrado criam automaticamente um **ciclo de quarentena** — nenhum dado é descartado
- Botão de import diretamente na barra de cabeçalho

### Cadastros (CRUD completo)
- **Ciclos** — períodos de apuração com datas início/fim, bloqueio após fechamento, busca em tempo real, import/export CSV
- **Projetos / PEPs** — código WBS, nome, cliente, gerente, budget de horas e budget em R$, status (Ativo / Suspenso / Encerrado), alertas de budget (⚠ ≥90%, 🔴 ≥100%)
- **Equipe e Rate Card** — níveis de senioridade, taxas por hora com vigência, atribuição por colaborador, atribuição em lote

### Módulo EVM (Earned Value Management)
- Taxa por hora congelada no momento da importação (`cost_per_hour` imutável após ingestão)
- Multiplicadores globais configuráveis para horas extras e sobreaviso
- Custo real calculado como: `custo = normal_h × rate + extra_h × rate × mult_extra + standby_h × rate × mult_standby`

### Outras capacidades
- **Filtros em cascata** — ciclo → PEP (código) → PEP (descrição) → colaborador, com atualização dinâmica entre filtros
- **Filtro por período** — date_from / date_to aplicado em todos os três sub-tabs analíticos
- **Internacionalização** — toggle PT/EN com persistência em localStorage; todos os textos dinâmicos traduzidos
- **Exportação CSV** — esforço da equipe, ciclos e projetos exportáveis com um clique
- **Timeline por colaborador** — gráfico de evolução de horas por ciclo ao clicar em uma barra
- **Gestão de usuários** — múltiplos usuários com perfis admin/usuário, autenticação JWT
- **Schema migration** — `ALTER TABLE` automático no startup para bancos existentes (sem perda de dados)
- **Executável standalone** — build PyInstaller para Linux x64 e Windows x64 (com ícone)


<img width="1917" height="911" alt="image" src="https://github.com/user-attachments/assets/8e49971c-eb7d-4e31-ac63-6145f618b54e" />
--
<img width="1917" height="907" alt="image" src="https://github.com/user-attachments/assets/6f2093fd-65e2-4a1f-88be-2ea7be12c87c" />
--
<img width="1916" height="902" alt="image" src="https://github.com/user-attachments/assets/083e6051-22a5-4711-9aa4-c553f663484d" />
--
<img width="1915" height="905" alt="image" src="https://github.com/user-attachments/assets/ebe58695-6c89-4862-b457-5b951d819414" />


---

## Requisitos

- Python **3.11** ou **3.12**
- Dependências listadas em `requirements.txt`

---

## Instalação e execução

```bash
# 1. Clone o repositório
git clone https://github.com/RtaSistemas/PMAS.git
cd PMAS

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Inicie o servidor
python -m uvicorn backend.app.main:app --reload
```

Acesse em **http://127.0.0.1:8000** — login padrão: `admin` / `admin`.

> O banco `pmas.db` (SQLite) é criado automaticamente na primeira execução.  
> Novas colunas de versões posteriores são aplicadas via `ALTER TABLE` no startup, sem perda de dados.

---

## Executável standalone (sem Python)

```bash
# Gera pmas-linux-x64 ou pmas-windows-x64.exe via GitHub Actions
git tag v1.0.0
git push origin v1.0.0
```

O workflow `release.yml` compila o executável com PyInstaller e publica na aba **Releases** do GitHub.  
O executável Windows inclui ícone personalizado (`assets/icon.ico`).

Para build local:

```bash
pip install pyinstaller
# Linux
pyinstaller --onefile --name pmas --add-data "frontend:frontend" run.py
# Windows
pyinstaller --onefile --name pmas --icon assets\icon.ico --add-data "frontend;frontend" run.py
```

---

## Testes

```bash
pip install pytest httpx
pytest tests/ -v
```

**170 testes** em 7 arquivos, todos usando SQLite em memória (StaticPool) — nenhum arquivo `pmas.db` é tocado.

| Arquivo | Testes | Cobertura |
|---|---:|---|
| `test_cycles.py` | 16 | CRUD de ciclos, bloqueio, import CSV |
| `test_projects.py` | 15 | CRUD de projetos, import CSV, budget |
| `test_dashboard.py` | 9 | Agregação por colaborador, filtros |
| `test_ingestion.py` | 21 | CSV/XLSX, dedup, quarentena, start_time |
| `test_reference.py` | 12 | `/collaborators`, `/peps`, cascata |
| `test_analytics.py` | 22 | portfolio-health, trends, pep-radar |
| `test_ratecard.py` | 26 | Seniority, rate cards, EVM freeze, config |
| `test_users.py` | 20 | Autenticação JWT, CRUD usuários |

CI executa a suite em **Python 3.11 e 3.12** a cada push (GitHub Actions).

---

## Formato do arquivo de timesheet

| Coluna | Obrigatório | Tipo | Descrição |
|---|:---:|---|---|
| `Colaborador` | ✅ | Texto | Nome completo do colaborador |
| `Data` | ✅ | DD/MM/AAAA | Data do registro |
| `Horas totais (decimal)` | ✅ | Decimal | Total de horas (ex: `8.5`) |
| `Hora extra` | — | `Sim`/`Não` | Indica horas extras |
| `Hora sobreaviso` | — | `Sim`/`Não` | Indica horas de sobreaviso |
| `Código PEP` | — | Texto | Código WBS do projeto (ex: `60OP-03333`) |
| `PEP` | — | Texto | Descrição do PEP (ex: `COPEL-D | OMS`) |
| `Hora Inicial [H]` | — | HH:MM | Diferencia lançamentos do mesmo dia no mesmo PEP |

> Arquivos de exemplo disponíveis em `samples/`.

<img width="1917" height="912" alt="image" src="https://github.com/user-attachments/assets/2eb44e66-560a-4576-aa2c-bad75390a537" />

---

## Stack tecnológico

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11+ · FastAPI · SQLAlchemy 2.0 |
| Banco de dados | SQLite (`pmas.db`) |
| Autenticação | JWT (python-jose) · bcrypt |
| Frontend | HTML5 · CSS3 · JavaScript Vanilla |
| Gráficos | Apache ECharts 5 |
| Parsing | pandas · openpyxl |
| Testes | pytest · httpx · FastAPI TestClient |
| Build | PyInstaller (Linux + Windows) |
| CI | GitHub Actions (Python 3.11 / 3.12) |

---

## API REST

### Dashboard

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/dashboard` | Horas por colaborador — toda a base |
| `GET` | `/api/dashboard/{cycle_id}` | Horas por colaborador no ciclo |
| `GET` | `/api/dashboard/pep-radar` | Horas e custo por PEP (descrição) — radar chart |
| `GET` | `/api/dashboard/collaborator-timeline` | Evolução de horas por colaborador ao longo dos ciclos |

Todos suportam `?pep_code=&pep_description=&collaborator_id=&date_from=&date_to=`.

### Analytics

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/portfolio-health` | Consumo e budget por PEP (horas + custo real) |
| `GET` | `/api/trends` | Queima de horas e custo por ciclo (cronológico) |

### Ciclos

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/cycles` | Lista com contagem de registros |
| `POST` | `/api/cycles` | Criar ciclo |
| `PUT` | `/api/cycles/{id}` | Atualizar ciclo |
| `DELETE` | `/api/cycles/{id}` | Excluir ciclo (apenas sem registros) |
| `PATCH` | `/api/cycles/{id}/toggle-status` | Bloquear / desbloquear |
| `POST` | `/api/cycles/import` | Importar ciclos via CSV |

### Projetos

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/projects` | Lista projetos |
| `POST` | `/api/projects` | Criar projeto |
| `PUT` | `/api/projects/{id}` | Atualizar projeto |
| `DELETE` | `/api/projects/{id}` | Excluir projeto |
| `POST` | `/api/projects/import` | Importar projetos via CSV (upsert por PEP) |

### Equipe e Rate Card

| Método | Rota | Descrição |
|---|---|---|
| `GET/POST/PUT/DELETE` | `/api/seniority-levels[/{id}]` | CRUD de níveis de senioridade |
| `GET/POST/PUT/DELETE` | `/api/rate-cards[/{id}]` | CRUD de taxas horárias |
| `GET` | `/api/team` | Colaboradores com senioridade e taxa atual |
| `PUT` | `/api/team/{id}/seniority` | Atribuir senioridade a um colaborador |
| `PUT` | `/api/team/bulk-seniority` | Atribuir senioridade a todos |

### Referência e configuração

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/collaborators` | Lista colaboradores com registros |
| `GET` | `/api/peps` | Lista PEPs com agrupamento de descrições |
| `POST` | `/api/upload-timesheet` | Ingestão de CSV/XLSX |
| `GET/PUT` | `/api/config` | Multiplicadores globais (hora extra, sobreaviso) |

### Autenticação e usuários

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/token` | Login — retorna JWT |
| `GET/POST` | `/api/users[/{id}]` | Listar / criar usuários (admin) |
| `PUT` | `/api/users/{id}/password` | Alterar senha |
| `DELETE` | `/api/users/{id}` | Excluir usuário |

---

## Estrutura do projeto

```
PMAS/
├── assets/
│   ├── icon.ico             # Ícone Windows (6 tamanhos: 16–256px)
│   └── icon.png             # Ícone PNG 256px (referência)
├── backend/app/
│   ├── main.py              # FastAPI: CORS, routers, static files, upload, startup
│   ├── models.py            # ORM: Collaborator, Cycle, Project, TimesheetRecord,
│   │                        #       SeniorityLevel, RateCard, GlobalConfig, User
│   ├── schemas.py           # Pydantic: inputs, outputs, EVM types
│   ├── database.py          # Engine SQLite, get_db(), init_db(), _migrate_columns()
│   ├── deps.py              # Dependências JWT: get_current_user, require_admin
│   ├── routers/
│   │   ├── cycles.py        # CRUD + import CSV + toggle-status
│   │   ├── projects.py      # CRUD + import CSV (upsert)
│   │   ├── dashboard.py     # Horas por colaborador, pep-radar, collaborator-timeline
│   │   ├── analytics.py     # portfolio-health, trends (com actual_cost)
│   │   ├── reference.py     # /collaborators, /peps (cascata)
│   │   ├── ratecard.py      # seniority-levels, rate-cards, team, config
│   │   └── users.py         # Autenticação JWT, gestão de usuários
│   └── services/
│       └── ingestion.py     # Parser pandas: dedup por start_time, _lookup_rate() EVM freeze
├── frontend/
│   ├── index.html           # 5 abas + 3 sub-abas analíticas + modais
│   ├── style.css            # Design system: Navy + Sky Blue + tokens CSS
│   ├── multiselect.js       # Componente MultiSelect (cascata)
│   └── app.js               # i18n PT/EN, ECharts, CRUD, filtros, export/import
├── docs/
│   └── banner.png           # Banner do README
├── samples/                 # Arquivos CSV de exemplo
├── tests/
│   ├── conftest.py          # Fixtures: SQLite in-memory, StaticPool, usuário admin
│   ├── test_cycles.py
│   ├── test_projects.py
│   ├── test_dashboard.py
│   ├── test_ingestion.py
│   ├── test_reference.py
│   ├── test_analytics.py
│   ├── test_ratecard.py
│   └── test_users.py
├── .github/workflows/
│   ├── tests.yml            # CI: pytest Python 3.11 e 3.12
│   └── release.yml          # Build PyInstaller Linux + Windows (com ícone)
├── CLAUDE.md                # Guia para Claude Code
├── MANUAL.md                # Manual do usuário (pt-BR)
├── requirements.txt
├── run.py                   # Entrypoint para PyInstaller
└── pmas.db                  # Banco SQLite (criado automaticamente, não versionado)
```

---

## Configuração e variáveis

Todas as configurações são feitas via interface web — não há arquivo `.env` obrigatório.

| Configuração | Onde | Default |
|---|---|---|
| Multiplicador hora extra | Equipe → Fatores Globais | `1.5` |
| Multiplicador sobreaviso | Equipe → Fatores Globais | `1.0` |
| Porta do servidor | `run.py` / linha de comando | `8000` |
| Usuário inicial | Criado no primeiro startup | `admin` / `admin` |

---

## Conceitos-chave

**Ciclo de apuração** — período contínuo (ex: Janeiro/2026) que agrupa registros de timesheet. Ao importar horas cujas datas não se encaixam em nenhum ciclo cadastrado, o sistema cria automaticamente um ciclo de *quarentena* — os dados ficam disponíveis para análise mas sinalizados.

**PEP / WBS** — código de projeto (ex: `60OP-03333`) e sua descrição (ex: `COPEL-D | OMS`). Cada registro de timesheet carrega ambos; os filtros operam sobre código e descrição independentemente.

**EVM freeze pattern** — o custo por hora (`cost_per_hour`) é resolvido no momento da importação via lookup no Rate Card (nível de senioridade do colaborador × data do registro). Mudanças futuras de taxa não afetam retroativamente os custos já registrados.

**Quarentena** — ciclos automáticos criados para datas sem ciclo correspondente. São incluídos nas visões de Portfólio e Esforço, mas excluídos do gráfico de Tendências (que pressupõe evolução cronológica entre ciclos regulares).

---

## Licença

Distribuído sob licença MIT. Consulte `LICENSE` para detalhes.
