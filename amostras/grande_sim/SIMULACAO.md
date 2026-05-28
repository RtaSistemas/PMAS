# PMAS — Grande Simulação: Documentação Completa

**Período simulado:** Janeiro/2022 – Dezembro/2026 (60 ciclos mensais)  
**Dados gerados:** Janeiro/2022 – Maio/2026 (53 meses de timesheets)  
**Total de horas:** 158.864 h  
**Custo acumulado:** R$ 20.730.393  
**Projetos:** 17  
**Colaboradores:** 22 + 3 externos (sem senioridade — testam N1/I3)

---

## 1. Níveis de Senioridade e Tabela de Taxas

Cada nível tem reajuste anual de ~8–10%. A taxa é **congelada na ingestão** pelo padrão EVM Freeze — mudanças futuras não afetam registros já importados.

| Nível         | 2022 (R$/h) | 2023 (R$/h) | 2024 (R$/h) | 2025 (R$/h) | 2026 (R$/h) |
|---------------|-------------|-------------|-------------|-------------|-------------|
| Arquiteto     | 200,00      | 220,00      | 240,00      | 260,00      | 275,00      |
| Especialista  | 160,00      | 175,00      | 190,00      | 205,00      | 215,00      |
| Sênior        | 120,00      | 132,00      | 145,00      | 158,00      | 165,00      |
| Pleno         |  80,00      |  88,00      |  97,00      | 106,00      | 112,00      |
| Júnior        |  50,00      |  55,00      |  61,00      |  67,00      |  71,00      |
| Trainee       |  25,00      |  28,00      |  31,00      |  34,00      |  36,00      |

---

## 2. Equipe de Colaboradores

| Colaborador         | Nível         | Entrada na Simulação | Taxa 2022 | Taxa 2026 |
|---------------------|---------------|----------------------|-----------|-----------|
| Rodrigo Andrade     | Arquiteto     | Jan/2022             | R$ 200/h  | R$ 275/h  |
| Beatriz Nunes       | Arquiteto     | Jul/2022             | —         | R$ 275/h  |
| Marcos Tavares      | Especialista  | Jan/2022             | R$ 160/h  | R$ 215/h  |
| Juliana Ramos       | Especialista  | Jan/2022             | R$ 160/h  | R$ 215/h  |
| Thiago Campos       | Especialista  | Abr/2023             | —         | R$ 215/h  |
| João Silva          | Sênior        | Jan/2022             | R$ 120/h  | R$ 165/h  |
| Maria Santos        | Sênior        | Jan/2022             | R$ 120/h  | R$ 165/h  |
| Carlos Oliveira     | Sênior        | Jul/2022             | —         | R$ 165/h  |
| Ana Ferreira        | Sênior        | Jan/2023             | —         | R$ 165/h  |
| Roberto Costa       | Sênior        | Jan/2022             | R$ 120/h  | R$ 165/h  |
| Lucas Pereira       | Pleno         | Jan/2022             | R$  80/h  | R$ 112/h  |
| Fernanda Lima       | Pleno         | Jan/2022             | R$  80/h  | R$ 112/h  |
| Gabriel Souza       | Pleno         | Jul/2023             | —         | R$ 112/h  |
| Amanda Torres       | Pleno         | Jan/2024             | —         | R$ 112/h  |
| Rafael Gomes        | Pleno         | Jan/2022             | R$  80/h  | R$ 112/h  |
| Camila Barbosa      | Pleno         | Abr/2023             | —         | R$ 112/h  |
| Pedro Carvalho      | Júnior        | Jan/2022             | R$  50/h  | R$  71/h  |
| Leticia Moreira     | Júnior        | Jan/2023             | —         | R$  71/h  |
| Diego Martins       | Júnior        | Jul/2023             | —         | R$  71/h  |
| Priscila Farias     | Júnior        | Jan/2024             | —         | R$  71/h  |
| Vinícius Mendes     | Trainee       | Jan/2024             | —         | R$  36/h  |
| Sara Alves          | Trainee       | Jul/2024             | —         | R$  36/h  |

> **Sobreaviso:** Roberto Costa (SUP-01) e Rafael Gomes (SUP-01) têm sobreaviso mensal de 3 e 2 dias respectivamente. Lucas Pereira (IOT-01) e Diego Martins (IOT-01) a partir de Jan/2025 e Jul/2025. Rodrigo Andrade (INF-01) a partir de Jul/2025. O sobreaviso é lançado com fator de custo 33% da taxa horária normal.

