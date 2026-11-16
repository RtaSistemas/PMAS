# PMAS — Documento-fonte para vídeo de apresentação

> Este documento é a única fonte para gerar o vídeo. Ele foi escrito a partir do código do sistema (versão 2.1.0).
> Cada afirmação sobre o sistema tem uma prova na Seção 8.

---

## 0. Instruções para a IA que gera o vídeo

**Objetivo.** Vídeo de apresentação comercial do PMAS (Project Management Assistant System).

**Público.** Diretores, gerentes de PMO e gerentes de projeto. Parte do público não conhece EVM.

**Ordem obrigatória.**
1. O problema de gestão (Seção 1).
2. O que é EVM e o que cada indicador significa (Seções 2 e 3).
3. Por que isso é útil para a organização e para a alta gestão (Seção 4).
4. O que o PMAS faz e como faz (Seções 5 e 6).
5. Fechamento (Seção 7).

**Tom.** Claro, direto, profissional. Explique cada sigla na primeira vez que ela aparece. Use o exemplo numérico da Seção 3.

**Regras de fidelidade (obrigatórias).**
- Use somente fatos deste documento. Não invente números, clientes, depoimentos, prêmios, certificações nem percentuais de ganho.
- Não prometa resultados ("reduz custos em X%"). Descreva o que o sistema calcula e mostra.
- Respeite a Seção 9 ("O que não afirmar").
- Quando falar de previsões, diga que são projeções calculadas a partir do histórico, não garantias.
- Idioma do vídeo: português do Brasil.

---

## 1. O problema

Em muitas organizações, as horas trabalhadas ficam em um sistema de apontamento. Esse sistema sabe quem trabalhou, quando e em qual projeto. Ele não responde às perguntas que a gestão faz:

- O projeto está gastando mais ou menos do que deveria para o que já foi entregue?
- O projeto está adiantado ou atrasado em relação ao plano?
- Se o ritmo atual continuar, quanto o projeto vai custar no final?
- Em quanto tempo o orçamento acaba?
- Quais projetos do portfólio precisam de atenção agora?

Comparar apenas "gasto real" com "orçamento" não responde a essas perguntas. Um projeto pode ter gasto 50% do orçamento e estar bem (se entregou 60% do trabalho) ou estar mal (se entregou 30%). Falta uma terceira medida: quanto valeu o trabalho já realizado. Essa medida é a base do EVM.

---

## 2. O que é EVM

**EVM** significa *Earned Value Management*, em português **Gerenciamento do Valor Agregado**. É um método que integra escopo, prazo e custo em um único conjunto de medidas.

**Referências do método** (fontes públicas):
- *Guia PMBOK*, do Project Management Institute (PMI), que descreve o Gerenciamento do Valor Agregado.
- Norma **ANSI/EIA-748**, que define critérios para sistemas de EVM.
- *Earned Schedule* (Prazo Agregado), extensão do método publicada por Walt Lipke em 2003.
- *AgileEVM*, adaptação do método para projetos ágeis publicada por Sulaiman, Barton e Blackburn em 2006.

### As quatro medidas de base

| Sigla | Nome | O que é |
|---|---|---|
| **BAC** | Budget at Completion — Orçamento no Término | O orçamento total aprovado do projeto. |
| **PV** | Planned Value — Valor Planejado | O valor do trabalho que o plano previa até hoje. |
| **EV** | Earned Value — Valor Agregado | O valor orçado do trabalho que foi realizado até hoje. |
| **AC** | Actual Cost — Custo Real | O que foi gasto de fato até hoje. |

A ideia central: **EV** traduz "trabalho feito" em dinheiro, usando os valores do orçamento. Com isso, é possível comparar o trabalho feito com o custo (EV contra AC) e com o plano (EV contra PV).

---

## 3. Os indicadores, um por um

Todos os indicadores abaixo são calculados pelo PMAS. As fórmulas são as que estão no código do sistema.

### Exemplo usado em todo o vídeo

