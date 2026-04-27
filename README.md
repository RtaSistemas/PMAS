# PMAS — Project Management Assistant System

Dashboard analítico de timesheet para gestão de horas e custos por projeto, colaborador e ciclo, com visões de Esforço da Equipe, Saúde do Portfólio e Tendências. Inclui módulo de RateCard para rastreamento de custo por hora congelado no momento da importação (EVM freeze pattern).

<img width="1920" height="908" alt="timesheet" src="https://github.com/user-attachments/assets/f322a8b2-1bf3-4239-ab6a-12c266b986f4" />

## Funcionalidades

- **Importação de Timesheet** — Carregue arquivos CSV ou XLSX. Duplicatas são detectadas e ignoradas automaticamente. Datas fora de qualquer ciclo cadastrado geram um ciclo de *quarentena* sem perda de dados.
- **Esforço da Equipe** — Gráfico de barras horizontais com horas normais, extras e sobreaviso por colaborador. Toggle entre vista empilhada e agrupada. Comparativo orçado vs. realizado por PEP. Exportação CSV com um clique.
- **Saúde do Portfólio** — Treemap com tamanho proporcional às horas/custo consumidos (blocos cinzas = PEP não cadastrado, vermelhos = acima do budget) + Bullet Chart com thresholds de cor por % de utilização. Toggle Horas / R$ para visão financeira.
- **Tendências** — Gráfico de linhas com a queima de horas normais e extras por ciclo em ordem cronológica, filtrável por PEP.
- **Filtros em Cascata** — Multi-seleção de Ciclo, Código PEP, Descrição PEP e Colaborador com atualização dinâmica. Filtros de Data início/fim aplicados a todos os três sub-tabs analíticos.
- **Cadastro de Ciclos** — Criação, edição e exclusão de períodos de apuração. Busca em tempo real na tabela.
- **Cadastro de Projetos/PEPs** — Registro de projetos com código PEP, nome, cliente, gerente, budget de horas, budget em R$ e status. Busca em tempo real + alertas de budget (Estourado ≥100%, Atenção ≥90%). 
- **Módulo Equipe / RateCard** — Cadastro de níveis de senioridade, tabela de taxas horárias por nível e período de vigência, atribuição de senioridade por colaborador. O custo por hora é congelado no momento da importação do timesheet (EVM freeze pattern).

<img width="1920" height="911" alt="Saude" src="https://github.com/user-attachments/assets/c600b225-8f6e-48e1-a221-1a7cb179d6dd" />

## Requisitos

- Python 3.11 ou 3.12
- Dependências em `requirements.txt`

## Instalação e execução

```bash
git clone <url-do-repositorio>
cd PMAS
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --reload
```

Acesse em: **http://127.0.0.1:8000**

O banco de dados `pmas.db` (SQLite) é criado automaticamente na primeira execução. Novas colunas adicionadas em versões posteriores são migradas via `ALTER TABLE` no startup, sem perda de dados.

## Testes

```bash
pip install pytest httpx
pytest tests/ -v
```

117 testes cobrindo ingestion, dashboard, CRUD de ciclos/projetos, endpoints de referência, analytics e módulo RateCard. O CI (GitHub Actions) executa a suite em Python 3.11 e 3.12 a cada push.

## Formato esperado do arquivo de timesheet

| Coluna | Obrigatório | Descrição |
|---|---|---|
| `Colaborador` | Sim | Nome completo do colaborador |
| `Data` | Sim | Data do registro (DD/MM/AAAA) |
| `Horas totais (decimal)` | Sim | Total de horas em decimal (ex: `8.5`) |
| `Hora extra` | Não | `Sim`/`Não` — indica horas extras |
| `Hora sobreaviso` | Não | `Sim`/`Não` — indica horas de sobreaviso |
| `Código PEP` | Não | Código WBS do projeto (ex: `60OP-03333`) |
| `PEP` | Não | Descrição do PEP (ex: `COPEL-D \| OMS`) |

<img width="1915" height="912" alt="ciclos" src="https://github.com/user-attachments/assets/939c98d7-9636-4c25-b450-4f7ebffd5b14" />

## Stack tecnológico

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11+ · FastAPI · SQLAlchemy |
| Banco de dados | SQLite (`pmas.db`) |
| Frontend | HTML5 · CSS3 · JavaScript (Vanilla) |
| Gráficos | Apache ECharts 5 |
| Parsing de arquivos | pandas · openpyxl |
| Testes | pytest · httpx · FastAPI TestClient |
| CI | GitHub Actions (matriz Python 3.11 / 3.12) |