---

## 3. Portfólio de Projetos

### 3.1 Visão Geral

| PEP           | Nome                        | Cliente            | Gestor             | Duração     | Budget h | Budget R$     | Status      | Cenário EVM  |
|---------------|-----------------------------|--------------------|--------------------|-------------|----------|---------------|-------------|--------------|
| 60IT-INF-01   | Plataforma Core Enterprise  | Banco Meridional   | Rodrigo Andrade    | Jan/22–Dez/26 | 24.300 h | R$ 3.727.000 | ativo       | ✅ ON TRACK  |
| 60IT-TRF-01   | Transformação Digital 360°  | GrupoVarejo S.A.   | Beatriz Nunes      | Jul/22–Dez/26 | 23.600 h | R$ 4.314.000 | ativo       | 🔵 BEHIND    |
| 60IT-ERP-01   | Implantação ERP Global      | IndustriaMax       | Marcos Tavares     | Jan/22–Dez/25 | 22.600 h | R$ 3.216.000 | encerrado   | 🔴 OVER BUDGET |
| 60IT-PLT-01   | Migração de Plataforma      | TechlogicBR        | Juliana Ramos      | Jan/23–Dez/26 | 19.700 h | R$ 2.781.000 | ativo       | 🟢 AHEAD     |
| 60IT-SEG-01   | Programa de Cibersegurança  | FinanceSeguro      | Thiago Campos      | Jan/22–Dez/24 | 8.400 h  | R$ 1.052.000 | encerrado   | ✅ COMPLETED |
| 60IT-CRM-01   | CRM Enterprise              | RetailPlus         | João Silva         | Jan/22–Jun/24 | 8.000 h  | R$   768.000 | encerrado   | ✅ COMPLETED |
| 60IT-GOV-01   | Governança & Compliance     | Holding Alfa       | Maria Santos       | Jan/23–Dez/24 | 4.300 h  | R$   634.000 | encerrado   | ✅ COMPLETED |
| 60IT-SUP-01   | Sustentação & Operações     | MultiCliente       | Roberto Costa      | Jan/22–Dez/26 | 11.400 h | R$ 1.148.000 | ativo       | ⚠️ WARNING   |
| 60IT-DAT-01   | Data Lakehouse              | AnaliticosBR       | Beatriz Nunes      | Jan/24–Dez/26 | 14.100 h | R$ 2.372.000 | ativo       | 🔵 BEHIND    |
| 60IT-RH-01    | RH Digital                  | Capital Humano     | Carlos Oliveira    | Jul/23–Dez/24 | 5.800 h  | R$   610.000 | encerrado   | ✅ COMPLETED |
| 60IT-API-01   | Gateway de APIs             | EcossistemaTech    | Ana Ferreira       | Jul/24–Dez/26 | 7.900 h  | R$   896.000 | ativo       | ✅ ON TRACK  |
| 60IT-INO-01   | Lab de Inovação             | Interno            | Rodrigo Andrade    | Jan/24–Dez/26 | 7.000 h  | R$ 1.303.000 | ativo       | 🟡 SPORADIC  |
| 60IT-MOB-01   | App Mobile B2C              | ConsumerApp        | Gabriel Souza      | Jul/24–Dez/25 | 7.400 h  | R$   647.000 | encerrado   | ⚠️ WARNING   |
| 60IT-MKT-01   | Plataforma de Marketing     | MídiaDigital       | Camila Barbosa     | Jan/25–Dez/26 | 6.400 h  | R$   629.000 | ativo       | 🔵 BEHIND    |
| 60IT-BI-01    | BI & Analytics              | DataDriven         | Thiago Campos      | Jan/25–Dez/25 | 4.500 h  | R$   587.000 | encerrado   | 🔴 OVER BUDGET |
| 60IT-IOT-01   | IoT Industrial              | FábricaSmart       | Lucas Pereira      | Jan/25–Dez/26 | 7.700 h  | R$   730.000 | ativo       | 🟢 AHEAD     |
| 60IT-CLD-01   | Cloud Migration             | TechlogicBR        | Juliana Ramos      | Jan/26–Dez/26 | 5.300 h  | R$   781.000 | ativo       | 🚀 RAMP-UP   |