Um projeto tem orçamento (BAC) de **R$ 100.000** e **1.000 horas** orçadas.
Até hoje: o plano previa **500 horas**; a equipe consumiu **400 horas**; o custo real (AC) é **R$ 48.000**.
Valor agregado (EV) = 400 ÷ 1.000 × R$ 100.000 = **R$ 40.000**.

### 3.1 Indicadores de situação atual

| Indicador | Fórmula | No exemplo | Como ler | Pergunta que responde |
|---|---|---|---|---|
| **CV** — Variação de Custo | EV − AC | 40.000 − 48.000 = **− R$ 8.000** | Negativo: gastou mais do que o valor entregue. | Quanto estamos acima ou abaixo do custo? |
| **SV** — Variação de Prazo (em horas) | horas realizadas − horas planejadas | 400 − 500 = **− 100 h** | Negativo: menos trabalho feito que o planejado. | Quanto estamos atrás ou à frente do plano? |
| **CPI** — Índice de Desempenho de Custo | EV ÷ AC | 40.000 ÷ 48.000 = **0,83** | Abaixo de 1: acima do custo. Acima de 1: abaixo do custo. | Cada real gasto está rendendo quanto? |
| **SPI** — Índice de Desempenho de Prazo | horas realizadas ÷ horas planejadas | 400 ÷ 500 = **0,80** | Abaixo de 1: atrasado. Acima de 1: adiantado. | O ritmo está de acordo com o plano? |

O PMAS escreve a leitura do indicador em linguagem comum. Para o exemplo, o sistema mostra:
- CPI 0,83 → **"Cada R$ 1,00 entregue custa R$ 1,20"**
- SPI 0,80 → **"Ritmo 20% abaixo do planejado"**

### 3.2 Indicadores de previsão

| Indicador | Fórmula | No exemplo | Como ler | Pergunta que responde |
|---|---|---|---|---|
| **EAC** — Estimativa no Término | BAC ÷ CPI | 100.000 ÷ 0,83 ≈ **R$ 120.000** | Custo final projetado se a eficiência atual continuar. | Quanto o projeto vai custar no final? |
| **EAC com prazo** | AC + (BAC − EV) ÷ (CPI × SPI) | 48.000 + 60.000 ÷ 0,667 = **R$ 138.000** | Projeção mais conservadora: considera também o atraso. | E se o atraso também pressionar o custo? |
| **ETC** — Estimativa para Terminar | EAC − AC | 120.000 − 48.000 = **R$ 72.000** | Quanto ainda falta gastar. | Quanto ainda precisamos desembolsar? |
| **VAC** — Variação no Término | BAC − EAC | 100.000 − 120.000 = **− R$ 20.000** | Negativo: estouro projetado. | De quanto será o estouro ou a economia? |
| **TCPI** — Índice de Desempenho para Terminar | (BAC − EV) ÷ (BAC − AC) | 60.000 ÷ 52.000 = **1,15** | Eficiência necessária daqui em diante para fechar no orçamento. | A meta de orçamento ainda é alcançável? |

Para o TCPI do exemplo, o PMAS mostra: **"Meta inviável no ritmo atual — exigiria 15% de ganho"**.
O sistema classifica o TCPI assim: até 1,00 "meta alcançável"; até 1,10 "meta apertada"; acima de 1,10 "meta inviável no ritmo atual".

### 3.3 Prazo Agregado (Earned Schedule)

O SPI clássico tem uma limitação conhecida: perto do fim do projeto ele tende a 1,0, mesmo quando o projeto termina atrasado. O **Prazo Agregado** resolve isso medindo o prazo em unidades de tempo.

| Indicador | Fórmula | Como ler |
|---|---|---|
| **ES** — Prazo Agregado | O momento do plano em que o valor planejado acumulado é igual ao EV atual | "O trabalho feito até hoje corresponde ao que o plano previa para o ciclo X." |
| **SPI(t)** | ES ÷ tempo decorrido | Abaixo de 1: atrasado, medido em tempo. |
| **SV(t)** | ES − tempo decorrido | Atraso ou adiantamento em número de ciclos. |
| **IEAC(t)** | duração planejada ÷ SPI(t) | Duração total projetada do projeto. |