## API REST

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/cycles` | Lista ciclos com contagem de registros |
| `POST/PUT/DELETE` | `/api/cycles[/{id}]` | CRUD de ciclos |
| `GET` | `/api/projects` | Lista projetos ordenados por PEP |
| `POST/PUT/DELETE` | `/api/projects[/{id}]` | CRUD de projetos |
| `GET` | `/api/dashboard` | Horas agregadas por colaborador (toda a base) com filtros `date_from`/`date_to` |
| `GET` | `/api/dashboard/{cycle_id}` | Horas agregadas por colaborador no ciclo com filtros `date_from`/`date_to` |
| `GET` | `/api/portfolio-health` | Horas e custo real consumidos por PEP + budget (horas e R$) com filtros `date_from`/`date_to` |
| `GET` | `/api/trends` | Queima de horas e custo real por ciclo (cronológico) com filtros `date_from`/`date_to` |
| `GET` | `/api/collaborators` | Lista colaboradores com registros |
| `GET` | `/api/peps` | Lista PEPs com agrupamento de descrições |
| `POST` | `/api/upload-timesheet` | Ingestão de CSV/XLSX |
| `GET` | `/api/seniority-levels` | Lista níveis de senioridade |
| `POST/PUT/DELETE` | `/api/seniority-levels[/{id}]` | CRUD de níveis de senioridade |
| `GET` | `/api/rate-cards` | Lista tabela de taxas (filtro por `seniority_level_id`) |
| `POST/PUT/DELETE` | `/api/rate-cards[/{id}]` | CRUD de rate cards |
| `GET` | `/api/team` | Colaboradores com senioridade e taxa atual |
| `PUT` | `/api/team/{collab_id}/seniority` | Atribui nível de senioridade ao colaborador |

## Estrutura do projeto

```
PMAS/
├── backend/app/
│   ├── main.py              # Aplicação FastAPI, CORS, static files, upload
│   ├── models.py            # ORM: Collaborator, Cycle, Project, TimesheetRecord, SeniorityLevel, RateCard
│   ├── schemas.py           # Pydantic: CycleIn, ProjectIn, SeniorityLevelIn, RateCardIn, CollaboratorSeniorityIn
│   ├── database.py          # Engine SQLite, get_db(), init_db(), migração de colunas
│   ├── routers/
│   │   ├── cycles.py        # GET/POST/PUT/DELETE /api/cycles
│   │   ├── projects.py      # GET/POST/PUT/DELETE /api/projects
│   │   ├── dashboard.py     # GET /api/dashboard[/{cycle_id}] + date_from/date_to
│   │   ├── reference.py     # GET /api/collaborators, /api/peps
│   │   ├── analytics.py     # GET /api/portfolio-health, /api/trends + actual_cost + date_from/date_to
│   │   └── ratecard.py      # CRUD /api/seniority-levels, /api/rate-cards, /api/team
│   └── services/
│       └── ingestion.py     # Parser pandas: CSV/XLSX → TimesheetRecord, _lookup_rate() EVM freeze
├── frontend/
│   ├── index.html           # 4 abas (Dashboard, Ciclos, Projetos, Equipe) + 3 sub-abas analíticas
│   ├── style.css            # Tema escuro slate/blue + search input + badge-budget + analytics
│   ├── multiselect.js       # Componente MultiSelect reutilizável
│   └── app.js               # Lógica do cliente, ECharts, CRUD, toggle Horas/R$, exportação CSV
├── tests/
│   ├── conftest.py          # Fixtures pytest (SQLite in-memory, StaticPool)
│   ├── test_cycles.py       # 16 testes CRUD de ciclos
│   ├── test_projects.py     # 15 testes CRUD de projetos
│   ├── test_dashboard.py    # 9 testes de agregação do dashboard
│   ├── test_ingestion.py    # 18 testes de ingestão CSV/XLSX
│   ├── test_reference.py    # 12 testes de endpoints de referência
│   ├── test_analytics.py    # 16 testes de portfolio-health e trends
│   └── test_ratecard.py     # 26 testes de seniority, rate cards, team e rate lookup
├── .github/workflows/
│   ├── tests.yml            # CI: pytest Python 3.11 e 3.12
│   └── release.yml          # Build PyInstaller (Linux + Windows)
├── .gitignore
├── CLAUDE.md                # Guia para Claude Code
├── MANUAL.md                # Manual do usuário (pt-BR)
├── requirements.txt
└── run.py                   # Entrypoint para PyInstaller
```

## Build (executável standalone)

```bash
git tag v1.0.0
git push origin v1.0.0
```

O workflow `release.yml` gera `pmas-linux-x64` e `pmas-windows-x64.exe` disponíveis na aba *Releases* do GitHub.