### 3.2 Consumo de Horas por Projeto e Ano

| PEP           | 2022    | 2023    | 2024    | 2025    | 2026  | **Total acum.** | Budget   | % consumido |
|---------------|--------:|--------:|--------:|--------:|------:|----------------:|---------:|:-----------:|
| 60IT-INF-01   | 3.782   | 6.248   | 5.785   | 4.434   | 1.302 | **21.551**      | 24.300   | 88,7%       |
| 60IT-TRF-01   | 2.096   | 3.965   | 4.192   | 4.488   | 1.908 | **16.649**      | 23.600   | 70,5%       |
| 60IT-ERP-01   | 4.684   | 5.103   | 6.820   | 8.018   | —     | **24.625**      | 22.600   | 108,9% 🔴   |
| 60IT-PLT-01   | —       | 3.776   | 4.588   | 4.959   | 1.319 | **14.642**      | 19.700   | 74,3%       |
| 60IT-SEG-01   | 1.951   | 2.860   | 3.144   | —       | —     | **7.955**       | 8.400    | 94,7%       |
| 60IT-CRM-01   | 2.860   | 3.380   | 1.300   | —       | —     | **7.540**       | 8.000    | 94,3%       |
| 60IT-GOV-01   | —       | 1.950   | 2.096   | —       | —     | **4.046**       | 4.300    | 94,1%       |
| 60IT-SUP-01   | 2.200   | 2.460   | 2.480   | 2.730   | 1.110 | **10.980**      | 11.400   | 96,3%       |
| 60IT-DAT-01   | —       | —       | 3.812   | 4.962   | 1.166 | **9.940**       | 14.100   | 70,5%       |
| 60IT-RH-01    | —       | 1.820   | 3.668   | —       | —     | **5.488**       | 5.800    | 94,6%       |
| 60IT-API-01   | —       | —       | 1.852   | 4.041   | 1.060 | **6.953**       | 7.900    | 88,0%       |
| 60IT-INO-01   | —       | —       | 2.096   | 1.824   | 424   | **4.344**       | 7.000    | 62,1%       |
| 60IT-MOB-01   | —       | —       | 2.382   | 4.762   | —     | **7.144**       | 7.400    | 96,5%       |
| 60IT-MKT-01   | —       | —       | —       | 3.018   | 1.484 | **4.502**       | 6.400    | 70,3%       |
| 60IT-BI-01    | —       | —       | —       | 4.864   | —     | **4.864**       | 4.500    | 108,1% 🔴   |
| 60IT-IOT-01   | —       | —       | —       | 3.927   | 1.798 | **5.725**       | 7.700    | 74,4%       |
| 60IT-CLD-01   | —       | —       | —       | —       | 1.918 | **1.918**       | 5.300    | 36,2%       |
| **TOTAL**     | **17.573** | **31.562** | **44.215** | **52.026** | **13.489** | **158.864** | | |

### 3.3 Custo Acumulado por Projeto e Ano (R$ mil)

| PEP           | 2022   | 2023   | 2024   | 2025   | 2026  | **Total**   |
|---------------|-------:|-------:|-------:|-------:|------:|------------:|
| 60IT-INF-01   | 572    | 828    | 867    | 659    | 220   | **3.147**   |
| 60IT-TRF-01   | 309    | 634    | 691    | 856    | 403   | **2.893**   |
| 60IT-ERP-01   | 518    | 673    | 947    | 1.197  | —     | **3.335**   |
| 60IT-PLT-01   | —      | 479    | 598    | 697    | 194   | **1.968**   |
| 60IT-SEG-01   | 207    | 340    | 399    | —      | —     | **946**     |
| 60IT-CRM-01   | 270    | 307    | 112    | —      | —     | **690**     |
| 60IT-GOV-01   | —      | 291    | 279    | —      | —     | **570**     |
| 60IT-SUP-01   | 210    | 245    | 245    | 276    | 118   | **1.095**   |
| 60IT-DAT-01   | —      | —      | 622    | 724    | 245   | **1.591**   |
| 60IT-RH-01    | —      | 170    | 378    | —      | —     | **548**     |
| 60IT-API-01   | —      | —      | 191    | 437    | 128   | **756**     |
| 60IT-INO-01   | —      | —      | 367    | 342    | 66    | **775**     |
| 60IT-MOB-01   | —      | —      | 186    | 407    | —     | **593**     |
| 60IT-MKT-01   | —      | —      | —      | 285    | 137   | **422**     |
| 60IT-BI-01    | —      | —      | —      | 608    | —     | **608**     |
| 60IT-IOT-01   | —      | —      | —      | 359    | 169   | **528**     |
| 60IT-CLD-01   | —      | —      | —      | —      | 266   | **266**     |
| **TOTAL**     | **2.087** | **3.967** | **5.882** | **6.847** | **1.947** | **R$ 20.730** |

