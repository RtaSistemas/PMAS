# Changelog

Todas as mudanças relevantes do PMAS (Project Management Assistant System) são registradas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto adota versionamento por tag de release.

---

## [RC2.0] — 2026-06-03

Release de consolidação. Esta versão amadurece o produto para um candidato a release estável: toda a camada de análise (Saúde do Portfólio, Tendências, Previsão) passou a ser servida por uma API dedicada com os números de EVM já calculados no servidor, eliminando divergências de fórmula entre telas. Foram adicionadas ferramentas de projeção (What-If, Monte Carlo, Runway, Cronograma Conquistado) e o acabamento de dezenas de detalhes de interface.

A suíte de testes passou de 406 para **590 testes** (todos verdes), com **188 testes dedicados a EVM**.

### Added

- **Previsão probabilística (Monte Carlo):** nova projeção que simula milhares de cenários de conclusão e apresenta os marcos otimista (P10), central (P50) e pessimista (P90), com histograma e curva de referência para apoiar o planejamento de buffer.
- **Simulação What-If:** painel onde o gestor ajusta a velocidade da equipe e horas extras por ciclo e vê na hora quantos ciclos faltam, o custo projetado ao término e a curva de avanço (burn-up) resultante.
- **Runway do portfólio:** tabela que estima, por PEP, quantos ciclos faltam para concluir, a média de horas/custo por ciclo e o risco de cronograma (SPI) e custo (CPI).
- **Cronograma Conquistado (Earned Schedule):** novos indicadores de prazo baseados em tempo — Prazo Conquistado (ES), SPI(t), SV(t) e estimativa de duração ao término IEAC(t).
- **Percentual Físico Concluído:** opção de informar o avanço físico real por ciclo, usado como base do Valor Agregado quando disponível (no lugar da proxy por horas).
- **Linha de base (baseline) de orçamento:** é possível travar uma revisão aprovada de orçamento por projeto; quando ativa, ela passa a ser o orçamento autoritativo nas análises, com banner e selo indicando o uso.
- **Histórico de revisões de orçamento:** registro de todas as mudanças de orçamento (horas/custo), exibido como minigráfico (sparkline) de evolução.
- **Detecção de sobrealocação:** identificação de colaboradores que excedem a capacidade no período, com filtros, ordenação e exportação CSV.
- **Datas e situação do projeto:** projetos agora têm data de início, data prevista de término, data de conclusão e situação (em andamento / encerrado); projetos encerrados têm suas métricas congeladas no estado final.
- **Linha de tendência total** opcional no gráfico de esforço da equipe e melhorias de leitura nos cartões de indicadores.
- **Paginação padronizada** em todas as tabelas (Ciclos, Projetos/PEPs, Usuários, Log de Auditoria, Histórico de Importações, Quarentena, Senioridade e Rate Card).
- **Glossário EVM em tooltip** ampliado para os novos indicadores (What-If, Monte Carlo, ES/SPI(t)/SV(t)/IEAC(t), médias de velocidade).
- Filtro de situação e exportação CSV no Histórico de Importações.

### Changed

- **Toda a análise migrada para a API v2:** as telas de Esforço, Portfólio, Tendências e Previsão passaram a consumir endpoints `/api/v2/*`. As respostas chegam prontas para exibição — todos os índices de EVM (CPI, SPI, EAC, TCPI, VAC, CV, SV) são calculados uma única vez no servidor.
- **Fonte única de verdade para EVM:** todas as fórmulas de Valor Agregado foram centralizadas em um único módulo no backend, eliminando cálculos duplicados e divergências entre telas. O frontend não recalcula mais nenhum índice de EVM.
- **Semáforo do portfólio** passou a usar a API v2 e a permitir clique em um projeto para filtrar a aba Portfólio por aquele PEP.
- Reorganização da arquitetura de informação da aba Previsão (ordem dos cartões e painéis, gestão de baseline movida para a aba Projetos).
- Indicadores de variação (deltas) reposicionados como selo no canto superior dos cartões do portfólio.
- Eixo dos gráficos de quadrante CPI×SPI limitado a 2,0 para melhor leitura.
- Regras de janela de velocidade documentadas e padronizadas entre Previsão, Runway, What-If e Monte Carlo (cada uma usa uma janela própria, por desenho).

### Fixed

- Cartão de Variação de Prazo (SV) na Previsão estava formatado como R$ quando o valor é em horas.
- Indicadores de variação voltaram a aparecer nos cartões de hora extra/sobreaviso quando o período anterior era zero.
- Representação dos percentis P10/P50/P90 no histograma de Monte Carlo corrigida, com rótulos escalonados para não se sobreporem.
- Painel de quarentena pessoal (`Minha Área`) passou a filtrar corretamente pela situação de revisão.
- Diversos ajustes de UX em gráficos e cartões das abas Portfólio e Previsão (fontes, cores, espaçamentos, rótulos e cores aderentes ao tema).
- Remoção da linha de média móvel remanescente do gráfico de tendências (Queima de Horas).

### Documentation

