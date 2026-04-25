# PMAS — Project Management Assistant System

Dashboard analítico de timesheet para gestão de horas por projeto, colaborador e ciclo, com visões de Esforço da Equipe, Saúde do Portfólio e Tendências.

## Funcionalidades

- **Importação de Timesheet** — Carregue arquivos CSV ou XLSX. Duplicatas são detectadas e ignoradas automaticamente. Datas fora de qualquer ciclo cadastrado geram um ciclo de *quarentena* sem perda de dados.
- **Esforço da Equipe** — Gráfico de barras horizontais com horas normais, extras e sobreaviso por colaborador. Toggle entre vista empilhada e agrupada. Comparativo orçado vs. realizado por PEP.
- **Saúde do Portfólio** — Treemap com tamanho proporcional às horas consumidas (blocos cinzas = PEP não cadastrado, vermelhos = acima do budget) + Bullet Chart com thresholds de cor por % de utilização.
- **Tendências** — Gráfico de linhas com a queima de horas normais e extras por ciclo em ordem cronológica, filtrável por PEP.
- **Filtros em Cascata** — Multi-seleção de Ciclo, Código PEP, Descrição PEP e Colaborador com atualização dinâmica.
- **Cadastro de Ciclos** — Criação, edição e exclusão de períodos de apuração.
- **Cadastro de Projetos/PEPs** — Registro de projetos com código PEP, nome, cliente, gerente, budget de horas e status.

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

91 testes cobrindo ingestion, dashboard, CRUD de ciclos/projetos, endpoints de referência e analytics. O CI (GitHub Actions) executa a suite em Python 3.11 e 3.12 a cada push.

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
| `GET` | `/api/dashboard` | Horas agregadas por colaborador (toda a base) |
| `GET` | `/api/dashboard/{cycle_id}` | Horas agregadas por colaborador no ciclo |
| `GET` | `/api/portfolio-health` | Horas consumidas por PEP + budget |
| `GET` | `/api/trends` | Queima de horas por ciclo (cronológico) |
| `GET` | `/api/collaborators` | Lista colaboradores com registros |
| `GET` | `/api/peps` | Lista PEPs com agrupamento de descrições |
| `POST` | `/api/upload-timesheet` | Ingestão de CSV/XLSX |

## Estrutura do projeto

```
PMAS/
├── backend/app/
│   ├── main.py              # Aplicação FastAPI, CORS, static files, upload
│   ├── models.py            # ORM: Collaborator, Cycle, Project, TimesheetRecord
│   ├── schemas.py           # Pydantic: CycleIn, ProjectIn
│   ├── database.py          # Engine SQLite, get_db(), init_db(), migração de colunas
│   ├── routers/
│   │   ├── cycles.py        # GET/POST/PUT/DELETE /api/cycles
│   │   ├── projects.py      # GET/POST/PUT/DELETE /api/projects
│   │   ├── dashboard.py     # GET /api/dashboard[/{cycle_id}]
│   │   ├── reference.py     # GET /api/collaborators, /api/peps
│   │   └── analytics.py     # GET /api/portfolio-health, /api/trends
│   └── services/
│       └── ingestion.py     # Parser pandas: CSV/XLSX → TimesheetRecord
├── frontend/
│   ├── index.html           # Estrutura HTML (3 abas principais + 3 sub-abas analíticas)
│   ├── style.css            # Tema escuro slate/blue + estilos de analytics
│   ├── multiselect.js       # Componente MultiSelect reutilizável
│   └── app.js               # Lógica do cliente, gestão ECharts, CRUD
├── tests/
│   ├── conftest.py          # Fixtures pytest (SQLite in-memory, StaticPool)
│   ├── test_cycles.py       # 16 testes CRUD de ciclos
│   ├── test_projects.py     # 15 testes CRUD de projetos
│   ├── test_dashboard.py    # 9 testes de agregação do dashboard
│   ├── test_ingestion.py    # 18 testes de ingestão CSV/XLSX
│   ├── test_reference.py    # 12 testes de endpoints de referência
│   └── test_analytics.py   # 16 testes de portfolio-health e trends
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