---

## 4. Resultados por Ciclo Mensal

Horas válidas (excluindo linhas em quarentena), projetos ativos no mês, colaboradores com lançamento e indicação de linhas em quarentena.

### 2022 — Arranque do Portfólio

| Ciclo     | Horas válidas | Projetos | Colaboradores | Quarentena |
|-----------|:-------------:|:--------:|:-------------:|:----------:|
| Jan/2022  | 1.165 h       | 5        | 9             | —          |
| Fev/2022  | 1.119 h       | 5        | 9             | I1 (Sáb 05/02) + I4 (duplicata) |
| Mar/2022  | 1.275 h       | 5        | 9             | —          |
| Abr/2022  | 1.165 h       | 5        | 9             | —          |
| Mai/2022  | 1.220 h       | 5        | 9             | Q5 (horas em branco) |
| Jun/2022  | 1.220 h       | 5        | 9             | —          |
| Jul/2022  | 1.669 h       | 6        | 12            | — *(entrada de Beatriz Nunes + Carlos Oliveira, TRF-01 iniciado)* |
| Ago/2022  | 1.827 h       | 6        | 12            | Q8 (colaborador vazio) |
| Set/2022  | 1.748 h       | 6        | 12            | —          |
| Out/2022  | 1.669 h       | 6        | 12            | —          |
| Nov/2022  | 1.748 h       | 6        | 12            | Q6 (horas > 24 h) |
| Dez/2022  | 1.748 h       | 6        | 12            | —          |
| **Total** | **17.573 h**  |          |               | **3 linhas em quarentena** |

> **Destaque 2022:** Fase 1 do ERP e da Plataforma Core em arquitetura. Portfólio de 5 projetos cresce para 6 em Jul com a entrada de TRF-01. Equipe sobe de 9 para 12 colaboradores.

### 2023 — Expansão do Portfólio

| Ciclo     | Horas válidas | Projetos | Colaboradores | Quarentena |
|-----------|:-------------:|:--------:|:-------------:|:----------:|
| Jan/2023  | 2.276 h       | 8        | 14            | — *(PLT-01, GOV-01, Thiago/Ana entram; 6 novos juniors)* |
| Fev/2023  | 2.074 h       | 8        | 14            | Q4 (horas negativas) + I1 (Sáb 04/02) |
| Mar/2023  | 2.379 h       | 8        | 14            | —          |
| Abr/2023  | 2.170 h       | 8        | 16            | — *(Camila Barbosa + Thiago Campos entram)* |
| Mai/2023  | 2.494 h       | 8        | 16            | —          |
| Jun/2023  | 2.392 h       | 8        | 16            | Q2 (data futura: 15/06/2028) |
| Jul/2023  | 2.866 h       | 9        | 17            | — *(RH-01 iniciado; Gabriel Souza + Diego Martins entram)* |
| Ago/2023  | 3.138 h       | 9        | 17            | —          |
| Set/2023  | 2.871 h       | 9        | 17            | Q1 (data impossível: 32/09/2023) |
| Out/2023  | 3.002 h       | 9        | 17            | —          |
| Nov/2023  | 3.002 h       | 9        | 17            | —          |
| Dez/2023  | 2.898 h       | 9        | 18            | I2 (carga >28 h/semana: Marcos) + N1 (Estágio Rotativo sem senioridade) |
| **Total** | **31.562 h**  |          |               | **5 linhas em quarentena** |

> **Destaque 2023:** Maior expansão do portfólio — passa de 6 para 9 projetos. Volume mensal cresce 80% em relação a 2022. ERP entra em fase 2. CRM encaminha encerramento em Jun/2024. Primeiro colaborador externo sem senioridade detectado (N1+I3).

### 2024 — Pico Operacional

