# PMAS — Manual do Usuário

**PMAS** (Project Management Assistant System) é um sistema de gestão de horas e análise de timesheets. Permite importar planilhas de horas e visualizar a distribuição por projeto, colaborador e ciclo de faturamento através de três visões analíticas.

---

## Sumário

1. [Instalação e inicialização](#1-instalação-e-inicialização)
2. [Conceitos fundamentais](#2-conceitos-fundamentais)
3. [Gerenciar ciclos](#3-gerenciar-ciclos)
4. [Gerenciar projetos](#4-gerenciar-projetos)
5. [Importar timesheets](#5-importar-timesheets)
6. [Dashboard — Esforço da Equipe](#6-dashboard--esforço-da-equipe)
7. [Dashboard — Saúde do Portfólio](#7-dashboard--saúde-do-portfólio)
8. [Dashboard — Tendências](#8-dashboard--tendências)
9. [Filtros e navegação](#9-filtros-e-navegação)
10. [Ciclos de quarentena](#10-ciclos-de-quarentena)
11. [Referência da API REST](#11-referência-da-api-rest)
12. [Estrutura de arquivos CSV/XLSX](#12-estrutura-de-arquivos-csvxlsx)

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

Acesse o sistema em: **http://127.0.0.1:8000**

O banco de dados SQLite (`pmas.db`) é criado automaticamente na primeira execução. Atualizações de schema são aplicadas automaticamente no startup — nenhum dado existente é perdido.

---

## 2. Conceitos fundamentais

| Conceito | Descrição |
|---|---|
| **Ciclo** | Período de faturamento (ex.: Janeiro/2026). Define o intervalo de datas em que as horas foram lançadas. |
| **PEP / WBS** | Código de projeto no sistema de gestão (ex.: `60OP-03333`). Cada registro de hora é associado a um código PEP. |
| **Colaborador** | Profissional cujas horas são registradas. Criado automaticamente na importação. |
| **Timesheet Record** | Linha de hora: um colaborador, uma data, um PEP e a quantidade de horas (normais, extras ou sobreaviso). |
| **Quarentena** | Ciclo especial criado automaticamente quando uma data importada não se encaixa em nenhum ciclo cadastrado. |
| **cost_per_hour** | Campo reservado para integração futura com módulo de RateCard. Armazenado como `0.0` até que o módulo seja ativado. |

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
2. Clique em **+ Novo ciclo** e preencha o formulário:
   - **Nome**: identificação do ciclo (ex.: `Janeiro/2026`)
   - **Data início** e **Data fim**: intervalo do período
3. Clique em **Salvar**.

> O sistema valida que a data de início não é posterior à data de fim.

### Editar e excluir

- Clique em **Editar** para alterar nome ou datas.
- Clique em **Excluir** para remover o ciclo.

> Ciclos com registros de timesheet associados **não podem ser excluídos**. Remova os registros antes de excluir o ciclo.

### Contador de registros

A lista exibe o número de registros associados a cada ciclo. Ciclos de quarentena aparecem marcados com o badge **QUARENTENA**.

---

## 4. Gerenciar projetos

A aba **Projetos** mantém o cadastro de projetos com orçamento de horas, usado para a comparação orçado vs. realizado nos gráficos de Esforço e Saúde do Portfólio.

### Criar um projeto

1. Clique na aba **Projetos**.
2. Clique em **+ Novo projeto** e preencha o formulário:
   - **Código PEP** (obrigatório): código único (ex.: `60OP-03333`)
   - **Nome do projeto**, **Cliente**, **Gerente** (opcionais)
   - **Horas orçadas**: total de horas planejadas
   - **Status**: `ativo`, `suspenso` ou `encerrado`
3. Clique em **Salvar**.

### Editar e excluir

- O código PEP pode ser alterado desde que não conflite com outro projeto já cadastrado.
- Excluir o projeto não remove os registros de timesheet associados. Os gráficos de orçado vs. realizado deixam de exibir o PEP, mas as horas continuam acessíveis.

---

## 5. Importar timesheets

A aba **Importar** dentro do Dashboard permite carregar arquivos de horas.

### Formatos aceitos

- `.csv` (separado por vírgula)
- `.xlsx` / `.xls` (Excel)

### Como importar

1. Arraste o arquivo para a área pontilhada, ou clique em **Clique para selecionar CSV ou XLSX**.
2. O sistema processa imediatamente e exibe um resumo:
   - Registros inseridos
   - Registros ignorados (duplicatas)
   - Ciclos de quarentena criados

### Deduplicação automática

O sistema detecta e ignora registros duplicados (mesmo colaborador, data, ciclo e PEP). É seguro importar o mesmo arquivo mais de uma vez.

### Estrutura esperada

Veja a seção [12. Estrutura de arquivos CSV/XLSX](#12-estrutura-de-arquivos-csvxlsx).

---

## 6. Dashboard — Esforço da Equipe

A sub-aba **Esforço da Equipe** exibe um gráfico de barras horizontais com as horas de cada colaborador.

### Vista empilhada vs. agrupada

Clique no botão **Vista: Empilhada / Vista: Agrupada** para alternar entre:

- **Empilhada** — mostra a capacidade total e a proporção entre tipos de hora.
- **Agrupada** — barras lado a lado, ideal para identificar abusos de horas extras ou sobreaviso em relação às horas normais.

### Cards de resumo

Acima do gráfico aparecem cards com o total de:
- Horas Normais, Extras e Sobreaviso
- Total geral e número de colaboradores
- Orçado (PEPs com budget cadastrado) e percentual Realizado vs. Orçado

### Orçado vs. Realizado

Quando há projetos com `budget_hours` cadastrados para os PEPs filtrados, um gráfico secundário aparece abaixo do principal comparando o budget com as horas realizadas. A barra fica **verde** quando dentro do orçamento e **vermelha** quando ultrapassado.

> O gráfico exibe no máximo 40 colaboradores. Use os filtros para restringir o resultado.

---

## 7. Dashboard — Saúde do Portfólio

A sub-aba **Saúde do Portfólio** oferece uma visão gerencial agregada por PEP.

### Treemap — Distribuição de horas

Cada bloco representa um PEP. O **tamanho** é proporcional às horas consumidas.

| Cor do bloco | Significado |
|---|---|
| Azul | PEP cadastrado no sistema, dentro do orçamento |
| Vermelho | PEP cadastrado e acima do orçamento |
| Cinza | PEP não cadastrado (sem projeto associado) |

Passe o mouse sobre um bloco para ver o tooltip com horas consumidas, budget e % de utilização.

### Bullet Chart — Orçado vs. Realizado

Exibido apenas quando há PEPs com `budget_hours` cadastrados. Cada barra de projeto mostra:

| Cor da barra | Utilização |
|---|---|
| Azul | < 75% do budget |
| Âmbar | 75% a 99% do budget |
| Vermelho | ≥ 100% do budget (estourado) |

O valor percentual é exibido ao lado direito de cada barra.

> O Bullet Chart só aparece para PEPs com projeto cadastrado na aba Projetos.

---

## 8. Dashboard — Tendências

A sub-aba **Tendências** mostra a evolução da queima de horas ao longo dos ciclos.

### Gráfico de linhas

- Eixo X: ciclos em ordem cronológica (ciclos de quarentena excluídos)
- Eixo Y: volume de horas
- Duas linhas: **Horas Normais** (azul) e **Horas Extras** (âmbar)
- Área sombreada para facilitar a leitura de tendências

### Interpretação

- Linha crescente de horas extras pode indicar que o projeto está sobrecarregado ou mal dimensionado.
- Linhas estabilizando indicam operação em regime.
- Pico seguido de queda brusca pode indicar entrega ou encerramento de escopo.

### Filtrar por PEP

Use o filtro **PEP (Código)** para isolar as tendências de um projeto específico. Sem filtro, as linhas somam todas as horas de todos os PEPs no ciclo.

---

## 9. Filtros e navegação

Os filtros são compartilhados pelas três sub-abas e aplicados ao clicar em **Carregar**.

### Ordem de cascata

```
Ciclo → Código PEP → Descrição PEP → Colaborador
```

Selecionar um valor restringe as opções dos filtros seguintes.

### Filtros disponíveis

| Filtro | Esforço | Portfólio | Tendências |
|---|---|---|---|
| **Ciclo** | Sim | Sim (1º selecionado) | Ignorado |
| **Código PEP** | Sim | Sim | Sim |
| **Descrição PEP** | Sim | — | — |
| **Colaborador** | Sim | — | — |

> Saúde do Portfólio usa apenas o **primeiro ciclo selecionado** (ou toda a base se nenhum for selecionado). Tendências sempre mostra todos os ciclos no eixo X.

### Multi-seleção

Todos os filtros suportam múltipla seleção. Clique no controle para abrir o painel, marque os itens desejados e clique fora para fechar. Use a opção **Todos** para marcar/desmarcar tudo de uma vez.

### Limpar filtros

Clique em **Limpar** para redefinir todos os filtros e limpar os gráficos.

---

## 10. Ciclos de quarentena

Quando um arquivo importado contém datas fora de qualquer ciclo cadastrado, o sistema cria automaticamente um ciclo de quarentena para preservar os dados.

### Identificação

Ciclos de quarentena aparecem:
- Com o prefixo `Quarentena —` no nome (ex.: `Quarentena - Set/2099`)
- Com o badge **QUARENTENA** na lista de ciclos
- Com `is_quarantine: true` na API

### Comportamento nos gráficos

- **Esforço da Equipe**: visível ao selecionar o ciclo de quarentena no filtro.
- **Saúde do Portfólio**: incluído se o ciclo de quarentena estiver selecionado.
- **Tendências**: **excluído automaticamente** — ciclos de quarentena não têm posição cronológica significativa.

### Procedimento recomendado

1. Identifique a data incorreta no arquivo original.
2. Crie o ciclo correto na aba **Ciclos** e reimporte o arquivo corrigido.
3. O registro de quarentena pode ser mantido — não interfere nos ciclos regulares.

---

## 11. Referência da API REST

URL base: `http://127.0.0.1:8000`

### Ciclos

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/cycles` | Lista ciclos com contagem de registros |
| `POST` | `/api/cycles` | Cria ciclo |
| `PUT` | `/api/cycles/{id}` | Atualiza ciclo |
| `DELETE` | `/api/cycles/{id}` | Remove ciclo (falha se tiver registros) |

**Body:**
```json
{ "name": "Janeiro/2026", "start_date": "2026-01-01", "end_date": "2026-01-31" }
```

### Projetos

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/projects` | Lista projetos por PEP |
| `POST` | `/api/projects` | Cria projeto |
| `PUT` | `/api/projects/{id}` | Atualiza projeto |
| `DELETE` | `/api/projects/{id}` | Remove projeto |

**Body:**
```json
{
  "pep_wbs": "60OP-03333", "name": "Projeto X", "client": "Cliente A",
  "manager": "Gerente B", "budget_hours": 160.0, "status": "ativo"
}
```

### Dashboard

| Método | Rota | Parâmetros | Descrição |
|---|---|---|---|
| `GET` | `/api/dashboard` | `pep_code[]`, `collaborator_id[]` | Agrega horas de toda a base |
| `GET` | `/api/dashboard/{cycle_id}` | `pep_code[]`, `collaborator_id[]`, `pep_description[]` | Agrega horas do ciclo |

### Analytics

| Método | Rota | Parâmetros | Descrição |
|---|---|---|---|
| `GET` | `/api/portfolio-health` | `cycle_id`, `pep_wbs[]` | Horas por PEP + budget do projeto |
| `GET` | `/api/trends` | `pep_wbs[]` | Queima de horas por ciclo (cronológico) |

**Resposta `/api/portfolio-health`:**
```json
[
  {
    "pep_wbs": "60OP-03333",
    "pep_description": "COPEL-D | OMS",
    "name": "Projeto X",
    "budget_hours": 160.0,
    "consumed_hours": 128.0,
    "is_registered": true
  }
]
```

**Resposta `/api/trends`:**
```json
[
  { "cycle_name": "Janeiro/2026", "normal_hours": 120.0, "extra_hours": 8.0, "standby_hours": 0.0 }
]
```

### Referência

| Método | Rota | Parâmetros | Descrição |
|---|---|---|---|
| `GET` | `/api/collaborators` | `cycle_id[]`, `pep_code[]`, `pep_description[]` | Colaboradores com registros |
| `GET` | `/api/peps` | `cycle_id[]`, `collaborator_id[]` | PEPs com agrupamento de descrições |

### Upload

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/upload-timesheet` | `multipart/form-data` com campo `file` (`.csv` / `.xlsx`) |

**Resposta:**
```json
{ "records_inserted": 42, "records_skipped": 3, "quarantine_cycles_created": 0 }
```

---

## 12. Estrutura de arquivos CSV/XLSX

### Colunas obrigatórias

| Coluna | Tipo | Exemplo | Descrição |
|---|---|---|---|
| `Colaborador` | Texto | `João Silva` | Nome completo do colaborador |
| `Data` | Data (DD/MM/AAAA) | `15/01/2026` | Data do lançamento |
| `Horas totais (decimal)` | Número | `8.0` | Total de horas do dia |

### Colunas opcionais

| Coluna | Valores | Descrição |
|---|---|---|
| `Hora extra` | `Sim` / `Não` | Indica horas extras |
| `Hora sobreaviso` | `Sim` / `Não` | Indica horas de sobreaviso |
| `Código PEP` | Texto | Código WBS do projeto |
| `PEP` | Texto | Descrição do projeto |

### Regras de classificação de horas

| `Hora extra` | `Hora sobreaviso` | Resultado |
|---|---|---|
| `Não` / ausente | `Não` / ausente | `normal_hours = total` |
| `Sim` | `Não` | `extra_hours = total`, `normal_hours = 0` |
| `Não` | `Sim` | `standby_hours = total`, `normal_hours = 0` |

### Observações

- Colunas não reconhecidas são ignoradas silenciosamente.
- Valores em branco em `Código PEP` ou `PEP` são tratados como `null`.
- O separador decimal deve ser ponto (`.`).
- Linhas duplicadas dentro do mesmo arquivo são ignoradas automaticamente.

---

## Executar os testes

```bash
pip install pytest httpx
pytest tests/ -v                         # todos os testes
pytest tests/test_analytics.py -v       # só analytics
pytest tests/ -v -k "portfolio"          # por palavra-chave
```

O CI (GitHub Actions) executa a suite completa em Python 3.11 e 3.12 a cada push.