Exemplo: passaram 4 ciclos, mas o trabalho feito equivale ao previsto para o ciclo 3,2. Então SPI(t) = 0,80. Se a duração planejada era de 8 ciclos, a duração projetada é 8 ÷ 0,80 = 10 ciclos.

---

## 4. Por que isso é útil para a organização e para a alta gestão

O método permite que a gestão:

1. **Veja o problema cedo.** CPI e SPI mostram o desvio enquanto o projeto ainda está em andamento, não só no fechamento.
2. **Compare projetos diferentes na mesma escala.** Um índice de 0,83 tem o mesmo significado em um projeto de R$ 100 mil e em um de R$ 10 milhões.
3. **Decida com base em projeção, não só em histórico.** EAC, VAC e TCPI respondem "onde vamos parar", não apenas "onde estamos".
4. **Separe problema de custo de problema de prazo.** Um projeto pode estar atrasado e barato, ou no prazo e caro. As ações são diferentes.
5. **Use uma linguagem comum.** Diretoria, PMO e gerentes passam a discutir os mesmos números, com a mesma definição.
6. **Priorize a atenção.** Com todos os projetos medidos do mesmo modo, é possível ordenar o portfólio por risco.

---

## 5. O que é o PMAS

O **PMAS** é um sistema web que transforma as planilhas de horas (timesheets) em painéis de gestão com EVM.

- A organização exporta as horas do seu sistema de apontamento em **CSV ou XLSX**.
- O PMAS importa o arquivo, valida os dados, calcula o custo e os indicadores de EVM.
- O gestor vê os resultados em painéis, por colaborador, por projeto e por ciclo de faturamento.

O PMAS não substitui o sistema de apontamento. Ele é uma camada de leitura e análise sobre os dados que já existem. Os dados entram somente por importação; não há digitação nem edição manual de horas dentro do PMAS.

---

## 6. O que o PMAS faz e como faz

### 6.1 Entrada de dados com controle

- **Importação de CSV e XLSX**, pela tela ou de forma automática.
- **Importação automática por chave de API:** um sistema externo envia o arquivo sem login, com uma chave criada pelo administrador. A chave vale somente para importação e pode ser revogada.
- **Motor de regras de validação:** cada linha passa por regras ordenadas e configuráveis. O sistema já vem com regras, por exemplo: mais de 24 horas em um dia vai para quarentena; horas negativas vão para quarentena; mais de 60 horas na semana gera aviso; lançamento em fim de semana gera aviso.
- **Quarentena:** a linha que falha em uma regra não é descartada nem contada. Ela fica em quarentena até um administrador aprovar ou rejeitar.
- **Datas fora de ciclo não se perdem:** uma data sem ciclo cadastrado vai para um ciclo de quarentena.
- **Rastreabilidade:** cada importação fica registrada com arquivo, usuário, data e contagem de linhas aceitas, ignoradas e em quarentena.

### 6.2 Custo real confiável

- **Tabela de taxas (rate card):** valor por hora por nível de senioridade, com período de validade.
- **Custo congelado na importação:** o custo de cada hora é calculado no momento da importação, com a taxa vigente na data do trabalho. Uma mudança de taxa posterior não altera o custo já registrado.
- **Tipos de hora:** horas normais, horas extras e horas de sobreaviso, com multiplicadores configuráveis (padrão: 1,5 para extra e 0,33 para sobreaviso).

### 6.3 Como o PMAS calcula o EVM