| Ciclo     | Horas válidas | Projetos | Colaboradores | Quarentena |
|-----------|:-------------:|:--------:|:-------------:|:----------:|
| Jan/2024  | 3.460 h       | 11       | 19            | — *(DAT-01 + INO-01 iniciados; Amanda Torres + Priscila Farias entram)* |
| Fev/2024  | 3.160 h       | 11       | 19            | —          |
| Mar/2024  | 3.160 h       | 11       | 19            | —          |
| Abr/2024  | 3.343 h       | 11       | 20            | N1+I3 (Consultor Freelance sem senioridade) + crise INF-01 |
| Mai/2024  | 3.460 h       | 11       | 19            | —          |
| Jun/2024  | 3.010 h       | 11       | 19            | — *(CRM-01 encerrado em 30/Jun)* |
| Jul/2024  | 4.288 h       | 12       | 20            | — *(API-01 + MOB-01 iniciados; Sara Alves entra)* |
| Ago/2024  | 4.108 h       | 12       | 20            | Q5 (horas em branco) + I4 (duplicata) |
| Set/2024  | 3.916 h       | 12       | 20            | —          |
| Out/2024  | 4.288 h       | 12       | 20            | —          |
| Nov/2024  | 3.916 h       | 12       | 20            | —          |
| Dez/2024  | 4.106 h       | 12       | 20            | I1 (Sáb 07/12) + Q8 (colaborador vazio) |
| **Total** | **44.215 h**  |          |               | **4 linhas em quarentena** |

> **Destaque 2024:** Maior adição de projetos simultâneos (11–12 ativos). Encerramento de CRM-01 (completed) e GOV-01 (completed). ERP entra na fase 3 crítica com carga intensificada. API-01 e MOB-01 entram em Jul. Volume mensal chega a 4.288 h (recorde até aqui).

### 2025 — Sprint Final e Crises

| Ciclo     | Horas válidas | Projetos | Colaboradores | Quarentena / Crises |
|-----------|:-------------:|:--------:|:-------------:|:--------------------|
| Jan/2025  | 4.642 h       | 12       | 19            | — *(BI-01, MKT-01, IOT-01 iniciados; sobreaviso IOT-01 começa)* |
| Fev/2025  | 4.039 h       | 12       | 19            | —          |
| Mar/2025  | 4.288 h       | 12       | 19            | Q4 (horas negativas Sara) + **Crise TRF-01** (deadline regulatório: +2–2,5 h/dia × 8 dias para Beatriz, Juliana, Thiago) |
| Abr/2025  | 4.441 h       | 12       | 19            | —          |
| Mai/2025  | 4.441 h       | 12       | 19            | —          |
| Jun/2025  | 4.240 h       | 12       | 19            | — *(SEG-01 encerrado em Dez/2024 — dados zeraram)* |
| Jul/2025  | 4.445 h       | 12       | 19            | Q2 (futura: 20/07/2028) + Q6 (>24 h: Diego) |
| Ago/2025  | 4.058 h       | 12       | 19            | —          |
| Set/2025  | 4.250 h       | 12       | 19            | —          |
| Out/2025  | 4.451 h       | 12       | 19            | Q1 (99/10/2025) + I4 (duplicata Camila) |
| Nov/2025  | 4.054 h       | 12       | 19            | **Crise ERP-01** (go-live: +2–3 h/dia × 8–12 dias) + **Crise MOB-01** (launch: +2–3 h/dia × 7–10 dias) + **Crise BI-01** (year-end crunch: +3 h/dia × 12 dias) |
| Dez/2025  | 4.677 h       | 12       | 19            | **Crise ERP-01** (sprint final: +2–3,5 h × 8–15 dias — **maior pico da simulação**) + **Crise BI-01** (+4 h × 15 dias Thiago) |
| **Total** | **52.026 h**  |          |               | **7 linhas em quarentena · 4 meses de crise** |

> **Destaque 2025:** Ano mais intenso — R$ 6,8 M em custo (33% do total). O ERP encerra em Dez/2025 com 108,9% de consumo, puxado pelas crises de Nov/Dez. O BI-01 também fecha over budget (108,1%) pelo crunch de ano. MOB-01 encerra em estado de warning (96,5%). TRF-01 tenta recuperação com sprint regulatório em Mar.

### 2026 — Ramp-up e Continuidade (dados até Mai/2026)

