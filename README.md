# PMAS — Project Management Assistant System

Dashboard de gestão de timesheet para análise de horas por projeto, colaborador e ciclo.

## Funcionalidades

- **Importação de Timesheet** — Carregue arquivos CSV ou XLSX exportados do sistema de timesheet. Duplicatas são detectadas e ignoradas automaticamente.
- **Dashboard de Horas** — Gráfico de barras horizontais empilhadas com horas normais, extras e sobreaviso por colaborador. Suporte a múltiplos painéis simultâneos (um por ciclo/filtro).
- **Filtros em Cascata** — Multi-seleção de Ciclo, Código PEP, Descrição PEP e Colaborador com atualização dinâmica entre os filtros.
- **Orçado vs. Realizado** — Comparativo visual entre as horas orçadas (cadastradas por projeto) e as horas realizadas por PEP, com alerta automático quando o orçamento é ultrapassado.
- **Cadastro de Ciclos** — Criação e edição de períodos de apuração (ciclos). Ciclos de *quarentena* são criados automaticamente para registros fora de qualquer ciclo cadastrado.
- **Cadastro de Projetos/PEPs** — Registro de projetos com código PEP, nome, cliente, gerente, budget de horas e status (ativo / suspenso / encerrado).

## Requisitos

- Python 3.10+
- Dependências listadas em `requirements.txt`

## Instalação e execução

```bash
# Clone o repositório
git clone <url-do-repositorio>
cd PMAS

# Instale as dependências
pip install -r requirements.txt

# Inicie o servidor de desenvolvimento
python -m uvicorn backend.app.main:app --reload
```

Acesse a aplicação em: **http://127.0.0.1:8000**

O banco de dados `pmas.db` (SQLite) é criado automaticamente na primeira execução.

## Formato esperado do arquivo de timesheet

| Coluna | Obrigatório | Descrição |
|---|---|---|
| `Colaborador` | Sim | Nome completo do colaborador |
| `Data` | Sim | Data do registro (DD/MM/AAAA) |
| `Horas totais (decimal)` | Sim | Total de horas no formato decimal (ex: `8.5`) |
| `Hora extra` | Não | `Sim`/`Não` — indica se são horas extras |
| `Hora sobreaviso` | Não | `Sim`/`Não` — indica se são horas de sobreaviso |
| `Código PEP` | Não | Código do PEP/WBS do projeto (ex: `60OP-03333`) |
| `PEP` | Não | Descrição do PEP (ex: `COPEL-D \| OMS`) |

## Stack tecnológico

| Camada | Tecnologia |
|---|---|
| Backend | Python 3 + FastAPI + SQLAlchemy |
| Banco de dados | SQLite (`pmas.db`) |
| Frontend | HTML5 + CSS3 + JavaScript (Vanilla) |
| Gráficos | Apache ECharts 5 |
| Parsing de arquivos | pandas + openpyxl |

## Build (executável standalone)

O projeto inclui um workflow GitHub Actions (`.github/workflows/release.yml`) que gera executáveis via PyInstaller para Linux e Windows ao criar uma tag de versão:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Os artefatos `pmas-linux-x64` e `pmas-windows-x64.exe` ficam disponíveis na aba *Releases* do GitHub.

## Estrutura do projeto

```
PMAS/
├── backend/
│   └── app/
│       ├── main.py          # Rotas FastAPI
│       ├── models.py        # Modelos SQLAlchemy
│       ├── database.py      # Configuração do banco
│       └── services/
│           └── ingestion.py # Parser de CSV/XLSX
├── frontend/
│   ├── index.html           # Interface (HTML + CSS embutido)
│   └── app.js               # Lógica do cliente
├── .github/workflows/
│   └── release.yml          # Build de executável
├── requirements.txt
└── run.py                   # Entrypoint para PyInstaller
```