- **Uma única fonte de fórmulas.** Todas as fórmulas de EVM ficam em um único módulo do sistema. As telas não refazem cálculos; elas recebem os números prontos do servidor.
- **Valor agregado (EV).** Por padrão, o EV é estimado pela proporção entre horas consumidas e horas orçadas, multiplicada pelo orçamento. Quando o gestor informa o **percentual físico concluído** de um ciclo, o sistema usa esse percentual no lugar da estimativa por horas.
- **EV limitado ao orçamento.** O valor agregado nunca passa do orçamento total (BAC).
- **SPI por horas.** O índice de prazo compara horas realizadas com horas planejadas acumuladas (abordagem AgileEVM).
- **Orçamento de referência (baseline).** O gestor pode travar uma versão aprovada do orçamento. Quando existe uma baseline ativa, ela é o orçamento usado nos cálculos. O sistema guarda o histórico de revisões de orçamento.
- **Plano por ciclo.** O gestor cadastra horas e custo planejados por ciclo. Esse plano gera a curva de referência.
- **Divisão por zero tratada.** Quando falta um dado (por exemplo, projeto sem orçamento), o indicador aparece como "sem dado", não como um número enganoso.

### 6.4 O que o gestor vê

O sistema tem seis áreas: **Dashboard, Ciclos, Projetos, Equipe, Minha Área e Admin**. O Dashboard tem três visões e 14 gráficos:

**Esforço da Equipe**
- Horas por colaborador (normais, extras, sobreaviso), tendência por ciclo e composição de custo por tipo de hora.
- Detalhe por colaborador com linha do tempo e calendário.

**Saúde do Portfólio**
- **Mapa de árvore (treemap)** e **gráfico de bala (bullet)** com consumo contra orçamento, em horas ou em reais.
- **Tabela de fôlego (runway):** para cada projeto, média por ciclo, ciclos restantes até o fim do orçamento, SPI, CPI e risco.
- **Risco de concentração:** mostra quando um projeto depende demais de uma só pessoa. O sistema classifica como risco alto quando um colaborador responde por 60% ou mais das horas, e médio a partir de 40%.
- **Matriz de alocação:** horas por colaborador e por projeto.

**Previsão (por projeto)**
- Cartões com CPI, SPI, EAC, TCPI, VAC, CV e SV, cada um com cor e frase de leitura.
- Indicadores de Prazo Agregado: ES, SPI(t), SV(t) e IEAC(t).
- Curva S e gráfico de burn-up: planejado contra realizado.
- **Faixa de incerteza:** cenário otimista e pessimista, calculados com o melhor e o pior ritmo dos últimos 3 ciclos.

**Semáforo do portfólio**
- Uma barra no topo mostra cada projeto em verde, amarelo, vermelho ou cinza.
- Verde: consumo abaixo de 90% do orçamento. Amarelo: de 90% a 99%. Vermelho: 100% ou mais. Cinza: sem orçamento definido. Os limites são configuráveis.
- Um clique no projeto abre o detalhe.

### 6.5 Simulações

- **Cenário "E se?" (What-If):** o gestor altera o ritmo (multiplicador de velocidade) ou soma horas extras por ciclo. O sistema recalcula ciclos até a conclusão, custo final projetado e o gráfico de burn-up.
- **Simulação de Monte Carlo:** o sistema roda 1.000 simulações por padrão (configurável de 100 a 10.000), sorteando o ritmo de cada ciclo a partir da média e da variação do histórico do projeto. O resultado mostra três cenários de prazo — **P10, P50 e P90** — e um histograma. P50 é o resultado mediano; P90 é um prazo que 90% das simulações cumpriram. A simulação exige pelo menos dois ciclos com horas registradas.

### 6.6 Alertas automáticos

Depois de cada importação, o sistema verifica os projetos afetados e cria alertas:

- **Alerta de orçamento:** quando o consumo atinge o limite de atenção (padrão 90%) ou o limite crítico (padrão 100%).
- **Alerta de risco de prazo:** quando o SPI fica abaixo do limite (padrão 0,85) por ciclos consecutivos (padrão 2 ciclos).
- Os alertas não se repetem para o mesmo problema e **se encerram sozinhos** quando o indicador se recupera.
- O usuário recebe notificações em uma bandeja no sistema. O administrador tem uma central de alertas com filtros.

### 6.7 Governança