| Ciclo     | Horas válidas | Projetos | Colaboradores | Quarentena |
|-----------|:-------------:|:--------:|:-------------:|:----------:|
| Jan/2026  | 2.776 h       | 10       | 17            | — *(CLD-01 iniciado; ERP/BI/MOB/SEG/CRM/GOV/RH encerrados saem do portfolio)* |
| Fev/2026  | 2.611 h       | 10       | 18            | N1+I3 (Técnico Terceirizado) + I2 (Juliana 12+12 h) + **Crise IOT-01** (factory launch) + **Crise PLT-01** (go-live migração) |
| Mar/2026  | 2.796 h       | 10       | 17            | — + **Crise INF-01** (sprint final: +2 h × 6 dias Rodrigo) |
| Abr/2026  | 2.780 h       | 10       | 17            | Q5 (horas em branco Carlos) + I1 (Sáb 04/04 Leticia) |
| Mai/2026  | 2.526 h       | 10       | 17            | —          |
| **Subtotal** | **13.489 h** |        |               | **3 linhas em quarentena** |

> **Destaque 2026:** Portfólio enxuto com 10 projetos ativos. CLD-01 inicia em modo ramp-up (36% do budget consumido em 5 meses). INF-01 e PLT-01 em fase de estabilização. TRF-01 em sprint de recuperação. 7 projetos já encerrados saem da visão ativa.

---

## 5. Crises e Horas Extras Programadas

Crises simulam picos realistas de horas extras (campo `Hora extra = Sim`).

| Mês crise   | Projeto      | Colaborador(es) afetados        | H extra/dia | Dias | Motivo                          |
|-------------|--------------|--------------------------------|------------|------|---------------------------------|
| Abr/2024    | INF-01       | Rodrigo Andrade (+2h), Ana (+1,5h) | 1,5–2,0 | 6–8 | Sprint de integração             |
| Mar/2025    | TRF-01       | Beatriz (+2,5h), Juliana (+2h), Thiago (+2h) | 2,0–2,5 | 6–8 | Deadline regulatório            |
| Nov/2025    | ERP-01       | Marcos (+3h), Thiago (+2,5h), Carlos (+2h) | 2,0–3,0 | 8–9 | Go-live sprint                  |
| Nov/2025    | MOB-01       | Gabriel (+3h), Camila (+2,5h), Diego (+2h) | 2,0–3,0 | 7–10 | Launch sprint do app            |
| Nov/2025    | BI-01        | Thiago (+3h), Priscila (+2h)   | 2,0–3,0    | 10–12 | Year-end crunch                |
| Dez/2025    | ERP-01       | Marcos (+3,5h), Thiago (+3h), Carlos (+2,5h), Fernanda (+2h) | 2,0–3,5 | 8–15 | **Sprint final go-live** |
| Dez/2025    | BI-01        | Thiago (+4h), Priscila (+3h), Amanda (+2h) | 2,0–4,0 | 10–15 | Fechamento de ano over budget |
| Fev/2026    | IOT-01       | Lucas (+2,5h), Diego (+2h)     | 2,0–2,5    | 6–8  | Factory launch                  |
| Fev/2026    | PLT-01       | Juliana (+2h), Thiago (+1,5h)  | 1,5–2,0    | 6–7  | Go-live migração                |
| Mar/2026    | INF-01       | Rodrigo (+2h), Ana (+1,5h)     | 1,5–2,0    | 5–6  | Sprint final plataforma         |

---

## 6. Sobreaviso Programado

Campo `Hora sobreaviso = Sim`. Custo contabilizado a 33% da taxa horária normal.

| Projeto  | Colaborador     | Período             | Dias/mês | Horas/dia |
|----------|-----------------|---------------------|:--------:|:---------:|
| SUP-01   | Roberto Costa   | Jan/2022 – Dez/2026 | 3        | 2,0       |
| SUP-01   | Rafael Gomes    | Jan/2022 – Dez/2026 | 2        | 2,0       |
| IOT-01   | Lucas Pereira   | Jan/2025 – Dez/2026 | 3        | 3,0       |
| IOT-01   | Diego Martins   | Jul/2025 – Dez/2026 | 2        | 2,5       |
| INF-01   | Rodrigo Andrade | Jul/2025 – Dez/2026 | 1        | 2,0       |

---

## 7. Cobertura das Regras de Ingestão

