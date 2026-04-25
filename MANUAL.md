# PMAS — Manual do Usuário

**PMAS** (Project Management Assistant System) é um sistema de gestão de horas e análise de timesheets. Permite importar planilhas de horas e visualizar a distribuição por projeto, colaborador e ciclo de faturamento.

---

## Sumário

1. [Instalação e inicialização](#1-instalação-e-inicialização)
2. [Conceitos fundamentais](#2-conceitos-fundamentais)
3. [Gerenciar ciclos](#3-gerenciar-ciclos)
4. [Gerenciar projetos](#4-gerenciar-projetos)
5. [Importar timesheets](#5-importar-timesheets)
6. [Visualizar o dashboard](#6-visualizar-o-dashboard)
7. [Filtros e navegação](#7-filtros-e-navegação)
8. [Ciclos de quarentena](#8-ciclos-de-quarentena)
9. [Referência da API REST](#9-referência-da-api-rest)
10. [Estrutura de arquivos CSV/XLSX](#10-estrutura-de-arquivos-csvxlsx)

---

## 1. Instalação e inicialização

### Pré-requisitos

- Python 3.11 ou 3.12
- pip

### Passos

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd PMAS

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Inicie o servidor
python -m uvicorn backend.app.main:app --reload
```

Acesse o sistema em: **http://127.0.0.1:8000/frontend/index.html**

O banco de dados SQLite (`pmas.db`) é criado automaticamente na primeira execução.

---

## 2. Conceitos fundamentais

| Conceito | Descrição |
|---|---|
| **Ciclo** | Período de faturamento (ex.: Janeiro/2026). Define o intervalo de datas em que as horas foram lançadas. |
| **PEP / WBS** | Código de projeto no sistema de gestão (ex.: `60OP-03333`). Cada registro de hora é associado a um código PEP. |
| **Colaborador** | Profissional cujas horas são registradas. Criado automaticamente na importação. |
| **Timesheet Record** | Linha de hora: um colaborador, uma data, um PEP, e a quantidade de horas (normais, extras ou sobreaviso). |
| **Quarentena** | Ciclo especial criado automaticamente quando uma data importada não se encaixa em nenhum ciclo cadastrado. |

### Tipos de hora

| Tipo | Coluna CSV | Descrição |
|---|---|---|
| Normal | — | Hora regular de trabalho (padrão quando nenhum flag está ativo) |
| Extra | `Hora extra = Sim` | Hora extra remunerada |
| Sobreaviso | `Hora sobreaviso = Sim` | Hora de sobreaviso/plantão |

---

## 3. Gerenciar ciclos

A aba **Ciclos** permite cadastrar e manter os períodos de faturamento.

### Criar um ciclo

1. Clique na aba **Ciclos**.
2. Preencha o formulário:
   - **Nome**: identificação do ciclo (ex.: `Janeiro/2026`)
   - **Data início** e **Data fim**: intervalo do período
3. Clique em **Criar Ciclo**.

> O sistema valida que a data de início não é posterior à data de fim.

### Editar um ciclo

1. Na lista de ciclos, clique em **Editar** ao lado do ciclo desejado.
2. Altere os campos no formulário que aparece.
3. Clique em **Salvar**.

### Excluir um ciclo

1. Clique em **Excluir** ao lado do ciclo.
2. Confirme a ação na caixa de diálogo.

> **Atenção:** ciclos com registros de timesheet associados **não podem ser excluídos**. Remova os registros antes de excluir o ciclo.

### Contador de registros

A lista de ciclos exibe o número de registros de timesheet associados a cada ciclo. Ciclos de quarentena aparecem marcados com o badge **QUARENTENA**.

---

## 4. Gerenciar projetos

A aba **Projetos** mantém o cadastro de projetos com orçamento de horas, usado para a comparação orçado vs. realizado no dashboard.

### Criar um projeto

1. Clique na aba **Projetos**.
2. Preencha o formulário:
   - **Código PEP** (obrigatório): código único do projeto (ex.: `60OP-03333`)
   - **Nome do projeto**: descrição comercial
   - **Cliente**: empresa contratante
   - **Gerente**: responsável pelo projeto
   - **Horas orçadas**: total de horas planejadas para o projeto
   - **Status**: `ativo` ou `encerrado`
3. Clique em **Criar Projeto**.

### Editar um projeto

1. Clique em **Editar** ao lado do projeto na lista.
2. Altere os campos desejados e clique em **Salvar**.

> O código PEP pode ser alterado, desde que o novo código não já exista em outro projeto.

### Excluir um projeto

1. Clique em **Excluir** ao lado do projeto.
2. Confirme a ação.

> Excluir o projeto não remove os registros de timesheet associados. Os registros continuam existindo, mas a comparação orçado vs. realizado deixará de aparecer no dashboard para aquele PEP.

---

## 5. Importar timesheets

A aba **Importar** permite carregar arquivos de horas no formato CSV ou XLSX.

### Formatos aceitos

| Formato | Extensão |
|---|---|
| CSV (separado por vírgula) | `.csv` |
| Excel | `.xlsx` |

### Como importar

1. Clique na aba **Importar**.
2. Arraste o arquivo para a área pontilhada, ou clique em **Selecionar arquivo**.
3. Clique em **Enviar**.
4. O sistema exibe um resumo da importação:
   - Registros inseridos
   - Registros ignorados (duplicatas)
   - Ciclos de quarentena criados

### Deduplicação automática

O sistema detecta e ignora registros duplicados (mesmo colaborador, data, ciclo e PEP). É seguro importar o mesmo arquivo mais de uma vez.

### Estrutura esperada do arquivo

Veja a seção [10. Estrutura de arquivos CSV/XLSX](#10-estrutura-de-arquivos-csvxlsx).

---

## 6. Visualizar o dashboard

O dashboard exibe um gráfico de barras horizontais empilhadas com as horas por colaborador.

### Acesso

1. Clique na aba **Dashboard**.
2. Por padrão, exibe **toda a base** (todos os ciclos).

### Selecionar um ciclo específico

1. No filtro **Ciclo**, selecione o período desejado.
2. O gráfico é atualizado automaticamente.

### Informações exibidas

| Elemento | Descrição |
|---|---|
| **Barras** | Horas normais (azul), extras (laranja) e sobreaviso (roxo) por colaborador |
| **Ciclo** | Nome e período do ciclo selecionado |
| **Orçado vs. Realizado** | Tabela comparando horas orçadas e horas reais por PEP (exibe apenas PEPs com projeto cadastrado) |
| **Breakdown** | Detalhamento das horas por PEP dentro do ciclo |

> O gráfico exibe no máximo 40 colaboradores por vez. Use os filtros para restringir o resultado.

---

## 7. Filtros e navegação

O dashboard oferece filtros em cascata para detalhar a análise.

### Ordem dos filtros

```
Ciclo → Código PEP → Descrição PEP → Colaborador
```

Selecionar um valor em um nível restringe as opções disponíveis nos níveis seguintes.

### Filtros disponíveis

| Filtro | Descrição |
|---|---|
| **Ciclo** | Filtra por período de faturamento |
| **Código PEP** | Filtra por código de projeto (ex.: `60OP-03333`) |
| **Descrição PEP** | Filtra pela descrição do projeto (ex.: `COPEL-D \| OMS`) |
| **Colaborador** | Filtra por um ou mais colaboradores (multi-seleção) |

### Multi-seleção de colaboradores

O filtro de colaboradores permite selecionar múltiplos nomes simultaneamente:

1. Clique no botão **Colaboradores**.
2. Marque os colaboradores desejados no painel que se abre.
3. Use **Todos** para selecionar/limpar todos de uma vez.
4. O painel fecha automaticamente ao clicar fora dele.

### Limpar filtros

Clique em **Limpar filtros** para redefinir todos os filtros e voltar à visão completa.

---

## 8. Ciclos de quarentena

Quando um arquivo importado contém datas que não correspondem a nenhum ciclo cadastrado, o sistema cria automaticamente um **ciclo de quarentena** para preservar os dados.

### Identificação

Ciclos de quarentena aparecem:
- Com o prefixo `Quarentena —` no nome (ex.: `Quarentena — Set/2099`)
- Com o badge **QUARENTENA** na lista de ciclos
- Com o flag `is_quarantine: true` na API

### Procedimento recomendado

1. Ao notar registros em quarentena, identifique a data incorreta no arquivo original.
2. Corrija o arquivo (datas fora do intervalo esperado) e reimporte.
3. Ou crie o ciclo correto correspondente ao período e reimporte.

> Os dados em quarentena **não são perdidos**. Eles ficam acessíveis no dashboard ao selecionar o ciclo de quarentena.

---

## 9. Referência da API REST

Todos os endpoints retornam JSON. A URL base é `http://127.0.0.1:8000`.

### Ciclos

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/cycles` | Lista todos os ciclos com contagem de registros |
| `POST` | `/api/cycles` | Cria um novo ciclo |
| `PUT` | `/api/cycles/{id}` | Atualiza um ciclo existente |
| `DELETE` | `/api/cycles/{id}` | Remove um ciclo (falha se tiver registros) |

**Body para criação/atualização:**
```json
{
  "name": "Janeiro/2026",
  "start_date": "2026-01-01",
  "end_date": "2026-01-31"
}
```

### Projetos

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/projects` | Lista todos os projetos, ordenados por PEP |
| `POST` | `/api/projects` | Cria um novo projeto |
| `PUT` | `/api/projects/{id}` | Atualiza um projeto existente |
| `DELETE` | `/api/projects/{id}` | Remove um projeto |

**Body para criação/atualização:**
```json
{
  "pep_wbs": "60OP-03333",
  "name": "Projeto Exemplo",
  "client": "Cliente X",
  "manager": "Gerente Y",
  "budget_hours": 160.0,
  "status": "ativo"
}
```

### Dashboard

| Método | Rota | Parâmetros | Descrição |
|---|---|---|---|
| `GET` | `/api/dashboard` | `pep_code`, `collaborator_id` | Agrega horas de toda a base |
| `GET` | `/api/dashboard/{cycle_id}` | `pep_code`, `collaborator_id`, `pep_description` | Agrega horas do ciclo |

**Resposta:**
```json
{
  "cycle": {
    "id": 1,
    "name": "Janeiro/2026",
    "start_date": "2026-01-01",
    "end_date": "2026-01-31",
    "is_quarantine": false
  },
  "data": [
    {
      "collaborator": "João Silva",
      "normal_hours": 120.0,
      "extra_hours": 8.0,
      "standby_hours": 0.0
    }
  ],
  "breakdown": [
    {
      "pep_code": "60OP-03333",
      "pep_description": "COPEL-D | OMS",
      "normal_hours": 120.0,
      "extra_hours": 8.0,
      "standby_hours": 0.0
    }
  ],
  "budget_vs_actual": [
    {
      "pep_wbs": "60OP-03333",
      "name": "Projeto Exemplo",
      "budget_hours": 160.0,
      "actual_hours": 128.0
    }
  ]
}
```

### Referência (dropdowns)

| Método | Rota | Parâmetros | Descrição |
|---|---|---|---|
| `GET` | `/api/collaborators` | `cycle_id`, `pep_code`, `pep_description` | Lista colaboradores que têm registros |
| `GET` | `/api/peps` | `cycle_id`, `collaborator_id` | Lista PEPs com agrupamento de descrições |

### Upload de timesheet

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/upload-timesheet` | Recebe `multipart/form-data` com campo `file` |

**Resposta:**
```json
{
  "records_inserted": 42,
  "records_skipped": 3,
  "quarantine_cycles_created": 0
}
```

---

## 10. Estrutura de arquivos CSV/XLSX

### Colunas obrigatórias

| Coluna | Tipo | Exemplo | Descrição |
|---|---|---|---|
| `Colaborador` | Texto | `João Silva` | Nome completo do colaborador |
| `Data` | Data (`DD/MM/AAAA`) | `15/01/2026` | Data do lançamento de horas |
| `Horas totais (decimal)` | Número | `8.0` | Total de horas do dia (em decimal) |

### Colunas opcionais

| Coluna | Tipo | Valores | Descrição |
|---|---|---|---|
| `Hora extra` | Texto | `Sim` / `Não` | Indica se são horas extras |
| `Hora sobreaviso` | Texto | `Sim` / `Não` | Indica se são horas de sobreaviso |
| `Código PEP` | Texto | `60OP-03333` | Código do projeto no sistema WBS |
| `PEP` | Texto | `COPEL-D \| OMS` | Descrição do projeto |

### Exemplo de CSV válido

```csv
Colaborador,Data,Horas totais (decimal),Hora extra,Hora sobreaviso,Código PEP,PEP
João Silva,15/01/2026,8.0,Não,Não,60OP-03333,COPEL-D | OMS
Maria Oliveira,15/01/2026,8.0,Não,Não,60OP-03333,COPEL-D | OMS
João Silva,16/01/2026,4.0,Sim,Não,60OP-03333,COPEL-D | OMS
```

### Regras de classificação de horas

| `Hora extra` | `Hora sobreaviso` | Resultado |
|---|---|---|
| `Não` | `Não` | `normal_hours = total` |
| `Sim` | `Não` | `extra_hours = total`, `normal_hours = 0` |
| `Não` | `Sim` | `standby_hours = total`, `normal_hours = 0` |
| (ausente) | (ausente) | `normal_hours = total` |

### Observações

- Colunas não reconhecidas são ignoradas silenciosamente.
- Valores em branco em `Código PEP` ou `PEP` são tratados como `null` (sem vinculação de projeto).
- O separador decimal deve ser ponto (`.`), não vírgula.
- O arquivo pode conter linhas duplicadas; apenas a primeira é inserida.

---

## Executar os testes

```bash
# Instalar dependências de teste
pip install pytest httpx

# Executar todos os testes
pytest tests/ -v

# Executar um módulo específico
pytest tests/test_dashboard.py -v
```

O CI (GitHub Actions) executa automaticamente a suíte completa a cada push, nas versões Python 3.11 e 3.12.