- **Perfis:** administrador e usuário.
- **Acesso por projeto:** cada usuário pode ser limitado a uma lista de projetos. A limitação vale para os painéis e para a importação.
- **Log de auditoria:** registra quem fez o quê, incluindo criação e revogação de chaves de API e cada importação automática.
- **Ciclos fechados:** um ciclo fechado não aceita nova importação.

### 6.8 Uso e operação

- **Relatório impresso ou PDF:** a impressão sai com cabeçalho (logo, nome do relatório, data, usuário, filtros ativos) e numeração de páginas.
- **Exportação em CSV** das tabelas.
- **Primeiro uso guiado:** um checklist mostra os três passos iniciais (criar ciclo, cadastrar projeto, importar arquivo) com o progresso real.
- **Ajuda dentro do sistema** e glossário de EVM nos indicadores.
- **Idiomas:** português e inglês.
- **Identidade visual configurável:** logo, nome, cores e paleta dos gráficos.
- **Instalação:** executável único para Linux e para Windows, sem necessidade de instalar Python. Para Linux há um pacote com instalador, serviço que inicia com o servidor e backup diário automático.
- **Qualidade:** o projeto tem 750 testes automatizados de servidor, 37 testes de unidade de interface e 48 testes de ponta a ponta no navegador.

---

## 7. Fechamento sugerido

O PMAS usa os dados de horas que a organização já tem e aplica um método reconhecido — o Gerenciamento do Valor Agregado — para responder a três perguntas: **como estamos, para onde vamos e onde agir primeiro**. Os dados entram por importação controlada, o custo é congelado na origem, as fórmulas ficam em um único lugar, e cada indicador vem com uma leitura em linguagem comum.

---

## 8. Provas — onde cada afirmação está no código

| Afirmação | Prova (arquivo do repositório) |
|---|---|
| Fórmulas de CPI, SPI, EAC, EAC com prazo, ETC, VAC, TCPI, CV, SV | `backend/app/services/evm.py` (`compute_cpi`, `compute_spi`, `compute_eac`, `compute_eac_schedule`, `compute_etc`, `compute_vac`, `compute_tcpi`, `compute_cv`, `compute_sv`) |
| Frases "Cada R$ 1,00 entregue custa…", "Ritmo X% abaixo do planejado", "Meta inviável no ritmo atual…" | `evm.py` (`cpi_label`, `spi_label`, `tcpi_label`) |
| Faixas do TCPI (1,00 e 1,10) e cores de CPI e SPI (1,0 e 0,9) | `evm.py` (`tcpi_color`, `cpi_color`, `spi_color`) |
| EV por horas, limitado ao BAC | `evm.py` (`compute_ev_capped`) |
| EV por percentual físico quando informado | `backend/app/routers/v2/forecast.py` (`ev_source = "physical"` ou `"hours"`) |
| Prazo Agregado: ES, SPI(t), SV(t), IEAC(t) | `evm.py` (`compute_earned_schedule`, `compute_spi_t`, `compute_sv_t`, `compute_ieac_t`) |
| Baseline ativa tem precedência como orçamento | `evm.py` (`resolve_effective_budget`); `routers/baselines.py` |
| Fórmulas em um único módulo, verificado por teste | `tests/test_golden_rules.py`; `tests/test_evm_service.py` (110 testes) |
| Faixa de incerteza com os últimos 3 ciclos | `routers/v2/forecast.py` |
| Monte Carlo: 1.000 iterações padrão, 100 a 10.000, distribuição normal, P10/P50/P90, histograma, mínimo de 2 ciclos | `routers/v2/monte_carlo.py` |
| What-If: multiplicador de velocidade e horas extras por ciclo | `routers/v2/simulate.py` |
| Runway, risco e ciclos até o fim | `routers/v2/runway.py` |
| Risco de concentração: 60% alto, 40% médio | `evm.py` (`classify_concentration_risk`); `routers/v2/concentration.py` |
| Semáforo e limites de 90% e 100% configuráveis | `evm.py` (`classify_health`, `get_thresholds`); `frontend/tabs/header.js` |
| 14 gráficos em três visões | `frontend/app.js` (`CHARTS_PER_TAB`) |
| Custo congelado na importação; multiplicadores 1,5 e 0,33 | `evm.py` (`freeze_costs`); `services/ingestion.py` (`_lookup_rate`); `models.py` (`GlobalConfig`) |
| Regras de validação do sistema e quarentena | `backend/app/database.py` (`_seed_validation_rules`); `services/rule_engine.py`; `routers/quarantine.py` |
| Alertas de orçamento e de prazo, sem repetição e com encerramento automático; SPI 0,85 por 2 ciclos | `services/notifications_svc.py`; `models.py` (`spi_warning_threshold`, `spi_risk_consecutive_cycles`) |
| Chave de API só para importação, guardada como hash, revogável, auditada | `routers/api_keys.py`; `deps.py` (`get_upload_user`); `tests/test_api_keys.py` |
| Acesso por projeto e log de auditoria | `routers/acl.py`; `routers/v2/portfolio.py` (`_allowed_peps`); `audit.py` |
| Cabeçalho do relatório impresso | `frontend/tabs/print-report.js`; `frontend/style.css` (`@media print`) |
| Checklist de primeiro uso; ajuda; dois idiomas | `frontend/tabs/onboarding.js`; `frontend/help.html`; `frontend/lang/pt.js`, `en.js` |
| Executável Linux e Windows; pacote Linux com serviço e backup diário | `.github/workflows/release.yml`; `packaging/`; `docs/OPERATIONS.md` |
| Contagem de testes (execução local em 14/11/2026: 749 aprovados e 1 ignorado no servidor; 37; 48) | `tests/`; `tests/frontend/` |