Cada regra do sistema aparece em ao menos um mês específico, distribuído ao longo dos 53 timesheets.

| Código | Regra                              | Mês(es) de ocorrência                     | Colaborador/dado afetado           |
|--------|-------------------------------------|-------------------------------------------|-------------------------------------|
| **Q1** | Data com formato impossível (dia 99/32) | Set/2023, Out/2025                    | Carlos Oliveira (32/09), Priscila (99/10) |
| **Q2** | Data futura                         | Jun/2023, Jul/2025                        | Ana Ferreira (2028), Vinícius (2028) |
| **Q4** | Horas negativas                     | Fev/2023, Mar/2025                        | Pedro Carvalho (-3h), Sara Alves (-1,5h) |
| **Q5** | Campo de horas em branco            | Mai/2022, Ago/2024, Abr/2026              | João Silva, Amanda Torres, Carlos Oliveira |
| **Q6** | Horas > 24 em um dia                | Nov/2022, Jul/2025                        | Fernanda Lima (25,5h), Diego Martins (26h) |
| **Q8** | Colaborador com nome vazio          | Ago/2022, Dez/2024, *(linha extra 2026)*  | Linha sem nome no campo Colaborador |
| **I1** | Lançamento em dia de fim de semana  | Fev/2022, Fev/2023, Dez/2024, Abr/2026   | Rodrigo (Sáb), Leticia (Sáb), Diego (Sáb), Leticia (Sáb) |
| **I2** | Carga semanal excessiva (>14h+14h)  | Dez/2023, Fev/2026                        | Marcos Tavares (14+14h), Juliana Ramos (12+12h) |
| **I3** | Colaborador sem senioridade         | Dez/2023, Abr/2024, Fev/2026             | Estágio Rotativo, Consultor Freelance, Técnico Terceirizado |
| **I4** | Linha duplicada                     | Fev/2022, Ago/2024, Out/2025             | Marcos (dup INF-01), Gabriel (dup MOB-01), Camila (dup MKT-01) |
| **N1** | Novo colaborador (auto-criação)     | Dez/2023, Abr/2024, Fev/2026             | Junto com I3 acima — auto-criados sem seniority |

> **Resultado esperado após importação:** O sistema deve criar ~22 linhas de quarentena distribuídas em 16 dos 53 meses. Os 3 colaboradores externos (Estágio Rotativo, Consultor Freelance, Técnico Terceirizado) são auto-criados sem nível de senioridade — aparecerão no painel de equipe sem taxa associada.

---

## 8. Planos de Baseline (S-Curve)

570 linhas cobrindo os 17 projetos × seus respectivos meses de duração. A curva S segue:

- **Rampa inicial (20% dos ciclos):** crescimento linear de 0% até 100% da alocação mensal
- **Fase constante (60% dos ciclos):** alocação plena
- **Rampa de encerramento (20% dos ciclos):** redução linear até ~17% da alocação mensal

| Projeto     | Ciclos planejados | Budget h | Primeiro ciclo planejado | Último ciclo |
|-------------|:-----------------:|:--------:|--------------------------|--------------|
| INF-01      | 60                | 24.300   | Jan/2022                 | Dez/2026     |
| TRF-01      | 54                | 23.600   | Jul/2022                 | Dez/2026     |
| ERP-01      | 48                | 22.600   | Jan/2022                 | Dez/2025     |
| PLT-01      | 48                | 19.700   | Jan/2023                 | Dez/2026     |
| SEG-01      | 36                | 8.400    | Jan/2022                 | Dez/2024     |
| CRM-01      | 30                | 8.000    | Jan/2022                 | Jun/2024     |
| GOV-01      | 24                | 4.300    | Jan/2023                 | Dez/2024     |
| SUP-01      | 60                | 11.400   | Jan/2022                 | Dez/2026     |
| DAT-01      | 36                | 14.100   | Jan/2024                 | Dez/2026     |
| RH-01       | 18                | 5.800    | Jul/2023                 | Dez/2024     |
| API-01      | 30                | 7.900    | Jul/2024                 | Dez/2026     |
| INO-01      | 36                | 7.000    | Jan/2024                 | Dez/2026     |
| MOB-01      | 18                | 7.400    | Jul/2024                 | Dez/2025     |
| MKT-01      | 24                | 6.400    | Jan/2025                 | Dez/2026     |
| BI-01       | 12                | 4.500    | Jan/2025                 | Dez/2025     |
| IOT-01      | 24                | 7.700    | Jan/2025                 | Dez/2026     |
| CLD-01      | 12                | 5.300    | Jan/2026                 | Dez/2026     |

