# Dados de Treinamento PMAS

Arquivos CSV simulando 12 meses de operação (2025) para uso no workshop.

## Arquivos

| Arquivo | Período | Registros | Anomalias |
|---|---|---|---|
| `ponto_q1_2025.csv` | Jan–Mar 2025 | 244 | `10/02`: Carla Dias 26h num dia |
| `ponto_q2_2025.csv` | Abr–Jun 2025 | 229 | `20/04`: Bruno Costa (domingo) |
| `ponto_q3_2025.csv` | Jul–Set 2025 | 244 | Horas extras de crise (INF) |
| `ponto_q4_2025.csv` | Out–Dez 2025 | 228 | INF supervisão mínima |
| `baseline_2025.csv` | Ano todo | 39 linhas | Baseline EVM para todos os projetos |

### Formato do baseline_2025.csv

```
pep_wbs,cycle_name,planned_hours
P-CRM-001,Janeiro 2025,233
...
```

Importe via **Previsão → Importar CSV** na interface do PMAS após cadastrar os ciclos.

## Equipe e Tarifas

| Colaborador | Nível | R$/h |
|---|---|---|
| Ana Lima | Sênior | 120,00 |
| Bruno Costa | Pleno | 80,00 |
| Carla Dias | Júnior | 50,00 |
| Diego Santos | Sênior | 120,00 |

## Projetos

| Código PEP | Nome | Budget (h) | Budget (R$) |
|---|---|---|---|
| P-CRM-001 | Sistema de Gestão de Clientes | 2.800 | 300.000 |
| P-INF-002 | Modernização de Infraestrutura | 1.800 | 160.000 |
| P-RH-003 | Portal do Colaborador | 600 | 40.000 |
| P-BI-004 | Inteligência de Negócio (inicia Q2) | 3.000 | 250.000 |

## Ciclos de Faturamento

Cadastre os 12 ciclos mensais de 01/01/2025 a 31/12/2025 antes de iniciar os uploads.

## Guia completo

Consulte `docs/treinamento.md` para o guia de workshop passo a passo.