- Adicionado o relatório de gate de release **RC2.0-GATE.md** (veredito GO, 0 bloqueadores) com auditoria completa de EVM e segurança.
- `CLAUDE.md` atualizado para refletir a camada v2, o módulo de EVM, os 20 modelos de dados e a nova suíte de 590 testes.
- Documentação das regras de janela de velocidade (Previsão / Runway / What-If / Monte Carlo).

### Security

- Verificação de acesso por PEP (ACL) aplicada de forma consistente a todos os endpoints de análise v2 e ao histórico de orçamento/quarentena.

### Known Issues

- **D1 — Credencial padrão `admin/admin`:** o primeiro acesso ainda não força a troca da senha padrão (mitigado por aviso no log; ferramenta self-hosted). Previsto para RC2.1.
- **D3 — Build apenas Windows:** o pipeline de release gera somente o executável Windows; Linux/macOS rodam a partir do código-fonte. Previsto para RC2.1.

---

## [v1.4.8] — Paginação e refinamento de tabelas

### Added
- Paginação em todas as tabelas de dados (Ciclos, Projetos/PEPs, Usuários, Log de Auditoria, Histórico, Senioridade e Rate Card), centralizada em um componente único.
- Filtro de situação e exportação CSV no Histórico de Importações.
- Botão de recolher/expandir no cartão de filtros do Dashboard.

### Fixed
- Modal de baseline alargado para melhor leitura.
- Ordem das colunas da tabela de Projetos e padronização da paginação de quarentena.
- Duplicidades dentro do mesmo arquivo passaram a ser registradas como informação (não erro).

---

## [v1.4.6 / v1.4.7] — Coerência de métricas EVM e revisão de especialista

### Changed
- Revisão de especialista (EVM/UX/implementação) endereçada em quatro frentes: base matemática, coerência de métricas, nomenclatura e polimento de UX.
- Variância de Prazo (SV) e SPI passaram a ser calculados em horas, não em R$.

### Added
- Presets de tema customizados com CRUD e importação/exportação CSV.
- Lógica de "fronteira de SPI congelado" extraída para o módulo de EVM (reuso entre Previsão e Runway).

### Removed
- Limpeza de documentos internos de trabalho (relatórios e propostas) que não pertenciam ao repositório do produto.

---

## [v1.4.4 / v1.4.5] — Consolidação arquitetural e início do EVM centralizado

### Changed
- Centralização das fórmulas de EVM e da resolução de orçamento em um módulo único de serviço.
- Classificação de saúde (verde/amarelo/vermelho) movida do frontend para o backend.
- Frontend modularizado: construtores de gráfico (Esforço, Portfólio, Previsão), glossário EVM e helpers de UX separados em arquivos próprios; padronização de CRUD de tabelas.

---

## [v1.4.1 → v1.4.3] — Acessibilidade, treemap dinâmico e auditoria EVM

### Added
- Auditoria completa de EVM e correções associadas: CV, TCPI, VAC e ETC adicionados à Previsão; CPI inline na Saúde do Portfólio; histórico de SPI por ciclo.
- Acessibilidade (WCAG): navegação por teclado no MultiSelect, textos alternativos em gráficos, papéis ARIA em abas e tokens de cor.
- Linha de base de planejamento (baseline S-curve) com importação/exportação CSV, modal, selo e banner.
- Altura dinâmica do treemap proporcional ao número de PEPs.

### Fixed
- Ponderação correta de horas extras/sobreaviso no numerador do Valor Agregado.
- Valor Agregado capado no orçamento (BAC), garantindo CPI < 1 em projetos estourados.

---

## [v1.4.0] — Base do produto

### Added
- Importação de timesheets CSV/XLSX com pipeline de ingestão multi-fase e motor de regras de validação configurável.
- Fluxo de quarentena para linhas que falham na validação (aprovar/rejeitar) e ciclos de quarentena automáticos para datas fora de período registrado.
- Padrão "EVM Freeze": custo por hora congelado no momento da importação.
- CRUD de Ciclos, Projetos/PEPs, Senioridade e Rate Cards, todos com importação/exportação CSV.
- Análises: Esforço da Equipe, Saúde do Portfólio (treemap + bullet, horas/R$), Tendências e Previsão (curva S).
- Autenticação JWT com bcrypt, controle de acesso por PEP (ACL), papéis admin/usuário e log de auditoria completo.
- Área "Minha Área" (preferências, histórico próprio, quarentena própria, alertas de orçamento), tema de UI configurável e suporte a i18n (pt-BR / en).

---

[RC2.0]: #rc20--2026-06-03
[v1.4.8]: #v148--paginação-e-refinamento-de-tabelas
[v1.4.6 / v1.4.7]: #v146--v147--coerência-de-métricas-evm-e-revisão-de-especialista
[v1.4.4 / v1.4.5]: #v144--v145--consolidação-arquitetural-e-início-do-evm-centralizado
[v1.4.1 → v1.4.3]: #v141--v143--acessibilidade-treemap-dinâmico-e-auditoria-evm
[v1.4.0]: #v140--base-do-produto