---

## 9. Cenários EVM e Interpretação no Sistema

| Cenário     | Projetos                                  | Budget = Consumo × | Leitura esperada                                          |
|-------------|-------------------------------------------|--------------------|-----------------------------------------------------------|
| ON TRACK    | INF-01, API-01                            | × 1,13             | CPI ≈ 1,0 · SPI ≈ 1,0 · Semáforo verde                  |
| BEHIND      | TRF-01, DAT-01, MKT-01                    | × 1,42             | SPI < 1 · progresso abaixo do planejado · semáforo amarelo |
| AHEAD       | PLT-01, IOT-01                            | × 1,35             | SPI > 1 · entregando mais rápido que o plano              |
| OVER BUDGET | ERP-01, BI-01                             | × 0,92             | CPI < 1 · consumo > budget · semáforo vermelho            |
| COMPLETED   | SEG-01, CRM-01, GOV-01, RH-01             | × 1,06             | Encerrados com ~94% consumido · status healthy            |
| WARNING     | SUP-01, MOB-01                            | × 1,04             | 94–96% consumido · semáforo amarelo próximo ao limite     |
| SPORADIC    | INO-01                                    | × 1,60             | Consumo baixo e irregular · lab interno / inovação        |
| RAMP-UP     | CLD-01                                    | × 2,80             | Apenas 36% consumido — projeto novo em aceleração         |

---

## 10. Instrução de Importação

Execute nessa ordem para garantir integridade referencial:

```
1. niveis_senioridade.csv  → Admin › Equipe › Importar Níveis de Senioridade
2. rate_cards.csv          → Admin › Equipe › Importar Rate Cards
3. ciclos.csv              → Admin › Ciclos › Importar CSV
4. projetos.csv            → Admin › Projetos › Importar CSV
5. planos_baseline.csv     → Admin › Projetos › [cada PEP] › Importar Baseline
                             (ou use o endpoint POST /api/projects/{id}/plans/import)
6. timesheets/2022-01.csv  → Upload Timesheet
   timesheets/2022-02.csv  → Upload Timesheet
   ...
   timesheets/2026-05.csv  → Upload Timesheet
   (53 arquivos, sempre na ordem cronológica)
```

> **Atenção:** os timesheets devem ser importados mês a mês em ordem crescente para que o cálculo de EVM acumulado (SPI/CPI ao longo dos ciclos) produza a curva S-real correta no gráfico de Previsão.

---

## 11. O que verificar após importação

| Verificação                                  | Local no sistema                                   | Resultado esperado                         |
|----------------------------------------------|----------------------------------------------------|--------------------------------------------|
| Semáforo do portfólio                        | Dashboard › barra de semáforo                      | 2 vermelhos, 3 amarelos, 9 verdes, 3 ramp  |
| Projetos over budget                         | Admin › Projetos › coluna Budget                   | ERP-01 e BI-01 com badge "Estourado"       |
| Projetos em warning                          | Admin › Projetos                                   | SUP-01 e MOB-01 com badge "Atenção ≥90%"  |
| Linhas em quarentena                         | Admin › Quarentena                                 | ~22 linhas pendentes (Q1–Q8, I1–I4, N1)   |
| Colaboradores sem senioridade                | Admin › Equipe                                     | 3 entradas: Estágio, Consultor, Técnico    |
| S-curve Previsão — INF-01                    | Dashboard › Previsão › selecionar 60IT-INF-01      | Curva S de 60 meses, atual ~88%            |
| S-curve Previsão — CLD-01                    | Dashboard › Previsão › selecionar 60IT-CLD-01      | Curva ramp-up, 5/12 meses, 36%            |
| Tendências (Trends chart)                    | Dashboard › Tendências                             | Crescimento de 1.165h/mês (Jan/22) para ~4.677h/mês (Dez/25) |
| Horas extras nos picos de crise              | Dashboard › filtrar Nov-Dez/2025                   | Pico ERP-01 visível no gráfico de esforço  |
| EVM R$ — portfólio completo                  | Dashboard › Saúde do Portfólio › botão R$          | Custo acumulado ~R$ 20,7 M                |