---

## 9. O que não afirmar

Estas afirmações **não têm prova** e não devem aparecer no vídeo:

- **Resultados de clientes:** não há dados de clientes, casos de uso, depoimentos nem percentuais de economia.
- **Certificação:** o PMAS aplica fórmulas de EVM. Ele **não** é certificado nem declarado conforme com a norma ANSI/EIA-748.
- **Inteligência artificial:** o sistema não usa IA. As previsões são fórmulas de EVM e simulação estatística.
- **Integrações nativas:** não há conector pronto com ERP, Jira ou sistemas de ponto. A entrada é por arquivo CSV/XLSX, pela tela ou por chave de API.
- **Tempo real:** os números se atualizam a cada importação, não de forma contínua.
- **Aplicativo móvel:** é um sistema web. Não há aplicativo para celular.
- **Multiempresa (SaaS):** cada instalação atende uma organização.
- **Medição de progresso físico automática:** por padrão o valor agregado é estimado por horas. O percentual físico só é usado quando o gestor informa.
- **Garantia de previsão:** EAC, Monte Carlo e What-If são projeções baseadas no histórico.
- **Segurança:** não faça afirmações de segurança, conformidade legal ou proteção de dados.

---

## 10. Roteiro sugerido (cenas)

| Cena | Conteúdo | Seção |
|---|---|---|
| 1 | O problema: as horas existem, as respostas não. | 1 |
| 2 | O que é EVM: BAC, PV, EV, AC. | 2 |
| 3 | O exemplo de R$ 100.000: CPI 0,83 e SPI 0,80, com as frases de leitura. | 3.1 |
| 4 | Para onde vamos: EAC R$ 120.000, VAC, TCPI 1,15. | 3.2 |
| 5 | Prazo Agregado: prazo medido em tempo. | 3.3 |
| 6 | Por que a alta gestão ganha com isso (6 pontos). | 4 |
| 7 | O PMAS: do arquivo de horas ao painel. | 5 e 6.1 |
| 8 | Custo confiável e fórmulas em um só lugar. | 6.2 e 6.3 |
| 9 | Os painéis: equipe, portfólio, previsão e semáforo. | 6.4 |
| 10 | Simulações: What-If e Monte Carlo (P10, P50, P90). | 6.5 |
| 11 | Alertas, governança e operação. | 6.6 a 6.8 |
| 12 | Fechamento: como estamos, para onde vamos, onde agir primeiro. | 7 |
