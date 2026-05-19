/* PMAS — Frontend App */

// ---------------------------------------------------------------------------
// i18n
// ---------------------------------------------------------------------------
const _LANG = {
  pt: {
    'btn.import_ts':'⬆ Importar','btn.logout':'Sair','btn.lang':'EN',
    'tab.projects':'Projetos','tab.team':'Equipe','tab.my':'Minha Área',
    'filters.title':'Filtros','filter.cycle':'Ciclo','filter.pep_code':'PEP (Código)',
    'filter.pep_desc':'PEP (Descrição)','filter.collab':'Colaborador',
    'filter.dfrom':'Data início','filter.dto':'Data fim',
    'btn.load':'Carregar','btn.clear':'Limpar',
    'btn.last_month':'Últ. mês','btn.last_quarter':'Últ. trimestre','btn.this_year':'Este ano',
    'atab.effort':'Esforço da Equipe','atab.portfolio':'Saúde do Portfólio','atab.trends':'Tendências','atab.allocation':'Alocação','atab.forecast':'Previsão',
    'allocation.empty':'Nenhum dado encontrado para os filtros selecionados.',
    'allocation.collaborator':'Colaborador','allocation.total':'Total',
    'allocation.btn_h':'Horas','allocation.btn_r':'R$',
    'forecast.title':'Previsão de Conclusão (EVM)',
    'forecast.select_pep':'— selecione um PEP —',
    'forecast.empty':'Selecione um PEP para visualizar a previsão de conclusão.',
    'forecast.consumed':'Horas Consumidas','forecast.remaining':'Horas Restantes',
    'forecast.utilization':'Utilização','forecast.completion':'Conclusão Estimada',
    'forecast.realized':'Realizado','forecast.projection':'Projeção','forecast.budget_line':'Orçamento',
    'forecast.now_marker':'Atual',
    'forecast.pv_line':'VP (Valor Planejado)',
    'forecast.spi':'IDP / SPI','forecast.sv':'Variação de Prazo (SV)',
    'forecast.no_budget':'Sem orçamento cadastrado para este PEP.',
    'effort.empty':'Selecione um ciclo ou PEP nos filtros e clique em Carregar.',
    'btn.stacked':'Vista: Empilhada','btn.grouped':'Vista: Agrupada',
    'btn.export_csv':'⬇ Exportar CSV','budget.title':'Orçado vs. Realizado por PEP',
    'scatter.title':'Quadrante EVM — CPI × SPI',
    'scatter.note':'Eixo X = SPI (prazo) · Eixo Y = CPI (custo) · Referência em 1,0',
    'scatter.empty':'Nenhum dado de PEP disponível para os filtros selecionados.',
    'q.tr':'No prazo e no orçamento','q.tl':'Custo ok · Prazo em risco',
    'q.br':'Prazo ok · Custo em risco','q.bl':'Custo e prazo em risco',
    'portfolio.treemap_h':'Distribuição de Horas por PEP (Treemap)',
    'portfolio.treemap_r':'Custo Real por PEP (Treemap)',
    'portfolio.empty':'Nenhum dado de horas encontrado para os filtros selecionados.',
    'portfolio.note':'Blocos cinzas = PEP sem projeto cadastrado',
    'btn.view_hours':'Vista: Horas','btn.view_cost':'Vista: R$',
    'btn.view_cpi':'Ver: CPI por PEP','btn.hide_cpi':'Ocultar CPI por PEP',
    'bullet.title':'Orçado vs. Realizado — Bullet Chart',
    'pepcpi.title':'CPI por PEP ao longo dos Ciclos',
    'pepcpi.note':'Orçamento / Custo Real por ciclo · Linha de referência em 1.0 · Requer orçamento (R$) nos projetos',
    'pepcpi.empty':'Sem dados de orçamento. Defina o orçamento (R$) nos projetos para habilitar o rastreamento de CPI.',
    'cpi.zone_critical':'Crítico < 0,9','cpi.zone_warning':'Atenção 0,9–1,0',
    'trends.title':'Queima de Horas por Ciclo','trends.pep_lbl':'PEP:',
    'trends.all':'Todos',
    'trends.empty':'Nenhum dado encontrado. Importe timesheets e crie ciclos para visualizar tendências.',
    'cycles.title':'Ciclos cadastrados','btn.new_cycle':'+ Novo ciclo',
    'cycles.search_ph':'Buscar por nome de ciclo…',
    'cycles.th.name':'Nome','cycles.th.start':'Início','cycles.th.end':'Fim',
    'cycles.th.type':'Tipo','cycles.th.recs':'Registros',
    'projects.title':'Projetos / PEPs','btn.new_project':'+ Novo projeto',
    'projects.search_ph':'Buscar por PEP, nome ou cliente…',
    'projects.th.pep':'Código PEP','projects.th.name':'Nome do Projeto',
    'projects.th.client':'Cliente','projects.th.mgr':'Gerente',
    'projects.th.budget':'Orçamento (h)','projects.th.status':'Status',
    'seniority.title':'Níveis de Senioridade','seniority.th.name':'Nome',
    'btn.new_seniority':'+ Novo nível',
    'ratecard.title':'Tabela de Taxas (Rate Card)','btn.new_ratecard':'+ Nova taxa',
    'ratecard.th.level':'Nível','ratecard.th.rate':'Valor/hora (R$)',
    'ratecard.th.from':'Vigência início','ratecard.th.to':'Vigência fim',
    'config.title':'Fatores Globais de Custo',
    'config.extra_lbl':'Multiplicador — Hora Extra',
    'config.standby_lbl':'Multiplicador — Hora Sobreaviso',
    'config.anomaly_lbl':'Máx. Horas/Dia (Alerta Anomalia)',
    'btn.save_config':'Salvar fatores',
    'team.title':'Colaboradores','btn.assign_all':'Atribuir a todos',
    'team.th.name':'Nome','team.th.seniority':'Senioridade','team.th.rate':'Taxa atual (R$/h)',
    'admin.title':'Gestão de Usuários','btn.new_user':'+ Novo usuário',
    'user.th.user':'Usuário','user.th.role':'Perfil',
    'btn.cancel':'Cancelar','btn.save':'Salvar','btn.edit':'Editar','btn.delete':'Excluir',
    'btn.export_csv2':'⬇ Exportar CSV','btn.import_csv':'⬆ Importar CSV',
    'cm.title_new':'Novo Ciclo','cm.title_edit':'Editar Ciclo',
    'cm.name_lbl':'Nome *','cm.name_ph':'Ex: Janeiro/2026',
    'cm.start_lbl':'Data início *','cm.end_lbl':'Data fim *',
    'pm.title_new':'Novo Projeto','pm.title_edit':'Editar Projeto',
    'pm.pep_lbl':'Código PEP *','pm.pep_ph':'Ex: 60OP-03333','pm.status_lbl':'Status',
    'pm.name_lbl':'Nome do Projeto','pm.name_ph':'Nome descritivo',
    'pm.client_lbl':'Cliente','pm.client_ph':'Nome do cliente',
    'pm.mgr_lbl':'Gerente','pm.mgr_ph':'Nome do gerente',
    'pm.bh_lbl':'Orçamento de horas','pm.bc_lbl':'Orçamento (R$)',
    'opt.ativo':'Ativo','opt.suspenso':'Suspenso','opt.encerrado':'Encerrado',
    'sm.title_new':'Novo Nível de Senioridade','sm.name_lbl':'Nome *','sm.name_ph':'Ex: Pleno, Sênior',
    'rm.title_new':'Nova Taxa','rm.level_lbl':'Nível de Senioridade *',
    'rm.rate_lbl':'Valor/hora (R$) *','rm.rate_ph':'Ex: 120.00',
    'rm.from_lbl':'Vigência início *','rm.to_lbl':'Vigência fim (opcional)',
    'as.title':'Atribuir Senioridade','as.level_lbl':'Nível de Senioridade',
    'as.none_opt':'— Sem senioridade —',
    'um.title':'Novo Usuário','um.user_lbl':'Usuário *','um.user_ph':'mínimo 3 caracteres',
    'um.pwd_lbl':'Senha *','um.pwd_ph':'mínimo 6 caracteres','um.role_lbl':'Perfil',
    'opt.user':'Usuário',
    'pwdm.title':'Alterar Senha','pwdm.new_lbl':'Nova senha *','pwdm.new_ph':'mínimo 6 caracteres',
    'ch.normal_h':'Horas Normais','ch.extra_h':'Horas Extras','ch.standby_h':'Sobreaviso',
    'ch.budget':'Orçado','ch.actual':'Realizado','ch.hours':'Horas','ch.cost':'Custo (R$)',
    'ch.cycle_axis':'Ciclo','ch.cost_axis':'Custo Real (R$)',
    'badge.quarantine':'Quarentena','badge.regular':'Regular',
    'title.lock':'Bloquear ciclo','title.unlock':'Desbloquear ciclo',
    'title.archive':'Arquivar ciclo','title.restore':'Restaurar ciclo',
    'cycles.show_archived':'Mostrar arquivados',
    'anomaly.title':'⚠ Alertas de Anomalia na Importação',
    'stat.normal_h':'Horas Normais','stat.extra_h':'Horas Extras','stat.standby_h':'Sobreaviso',
    'stat.total':'Total','stat.collabs':'Colaboradores',
    'stat.budgeted':'Orçado (PEPs c/ orçamento)','stat.vs_budget':'Realizado vs Orçado',
    'stat.cost_normal':'Custo Horas Normais','stat.cost_extra':'Custo Horas Extras',
    'stat.cost_standby':'Custo Sobreaviso','stat.cost_total':'Custo Total Real',
    'stat.peps_active':'PEPs Ativos','stat.budget_cost':'Orçamento (R$)',
    'stat.vs_budget_cost':'Realizado vs Orçado',
    'budget.exceeded':'Estourado','budget.warning':'Atenção',
    'config.warning_threshold_lbl':'Limiar de Atenção (0–1)',
    'config.critical_threshold_lbl':'Limiar Crítico (0–1)',
    'lbl.admin':'Admin','lbl.user':'Usuário',
    'loading':'Carregando…','no_cycles':'Nenhum ciclo encontrado.',
    'no_projects':'Nenhum projeto encontrado.','no_seniority':'Nenhum nível cadastrado.',
    'no_rates':'Nenhuma taxa cadastrada.','no_team':'Nenhum colaborador encontrado.',
    'no_users':'Nenhum usuário encontrado.',
    'btn.assign':'Atribuir','btn.pwd':'Senha',
    'ch.actual_cost':'Custo Real',
    'tt.over_budget':'Acima do orçado','tt.utilization':'Utilização','tt.total_hours':'Total horas',
    'tt.project':'Projeto','tt.consumed':'Consumido','tt.actual_cost_lbl':'Custo real',
    'tt.utilized':'utilizado','tt.pep_not_reg':'⚠ PEP não cadastrado',
    'collab.timeline_title': 'Evolução por Ciclo — ',
    'collab.timeline_empty': 'Nenhum dado encontrado para este colaborador.',
    'collab.calendar_empty': 'Sem atividade neste mês.',
    'collab.section_cycles': 'Horas por Ciclo',
    'collab.section_calendar': 'Atividade Diária',
    'cal.stat.total': 'Total',
    'cal.stat.active_days': 'Dias ativos',
    'cal.stat.avg_day': 'Média/dia',
    'cal.stat.peak': 'Pico',
    'cal.stat.quarantine': '⚠ Em quarentena',
    'cal.months': ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'],
    'cal.day_names': ['Dom','Seg','Ter','Qua','Qui','Sex','Sáb'],
    'cal.week_range': '(Domingo - Sábado)',
    'auditlog.title':'Log de Auditoria','btn.refresh':'↺ Atualizar',
    'auditlog.filter.all_entity':'Todas entidades','auditlog.filter.all_action':'Todas ações',
    'auditlog.th.when':'Quando','auditlog.th.user':'Usuário','auditlog.th.action':'Ação',
    'auditlog.th.entity':'Entidade','auditlog.th.id':'ID','auditlog.th.detail':'Detalhe',
    'no_audit':'Nenhum evento registrado.',
    'cpi.title':'IDP — Índice de Desempenho de Custo por Ciclo',
    'toolbox.save':'Salvar Imagem','toolbox.restore':'Restaurar','toolbox.data_view':'Ver Dados',
    'toolbox.data_view_lang':['Dados do Gráfico','Fechar','Atualizar'],
    'toolbox.zoom':'Zoom','toolbox.zoom_back':'Desfazer Zoom',
    'toolbox.stack':'Empilhado','toolbox.tiled':'Lado a Lado',
    'plan.title':'Baseline de Planejamento (Horas/Ciclo)',
    'plan.btn_add':'+ Adicionar ciclo','plan.btn_export':'↓ Exportar CSV','plan.btn_import':'↑ Importar CSV',
    'plan.hint':'Define as horas planejadas por ciclo para calcular VP, IDP e Variação de Prazo.',
    'plan.th.cycle':'Ciclo','plan.th.hours':'Horas Planejadas',
    'plan.select_cycle':'— selecione um ciclo —','plan.no_plans':'Nenhum baseline definido.',
    'plan.modal_title':'Adicionar ciclos ao baseline',
    'plan.modal_hint':'Selecione os ciclos e defina as horas planejadas. Ciclos já com baseline não são listados.',
    'plan.modal_add_row':'+ Mais um ciclo',
    'myarea.upload':'Importação de Arquivo','myarea.history':'Histórico de Importações',
    'myarea.quarantine':'Quarentena',
    'upload.inserted':'registros inseridos','upload.skipped':'duplicatas ignoradas',
    'upload.quarantine':'registros em quarentena','upload.warnings':'avisos','upload.infos':'informações',
    'history.th.when':'Quando','history.th.file':'Arquivo','history.th.inserted':'Inseridos',
    'history.th.skipped':'Ignorados','history.th.quarantine':'Quarentena',
    'history.th.warnings':'Avisos','history.th.status':'Status',
    'history.status.ok':'✅ OK','history.status.warnings':'⚠️ Com avisos',
    'history.status.quarantine':'🔒 Com quarentena','history.status.rejected':'❌ Rejeitado',
    'qr.th.date':'Data','qr.th.collaborator':'Colaborador','qr.th.hours':'Horas',
    'qr.th.pep':'PEP','qr.th.reason':'Motivo','qr.th.type':'Tipo',
    'qr.th.reviewed':'Revisado','qr.th.sent_by':'Enviado por',
    'qr.type.structural':'Estrutural','qr.type.rule':'Regra',
    'qr.btn.export':'⬇ Exportar CSV','qr.btn.review':'✅ Marcar revisado',
    'qr.btn.discard':'🗑 Descartar','qr.filter.pending':'Apenas pendentes',
    'qr.btn.detail':'🔍 Detalhar',
    'qr.btn.approve':'✅ Aprovar','qr.btn.reject':'❌ Rejeitar',
    'qr.status.pending':'⏳ Pendente','qr.status.approved':'✅ Aprovado','qr.status.rejected':'❌ Rejeitado',
    'qr.modal.title':'Registro em Quarentena #','qr.modal.collab':'Colaborador',
    'qr.modal.date':'Data','qr.modal.hours':'Horas','qr.modal.pep':'PEP',
    'qr.modal.extra':'Hora Extra','qr.modal.standby':'Sobreaviso',
    'qr.modal.reason':'Motivo','qr.modal.rule':'Regra violada',
    'qr.modal.session':'Sessão de Importação','qr.modal.status':'Status',
    'qr.modal.reviewed_by':'Revisado por','qr.modal.raw':'Dados brutos',
    'alerts.th.rule':'Regra','alerts.th.occurrences':'Ocorrências',
    'alerts.th.last':'Último disparo','alerts.th.action':'Ação','alerts.th.trend':'Tendência',
    'vr.title':'Regras de Validação','vr.btn.new':'+ Nova Regra',
    'vr.th.order':'Ordem','vr.th.field':'Campo','vr.th.operator':'Operador',
    'vr.th.value':'Valor','vr.th.action':'Ação','vr.th.description':'Descrição',
    'vr.th.active':'Ativa','vr.th.system':'Sistema',
    'vr.badge.system':'Sistema','vr.hint.aggregate':'Regras de agregado permitem apenas info ou warning.',
    'vr.system_hint':'Regras de sistema (🔒) não podem ser editadas ou excluídas, mas podem ser ativadas/desativadas.',
    'vr.empty':'Nenhuma regra cadastrada.',
    'vr.modal.new':'Nova Regra de Validação','vr.modal.edit':'Editar Regra',
    'vr.btn.activate':'Ativar','vr.btn.deactivate':'Desativar',
    'vr.saved':'Regra salva.',
    'vr.desc_ph':'Descrição legível da regra','vr.value_ph':'Ex: 24 ou 5,6',
    'opt.yes':'Sim','opt.no':'Não',
    'pwdm.current_lbl':'Senha atual *','pwdm.current_ph':'senha atual',
    'prefs.customize':'⚙ Personalizar Layout','prefs.save':'Salvar preferências',
    'prefs.saved':'Preferências salvas.','prefs.save_error':'Erro ao salvar preferências.',
    'prefs.restore':'Restaurar padrão','prefs.visible':'Visível','prefs.grid_cols':'Colunas',
    'size.small':'Pequeno','size.medium':'Médio','size.large':'Grande','size.full':'Largura total',
    'chart.effortChart':'Esforço por Colaborador','chart.trendsChart':'Tendências por Ciclo',
    'chart.cpiChart':'CPI por Ciclo','chart.pepCpiChart':'CPI por PEP',
    'chart.treemapChart':'Treemap de Portfólio','chart.bulletChart':'Orçado vs Realizado',
    'chart.scatterChart':'Dispersão Custo × Horas','chart.forecastChart':'Previsão de Conclusão',
    'appearance.title':'Aparência do Sistema','appearance.app_name':'Nome do sistema',
    'appearance.logo':'Logo','appearance.logo_upload':'⬆ Enviar novo logo',
    'appearance.logo_remove':'🗑 Remover logo','appearance.density':'Densidade',
    'appearance.density.compact':'Compacto','appearance.density.normal':'Normal',
    'appearance.density.relaxed':'Espaçado','appearance.colors':'Cores',
    'appearance.palette':'Paleta de gráficos','appearance.presets':'Paletas predefinidas',
    'appearance.preset.pmas':'● Padrão PMAS','appearance.preset.corporate':'● Azul Corporativo',
    'appearance.preset.high_contrast':'● Alto Contraste',
    'appearance.restore':'Restaurar padrões','appearance.save':'Salvar aparência',
    'appearance.saved':'Aparência salva com sucesso.',
    'login.user_lbl':'Usuário','login.user_ph':'usuário',
    'login.pwd_lbl':'Senha','login.pwd_ph':'senha',
    'login.btn':'Entrar',
    'btn.close':'Fechar',
    'session.title':'Detalhes da Importação',
    'session.warnings':'⚠ Avisos','session.infos':'ℹ Informações',
    'myarea.profile':'Perfil','myarea.profile_title':'Meu Perfil',
    'myarea.change_pwd':'Alterar senha',
    'myarea.layout_title':'Layout do Dashboard',
    'myarea.layout_save':'Salvar layout',
    'myarea.layout_hint':'Arraste para reordenar os painéis do dashboard.',
    'myarea.upload_hint':'Importe um arquivo CSV ou XLSX de timesheets.',
    'myarea.history_hint':'Clique em uma linha para ver o detalhe completo de avisos e informações.',
    'myarea.quarantine_hint':'Registros em quarentena. Clique para ver detalhes.',
    'history.th.sent_by':'Enviado por','history.th.infos':'Infos',
    'qr.th.ingested':'Data reg.','qr.th.status':'Status',
    'config.timezone_lbl':'Fuso horário',
    'acl.title':'Controle de Acesso',
    'acl.hint':'Usuários com permissão explícita para importar timesheets neste projeto. Admins têm acesso irrestrito.',
    'acl.granted':'Acessos concedidos',
    'acl.add_user':'Adicionar usuário',
    'btn.grant':'Conceder','btn.revoke':'Revogar',
    'ms.cycle_ph':'— Selecione ciclo(s) —','ms.pep_ph':'— Todos os PEPs —',
    'ms.pep_desc_ph':'— Todas as descrições —','ms.collab_ph':'— Todos —',
    'ms.select_ph':'— selecione —',
    'msg.load_before_export':'Carregue dados antes de exportar.',
    'msg.no_cycles_export':'Nenhum ciclo para exportar.',
    'msg.no_projects_export':'Nenhum projeto para exportar.',
    'msg.no_levels_export':'Nenhum nível para exportar.',
    'msg.no_rates_export':'Nenhuma taxa para exportar.',
    'msg.no_baseline_export':'Nenhum baseline para exportar.',
    'msg.fields_required':'Preencha todos os campos obrigatórios.',
    'msg.pep_required':'Código PEP é obrigatório.',
    'msg.positive_numbers':'Os valores devem ser números positivos.',
    'msg.config_saved':'Fatores salvos com sucesso.',
    'msg.invalid_credentials':'Credenciais inválidas.',
    'msg.connection_error':'Erro de conexão. Tente novamente.',
    'msg.pwd_changed':'Senha alterada com sucesso.',
    'msg.pwd_fill_all':'Preencha todos os campos.',
    'msg.user_not_found':'Usuário não encontrado.',
    'msg.name_required':'Nome é obrigatório.',
    'msg.select_user':'Selecione um usuário.',
    'msg.rule_reorder_error':'Erro ao reordenar regras.',
    'msg.select_cycle_all':'Selecione um ciclo em todas as linhas.',
    'msg.duplicate_cycle':'Ciclo duplicado na lista.',
    'msg.valid_hours':'Informe horas válidas (≥ 0) em todas as linhas.',
    'msg.all_baseline_set':'Todos os ciclos já têm baseline definido.',
    'msg.baseline_removed':'Linha removida.',
    'msg.pep_not_registered':'(PEP não cadastrado)',
    'msg.no_import_sessions':'Nenhuma importação registrada.',
    'msg.no_quarantine':'Nenhum registro em quarentena.',
    'msg.no_access_granted':'Nenhum acesso concedido.',
    'msg.no_warnings_infos':'Sem avisos ou informações adicionais.',
    'msg.user_created':'Usuário criado com sucesso.',
    'msg.seniority_title':'Senioridade — ','msg.acl_title':'Acesso — ',
    'msg.pwd_field_required':'Informe a nova senha.',
    'confirm.delete_cycle':'Excluir o ciclo?','confirm.delete_project':'Excluir o projeto?',
    'confirm.delete_user':'Excluir este usuário?',
    'confirm.delete_level':'Excluir este nível?',
    'confirm.revoke_access':'Revogar acesso deste usuário?',
    'confirm.assign_all':'Atribuir esta senioridade a TODOS os colaboradores?',
    'confirm.remove_baseline':'Remover esta linha do baseline?',
    'page.label':'Página','page.of':'de',
    'sm.title_edit':'Editar Nível','rm.title_edit':'Editar Taxa',
    'runway.title':'Runway do Portfólio',
    'runway.note':'Ciclos restantes no ritmo atual · apenas PEPs com orçamento',
    'runway.empty':'Nenhum PEP com orçamento encontrado.',
    'runway.th.pep':'PEP','runway.th.project':'Projeto','runway.th.consumed':'Consumido (h)',
    'runway.th.progress':'Progresso','runway.th.avg':'Média/ciclo',
    'runway.th.cycles':'Ciclos restantes','runway.th.completion':'Conclusão estimada',
    'runway.overrun':'Estourado','runway.no_budget':'Sem orçamento',
    'runway.th.spi':'SPI','runway.th.status':'Status',
    'runway.status.on_track':'No prazo','runway.status.at_risk':'Atenção',
    'runway.status.behind':'Atrasado','runway.status.no_baseline':'Sem baseline',
    'costcomp.title':'Composição de Custo por Tipo de Hora',
    'costcomp.note':'Custo de horas regulares · extras · sobreaviso por ciclo',
    'costcomp.empty':'Nenhum dado de custo encontrado.',
    'conc.title':'Concentração de Risco por Projeto',
    'conc.note':'% de horas por colaborador · ⚠ risco quando um único colaborador detém >60%',
    'conc.empty':'Nenhum dado de horas encontrado.',
    'conc.others':'Outros',
    'msg.pep_not_available': 'PEP não disponível para o seu perfil.',
    'msg.import_done':'Importação concluída',
    'msg.created_n':'criado(s)','msg.updated_n':'atualizado(s)','msg.errors_n':'erro(s)',
    'msg.qr_approved':'Registro aprovado e inserido.','msg.qr_rejected':'Registro rejeitado.',
    'confirm.lock_cycle':'Bloquear este ciclo?','confirm.unlock_cycle':'Desbloquear este ciclo?',
    'confirm.archive_cycle':'Arquivar este ciclo?','confirm.restore_cycle':'Restaurar este ciclo?',
  },
  en: {
    'btn.import_ts':'⬆ Import','btn.logout':'Sign Out','btn.lang':'PT',
    'tab.projects':'Projects','tab.team':'Team','tab.my':'My Area',
    'filters.title':'Filters','filter.cycle':'Cycle','filter.pep_code':'PEP (Code)',
    'filter.pep_desc':'PEP (Description)','filter.collab':'Collaborator',
    'filter.dfrom':'Start date','filter.dto':'End date',
    'btn.load':'Load','btn.clear':'Clear',
    'btn.last_month':'Last month','btn.last_quarter':'Last quarter','btn.this_year':'This year',
    'atab.effort':'Team Effort','atab.portfolio':'Portfolio Health','atab.trends':'Trends','atab.allocation':'Allocation','atab.forecast':'Forecast',
    'allocation.empty':'No data found for the selected filters.',
    'allocation.collaborator':'Collaborator','allocation.total':'Total',
    'allocation.btn_h':'Hours','allocation.btn_r':'R$',
    'forecast.title':'Completion Forecast (EVM)',
    'forecast.select_pep':'— select a PEP —',
    'forecast.empty':'Select a PEP to view the completion forecast.',
    'forecast.consumed':'Consumed Hours','forecast.remaining':'Remaining Hours',
    'forecast.utilization':'Utilization','forecast.completion':'Est. Completion',
    'forecast.realized':'Realized','forecast.projection':'Projection','forecast.budget_line':'Budget',
    'forecast.now_marker':'Now',
    'forecast.pv_line':'PV (Planned Value)',
    'forecast.spi':'SPI','forecast.sv':'Schedule Variance (SV)',
    'forecast.no_budget':'No budget registered for this PEP.',
    'effort.empty':'Select a cycle or PEP in the filters and click Load.',
    'btn.stacked':'View: Stacked','btn.grouped':'View: Grouped',
    'btn.export_csv':'⬇ Export CSV','budget.title':'Budget vs. Actual by PEP',
    'scatter.title':'EVM Quadrant — CPI × SPI',
    'scatter.note':'X = SPI (schedule) · Y = CPI (cost) · Reference at 1.0',
    'scatter.empty':'No PEP data available for selected filters.',
    'q.tr':'On schedule and on budget','q.tl':'Cost ok · Schedule at risk',
    'q.br':'Schedule ok · Cost at risk','q.bl':'Cost & schedule at risk',
    'portfolio.treemap_h':'Hour Distribution by PEP (Treemap)',
    'portfolio.treemap_r':'Actual Cost by PEP (Treemap)',
    'portfolio.empty':'No hour data found for the selected filters.',
    'portfolio.note':'Gray blocks = PEP without registered project',
    'btn.view_hours':'View: Hours','btn.view_cost':'View: R$',
    'btn.view_cpi':'View: CPI per PEP','btn.hide_cpi':'Hide CPI per PEP',
    'bullet.title':'Budget vs. Actual — Bullet Chart',
    'pepcpi.title':'CPI per PEP by Cycle',
    'pepcpi.note':'Budget / Actual Cost per cycle · Reference line at 1.0 · Requires budget_cost on projects',
    'pepcpi.empty':'No budget data found. Set budget_cost on projects to enable CPI tracking.',
    'cpi.zone_critical':'Critical < 0.9','cpi.zone_warning':'Warning 0.9–1.0',
    'trends.title':'Hours Burn by Cycle','trends.pep_lbl':'PEP:',
    'trends.all':'All',
    'trends.empty':'No data found. Import timesheets and create cycles to view trends.',
    'cycles.title':'Registered Cycles','btn.new_cycle':'+ New cycle',
    'cycles.search_ph':'Search by cycle name…',
    'cycles.th.name':'Name','cycles.th.start':'Start','cycles.th.end':'End',
    'cycles.th.type':'Type','cycles.th.recs':'Records',
    'projects.title':'Projects / PEPs','btn.new_project':'+ New project',
    'projects.search_ph':'Search by PEP, name or client…',
    'projects.th.pep':'PEP Code','projects.th.name':'Project Name',
    'projects.th.client':'Client','projects.th.mgr':'Manager',
    'projects.th.budget':'Budget (h)','projects.th.status':'Status',
    'seniority.title':'Seniority Levels','seniority.th.name':'Name',
    'btn.new_seniority':'+ New level',
    'ratecard.title':'Rate Card Table','btn.new_ratecard':'+ New rate',
    'ratecard.th.level':'Level','ratecard.th.rate':'Rate/hour (R$)',
    'ratecard.th.from':'Valid from','ratecard.th.to':'Valid to',
    'config.title':'Global Cost Factors',
    'config.extra_lbl':'Multiplier — Overtime',
    'config.standby_lbl':'Multiplier — Standby',
    'config.anomaly_lbl':'Max. Hours/Day (Anomaly Alert)',
    'btn.save_config':'Save factors',
    'team.title':'Collaborators','btn.assign_all':'Assign to all',
    'team.th.name':'Name','team.th.seniority':'Seniority','team.th.rate':'Current rate (R$/h)',
    'admin.title':'User Management','btn.new_user':'+ New user',
    'user.th.user':'Username','user.th.role':'Role',
    'btn.cancel':'Cancel','btn.save':'Save','btn.edit':'Edit','btn.delete':'Delete',
    'btn.export_csv2':'⬇ Export CSV','btn.import_csv':'⬆ Import CSV',
    'cm.title_new':'New Cycle','cm.title_edit':'Edit Cycle',
    'cm.name_lbl':'Name *','cm.name_ph':'E.g.: January/2026',
    'cm.start_lbl':'Start date *','cm.end_lbl':'End date *',
    'pm.title_new':'New Project','pm.title_edit':'Edit Project',
    'pm.pep_lbl':'PEP Code *','pm.pep_ph':'E.g.: 60OP-03333','pm.status_lbl':'Status',
    'pm.name_lbl':'Project Name','pm.name_ph':'Descriptive name',
    'pm.client_lbl':'Client','pm.client_ph':'Client name',
    'pm.mgr_lbl':'Manager','pm.mgr_ph':'Manager name',
    'pm.bh_lbl':'Hours budget','pm.bc_lbl':'Budget (R$)',
    'opt.ativo':'Active','opt.suspenso':'Suspended','opt.encerrado':'Closed',
    'sm.title_new':'New Seniority Level','sm.name_lbl':'Name *','sm.name_ph':'E.g.: Mid, Senior',
    'rm.title_new':'New Rate','rm.level_lbl':'Seniority Level *',
    'rm.rate_lbl':'Rate/hour (R$) *','rm.rate_ph':'E.g.: 120.00',
    'rm.from_lbl':'Valid from *','rm.to_lbl':'Valid to (optional)',
    'as.title':'Assign Seniority','as.level_lbl':'Seniority Level',
    'as.none_opt':'— No seniority —',
    'um.title':'New User','um.user_lbl':'Username *','um.user_ph':'minimum 3 characters',
    'um.pwd_lbl':'Password *','um.pwd_ph':'minimum 6 characters','um.role_lbl':'Role',
    'opt.user':'User',
    'pwdm.title':'Change Password','pwdm.new_lbl':'New password *','pwdm.new_ph':'minimum 6 characters',
    'ch.normal_h':'Normal Hours','ch.extra_h':'Overtime','ch.standby_h':'Standby',
    'ch.budget':'Budget','ch.actual':'Actual','ch.hours':'Hours','ch.cost':'Cost (R$)',
    'ch.cycle_axis':'Cycle','ch.cost_axis':'Actual Cost (R$)',
    'badge.quarantine':'Quarantine','badge.regular':'Regular',
    'title.lock':'Lock cycle','title.unlock':'Unlock cycle',
    'title.archive':'Archive cycle','title.restore':'Restore cycle',
    'cycles.show_archived':'Show archived',
    'anomaly.title':'⚠ Ingestion Anomaly Alerts',
    'stat.normal_h':'Normal Hours','stat.extra_h':'Overtime','stat.standby_h':'Standby',
    'stat.total':'Total','stat.collabs':'Collaborators',
    'stat.budgeted':'Budgeted (PEPs w/ budget)','stat.vs_budget':'Actual vs Budget',
    'stat.cost_normal':'Normal Hours Cost','stat.cost_extra':'Overtime Cost',
    'stat.cost_standby':'Standby Cost','stat.cost_total':'Total Actual Cost',
    'stat.peps_active':'Active PEPs','stat.budget_cost':'Budget (Cost)',
    'stat.vs_budget_cost':'Actual vs Budget',
    'budget.exceeded':'Exceeded','budget.warning':'Warning',
    'config.warning_threshold_lbl':'Warning Threshold (0–1)',
    'config.critical_threshold_lbl':'Critical Threshold (0–1)',
    'lbl.admin':'Admin','lbl.user':'User',
    'loading':'Loading…','no_cycles':'No cycles found.',
    'no_projects':'No projects found.','no_seniority':'No levels registered.',
    'no_rates':'No rates registered.','no_team':'No collaborators found.',
    'no_users':'No users found.',
    'btn.assign':'Assign','btn.pwd':'Password',
    'ch.actual_cost':'Actual Cost',
    'tt.over_budget':'Above budget','tt.utilization':'Utilization','tt.total_hours':'Total hours',
    'tt.project':'Project','tt.consumed':'Consumed','tt.actual_cost_lbl':'Actual cost',
    'tt.utilized':'utilized','tt.pep_not_reg':'⚠ PEP not registered',
    'collab.timeline_title': 'Cycle Evolution — ',
    'collab.timeline_empty': 'No data found for this collaborator.',
    'collab.calendar_empty': 'No activity this month.',
    'collab.section_cycles': 'Hours by Cycle',
    'collab.section_calendar': 'Daily Activity',
    'cal.stat.total': 'Total',
    'cal.stat.active_days': 'Active days',
    'cal.stat.avg_day': 'Avg/day',
    'cal.stat.peak': 'Peak',
    'cal.stat.quarantine': '⚠ In quarantine',
    'cal.months': ['January','February','March','April','May','June','July','August','September','October','November','December'],
    'cal.day_names': ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'],
    'cal.week_range': '(Sunday - Saturday)',
    'auditlog.title':'Audit Log','btn.refresh':'↺ Refresh',
    'auditlog.filter.all_entity':'All entities','auditlog.filter.all_action':'All actions',
    'auditlog.th.when':'When','auditlog.th.user':'User','auditlog.th.action':'Action',
    'auditlog.th.entity':'Entity','auditlog.th.id':'ID','auditlog.th.detail':'Detail',
    'no_audit':'No events recorded.',
    'cpi.title':'CPI — Cost Performance Index per Cycle',
    'toolbox.save':'Save Image','toolbox.restore':'Restore','toolbox.data_view':'View Data',
    'toolbox.data_view_lang':['Chart Data','Close','Refresh'],
    'toolbox.zoom':'Zoom','toolbox.zoom_back':'Undo Zoom',
    'toolbox.stack':'Stacked','toolbox.tiled':'Side by Side',
    'plan.title':'Planning Baseline (Hours/Cycle)',
    'plan.btn_add':'+ Add cycle','plan.btn_export':'↓ Export CSV','plan.btn_import':'↑ Import CSV',
    'plan.hint':'Set planned hours per cycle to compute PV, SPI and Schedule Variance.',
    'plan.th.cycle':'Cycle','plan.th.hours':'Planned Hours',
    'plan.select_cycle':'— select a cycle —','plan.no_plans':'No baseline defined.',
    'plan.modal_title':'Add cycles to baseline',
    'plan.modal_hint':'Select cycles and set planned hours. Cycles already in the baseline are not listed.',
    'plan.modal_add_row':'+ One more cycle',
    'myarea.upload':'Upload','myarea.history':'Import History',
    'myarea.quarantine':'Quarantine',
    'upload.inserted':'records inserted','upload.skipped':'duplicates skipped',
    'upload.quarantine':'records quarantined','upload.warnings':'warnings','upload.infos':'info messages',
    'history.th.when':'When','history.th.file':'File','history.th.inserted':'Inserted',
    'history.th.skipped':'Skipped','history.th.quarantine':'Quarantine',
    'history.th.warnings':'Warnings','history.th.status':'Status',
    'history.status.ok':'✅ OK','history.status.warnings':'⚠️ With warnings',
    'history.status.quarantine':'🔒 With quarantine','history.status.rejected':'❌ Rejected',
    'qr.th.date':'Date','qr.th.collaborator':'Collaborator','qr.th.hours':'Hours',
    'qr.th.pep':'PEP','qr.th.reason':'Reason','qr.th.type':'Type',
    'qr.th.reviewed':'Reviewed','qr.th.sent_by':'Sent by',
    'qr.type.structural':'Structural','qr.type.rule':'Rule',
    'qr.btn.export':'⬇ Export CSV','qr.btn.review':'✅ Mark reviewed',
    'qr.btn.discard':'🗑 Discard','qr.filter.pending':'Pending only',
    'qr.btn.detail':'🔍 Detail',
    'qr.btn.approve':'✅ Approve','qr.btn.reject':'❌ Reject',
    'qr.status.pending':'⏳ Pending','qr.status.approved':'✅ Approved','qr.status.rejected':'❌ Rejected',
    'qr.modal.title':'Quarantine Record #','qr.modal.collab':'Collaborator',
    'qr.modal.date':'Date','qr.modal.hours':'Hours','qr.modal.pep':'PEP',
    'qr.modal.extra':'Overtime','qr.modal.standby':'Standby',
    'qr.modal.reason':'Reason','qr.modal.rule':'Violated rule',
    'qr.modal.session':'Upload Session','qr.modal.status':'Status',
    'qr.modal.reviewed_by':'Reviewed by','qr.modal.raw':'Raw data',
    'alerts.th.rule':'Rule','alerts.th.occurrences':'Occurrences',
    'alerts.th.last':'Last trigger','alerts.th.action':'Action','alerts.th.trend':'Trend',
    'vr.title':'Validation Rules','vr.btn.new':'+ New Rule',
    'vr.th.order':'Order','vr.th.field':'Field','vr.th.operator':'Operator',
    'vr.th.value':'Value','vr.th.action':'Action','vr.th.description':'Description',
    'vr.th.active':'Active','vr.th.system':'System',
    'vr.badge.system':'System','vr.hint.aggregate':'Aggregate rules only allow info or warning.',
    'vr.system_hint':'System rules (🔒) cannot be edited or deleted, but can be activated/deactivated.',
    'vr.empty':'No rules registered.',
    'vr.modal.new':'New Validation Rule','vr.modal.edit':'Edit Rule',
    'vr.btn.activate':'Activate','vr.btn.deactivate':'Deactivate',
    'vr.saved':'Rule saved.',
    'vr.desc_ph':'Human-readable rule description','vr.value_ph':'E.g.: 24 or 5,6',
    'opt.yes':'Yes','opt.no':'No',
    'pwdm.current_lbl':'Current password *','pwdm.current_ph':'current password',
    'prefs.customize':'⚙ Customize Layout','prefs.save':'Save preferences',
    'prefs.saved':'Preferences saved.','prefs.save_error':'Error saving preferences.',
    'prefs.restore':'Restore defaults','prefs.visible':'Visible','prefs.grid_cols':'Columns',
    'size.small':'Small','size.medium':'Medium','size.large':'Large','size.full':'Full width',
    'chart.effortChart':'Effort by Collaborator','chart.trendsChart':'Trends by Cycle',
    'chart.cpiChart':'CPI by Cycle','chart.pepCpiChart':'CPI by PEP',
    'chart.treemapChart':'Portfolio Treemap','chart.bulletChart':'Budget vs Actual',
    'chart.scatterChart':'Cost × Hours Scatter','chart.forecastChart':'Completion Forecast',
    'appearance.title':'System Appearance','appearance.app_name':'System name',
    'appearance.logo':'Logo','appearance.logo_upload':'⬆ Upload new logo',
    'appearance.logo_remove':'🗑 Remove logo','appearance.density':'Density',
    'appearance.density.compact':'Compact','appearance.density.normal':'Normal',
    'appearance.density.relaxed':'Relaxed','appearance.colors':'Colors',
    'appearance.palette':'Chart palette','appearance.presets':'Preset palettes',
    'appearance.preset.pmas':'● PMAS Default','appearance.preset.corporate':'● Corporate Blue',
    'appearance.preset.high_contrast':'● High Contrast',
    'appearance.restore':'Restore defaults','appearance.save':'Save appearance',
    'appearance.saved':'Appearance saved successfully.',
    'login.user_lbl':'Username','login.user_ph':'username',
    'login.pwd_lbl':'Password','login.pwd_ph':'password',
    'login.btn':'Sign In',
    'btn.close':'Close',
    'session.title':'Import Details',
    'session.warnings':'⚠ Warnings','session.infos':'ℹ Info',
    'myarea.profile':'Profile','myarea.profile_title':'My Profile',
    'myarea.change_pwd':'Change password',
    'myarea.layout_title':'Dashboard Layout',
    'myarea.layout_save':'Save layout',
    'myarea.layout_hint':'Drag to reorder dashboard panels.',
    'myarea.upload_hint':'Import a CSV or XLSX timesheet file.',
    'myarea.history_hint':'Click a row to see full details of warnings and info.',
    'myarea.quarantine_hint':'Quarantine records. Click to view details.',
    'history.th.sent_by':'Sent by','history.th.infos':'Info',
    'qr.th.ingested':'Recorded','qr.th.status':'Status',
    'config.timezone_lbl':'Timezone',
    'acl.title':'Access Control',
    'acl.hint':'Users with explicit permission to import timesheets into this project. Admins have unrestricted access.',
    'acl.granted':'Granted access',
    'acl.add_user':'Add user',
    'btn.grant':'Grant','btn.revoke':'Revoke',
    'ms.cycle_ph':'— Select cycle(s) —','ms.pep_ph':'— All PEPs —',
    'ms.pep_desc_ph':'— All descriptions —','ms.collab_ph':'— All —',
    'ms.select_ph':'— select —',
    'msg.load_before_export':'Load data before exporting.',
    'msg.no_cycles_export':'No cycles to export.',
    'msg.no_projects_export':'No projects to export.',
    'msg.no_levels_export':'No levels to export.',
    'msg.no_rates_export':'No rates to export.',
    'msg.no_baseline_export':'No baseline to export.',
    'msg.fields_required':'Fill in all required fields.',
    'msg.pep_required':'PEP code is required.',
    'msg.positive_numbers':'Values must be positive numbers.',
    'msg.config_saved':'Factors saved successfully.',
    'msg.invalid_credentials':'Invalid credentials.',
    'msg.connection_error':'Connection error. Please try again.',
    'msg.pwd_changed':'Password changed successfully.',
    'msg.pwd_fill_all':'Fill in all fields.',
    'msg.user_not_found':'User not found.',
    'msg.name_required':'Name is required.',
    'msg.select_user':'Select a user.',
    'msg.rule_reorder_error':'Error reordering rules.',
    'msg.select_cycle_all':'Select a cycle in all rows.',
    'msg.duplicate_cycle':'Duplicate cycle in list.',
    'msg.valid_hours':'Enter valid hours (≥ 0) in all rows.',
    'msg.all_baseline_set':'All cycles already have a baseline defined.',
    'msg.baseline_removed':'Row removed.',
    'msg.pep_not_registered':'(PEP not registered)',
    'msg.no_import_sessions':'No imports recorded.',
    'msg.no_quarantine':'No quarantine records.',
    'msg.no_access_granted':'No access granted.',
    'msg.no_warnings_infos':'No warnings or additional info.',
    'msg.user_created':'User created successfully.',
    'msg.seniority_title':'Seniority — ','msg.acl_title':'Access — ',
    'msg.pwd_field_required':'Enter the new password.',
    'confirm.delete_cycle':'Delete this cycle?','confirm.delete_project':'Delete this project?',
    'confirm.delete_user':'Delete this user?',
    'confirm.delete_level':'Delete this level?',
    'confirm.revoke_access':'Revoke this user\'s access?',
    'confirm.assign_all':'Assign this seniority to ALL collaborators?',
    'confirm.remove_baseline':'Remove this baseline row?',
    'page.label':'Page','page.of':'of',
    'sm.title_edit':'Edit Level','rm.title_edit':'Edit Rate',
    'runway.title':'Portfolio Runway',
    'runway.note':'Remaining cycles at current burn rate · only PEPs with budget',
    'runway.empty':'No PEPs with budget found.',
    'runway.th.pep':'PEP','runway.th.project':'Project','runway.th.consumed':'Consumed (h)',
    'runway.th.progress':'Progress','runway.th.avg':'Avg/cycle',
    'runway.th.cycles':'Cycles remaining','runway.th.completion':'Est. completion',
    'runway.overrun':'Overrun','runway.no_budget':'No budget',
    'runway.th.spi':'SPI','runway.th.status':'Status',
    'runway.status.on_track':'On track','runway.status.at_risk':'At risk',
    'runway.status.behind':'Behind','runway.status.no_baseline':'No baseline',
    'costcomp.title':'Cost Composition by Hour Type',
    'costcomp.note':'Cost of regular · overtime · standby hours per cycle',
    'costcomp.empty':'No cost data found.',
    'conc.title':'Project Concentration Risk',
    'conc.note':'% of hours per collaborator · ⚠ risk when a single collaborator holds >60%',
    'conc.empty':'No hour data found.',
    'conc.others':'Others',
    'msg.pep_not_available': 'PEP not available for your profile.',
    'msg.import_done':'Import complete',
    'msg.created_n':'created','msg.updated_n':'updated','msg.errors_n':'error(s)',
    'msg.qr_approved':'Record approved and inserted.','msg.qr_rejected':'Record rejected.',
    'confirm.lock_cycle':'Lock this cycle?','confirm.unlock_cycle':'Unlock this cycle?',
    'confirm.archive_cycle':'Archive this cycle?','confirm.restore_cycle':'Restore this cycle?',
  },
};
let _locale = localStorage.getItem('pmas_lang') || 'pt';
function _t(key) { return (_LANG[_locale] || _LANG.pt)[key] || key; }
function _applyI18n() {
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = _t(el.dataset.i18n); });
  document.querySelectorAll('[data-i18n-ph]').forEach(el => { el.placeholder = _t(el.dataset.i18nPh); });
}

// ---------------------------------------------------------------------------
// EVM glossary — tooltip shown on any [data-evm="KEY"] element
// ---------------------------------------------------------------------------
const _EVM_TERMS = {
  CPI: {
    pt: {
      name: 'IDC — Índice de Desempenho de Custo',
      desc: 'Mede a eficiência do custo realizado. > 1,0 = abaixo do orçamento; < 1,0 = acima.',
      formula: 'IDC = VA ÷ CR\n  VA = Valor Agregado\n  CR = Custo Real acumulado',
    },
    en: {
      name: 'CPI — Cost Performance Index',
      desc: 'Measures cost efficiency. > 1.0 = under budget; < 1.0 = over budget.',
      formula: 'CPI = EV ÷ AC\n  EV = Earned Value\n  AC = Actual Cost',
    },
  },
  SPI: {
    pt: {
      name: 'IDP — Índice de Desempenho de Prazo',
      desc: 'Mede a eficiência do cronograma. > 1,0 = adiantado; < 1,0 = atrasado.',
      formula: 'IDP = VA ÷ VP\n  VA = Valor Agregado\n  VP = Valor Planejado acumulado',
    },
    en: {
      name: 'SPI — Schedule Performance Index',
      desc: 'Measures schedule efficiency. > 1.0 = ahead of schedule; < 1.0 = behind.',
      formula: 'SPI = EV ÷ PV\n  EV = Earned Value\n  PV = Planned Value (cumulative)',
    },
  },
  EAC: {
    pt: {
      name: 'EAC — Estimativa para Conclusão',
      desc: 'Projeção do custo total do projeto com base no desempenho de custo atual.',
      formula: 'EAC = OAC ÷ IDC\n  OAC = Orçamento ao Término (BAC)',
    },
    en: {
      name: 'EAC — Estimate at Completion',
      desc: 'Projected total cost of the project at the current cost performance rate.',
      formula: 'EAC = BAC ÷ CPI\n  BAC = Budget at Completion',
    },
  },
  SV: {
    pt: {
      name: 'VS — Variação de Prazo',
      desc: 'Diferença entre o valor do trabalho realizado e o planejado. Negativo = atrasado.',
      formula: 'VS = VA − VP\n  VA = Valor Agregado\n  VP = Valor Planejado',
    },
    en: {
      name: 'SV — Schedule Variance',
      desc: 'Difference between earned and planned value. Negative = behind schedule.',
      formula: 'SV = EV − PV\n  EV = Earned Value\n  PV = Planned Value',
    },
  },
  PV: {
    pt: {
      name: 'VP — Valor Planejado',
      desc: 'Custo orçado acumulado do trabalho que deveria ter sido realizado até o momento (baseline).',
      formula: 'VP = Σ (horas planejadas por ciclo)\naté o ciclo de referência',
    },
    en: {
      name: 'PV — Planned Value',
      desc: 'Cumulative budgeted cost of work that should have been completed by now (baseline).',
      formula: 'PV = Σ (planned hours per cycle)\nup to the reference cycle',
    },
  },
  EVM: {
    pt: {
      name: 'EVM — Gestão de Valor Agregado',
      desc: 'Metodologia que integra escopo, prazo e custo para medir o desempenho real do projeto e projetar tendências.',
      formula: 'Indicadores: IDC (CPI), IDP (SPI),\n  EAC, VS (SV), VP (PV)',
    },
    en: {
      name: 'EVM — Earned Value Management',
      desc: 'Methodology integrating scope, schedule and cost to measure actual project performance and forecast trends.',
      formula: 'Metrics: CPI, SPI, EAC, SV, PV',
    },
  },
};

let _evmTipEl    = null;
let _evmTipTimer = null;

function _showEvmTip(anchor) {
  const key  = anchor.dataset.evm;
  const term = _EVM_TERMS[key];
  if (!term) return;
  const loc  = term[_locale] || term.pt;

  if (!_evmTipEl) {
    _evmTipEl = document.createElement('div');
    _evmTipEl.className = 'evm-tooltip';
    document.body.appendChild(_evmTipEl);
  }
  _evmTipEl.innerHTML =
    `<div class="evm-tip-name">${escHtml(loc.name)}</div>` +
    `<div class="evm-tip-desc">${escHtml(loc.desc)}</div>` +
    `<div class="evm-tip-formula">${escHtml(loc.formula)}</div>`;
  _evmTipEl.hidden = false;

  const rect = anchor.getBoundingClientRect();
  const tipW = 270;
  let left = rect.left;
  let top  = rect.bottom + 6;
  if (left + tipW > window.innerWidth - 8) left = Math.max(8, window.innerWidth - tipW - 8);
  if (top + 120 > window.innerHeight)      top  = rect.top - 8 - (_evmTipEl.offsetHeight || 120);
  _evmTipEl.style.left = `${left}px`;
  _evmTipEl.style.top  = `${top}px`;
}

function _hideEvmTip() {
  clearTimeout(_evmTipTimer);
  if (_evmTipEl) _evmTipEl.hidden = true;
}

document.addEventListener('mouseover', e => {
  const el = e.target.closest('[data-evm]');
  if (!el) return;
  clearTimeout(_evmTipTimer);
  _evmTipTimer = setTimeout(() => _showEvmTip(el), 350);
});
document.addEventListener('mouseout', e => {
  if (!e.target.closest('[data-evm]')) return;
  clearTimeout(_evmTipTimer);
  _hideEvmTip();
});

// ---------------------------------------------------------------------------
// Multi-currency display (UI-only conversion, no backend calls)
// ---------------------------------------------------------------------------
let _currencyFactor = 1;
let _currencySymbol = 'R$';

function _fmtCost(rawValue) {
  const v = rawValue * _currencyFactor;
  return `${_currencySymbol} ${v.toLocaleString(_locale === 'pt' ? 'pt-BR' : 'en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function _applyConversion(factor, symbol) {
  _currencyFactor = factor > 0 ? factor : 1;
  _currencySymbol = symbol || 'R$';
}

function _onCurrencyChange() {
  const factor = parseFloat(document.getElementById('currencyFactor').value);
  const symbol = document.getElementById('currencySymbol').value.trim();
  _applyConversion(factor, symbol);
  _renderActiveTab();
}

document.getElementById('currencyFactor').addEventListener('change', _onCurrencyChange);
document.getElementById('currencySymbol').addEventListener('change', _onCurrencyChange);

// ---------------------------------------------------------------------------
// Table sort
// ---------------------------------------------------------------------------
const _tableSortState = {};

function _sortData(data, key, type, dir) {
  return [...data].sort((a, b) => {
    let va = a[key], vb = b[key];
    if (type === 'num')        { va = parseFloat(va) || 0; vb = parseFloat(vb) || 0; }
    else if (type === 'date')  { va = va ? +new Date(va) : 0; vb = vb ? +new Date(vb) : 0; }
    else { va = (va ?? '').toString().toLowerCase(); vb = (vb ?? '').toString().toLowerCase(); }
    return dir * (va < vb ? -1 : va > vb ? 1 : 0);
  });
}

function _applySort(tableId, data) {
  const st = _tableSortState[tableId];
  return st?.col ? _sortData(data, st.col, st.type, st.dir) : data;
}

function _makeSortable(tableId, colDefs, getDataFn, renderFn) {
  const table = document.getElementById(tableId);
  if (!table) return;
  const ths = table.querySelectorAll('thead th');
  _tableSortState[tableId] = { col: null, type: null, dir: 1 };
  ths.forEach((th, i) => {
    const def = colDefs[i];
    if (!def) return;
    th.classList.add('sortable');
    th.addEventListener('click', () => {
      const st = _tableSortState[tableId];
      if (st.col === def.key) { st.dir *= -1; }
      else { st.col = def.key; st.type = def.type; st.dir = 1; }
      ths.forEach(t => t.classList.remove('sort-asc', 'sort-desc'));
      th.classList.add(st.dir === 1 ? 'sort-asc' : 'sort-desc');
      renderFn(_applySort(tableId, getDataFn()));
    });
  });
}

// ---------------------------------------------------------------------------
// Theme-aware helpers
// ---------------------------------------------------------------------------
function _cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function _echartsTip(extra = {}) {
  return Object.assign({
    backgroundColor: _cssVar('--card'),
    borderColor:     _cssVar('--border'),
    textStyle:       { color: _cssVar('--text') },
  }, extra);
}

// ---------------------------------------------------------------------------
// Top-level tab navigation
// ---------------------------------------------------------------------------
const tabBtns     = document.querySelectorAll('.tab-btn');
const tabSections = document.querySelectorAll('.tab-section');

tabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    tabBtns.forEach(b => b.classList.remove('active'));
    tabSections.forEach(s => s.hidden = true);
    btn.classList.add('active');
    document.getElementById(`tab-${btn.dataset.tab}`).hidden = false;

    if (btn.dataset.tab === 'dashboard') _renderActiveTab();
    if (btn.dataset.tab === 'projects') { loadCyclesTable(); loadProjectsTable(); }
    if (btn.dataset.tab === 'team')     loadTeamTab();
    if (btn.dataset.tab === 'my')       _initMyArea();
    if (btn.dataset.tab === 'admin')  { loadUsersTable(); loadAuditLog(); loadRulesList(); _loadThemeEditor(); }
  });
});

// ---------------------------------------------------------------------------
// Analytics sub-tab navigation + ECharts instance registry
// ---------------------------------------------------------------------------

// Chart instance registry — keyed by DOM element id
const _charts = {};

// Which chart IDs belong to each sub-tab (to dispose on leave)
const CHARTS_PER_TAB = {
  effort:     ['effortChart', 'trendsChart', 'pepCpiChart', 'costCompositionChart', 'collabInlineTimelineChart', 'collabCalendarChart'],
  portfolio:  ['treemapChart', 'bulletChart', 'scatterChart'],
  forecast:   ['forecastChart'],
};

function _disposeTabCharts(tabId) {
  (CHARTS_PER_TAB[tabId] || []).forEach(id => {
    if (_charts[id] && !_charts[id].isDisposed()) {
      _charts[id].dispose();
    }
    delete _charts[id];
  });
}

function _getOrCreateChart(id) {
  if (!_charts[id] || _charts[id].isDisposed()) {
    _charts[id] = echarts.init(document.getElementById(id), 'dark', { renderer: 'svg' });
  }
  return _charts[id];
}


// ResizeObserver — resize all live charts when container changes
const _ro = new ResizeObserver(() => {
  Object.values(_charts).forEach(c => { try { if (!c.isDisposed()) c.resize(); } catch (_) {} });
});
_ro.observe(document.querySelector('main'));

// Print hooks — hide toolbox icons before printing (SVG renderer embeds them
// as <path> elements inside <svg>, so @media print CSS cannot target them).
// Restore immediately after the print dialog closes.
window.addEventListener('beforeprint', () => {
  Object.values(_charts).forEach(c => { try { if (!c.isDisposed()) c.setOption({ toolbox: { show: false } }); } catch (_) {} });
});
window.addEventListener('afterprint', () => {
  Object.values(_charts).forEach(c => { try { if (!c.isDisposed()) c.setOption({ toolbox: { show: true  } }); } catch (_) {} });
});

// Sub-tab state
let _activeATab = 'effort';
let _stackMode  = true;   // true = stacked, false = grouped
let _evmMode    = false;  // false = hours, true = R$
let _pepCpiMode = false;  // false = hidden, true = per-PEP CPI panel visible

const atabBtns     = document.querySelectorAll('.atab-btn');
const atabSections = document.querySelectorAll('.atab-section');

atabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    _disposeTabCharts(_activeATab);
    atabBtns.forEach(b => b.classList.remove('active'));
    atabSections.forEach(s => s.hidden = true);
    btn.classList.add('active');
    _activeATab = btn.dataset.atab;
    document.getElementById(`atab-${_activeATab}`).hidden = false;
    if (_activeATab === 'forecast') _populateForecastPepSelect();
    _renderActiveTab();
  });
});

document.getElementById('evmToggleBtn').addEventListener('click', () => {
  _evmMode = !_evmMode;
  document.getElementById('evmToggleBtn').textContent = _evmMode ? _t('btn.view_cost') : _t('btn.view_hours');
  _renderPortfolioTab();
});

document.getElementById('cpiToggleBtn').addEventListener('click', () => {
  _pepCpiMode = !_pepCpiMode;
  document.getElementById('cpiToggleBtn').textContent =
    _pepCpiMode ? _t('btn.hide_cpi') : _t('btn.view_cpi');
  if (_activeATab === 'effort') _renderActiveTab();
});

document.getElementById('exportCsvBtn').addEventListener('click', () => {
  if (!_lastEffortData.length) { notify(_t('msg.load_before_export'), 'info'); return; }
  const header = 'Colaborador,Horas Normais,Horas Extras,Sobreaviso,Total';
  const rows = _lastEffortData.map(d => {
    const total = (d.normal_hours + d.extra_hours + d.standby_hours).toFixed(1);
    return `"${d.collaborator.replace(/"/g, '""')}",${d.normal_hours.toFixed(1)},${d.extra_hours.toFixed(1)},${d.standby_hours.toFixed(1)},${total}`;
  });
  const csv  = [header, ...rows].join('\n');
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = 'esforco-equipe.csv'; a.click();
  URL.revokeObjectURL(url);
});

document.getElementById('runwayExportBtn').addEventListener('click', () => {
  if (!_lastRunwayData.length) { notify(_t('msg.load_before_export'), 'info'); return; }
  const header = 'PEP,Projeto,Consumido (h),Orçado (h),% Consumido,Média/ciclo,Ciclos restantes,Conclusão estimada,CPI,Risco';
  const rows = _lastRunwayData.map(d => {
    const risk = { ok: 'OK', warning: 'Atenção', critical: 'Crítico', overrun: _t('runway.overrun'), no_budget: _t('runway.no_budget') }[d.risk] || d.risk;
    return [
      `"${d.pep_wbs}"`, `"${d.name || ''}"`,
      d.consumed_hours.toFixed(1),
      d.budget_hours != null ? d.budget_hours.toFixed(1) : '',
      d.pct_consumed  != null ? d.pct_consumed.toFixed(1)  : '',
      d.avg_hours_per_cycle.toFixed(1),
      d.cycles_to_complete != null ? d.cycles_to_complete.toFixed(1) : '',
      `"${d.estimated_completion_cycle || ''}"`,
      d.cpi != null ? d.cpi.toFixed(2) : '',
      `"${risk}"`,
    ].join(',');
  });
  const csv  = [header, ...rows].join('\n');
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = 'runway-portfolio.csv'; a.click();
  URL.revokeObjectURL(url);
});

document.getElementById('stackToggleBtn').addEventListener('click', () => {
  _stackMode = !_stackMode;
  document.getElementById('stackToggleBtn').textContent =
    _stackMode ? _t('btn.stacked') : _t('btn.grouped');
  const ch = _charts['effortChart'];
  if (ch && !ch.isDisposed()) {
    ch.setOption(_buildEffortSeriesOnly(_stackMode), false);
  }
});

// ---------------------------------------------------------------------------
// Dashboard — DOM refs and multi-selects
// ---------------------------------------------------------------------------
const loadBtn  = document.getElementById('loadBtn');
const clearBtn   = document.getElementById('clearBtn');

const _msRegistry = [];
function _createMS(el, placeholder, onChange) {
  const ms = new MultiSelect(el, placeholder, onChange);
  _msRegistry.push(ms);
  return ms;
}

const cycleMs        = _createMS(document.getElementById('cycleMs'),        _t('ms.cycle_ph'),    onCycleChange);
const pepMs          = _createMS(document.getElementById('pepMs'),           _t('ms.pep_ph'),      onPepChange);
const pepDescMs      = _createMS(document.getElementById('pepDescMs'),       _t('ms.pep_desc_ph'), onPepDescChange);
const collaboratorMs = _createMS(document.getElementById('collaboratorMs'),  _t('ms.collab_ph'),   onCollabChange);

let pepDataCache = {};

async function onCycleChange()    { await Promise.all([refreshPeps(), refreshCollaborators()]); }
async function onPepChange()      { refreshPepDescriptions(); await refreshCollaborators(); }
async function onPepDescChange()  { await refreshCollaborators(); }
async function onCollabChange()   { await refreshPeps(); }

// ---------------------------------------------------------------------------
// Filter cascade helpers
// ---------------------------------------------------------------------------
async function loadDashboardCycles() {
  try {
    const cycles = await apiFetch('/api/cycles');
    _allCycles = cycles;
    cycleMs.setItems(cycles.map(c => ({ value: c.id, label: c.name })));
  } catch (e) { notify(`Erro ao carregar ciclos: ${e.message}`, 'error'); }
}

async function refreshPeps() {
  const cycleIds  = cycleMs.getValues();
  const collabIds = collaboratorMs.getValues();
  const p = new URLSearchParams();
  cycleIds.forEach(id  => p.append('cycle_id', id));
  collabIds.forEach(id => p.append('collaborator_id', id));
  try {
    const peps = await apiFetch(`/api/peps?${p}`);
    pepDataCache = {};
    peps.forEach(p => { pepDataCache[p.code] = p.descriptions || []; });
    pepMs.setItems(peps.map(p => ({ value: p.code, label: p.code })), true);
    refreshPepDescriptions();
  } catch (_) {}
}

function refreshPepDescriptions() {
  const selected = pepMs.getValues();
  const descs = [...new Set(selected.flatMap(code => pepDataCache[code] || []))];
  pepDescMs.setItems(descs.map(d => ({ value: d, label: d })), true);
}

async function refreshCollaborators() {
  const cycleIds = cycleMs.getValues();
  const pepCodes = pepMs.getValues();
  const pepDescs = pepDescMs.getValues();
  const p = new URLSearchParams();
  cycleIds.forEach(id => p.append('cycle_id', id));
  pepCodes.forEach(c  => p.append('pep_code', c));
  pepDescs.forEach(d  => p.append('pep_description', d));
  try {
    const collabs = await apiFetch(`/api/collaborators?${p}`);
    collaboratorMs.setItems(collabs.map(c => ({ value: c.id, label: c.name })), true);
  } catch (_) {}
}

// ---------------------------------------------------------------------------
// Upload result panel
// ---------------------------------------------------------------------------
function _showIngestResult(json, filename) {
  const panel   = document.getElementById('ingestResultPanel');
  const summary = document.getElementById('ingestResultSummary');
  const details = document.getElementById('ingestResultDetails');

  const chip = (label, val, color) =>
    val > 0 ? `<span style="background:${color}22;color:${color};border:1px solid ${color}44;border-radius:.3rem;padding:.1rem .5rem;font-size:.78rem;white-space:nowrap">${label}: <strong>${val}</strong></span>` : '';

  summary.innerHTML =
    `<span style="font-weight:600;color:#e2e8f0">${escHtml(filename)}</span>` +
    chip('Inseridos',   json.records_inserted,         '#2ecc71') +
    chip('Ignorados',   json.records_skipped,           _cssVar('--text-3')) +
    chip('Quarentena',  json.quarantine_records_added,  _cssVar('--red')) +
    chip('Avisos',      json.warning_count,             _cssVar('--amber')) +
    chip('Infos',       json.info_count,                '#60a5fa');

  let html = '';
  if (json.warnings?.length) {
    html += `<details open style="padding:.6rem 1rem;border-bottom:1px solid ${_cssVar('--surface')}">
      <summary style="cursor:pointer;color:${_cssVar('--amber')};font-weight:600;font-size:.8rem;list-style:none">⚠ ${json.warnings.length} aviso(s)</summary>
      <ul style="margin:.4rem 0 0;padding-left:1.2rem;display:flex;flex-direction:column;gap:.2rem;max-height:180px;overflow-y:auto">
        ${json.warnings.map(w => `<li style="color:#fcd34d;font-size:.79rem">${escHtml(w)}</li>`).join('')}
      </ul></details>`;
  }
  if (json.infos?.length) {
    html += `<details open style="padding:.6rem 1rem">
      <summary style="cursor:pointer;color:#60a5fa;font-weight:600;font-size:.8rem;list-style:none">ℹ ${json.infos.length} informação(ões)</summary>
      <ul style="margin:.4rem 0 0;padding-left:1.2rem;display:flex;flex-direction:column;gap:.2rem;max-height:180px;overflow-y:auto">
        ${json.infos.map(i => `<li style="color:#93c5fd;font-size:.79rem">${escHtml(i)}</li>`).join('')}
      </ul></details>`;
  }
  details.innerHTML = html || `<p style="padding:.6rem 1rem;color:#475569;font-size:.8rem;margin:0">${_t('msg.no_warnings_infos')}</p>`;
  panel.hidden = false;
  clearTimeout(panel._dismissTimer);
  panel._dismissTimer = setTimeout(() => { panel.hidden = true; }, 6000);
}

// ---------------------------------------------------------------------------
// Upload
// ---------------------------------------------------------------------------
// Language toggle
document.getElementById('langToggleBtn').addEventListener('click', () => {
  _locale = _locale === 'pt' ? 'en' : 'pt';
  localStorage.setItem('pmas_lang', _locale);
  document.getElementById('langToggleBtn').textContent = _t('btn.lang');
  _applyI18n();
  // Re-render dynamic content for active tab
  const tab = document.querySelector('.tab-btn.active')?.dataset.tab;
  if (tab === 'cycles')   _renderCyclesTable(_allCycles);
  if (tab === 'projects') _renderProjectsTable(_allProjects);
  if (tab === 'team')     loadTeamTab();
  if (tab === 'dashboard') _renderActiveTab();
  if (tab === 'admin')    { loadUsersTable(); loadAuditLog(); loadRulesList(); _loadThemeEditor(); }
  if (tab === 'my')       _initMyArea();
});

// ---------------------------------------------------------------------------
// Load button
// ---------------------------------------------------------------------------
loadBtn.addEventListener('click', () => _renderActiveTab());

clearBtn.addEventListener('click', () => {
  cycleMs.clear(); pepMs.clear(); pepDescMs.clear(); collaboratorMs.clear();
  document.getElementById('dateFromInput').value = '';
  document.getElementById('dateToInput').value   = '';
  pepDataCache = {};
  _evmMode = false;
  document.getElementById('evmToggleBtn').textContent = _t('btn.view_hours');
  _pepCpiMode = false;
  document.getElementById('cpiToggleBtn').textContent = _t('btn.view_cpi');
  document.getElementById('pepCpiPanel').hidden = true;
  _showEmpty('pepCpiEmpty', false);
  document.getElementById('scatterPanel').hidden = true;
  _showEmpty('scatterEmpty', false);
  _disposeTabCharts('effort');
  _disposeTabCharts('portfolio');
  document.getElementById('allocationMatrix').innerHTML = '';
  _showEmpty('allocationEmpty', false);
  _disposeTabCharts('forecast');
  document.getElementById('forecastKpis').hidden = true;
  document.getElementById('forecastKpis').innerHTML = '';
  _showEmpty('forecastEmpty', true);
  document.getElementById('effortStats').innerHTML = '';
  document.getElementById('portfolioStats').innerHTML = '';
  document.getElementById('bulletPanel').hidden  = true;
  document.getElementById('runwayTable').hidden = true;
  document.getElementById('runwayEmpty').hidden = true;
  document.getElementById('concentrationPanel').hidden = true;
  document.getElementById('concentrationGrid').innerHTML = '';
  _showEmpty('effortEmpty',    false);
  _showEmpty('portfolioEmpty', false);
  _showEmpty('trendsEmpty',    false);
});

// ---------------------------------------------------------------------------
// Date filter shortcuts
// ---------------------------------------------------------------------------
(function () {
  function _isoDate(d) {
    return d.toISOString().slice(0, 10);
  }
  function _applyDates(from, to) {
    document.getElementById('dateFromInput').value = _isoDate(from);
    document.getElementById('dateToInput').value   = _isoDate(to);
    loadBtn.click();
  }
  document.getElementById('shortcutLastMonth')?.addEventListener('click', () => {
    const now = new Date();
    _applyDates(
      new Date(now.getFullYear(), now.getMonth() - 1, 1),
      new Date(now.getFullYear(), now.getMonth(), 0)
    );
  });
  document.getElementById('shortcutLastQuarter')?.addEventListener('click', () => {
    const now = new Date();
    const q = Math.floor(now.getMonth() / 3);
    const prevQ = q === 0 ? 3 : q - 1;
    const prevQYear = q === 0 ? now.getFullYear() - 1 : now.getFullYear();
    _applyDates(
      new Date(prevQYear, prevQ * 3, 1),
      new Date(prevQYear, prevQ * 3 + 3, 0)
    );
  });
  document.getElementById('shortcutThisYear')?.addEventListener('click', () => {
    const y = new Date().getFullYear();
    _applyDates(new Date(y, 0, 1), new Date(y, 11, 31));
  });
})();

// ---------------------------------------------------------------------------
// Analytics — render dispatcher
// ---------------------------------------------------------------------------
async function _renderActiveTab() {
  if (_activeATab === 'effort')    await _renderEffortTab();
  if (_activeATab === 'portfolio') await _renderPortfolioTab();
  if (_activeATab === 'forecast')  await _renderForecastTab();
}

function _showEmpty(id, show) {
  const el = document.getElementById(id);
  if (el) el.hidden = !show;
}

// ---------------------------------------------------------------------------
// Esforço da Equipe
// ---------------------------------------------------------------------------
let _lastEffortData = [];
let _lastRunwayData = [];
let _selectedCollaborator = null;
let _calYear  = new Date().getFullYear();
let _calMonth = new Date().getMonth() + 1; // 1-12

async function _renderEffortTab() {
  _closeCollabDetail();
  const cycleIds  = cycleMs.getValues();
  const pepCodes  = pepMs.getValues();
  const pepDescs  = pepDescMs.getValues();
  const collabIds = collaboratorMs.getValues();
  const dateFrom  = document.getElementById('dateFromInput').value;
  const dateTo    = document.getElementById('dateToInput').value;

  const p = new URLSearchParams();
  pepCodes.forEach(c  => p.append('pep_code', c));
  pepDescs.forEach(d  => p.append('pep_description', d));
  collabIds.forEach(id => p.append('collaborator_id', id));
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to',   dateTo);

  try {
    let payload;
    if (cycleIds.length === 0) {
      payload = await apiFetch(`/api/dashboard?${p}`);
    } else {
      payload = await apiFetch(`/api/dashboard/${cycleIds[0]}?${p}`);
    }

    const data = payload.data || [];
    _lastEffortData = data;
    const bva  = (payload.budget_vs_actual || []).filter(d => d.budget_hours > 0);

    // Stats row
    document.getElementById('effortStats').innerHTML = '';
    document.getElementById('effortStats').appendChild(_buildStatsRow(data, bva));

    // Title
    document.getElementById('effortTitle').textContent = _buildEffortTitle(payload, cycleIds.length);

    if (data.length === 0) {
      _showEmpty('effortEmpty', true);
      _disposeTabCharts('effort');
      return;
    }
    _showEmpty('effortEmpty', false);

    // Sort ascending — ECharts horizontal bar renders bottom-to-top,
    // so low→high puts the highest contributor at the visual top.
    const sortedData = [...data].sort((a, b) =>
      (a.normal_hours + a.extra_hours + a.standby_hours) -
      (b.normal_hours + b.extra_hours + b.standby_hours)
    );
    const h = calcHeight(sortedData.length);
    document.getElementById('effortChart').style.height = `${h}px`;
    const ch = _getOrCreateChart('effortChart');
    ch.setOption(_buildHoursBarOption({
      data:        sortedData,
      categoryKey: 'collaborator',
      orientation: 'horizontal',
      stacked:     _stackMode,
      showTotal:   true,
      richLabel:   true,
      maxItems:    40,
      toolboxName: 'PMAS-Esforco',
    }), true);
    ch.resize();
    ch.off('click');
    ch.on('click', async (params) => {
      if (params && params.name) {
        if (_selectedCollaborator === params.name) {
          _closeCollabDetail();
        } else {
          await _openCollabDetail(params.name);
        }
      }
    });

    // Trends + CPI charts — full filter passthrough with cycle window logic
    await _renderTrendsCharts(pepCodes, pepDescs, collabIds, cycleIds, dateFrom, dateTo);

  } catch (err) {
    notify(`Erro: ${err.message}`, 'error');
  }
}

// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// Portfolio Runway panel
// ---------------------------------------------------------------------------
function _riskColor(risk) {
  const colors = {
    ok:       'var(--primary, #4f8ef7)',
    warning:  'var(--amber,   #d9b273)',
    critical: 'var(--red,     #c56d76)',
    overrun:  'var(--red,     #c56d76)',
    no_budget:'var(--text-3,  #818998)',
  };
  return colors[risk] || colors.no_budget;
}

function _renderRunwayPanel(runway) {
  _lastRunwayData = runway;
  const table     = document.getElementById('runwayTable');
  const empty     = document.getElementById('runwayEmpty');
  const exportBtn = document.getElementById('runwayExportBtn');

  const withBudget = runway.filter(r => r.budget_hours != null);
  if (exportBtn) exportBtn.hidden = !runway.length;
  if (!withBudget.length) {
    table.hidden = true;
    empty.hidden = false;
    return;
  }
  empty.hidden = true;
  table.hidden = false;
  _drawRunwayRows(_applySort('runwayTable', withBudget));
}

function _drawRunwayRows(data) {
  const tbody = document.getElementById('runwayBody');
  tbody.innerHTML = '';
  data.forEach(item => {
    const pct   = item.pct_consumed != null ? Math.min(item.pct_consumed, 100) : 0;
    const color = _riskColor(item.risk);

    const bar = `<div style="background:#1e293b;border-radius:3px;height:6px;width:120px">` +
      `<div style="height:6px;border-radius:3px;background:${color};width:${pct}%"></div></div>` +
      `<span style="font-size:.75rem;color:#94a3b8;margin-left:.4rem">${item.pct_consumed != null ? item.pct_consumed.toFixed(1) + '%' : '—'}</span>`;

    let cyclesCell = '—';
    if (item.risk === 'overrun') {
      cyclesCell = `<span style="color:var(--red,#c56d76);font-weight:600">${_t('runway.overrun')}</span>`;
    } else if (item.cycles_to_complete != null) {
      cyclesCell = item.cycles_to_complete.toFixed(1);
    }

    let spiCell = '—';
    if (item.spi != null) {
      const spiColor = item.spi >= 1 ? 'var(--primary,#4f8ef7)' : item.spi >= 0.9 ? 'var(--amber,#d9b273)' : 'var(--red,#c56d76)';
      spiCell = `<span style="color:${spiColor};font-weight:600">${item.spi.toFixed(2)}</span>`;
    }

    const statusMap = {
      on_track:    { label: _t('runway.status.on_track')    || 'No prazo',     color: 'var(--primary,#4f8ef7)' },
      at_risk:     { label: _t('runway.status.at_risk')     || 'Atenção',      color: 'var(--amber,#d9b273)' },
      behind:      { label: _t('runway.status.behind')      || 'Atrasado',     color: 'var(--red,#c56d76)' },
      no_baseline: { label: _t('runway.status.no_baseline') || 'Sem baseline', color: '#475569' },
    };
    const st = statusMap[item.schedule_status] || statusMap.no_baseline;
    const statusCell = `<span style="font-size:.78rem;font-weight:600;color:${st.color}">${st.label}</span>`;

    let cpiCell = '—';
    if (item.cpi != null) {
      const cpiColor = item.cpi >= 1 ? 'var(--primary,#4f8ef7)' : item.cpi >= 0.8 ? 'var(--amber,#d9b273)' : 'var(--red,#c56d76)';
      cpiCell = `<span style="color:${cpiColor};font-weight:600">${item.cpi.toFixed(2)}</span>`;
    }

    const rowBg = (item.risk === 'critical' || item.risk === 'overrun')
      ? 'background:rgba(197,109,118,.07)'
      : '';

    const tr = document.createElement('tr');
    tr.style.cssText = rowBg;
    tr.innerHTML = `
      <td style="font-family:monospace;font-size:.82rem">${escHtml(item.pep_wbs)}</td>
      <td style="font-size:.82rem;color:#94a3b8">${escHtml(item.name || '—')}</td>
      <td style="text-align:right">${item.consumed_hours.toFixed(1)}</td>
      <td style="white-space:nowrap">${bar}</td>
      <td style="text-align:right">${item.avg_hours_per_cycle.toFixed(1)}</td>
      <td style="text-align:right">${cyclesCell}</td>
      <td style="font-size:.82rem">${escHtml(item.estimated_completion_cycle || '—')}</td>
      <td style="text-align:right">${spiCell}</td>
      <td>${statusCell}</td>
      <td style="text-align:right">${cpiCell}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ---------------------------------------------------------------------------
// Concentration Risk panel
// ---------------------------------------------------------------------------
function _renderConcentrationPanel(concentration) {
  const panel = document.getElementById('concentrationPanel');
  const empty = document.getElementById('concentrationEmpty');
  const grid  = document.getElementById('concentrationGrid');
  grid.innerHTML = '';

  if (!concentration || !concentration.length) {
    panel.hidden = false;
    empty.hidden = false;
    return;
  }
  empty.hidden = true;
  panel.hidden = false;

  concentration.forEach(item => {
    const top1 = item.top_contributors.length > 0 ? item.top_contributors[0].pct : 0;
    const riskKey = item.risk === 'high' ? 'critical' : item.risk === 'medium' ? 'warning' : 'ok';
    const dotColor = _riskColor(riskKey);

    const barsHtml = item.top_contributors.map(c => {
      const barWidth = top1 > 0 ? Math.round(c.pct / top1 * 100) : 0;
      return `<div style="display:flex;align-items:center;gap:.35rem;min-width:0">` +
        `<span style="font-size:.78rem;color:#cbd5e1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100px" title="${escHtml(c.name)}">${escHtml(c.name)}</span>` +
        `<div style="flex:1;min-width:40px;max-width:80px;background:#1e293b;border-radius:2px;height:8px">` +
          `<div style="height:8px;border-radius:2px;background:${dotColor};width:${barWidth}%"></div>` +
        `</div>` +
        `<span style="font-size:.75rem;color:#94a3b8;white-space:nowrap">${c.pct.toFixed(0)}%</span>` +
        `</div>`;
    }).join('');

    const row = document.createElement('div');
    row.style.cssText = 'display:flex;align-items:center;gap:1rem;padding:.4rem .5rem;border-radius:.35rem;background:#0e2038';
    row.innerHTML = `
      <div style="min-width:14px;display:flex;align-items:center"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;flex-shrink:0;background:${dotColor}"></span></div>
      <div style="min-width:130px">
        <div style="font-family:monospace;font-size:.8rem;color:#e2e8f0">${escHtml(item.pep_wbs)}</div>
        <div style="font-size:.72rem;color:#64748b;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:130px" title="${escHtml(item.name || '')}">${escHtml(item.name || '')}</div>
      </div>
      <div style="display:flex;gap:.75rem;flex-wrap:wrap;flex:1">${barsHtml}</div>
      <div style="font-size:.72rem;color:#475569;white-space:nowrap">${item.total_hours.toFixed(0)}h</div>
    `;
    grid.appendChild(row);
  });
}

// ---------------------------------------------------------------------------
// Saúde do Portfólio
// ---------------------------------------------------------------------------
async function _renderPortfolioTab() {
  const cycleIds  = cycleMs.getValues();
  const pepCodes  = pepMs.getValues();
  const pepDescs  = pepDescMs.getValues();
  const collabIds = collaboratorMs.getValues();
  const dateFrom  = document.getElementById('dateFromInput').value;
  const dateTo    = document.getElementById('dateToInput').value;

  // Single params object shared by all four portfolio charts
  const p = new URLSearchParams();
  cycleIds.forEach(id  => p.append('cycle_id', id));
  pepCodes.forEach(c   => p.append('pep_wbs', c));
  pepDescs.forEach(d   => p.append('pep_description', d));
  collabIds.forEach(id => p.append('collaborator_id', id));
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to',   dateTo);

  try {
    const [health, trends, runway, concentration] = await Promise.all([
      apiFetch(`/api/portfolio-health?${p}`),
      apiFetch(`/api/trends?${p}`).catch(() => []),
      apiFetch(`/api/portfolio-runway?${p}`).catch(() => []),
      apiFetch(`/api/portfolio-concentration?${p}`).catch(() => []),
    ]);

    // Stats row — rendered before the empty-state guard so it clears on no data
    const statsEl = document.getElementById('portfolioStats');
    statsEl.innerHTML = '';
    if (health.length > 0) {
      statsEl.appendChild(_buildPortfolioStatsRow(health, trends));
    }

    // Runway panel — always rendered (shows empty state if no budgeted PEPs)
    _renderRunwayPanel(runway);

    // Concentration panel
    _renderConcentrationPanel(concentration);

    if (!health.length) {
      _showEmpty('portfolioEmpty', true);
      _disposeTabCharts('portfolio');
      document.getElementById('bulletPanel').hidden = true;
      return;
    }
    _showEmpty('portfolioEmpty', false);

    // Update treemap title
    document.getElementById('portfolioTreemapTitle').textContent =
      _evmMode ? _t('portfolio.treemap_r') : _t('portfolio.treemap_h');

    // Treemap
    const tm = _getOrCreateChart('treemapChart');
    tm.setOption(_buildTreemapOption(health, _evmMode), true);
    tm.resize();

    // Bullet chart — in hours mode use budget_hours, in R$ mode use budget_cost
    const withBudget = _evmMode
      ? health.filter(d => d.budget_cost != null)
      : health.filter(d => d.budget_hours != null);
    if (withBudget.length > 0) {
      document.getElementById('bulletPanel').hidden = false;
      document.getElementById('bulletChart').style.height =
        `${Math.max(220, withBudget.length * 60 + 80)}px`;
      const bc = _getOrCreateChart('bulletChart');
      bc.setOption(_buildBulletOption(withBudget, _evmMode), true);
      bc.resize();
    } else {
      document.getElementById('bulletPanel').hidden = true;
    }

    // EVM Quadrant (CPI × SPI) — uses runway data already fetched above
    const quadrantItems = runway.filter(r => r.cpi != null && r.spi != null);
    if (quadrantItems.length >= 1) {
      _showEmpty('scatterEmpty', false);
      document.getElementById('scatterPanel').hidden = false;
      document.getElementById('scatterChart').style.height = '380px';
      const sc = _getOrCreateChart('scatterChart');
      sc.setOption(_buildEvmQuadrantOption(quadrantItems), true);
      sc.resize();
    } else {
      _showEmpty('scatterEmpty', quadrantItems.length === 0);
      document.getElementById('scatterPanel').hidden = true;
      if (_charts['scatterChart'] && !_charts['scatterChart'].isDisposed()) {
        _charts['scatterChart'].dispose();
        delete _charts['scatterChart'];
      }
    }

    // Allocation matrix — last item in portfolio
    await _renderAllocationTab();

  } catch (err) { notify(`Erro: ${err.message}`, 'error'); }
}

// ---------------------------------------------------------------------------
// Cost Composition by Hour Type chart
// ---------------------------------------------------------------------------
function _renderCostCompositionChart(trends) {
  const panel = document.getElementById('costCompositionPanel');
  const emptyEl = document.getElementById('costCompositionEmpty');

  const filtered = (trends || []).filter(t =>
    (t.normal_cost || 0) + (t.extra_cost || 0) + (t.standby_cost || 0) > 0
  );

  if (!filtered.length) {
    panel.hidden = false;
    emptyEl.hidden = false;
    if (_charts['costCompositionChart'] && !_charts['costCompositionChart'].isDisposed()) {
      _charts['costCompositionChart'].dispose();
      delete _charts['costCompositionChart'];
    }
    document.getElementById('costCompositionChart').style.visibility = 'hidden';
    return;
  }

  panel.hidden = false;
  emptyEl.hidden = true;
  document.getElementById('costCompositionChart').style.visibility = '';

  const sym = document.getElementById('currencySymbol')?.value || 'R$';
  const factor = parseFloat(document.getElementById('currencyFactor')?.value) || 1;

  const categories = filtered.map(t => t.cycle_name);
  const normalData  = filtered.map(t => +((t.normal_cost  || 0) * factor).toFixed(2));
  const extraData   = filtered.map(t => +((t.extra_cost   || 0) * factor).toFixed(2));
  const standbyData = filtered.map(t => +((t.standby_cost || 0) * factor).toFixed(2));

  const pal = _getPalette();
  const cc = _getOrCreateChart('costCompositionChart');
  cc.setOption({
    backgroundColor: 'transparent',
    legend: { top: 0, textStyle: { color: '#94a3b8', fontSize: 11 } },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter(params) {
        const total = params.reduce((s, p) => s + (p.value || 0), 0);
        let html = `<b>${params[0].axisValue}</b><br/>`;
        params.forEach(p => {
          const pct = total > 0 ? (p.value / total * 100).toFixed(1) : '0.0';
          html += `${p.marker}${p.seriesName}: ${sym} ${p.value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} (${pct}%)<br/>`;
        });
        html += `<b>Total: ${sym} ${total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</b>`;
        return html;
      },
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: categories, axisLabel: { color: '#94a3b8', fontSize: 11, rotate: categories.length > 8 ? 30 : 0 } },
    yAxis: { type: 'value', axisLabel: { color: '#94a3b8', fontSize: 11, formatter: v => `${sym} ${v.toLocaleString('pt-BR')}` } },
    series: [
      { name: _t('trends.normal') || 'Normal',      type: 'bar', stack: 'cost', data: normalData,  itemStyle: { color: pal[0] } },
      { name: _t('trends.extra')  || 'Extra',       type: 'bar', stack: 'cost', data: extraData,   itemStyle: { color: pal[1] } },
      { name: _t('trends.standby')|| 'Sobreaviso',  type: 'bar', stack: 'cost', data: standbyData, itemStyle: { color: pal[2] } },
    ],
  }, true);
  cc.resize();
}

// ---------------------------------------------------------------------------
// Compute date window for Queima/IDP when cycles are selected.
// Returns {dateFrom, dateTo} covering selected cycles ±1 neighbor.
// If no cycles selected, returns the manually entered date range unchanged.
// ---------------------------------------------------------------------------
function _computeTrendsWindow(cycleIds, dateFrom, dateTo) {
  if (!cycleIds.length) return { dateFrom, dateTo };

  const sorted = [..._allCycles]
    .sort((a, b) => new Date(a.start_date) - new Date(b.start_date));

  if (!sorted.length) return { dateFrom, dateTo };

  const indices = cycleIds
    .map(id => sorted.findIndex(c => String(c.id) === String(id)))
    .filter(i => i >= 0);

  if (!indices.length) return { dateFrom, dateTo };

  const minIdx = Math.min(...indices);
  const maxIdx = Math.max(...indices);
  const prevIdx = Math.max(0, minIdx - 1);
  const nextIdx = Math.min(sorted.length - 1, maxIdx + 1);

  return {
    dateFrom: sorted[prevIdx].start_date,
    dateTo:   sorted[nextIdx].end_date,
  };
}

// Trends + CPI helper — called from _renderEffortTab
// ---------------------------------------------------------------------------
async function _renderTrendsCharts(pepCodes, pepDescs, collabIds, cycleIds, dateFrom, dateTo) {
  const { dateFrom: wFrom, dateTo: wTo } = _computeTrendsWindow(cycleIds, dateFrom, dateTo);

  const p = new URLSearchParams();
  pepCodes.forEach(c   => p.append('pep_wbs', c));
  pepDescs.forEach(d   => p.append('pep_description', d));
  collabIds.forEach(id => p.append('collaborator_id', id));
  if (wFrom) p.set('date_from', wFrom);
  if (wTo)   p.set('date_to',   wTo);

  try {
    const trends = await apiFetch(`/api/trends?${p}`);

    if (!trends.length) {
      _showEmpty('trendsEmpty', true);
      if (_charts['trendsChart'] && !_charts['trendsChart'].isDisposed()) {
        _charts['trendsChart'].dispose(); delete _charts['trendsChart'];
      }
      document.getElementById('costCompositionPanel').hidden = true;
      if (_charts['costCompositionChart'] && !_charts['costCompositionChart'].isDisposed()) {
        _charts['costCompositionChart'].dispose(); delete _charts['costCompositionChart'];
      }
      return;
    }
    _showEmpty('trendsEmpty', false);

    // Trends chart — G2 ✅
    const tc = _getOrCreateChart('trendsChart');
    tc.setOption(_buildHoursBarOption({
      data:        trends,
      categoryKey: 'cycle_name',
      orientation: 'vertical',
      stacked:     true,
      showTotal:   true,
      richLabel:   false,
      maxItems:    40,
      toolboxName: 'PMAS-Queima',
    }), true);
    tc.resize();


    // Cost Composition chart — G3
    _renderCostCompositionChart(trends);

    // Per-PEP CPI panel (toggle-controlled)
    if (!_pepCpiMode) {
      document.getElementById('pepCpiPanel').hidden = true;
      return;
    }
    // When no specific cycles are selected, use all non-quarantine cycles
    const effectiveCycleIds = cycleIds.length > 0
      ? cycleIds
      : (_allCycles || []).map(c => c.id);

    if (!effectiveCycleIds.length) {
      _showEmpty('pepCpiEmpty', true);
      document.getElementById('pepCpiPanel').hidden = false;
      return;
    }
    try {
      const cycleNameMap = {};
      (_allCycles || []).forEach(c => { cycleNameMap[c.id] = c.name; });

      const healthByCycle = await Promise.all(
        effectiveCycleIds.map(id =>
          apiFetch(`/api/portfolio-health?cycle_id=${id}`)
            .then(items => ({ cycleId: id, items }))
            .catch(() => ({ cycleId: id, items: [] }))
        )
      );

      const pepMap = {};
      healthByCycle.forEach(({ cycleId, items: hItems }) => {
        const cycleName = cycleNameMap[cycleId] ?? `Cycle ${cycleId}`;
        hItems.forEach(d => {
          if (d.budget_cost == null || d.budget_cost === 0 || d.actual_cost === 0) return;
          if (d.budget_hours == null || d.budget_hours === 0) return;
          if (!pepMap[d.pep_wbs]) {
            pepMap[d.pep_wbs] = { desc: d.pep_description ?? d.pep_wbs, points: [] };
          }
          const ev = (d.consumed_hours / d.budget_hours) * d.budget_cost;
          const cpiVal = +(ev / d.actual_cost).toFixed(3);
          pepMap[d.pep_wbs].points.push({ cycleName, cpi: cpiVal });
        });
      });

      const peps = Object.entries(pepMap);
      const allCycleNames = effectiveCycleIds.map(id => cycleNameMap[id] ?? `Cycle ${id}`);

      if (!peps.length) {
        _showEmpty('pepCpiEmpty', true);
        document.getElementById('pepCpiPanel').hidden = false;
        if (_charts['pepCpiChart'] && !_charts['pepCpiChart'].isDisposed()) {
          _charts['pepCpiChart'].dispose(); delete _charts['pepCpiChart'];
        }
        return;
      }
      _showEmpty('pepCpiEmpty', false);
      document.getElementById('pepCpiPanel').hidden = false;
      const pcc = _getOrCreateChart('pepCpiChart');
      pcc.setOption(_buildPepCpiOption(peps, allCycleNames), true);
      pcc.resize();
    } catch (err) {
      notify(`CPI por PEP — erro: ${err.message}`, 'error');
    }
  } catch (err) { notify(`Erro ao carregar tendências: ${err.message}`, 'error'); }
}

// ---------------------------------------------------------------------------
// Alocação — Matriz Colaborador × Projeto
// ---------------------------------------------------------------------------

let _allocEvmMode = false;

document.getElementById('allocToggleBtn').addEventListener('click', () => {
  _allocEvmMode = !_allocEvmMode;
  document.getElementById('allocToggleBtn').textContent = _allocEvmMode ? _t('allocation.btn_r') : _t('allocation.btn_h');
  if (_activeATab === 'portfolio') _renderAllocationTab();
});

let _lastAllocData  = null;
let _allocSortCol   = '__total__';
let _allocSortDir   = -1;

async function _renderAllocationTab() {
  const cycleIds  = cycleMs.getValues();
  const collabIds = collaboratorMs.getValues();
  const pepCodes  = pepMs.getValues();
  const pepDescs  = pepDescMs.getValues();
  const dateFrom  = document.getElementById('dateFromInput').value;
  const dateTo    = document.getElementById('dateToInput').value;

  const p = new URLSearchParams();
  cycleIds.forEach(id  => p.append('cycle_id', id));
  collabIds.forEach(id => p.append('collaborator_id', id));
  pepCodes.forEach(c   => p.append('pep_wbs', c));
  pepDescs.forEach(d   => p.append('pep_description', d));
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to', dateTo);

  try {
    const data = await apiFetch(`/api/allocation?${p}`);
    _lastAllocData = data;
    _allocSortCol  = '__total__';
    _allocSortDir  = -1;
    _drawAllocMatrix();
  } catch (err) {
    notify(`Erro: ${err.message}`, 'error');
  }
}

function _drawAllocMatrix() {
  const data     = _lastAllocData;
  const emptyEl  = document.getElementById('allocationEmpty');
  const matrixEl = document.getElementById('allocationMatrix');

  if (!data || !data.length) {
    _showEmpty('allocationEmpty', true);
    matrixEl.innerHTML = '';
    return;
  }
  _showEmpty('allocationEmpty', false);

  const pepLabels = {};
  data.forEach(d => {
    if (d.pep_wbs) pepLabels[d.pep_wbs] = d.pep_description || d.pep_wbs;
  });

  const collabTotals = {};
  const pepTotals    = {};
  const matrix       = {};

  data.forEach(d => {
    const pep = d.pep_wbs || '__none__';
    const val = _allocEvmMode ? d.actual_cost : d.total_hours;
    if (!matrix[d.collaborator]) matrix[d.collaborator] = {};
    matrix[d.collaborator][pep] = (matrix[d.collaborator][pep] || 0) + val;
    collabTotals[d.collaborator] = (collabTotals[d.collaborator] || 0) + val;
    pepTotals[pep] = (pepTotals[pep] || 0) + val;
  });

  const sortedPeps = Object.keys(pepTotals).sort((a, b) => pepTotals[b] - pepTotals[a]);
  const grandTotal = Object.values(collabTotals).reduce((a, b) => a + b, 0);
  const maxVal     = Math.max(...Object.values(collabTotals));

  const sortedCollabs = Object.keys(collabTotals).sort((a, b) => {
    const d = _allocSortDir;
    if (_allocSortCol === '__name__')  return d * (a < b ? -1 : a > b ? 1 : 0);
    if (_allocSortCol === '__total__') return d * (collabTotals[a] - collabTotals[b]);
    const va = matrix[a]?.[_allocSortCol] || 0;
    const vb = matrix[b]?.[_allocSortCol] || 0;
    return d * (va - vb);
  });

  const fmt = v => _allocEvmMode
    ? `R$ ${v.toLocaleString('pt-BR', {minimumFractionDigits: 0, maximumFractionDigits: 0})}`
    : `${v.toFixed(1)}h`;

  const cellBg = v => {
    if (!v) return '';
    const ratio = v / maxVal;
    const a = (0.08 + ratio * 0.72).toFixed(2);
    return `background:rgba(14,165,233,${a})`;
  };

  const thCls = key => {
    if (_allocSortCol !== key) return 'sortable';
    return `sortable ${_allocSortDir > 0 ? 'sort-asc' : 'sort-desc'}`;
  };

  let html = '<table class="alloc-matrix data-table"><thead><tr>';
  html += `<th class="${thCls('__name__')}" data-sort-key="__name__">${_t('allocation.collaborator')}</th>`;
  sortedPeps.forEach(pep => {
    const label = pep === '__none__' ? '(sem PEP)' : (pepLabels[pep] || pep);
    const short = label.length > 18 ? label.slice(0, 16) + '…' : label;
    html += `<th class="${thCls(pep)}" data-sort-key="${pep}" title="${escHtml(label)}">${escHtml(short)}</th>`;
  });
  html += `<th class="${thCls('__total__')}" data-sort-key="__total__">${_t('allocation.total')}</th></tr></thead><tbody>`;

  sortedCollabs.forEach(collab => {
    html += `<tr><td class="alloc-name">${escHtml(collab)}</td>`;
    sortedPeps.forEach(pep => {
      const v = matrix[collab]?.[pep] || 0;
      html += v
        ? `<td style="${cellBg(v)}">${fmt(v)}</td>`
        : `<td class="alloc-zero">—</td>`;
    });
    html += `<td class="alloc-total">${fmt(collabTotals[collab] || 0)}</td></tr>`;
  });

  html += `<tr class="alloc-footer"><td>${_t('allocation.total')}</td>`;
  sortedPeps.forEach(pep => {
    html += `<td>${fmt(pepTotals[pep] || 0)}</td>`;
  });
  html += `<td class="alloc-total">${fmt(grandTotal)}</td></tr>`;
  html += '</tbody></table>';

  matrixEl.innerHTML = html;

  matrixEl.querySelector('thead').addEventListener('click', e => {
    const th = e.target.closest('th[data-sort-key]');
    if (!th) return;
    const key = th.dataset.sortKey;
    if (_allocSortCol === key) { _allocSortDir *= -1; }
    else { _allocSortCol = key; _allocSortDir = -1; }
    _drawAllocMatrix();
  });
}

// ---------------------------------------------------------------------------
// Previsão de Conclusão (EVM)
// ---------------------------------------------------------------------------

async function _populateForecastPepSelect() {
  const sel = document.getElementById('forecastPepSelect');
  const current = sel.value;
  try {
    const peps = await apiFetch('/api/peps');
    sel.innerHTML = `<option value="">${_t('forecast.select_pep')}</option>` +
      peps.map(p => `<option value="${escHtml(p.code)}">${escHtml(p.code)}${p.descriptions[0] ? ' — ' + escHtml(p.descriptions[0]) : ''}</option>`).join('');
    if (peps.some(p => p.code === current)) sel.value = current;
  } catch (_) { /* non-critical */ }
}

document.getElementById('forecastPepSelect').addEventListener('change', () => {
  if (_activeATab === 'forecast') _renderForecastTab();
});

function _buildForecastKpis(fc) {
  const fmtH = h => `${(+h).toFixed(1)}h`;
  const fmtR = v => _fmtCost(v);

  const pct = fc.budget_hours
    ? `${Math.min(fc.consumed_hours / fc.budget_hours * 100, 999).toFixed(1)}%`
    : '—';
  const over = fc.budget_hours != null && fc.consumed_hours > fc.budget_hours;

  const cpiVal = fc.cpi != null ? (+fc.cpi).toFixed(2) : '—';
  const cpiCls = fc.cpi == null ? 'neutral' : fc.cpi >= 1.0 ? 'green' : fc.cpi >= 0.9 ? 'amber' : 'red';

  const spiVal = fc.spi != null ? (+fc.spi).toFixed(2) : '—';
  const spiCls = fc.spi == null ? 'neutral' : fc.spi >= 1.0 ? 'green' : fc.spi >= 0.9 ? 'amber' : 'red';
  const svFmt  = fc.sv != null ? (fc.sv >= 0 ? '+' : '') + fmtR(fc.sv) : '—';
  const svCls  = fc.sv == null ? 'neutral' : fc.sv >= 0 ? 'green' : 'red';

  const completionVal = fc.estimated_completion_cycle
    || (fc.estimated_cycles_to_complete != null ? `+${fc.estimated_cycles_to_complete} ciclos` : '—');

  const cards = [
    { val: fmtH(fc.consumed_hours),                          lbl: _t('forecast.consumed'),     cls: 'blue'              },
    { val: fc.remaining_hours != null ? fmtH(Math.max(0, fc.remaining_hours)) : '—',
                                                              lbl: _t('forecast.remaining'),    cls: over ? 'red' : 'neutral' },
    { val: pct,                                               lbl: _t('forecast.utilization'),  cls: over ? 'red' : 'green'   },
    { val: cpiVal,                                            lbl: 'CPI',                       cls: cpiCls,   evm: 'CPI' },
    { val: fc.eac != null ? fmtR(fc.eac) : '—',              lbl: 'EAC',                       cls: 'neutral', evm: 'EAC' },
    { val: spiVal,                                            lbl: _t('forecast.spi'),          cls: spiCls,   evm: 'SPI' },
    { val: svFmt,                                             lbl: _t('forecast.sv'),           cls: svCls,    evm: 'SV'  },
    { val: escHtml(String(completionVal)),                    lbl: _t('forecast.completion'),   cls: 'violet'              },
  ];
  return cards.map(({ val, lbl, cls, evm }) => {
    const lblHtml = evm
      ? `<span data-evm="${evm}">${escHtml(lbl)}</span>`
      : escHtml(lbl);
    return `<div class="stat-card ${cls}"><div class="val">${val}</div><div class="lbl">${lblHtml}</div></div>`;
  }).join('');
}

function _buildForecastOption(fc) {
  const history  = fc.history || [];
  const avg      = fc.avg_hours_per_cycle || 0;
  const lastCum  = history.length ? history.at(-1).cumulative_hours : 0;
  const budget   = fc.budget_hours;

  const projCount = budget && avg > 0
    ? Math.max(0, Math.min(Math.ceil((budget - lastCum) / avg) + 1, 14))
    : 6;

  const projCats = Array.from({ length: projCount }, (_, i) => `▸${i + 1}`);
  const projVals = [];
  for (let i = 1; i <= projCount; i++) {
    const v = lastCum + avg * i;
    projVals.push(+((budget ? Math.min(v, budget) : v)).toFixed(2));
  }

  const historyCats = history.map(h => h.cycle_name);
  const historyVals = history.map(h => h.cumulative_hours);
  const allCats = [...historyCats, ...projCats];
  const n = historyVals.length;

  // Realized series: historical values, null for projected slots
  const realizedData = [...historyVals, ...Array(projCount).fill(null)];
  const lastHistoryCat = historyCats.at(-1) ?? null;

  // Projection series: null up to last historical, then projected values (bridged from last historical)
  const projectionData = [
    ...Array(n - 1).fill(null),
    historyVals.at(-1) ?? 0,
    ...projVals,
  ];

  // Budget flat line
  const budgetData = budget ? allCats.map(() => budget) : null;

  // Planned Value (PV) curve — only if history contains cumulative_planned_hours
  const hasPV = history.some(h => h.cumulative_planned_hours != null);
  const pvData = hasPV
    ? [...history.map(h => h.cumulative_planned_hours ?? null), ...Array(projCount).fill(null)]
    : null;

  const _fpal = _getPalette();
  const _fC0  = _fpal[0] || '#0ea5e9';
  const series = [
    {
      name: _t('forecast.realized'),
      type: 'line', yAxisIndex: 0,
      data: realizedData,
      smooth: false, symbol: 'circle', symbolSize: 6,
      lineStyle: { color: _fC0, width: 2.5 },
      itemStyle: { color: _fC0 },
      areaStyle: { color: _fC0 + '1a' },
      connectNulls: false,
      ...(lastHistoryCat ? {
        markLine: {
          silent: true, symbol: 'none',
          lineStyle: { color: _cssVar('--border'), type: 'solid', width: 1 },
          data: [{ xAxis: lastHistoryCat,
            label: { show: true, formatter: _t('forecast.now_marker'),
              color: _cssVar('--text-3'), fontSize: 9, position: 'insideEndTop' } }],
        },
      } : {}),
    },
    {
      name: _t('forecast.projection'),
      type: 'line', yAxisIndex: 0,
      data: projectionData,
      smooth: false, symbol: 'circle', symbolSize: 5,
      lineStyle: { color: _cssVar('--text-3'), width: 2, type: 'dashed' },
      itemStyle: { color: _cssVar('--text-3') },
      connectNulls: false,
    },
  ];
  if (pvData) {
    const _fC3 = _fpal[3] || '#a78bfa';
    series.push({
      name: _t('forecast.pv_line'),
      type: 'line', yAxisIndex: 0,
      data: pvData,
      symbol: 'none',
      lineStyle: { color: _fC3, width: 2, type: 'dotted' },
      itemStyle: { color: _fC3 },
      connectNulls: true,
    });
  }
  if (budgetData) {
    series.push({
      name: _t('forecast.budget_line'),
      type: 'line', yAxisIndex: 0,
      data: budgetData,
      symbol: 'none',
      lineStyle: { color: _cssVar('--amber'), width: 1.5, type: 'dashed' },
      itemStyle: { color: _cssVar('--amber') },
    });
  }

  const legendData = [_t('forecast.realized'), _t('forecast.projection')];
  if (pvData) legendData.push(_t('forecast.pv_line'));
  if (budgetData) legendData.push(_t('forecast.budget_line'));

  return {
    backgroundColor: 'transparent',
    legend: {
      data: legendData, top: 8, left: 'center',
      textStyle: { color: _cssVar('--text'), fontSize: 12 },
      itemGap: 24, itemWidth: 18, itemHeight: 10,
    },
    grid: { top: 44, right: '4%', bottom: 56, left: '2%', containLabel: true },
    tooltip: {
      trigger: 'axis',
      backgroundColor: _cssVar('--card'), borderColor: _cssVar('--border'),
      textStyle: { color: _cssVar('--text') },
      formatter: params => {
        let html = `<b>${escHtml(params[0].axisValue)}</b><br>`;
        params.forEach(p => {
          if (p.value == null) return;
          html += `${p.marker} ${p.seriesName}: <b>${(+p.value).toFixed(1)}h</b><br>`;
        });
        return html;
      },
    },
    toolbox: _toolbox({
      dataZoom: { title: { zoom: _t('toolbox.zoom'), back: _t('toolbox.zoom_back') } },
    }, 'PMAS-IDP'),
    xAxis: {
      type: 'category', data: allCats,
      axisLabel: { color: _cssVar('--text-3'), rotate: allCats.length > 8 ? 30 : 0, fontSize: 11 },
      axisTick: { alignWithLabel: true },
    },
    yAxis: {
      type: 'value', name: _t('ch.hours'),
      nameTextStyle: { color: _cssVar('--text-3'), fontSize: 11 },
      axisLabel: { color: _cssVar('--text-3'), fontSize: 11, formatter: v => `${v}h` },
      splitLine: { lineStyle: { color: _cssVar('--border') } },
    },
    series,
  };
}

async function _renderForecastTab() {
  await _populateForecastPepSelect();
  const pep      = document.getElementById('forecastPepSelect').value;
  const dateFrom = document.getElementById('dateFromInput').value;
  const dateTo   = document.getElementById('dateToInput').value;

  const kpisEl  = document.getElementById('forecastKpis');
  const emptyEl = document.getElementById('forecastEmpty');

  if (!pep) {
    _showEmpty('forecastEmpty', true);
    kpisEl.hidden = true;
    _disposeTabCharts('forecast');
    return;
  }

  const p = new URLSearchParams({ pep_wbs: pep });
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to',   dateTo);

  try {
    const fc = await apiFetch(`/api/forecast?${p}`);
    _showEmpty('forecastEmpty', false);
    kpisEl.hidden = false;
    kpisEl.innerHTML = _buildForecastKpis(fc);
    const chart = _getOrCreateChart('forecastChart');
    chart.setOption(_buildForecastOption(fc), true);
    chart.resize();
    _currentForecastPep = pep;
    await _renderPlanTable(pep);
    document.getElementById('planCard').hidden = false;
  } catch (err) {
    _showEmpty('forecastEmpty', true);
    kpisEl.hidden = true;
    document.getElementById('planCard').hidden = true;
    _disposeTabCharts('forecast');
    if (!err.message?.includes('404')) notify(`Erro: ${err.message}`, 'error');
  }
}

// ---------------------------------------------------------------------------
// Plan management (ProjectCyclePlan)
// ---------------------------------------------------------------------------
let _currentForecastPep = null;
let _planProjectId = null;

async function _renderPlanTable(pep_wbs) {
  // Resolve project_id from pep_wbs
  try {
    const projects = await apiFetch('/api/projects');
    const proj = projects.find(p => p.pep_wbs === pep_wbs);
    _planProjectId = proj ? proj.id : null;
  } catch { _planProjectId = null; }

  const tbody = document.getElementById('planBody');
  if (!_planProjectId) {
    tbody.innerHTML = `<tr><td colspan="3" style="color:#64748b;font-size:.85rem;padding:.75rem">${_t('plan.no_plans')} ${_t('msg.pep_not_registered')}</td></tr>`;
    return;
  }
  try {
    const plans = await apiFetch(`/api/projects/${_planProjectId}/plans`);
    if (!plans.length) {
      tbody.innerHTML = `<tr><td colspan="3" style="color:#64748b;font-size:.85rem;padding:.75rem">${_t('plan.no_plans')}</td></tr>`;
      return;
    }
    tbody.innerHTML = plans.map(pl => `
      <tr>
        <td>${escHtml(pl.cycle_name)}</td>
        <td style="text-align:right">${(+pl.planned_hours).toLocaleString('pt-BR', {minimumFractionDigits:1, maximumFractionDigits:1})}</td>
        <td><button class="btn btn-danger btn-sm" onclick="deletePlan(${pl.cycle_id})">${_t('btn.delete')}</button></td>
      </tr>`).join('');
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

async function deletePlan(cycle_id) {
  if (!_planProjectId) return;
  if (!confirm(_t('confirm.remove_baseline'))) return;
  try {
    await apiFetchJSON(`/api/projects/${_planProjectId}/plans/${cycle_id}`, 'DELETE');
    await _renderPlanTable(_currentForecastPep);
    _renderForecastTab();
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

let _addPlanAvailableCycles = [];

function _addPlanRow(available) {
  const container = document.getElementById('addPlanRows');
  const row = document.createElement('div');
  row.style.cssText = 'display:flex;gap:.5rem;align-items:center';
  const sel = document.createElement('select');
  sel.className = 'form-select';
  sel.style.cssText = 'flex:2;height:2rem;font-size:.82rem';
  sel.innerHTML = `<option value="">— ${_t('plan.select_cycle')} —</option>` +
    available.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
  const inp = document.createElement('input');
  inp.type = 'number';
  inp.min = '0';
  inp.step = '0.5';
  inp.placeholder = _t('plan.th.hours');
  inp.style.cssText = 'flex:1;height:2rem;font-size:.82rem';
  const rm = document.createElement('button');
  rm.type = 'button';
  rm.className = 'btn btn-secondary btn-sm';
  rm.textContent = '✕';
  rm.onclick = () => row.remove();
  row.append(sel, inp, rm);
  container.appendChild(row);
}

document.getElementById('addPlanRowBtn').addEventListener('click', async () => {
  if (!_planProjectId) return;
  try {
    const [allCycles, existingPlans] = await Promise.all([
      apiFetch('/api/cycles?include_archived=false'),
      apiFetch(`/api/projects/${_planProjectId}/plans`),
    ]);
    const plannedCycleIds = new Set(existingPlans.map(p => p.cycle_id));
    _addPlanAvailableCycles = allCycles.filter(c => !plannedCycleIds.has(c.id));
    if (!_addPlanAvailableCycles.length) { notify(_t('msg.all_baseline_set'), 'info'); return; }
    document.getElementById('addPlanRows').innerHTML = '';
    document.getElementById('addPlanError').textContent = '';
    _addPlanRow(_addPlanAvailableCycles);
    document.getElementById('addPlanModal').hidden = false;
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
});

document.getElementById('addPlanAddRowBtn').addEventListener('click', () => {
  _addPlanRow(_addPlanAvailableCycles);
});

function _closeAddPlanModal() {
  document.getElementById('addPlanModal').hidden = true;
}
document.getElementById('addPlanModalClose').addEventListener('click', _closeAddPlanModal);
document.getElementById('addPlanCancelBtn').addEventListener('click', _closeAddPlanModal);

document.getElementById('addPlanSaveBtn').addEventListener('click', async () => {
  const rows = document.getElementById('addPlanRows').querySelectorAll('div');
  const errEl = document.getElementById('addPlanError');
  errEl.textContent = '';
  const entries = [];
  const seenIds = new Set();
  for (const row of rows) {
    const sel = row.querySelector('select');
    const inp = row.querySelector('input');
    const cycleId = parseInt(sel.value);
    const hours = parseFloat(inp.value);
    if (!cycleId) { errEl.textContent = _t('msg.select_cycle_all'); return; }
    if (seenIds.has(cycleId)) { errEl.textContent = _t('msg.duplicate_cycle'); return; }
    if (isNaN(hours) || hours < 0) { errEl.textContent = _t('msg.valid_hours'); return; }
    seenIds.add(cycleId);
    entries.push({ cycle_id: cycleId, planned_hours: hours });
  }
  if (!entries.length) { _closeAddPlanModal(); return; }
  try {
    await Promise.all(entries.map(e =>
      apiFetchJSON(`/api/projects/${_planProjectId}/plans/${e.cycle_id}`, 'PUT',
        { cycle_id: e.cycle_id, planned_hours: e.planned_hours })
    ));
    _closeAddPlanModal();
    await _renderPlanTable(_currentForecastPep);
    _renderForecastTab();
  } catch (e) { errEl.textContent = `Erro: ${e.message}`; }
});

document.getElementById('exportPlanBtn').addEventListener('click', async () => {
  if (!_planProjectId) return;
  try {
    const res = await fetch(`/api/projects/${_planProjectId}/plans/export`, {
      headers: _authHeaders(),
    });
    if (!res.ok) throw new Error(await res.text());
    const blob = await res.blob();
    const disp = res.headers.get('Content-Disposition') || '';
    const match = disp.match(/filename="([^"]+)"/);
    const fname = match ? match[1] : 'baseline.csv';
    const url = URL.createObjectURL(blob);
    Object.assign(document.createElement('a'), { href: url, download: fname }).click();
    URL.revokeObjectURL(url);
  } catch (e) { notify(`Erro ao exportar: ${e.message}`, 'error'); }
});

document.getElementById('importPlanFile').addEventListener('change', async function () {
  const file = this.files[0];
  if (!file) return;
  this.value = '';
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch('/api/projects/plans/import', {
      method: 'POST',
      headers: _authHeaders(),
      body: form,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || res.statusText);
    const msg = `Baseline importado: ${data.created} criados, ${data.updated} atualizados` +
      (data.errors.length ? ` — ${data.errors.length} erro(s)` : '');
    notify(msg, data.errors.length ? 'warning' : 'success');
    await _renderPlanTable(_currentForecastPep);
    _renderForecastTab();
  } catch (e) { notify(`Erro ao importar: ${e.message}`, 'error'); }
});

// ---------------------------------------------------------------------------
// Chart option builders
// ---------------------------------------------------------------------------

function calcHeight(count) { return Math.max(420, Math.min(count, 40) * 52 + 120); }

function _buildEffortTitle(payload, cycleCount) {
  const { cycle, filters } = payload;
  let t = cycleCount > 1 ? `${cycle.name} (+${cycleCount - 1} ciclo(s))` : cycle.name;
  if (filters.pep_codes?.length) t += `  |  PEP: ${filters.pep_codes.join(', ')}`;
  return t;
}

// ---------------------------------------------------------------------------
// Toolbox padrão ECharts — garante consistência visual em todos os gráficos.
// extra: objeto com features adicionais (magicType, dataZoom, etc.)
// ---------------------------------------------------------------------------
function _toolbox(extra = {}, name = 'PMAS') {
  return {
    right: 10,
    top: 10,
    feature: {
      dataView:    { readOnly: true, title: _t('toolbox.data_view'), lang: _t('toolbox.data_view_lang') },
      restore:     { title: _t('toolbox.restore') },
      saveAsImage: { title: _t('toolbox.save'), name, pixelRatio: 2 },
      ...extra,
    },
  };
}

// ============================================================
// _buildHoursBarOption — Builder unificado de barras de horas
// Substitui: _buildEffortOption, _buildTrendsOption (bloco de
// barras) e o bloco inline tc.setOption({…}) do modal timeline.
//
// Correções aplicadas vs. documento de design (seção 5):
//   [C1] showBackground preservado do G1 original (horizontal)
//   [C2] label da linha de total: 'right' (horizontal) / 'top' (vertical)
// ============================================================
function _buildHoursBarOption({
  data          = [],
  categoryKey   = 'collaborator',
  orientation   = 'horizontal',   // 'horizontal' | 'vertical'
  stacked       = true,
  showTotal     = true,
  richLabel     = false,
  maxItems      = 40,
  toolboxName   = 'PMAS-Horas',
} = {}) {

  // ── 1. Preparação dos dados ─────────────────────────────────────────
  const slice      = data.length > maxItems ? data.slice(0, maxItems) : data;
  const truncated  = data.length > maxItems;
  const stack      = stacked ? 'total' : undefined;
  const isHoriz    = orientation === 'horizontal';

  const categories = slice.map(r => r[categoryKey]);
  const normals    = slice.map(r => +(r.normal_hours  ?? 0).toFixed(2));
  const extras     = slice.map(r => +(r.extra_hours   ?? 0).toFixed(2));
  const standbys   = slice.map(r => +(r.standby_hours ?? 0).toFixed(2));
  const totals     = slice.map((_, i) =>
    +(normals[i] + extras[i] + standbys[i]).toFixed(2)
  );
  const maxTotal   = Math.max(...totals, 0);

  // Lookup rápido para richLabel (usado apenas em horizontal)
  const byCategory = Object.fromEntries(slice.map(r => [r[categoryKey], r]));

  // ── 2. Eixo de categoria ────────────────────────────────────────────
  const categoryAxis = {
    type: 'category',
    data: categories,
    axisTick: { show: false },
    axisLabel: richLabel && isHoriz
      // [C1] Label rico: nome + breakdown N/E/S — exclusivo do modo horizontal
      ? {
          color:      _cssVar('--text'),
          fontSize:   10,
          lineHeight: 16,
          formatter: name => {
            const d  = byCategory[name];
            if (!d) return name;
            const t  = (d.normal_hours + d.extra_hours + d.standby_hours).toFixed(1);
            const nm = name.length > 30 ? name.slice(0, 29) + '…' : name;
            return (
              `{nm|${nm}}\n` +
              `{hr|N:${d.normal_hours.toFixed(1)}h  ` +
              `E:${d.extra_hours.toFixed(1)}h  ` +
              `S:${d.standby_hours.toFixed(1)}h  \u2211${t}h}`
            );
          },
          rich: {
            nm: { color: _cssVar('--text'), fontSize: 11, lineHeight: 18 },
            hr: { color: _cssVar('--text-3'), fontSize: 9,  lineHeight: 14 },
          },
        }
      // Label simples para vertical (ciclos) — rotaciona quando há muitas categorias
      : {
          color:    _cssVar('--text-3'),
          fontSize: isHoriz ? 10 : 11,
          rotate:   (!isHoriz && categories.length > 6) ? 30 : 0,
        },
  };

  // ── 3. Eixo de valor ────────────────────────────────────────────────
  const valueAxis = {
    type: 'value',
    name: 'h',
    nameTextStyle: { color: _cssVar('--text-3'), fontSize: 11 },
    axisLabel: {
      color:     _cssVar('--text-3'),
      fontSize:  11,
      formatter: v => `${v}h`,
    },
    splitLine: { lineStyle: { color: _cssVar('--surface') } },
  };

  // ── 4. Tooltip unificado ────────────────────────────────────────────
  const tooltip = {
    trigger:     'axis',
    axisPointer: { type: 'shadow' },
    backgroundColor: _cssVar('--card'),
    borderColor:     _cssVar('--border'),
    textStyle:       { color: _cssVar('--text') },
    formatter: params => {
      const bars  = params.filter(p => p.seriesName !== _t('stat.total'));
      let html    = `<b>${params[0].axisValue}</b><br/>`;
      let total   = 0;
      bars.forEach(p => {
        if (p.value > 0) {
          html  += `${p.marker}${p.seriesName}: <b>${p.value.toFixed(1)}h</b><br/>`;
          total += p.value;
        }
      });
      html += `<hr style="border-color:${_cssVar('--border')};margin:4px 0"/>`;
      html += `Total: <b>${total.toFixed(1)}h</b>`;
      return html;
    },
  };

  // ── 5. Séries de barras ─────────────────────────────────────────────
  // [C1] showBackground preservado: presente em G1 (horizontal), ausente em G2/G3 (vertical)
  // const bgStyle = isHoriz
  const bgStyle = true
    ? { showBackground: true, backgroundStyle: { color: 'rgba(180, 180, 180, 0.01)' } }
    : {};

  const barMaxWidth = isHoriz ? 32 : 48;

  const _barSerie = (name, data, color) => ({
    name,
    type: 'bar',
    ...bgStyle,
    stack,
    data,
    itemStyle:   { color },
    barMaxWidth,
    label: {
      show:      !!stack,
      position:  'inside',
      fontSize:  9,
      color:     '#fff',
      formatter: p => p.value >= 10 ? `${p.value.toFixed(1)}h` : '',
    },
  });

  const _pal = _getPalette();
  const barSeries = [
    _barSerie(_t('ch.normal_h'),  normals,   _pal[0] || _cssVar('--primary')),
    _barSerie(_t('ch.extra_h'),   extras,    _pal[1] || _cssVar('--amber')),
    _barSerie(_t('ch.standby_h'), standbys,  _pal[2] || '#8b5cf6'),
  ];

  // ── 6. Série de linha de total (opcional) ───────────────────────────
  // [C2] position dinâmico: 'right' em horizontal (G1), 'top' em vertical (G2/G3)
  const totalLineSeries = showTotal ? [{
    name:       _t('stat.total'),
    type:       'line',
    color:      '#10b981',
    legendIcon: 'circle',
    data:       totals,
    symbolSize: val => val === maxTotal ? 10 : 6,
    lineStyle:  { width: 1, type: 'dashed' },
    itemStyle:  { color: p => p.value === maxTotal ? _cssVar('--red') : _cssVar('--green') },
    label: {
      show:       true,
      position:   isHoriz ? 'right' : 'top',   // [C2]
      fontSize:   10,
      fontWeight: 600,
      color:      _cssVar('--green'),
      formatter:  p => p.value === maxTotal
        ? `{peak|${p.value.toFixed(1)}h}`
        : `${p.value.toFixed(1)}h`,
      rich: { peak: { color: _cssVar('--red'), fontWeight: 700 } },
    },
    z: 10,
  }] : [];

  // ── 7. Legenda ──────────────────────────────────────────────────────
  const legendData = [
    _t('ch.normal_h'),
    _t('ch.extra_h'),
    _t('ch.standby_h'),
    ...(showTotal ? [_t('stat.total')] : []),
  ];

  // ── 8. Grid — margens ajustadas por orientação e presença de total ──
  const grid = {
    top:          44,
    right:        showTotal && isHoriz  ? '8%'  :
                  showTotal && !isHoriz ? '6%'  : '3%',
    bottom:       isHoriz ? 28 : 56,
    left:         '2%',
    containLabel: true,
  };

  // ── 9. Montagem final ───────────────────────────────────────────────
  return {
    backgroundColor: 'transparent',

    title: truncated ? {
      subtext:      `Exibindo os primeiros ${maxItems} itens`,
      left:         'center',
      top:          4,
      subtextStyle: { color: _cssVar('--text-3'), fontSize: 11 },
    } : undefined,

    legend: {
      data:       legendData,
      top:        8,
      left:       'center',
      textStyle:  { color: _cssVar('--text'), fontSize: 12 },
      itemGap:    24,
      itemWidth:  14,
      itemHeight: 10,
    },

    toolbox: _toolbox({
      magicType: {
        type:  ['stack', 'tiled'],
        title: {
          stack: _t('toolbox.stack'),
          tiled: _t('toolbox.tiled'),
        },
      },
    }, toolboxName),

    grid,
    tooltip,

    // Eixos: posição invertida conforme orientação
    xAxis: isHoriz ? valueAxis    : categoryAxis,
    yAxis: isHoriz ? categoryAxis : valueAxis,

    series: [...barSeries, ...totalLineSeries],
  };
}

// Only update the stack property — avoids full re-render flicker
function _buildEffortSeriesOnly(stacked) {
  const stack = stacked ? 'total' : undefined;
  return {
    series: [
      { name: _t('ch.normal_h'),  stack },
      { name: _t('ch.extra_h'),   stack },
      { name: _t('ch.standby_h'), stack },
    ],
  };
}

function _buildEvmQuadrantOption(items) {
  const red   = _cssVar('--red')    || '#ef4444';
  const amber = _cssVar('--amber')  || '#f59e0b';
  const green = _cssVar('--green')  || '#22c55e';
  const blue  = _cssVar('--primary') || '#4f8ef7';

  const colorOf = d => {
    if (d.cpi >= 1.0 && d.spi >= 1.0) return green;
    if (d.cpi >= 1.0 && d.spi < 1.0)  return amber;
    if (d.cpi < 1.0  && d.spi >= 1.0) return blue;
    return red;
  };

  const spis = items.map(d => d.spi);
  const cpis = items.map(d => d.cpi);
  const xMin = +Math.max(0, Math.min(...spis, 0.8) - 0.1).toFixed(2);
  const xMax = +Math.max(...spis, 1.2).toFixed(2) + 0.1;
  const yMin = +Math.max(0, Math.min(...cpis, 0.8) - 0.1).toFixed(2);
  const yMax = +Math.max(...cpis, 1.2).toFixed(2) + 0.1;

  return {
    backgroundColor: 'transparent',
    toolbox: _toolbox({}, 'PMAS-EVM-Quadrant'),
    tooltip: {
      trigger: 'item',
      backgroundColor: _cssVar('--card'),
      borderColor: _cssVar('--border'),
      textStyle: { color: _cssVar('--text'), fontSize: 12 },
      formatter: p => {
        const d = p.data._raw;
        const cC = d.cpi >= 1 ? green : d.cpi >= 0.9 ? amber : red;
        const sC = d.spi >= 1 ? green : d.spi >= 0.9 ? amber : red;
        return [
          `<b>${escHtml(d.pep_wbs)}</b>`,
          d.name ? `<span style="color:${_cssVar('--text-3')}">${escHtml(d.name)}</span>` : null,
          `CPI: <b style="color:${cC}">${d.cpi.toFixed(2)}</b>`,
          `SPI: <b style="color:${sC}">${d.spi.toFixed(2)}</b>`,
        ].filter(Boolean).join('<br/>');
      },
    },
    grid: { top: 40, bottom: 52, left: 60, right: 24, containLabel: false },
    xAxis: {
      name: 'SPI — Desempenho de Prazo',
      nameLocation: 'middle', nameGap: 34,
      nameTextStyle: { color: _cssVar('--text-3'), fontSize: 11 },
      axisLabel: { color: _cssVar('--text-3'), formatter: v => v.toFixed(1) },
      axisLine: { lineStyle: { color: _cssVar('--border') } },
      splitLine: { show: false },
      min: xMin, max: xMax,
    },
    yAxis: {
      name: 'CPI — Desempenho de Custo',
      nameLocation: 'middle', nameGap: 52,
      nameTextStyle: { color: _cssVar('--text-3'), fontSize: 11 },
      axisLabel: { color: _cssVar('--text-3'), formatter: v => v.toFixed(1) },
      axisLine: { lineStyle: { color: _cssVar('--border') } },
      splitLine: { show: false },
      min: yMin, max: yMax,
    },
    series: [{
      type: 'scatter',
      symbolSize: 16,
      data: items.map(d => ({
        value: [d.spi, d.cpi],
        itemStyle: { color: colorOf(d), opacity: 0.9, borderColor: _cssVar('--bg'), borderWidth: 2 },
        label: {
          show: true, formatter: d.pep_wbs,
          position: 'top', distance: 6,
          color: _cssVar('--text'), fontSize: 10, fontWeight: 600,
        },
        _raw: d,
      })),
      emphasis: { scale: 1.3, itemStyle: { borderWidth: 3, borderColor: _cssVar('--text') } },
      markLine: {
        silent: true, symbol: 'none',
        lineStyle: { color: _cssVar('--border'), type: 'dashed', width: 1.5 },
        data: [
          { xAxis: 1.0, label: { formatter: 'SPI=1', color: _cssVar('--text-3'), fontSize: 9 } },
          { yAxis: 1.0, label: { formatter: 'CPI=1', color: _cssVar('--text-3'), fontSize: 9 } },
        ],
      },
      markArea: {
        silent: true,
        data: [
          [{ coord: [xMin - 1, yMin - 1], itemStyle: { color: red   + '18' },
             label: { show: true, color: red,   fontSize: 9, position: 'insideTopLeft', formatter: _t('q.bl') } },
           { coord: [1.0, 1.0] }],
          [{ coord: [1.0, yMin - 1],       itemStyle: { color: blue  + '18' },
             label: { show: true, color: blue,  fontSize: 9, position: 'insideTopLeft', formatter: _t('q.br') } },
           { coord: [xMax + 1, 1.0] }],
          [{ coord: [xMin - 1, 1.0],       itemStyle: { color: amber + '18' },
             label: { show: true, color: amber, fontSize: 9, position: 'insideTopLeft', formatter: _t('q.tl') } },
           { coord: [1.0, yMax + 1] }],
          [{ coord: [1.0, 1.0],            itemStyle: { color: green + '18' },
             label: { show: true, color: green, fontSize: 9, position: 'insideTopLeft', formatter: _t('q.tr') } },
           { coord: [xMax + 1, yMax + 1] }],
        ],
      },
    }],
  };
}

function _drawScatterRefLine_unused(chart, avgRate, maxH, maxC) {
  const p0 = chart.convertToPixel({ gridIndex: 0 }, [0, 0]);
  const p1 = chart.convertToPixel({ gridIndex: 0 }, [maxH, Math.min(maxH * avgRate, maxC)]);
  if (!p0 || !p1) return;
  chart.setOption({
    graphic: [{
      type: 'group',
      children: [
        {
          type: 'line',
          shape: { x1: p0[0], y1: p0[1], x2: p1[0], y2: p1[1] },
          style: { stroke: _cssVar('--border'), lineWidth: 1.5, lineDash: [6, 4] },
          z: 0,
        },
        {
          type: 'text',
          x: p1[0] - 60, y: p1[1] - 16,
          style: {
            text: `avg ${_currencySymbol} ${avgRate.toFixed(0)}/h`,
            fill: _cssVar('--text-3'),
            fontSize: 10,
          },
          z: 0,
        },
      ],
    }],
  });
}

function _buildTreemapOption(health, evmMode = false) {
  const fmtVal = (v, raw = false) => evmMode
    ? (raw ? _fmtCost(v) : _fmtCost(v * _currencyFactor))
    : v.toFixed(1) + 'h';
  return {
    backgroundColor: 'transparent',
    toolbox: _toolbox({}, 'PMAS-Treemap'),
    tooltip: {
      trigger: 'item',
      backgroundColor: _cssVar('--card'), borderColor: _cssVar('--border'), textStyle: { color: _cssVar('--text') },
      formatter: params => {
        const d = health.find(x => x.pep_wbs === params.name);
        if (!d) return escHtml(params.name);
        let html = `<b>${escHtml(d.pep_wbs)}</b>`;
        if (d.pep_description) html += `<br><span style="color:${_cssVar('--text-3')}">${escHtml(d.pep_description)}</span>`;
        if (d.name)            html += `<br>${_t('tt.project')}: ${escHtml(d.name)}`;
        const consumed = evmMode ? d.actual_cost : d.consumed_hours;
        const budget   = evmMode ? d.budget_cost : d.budget_hours;
        html += `<br>${evmMode ? _t('tt.actual_cost_lbl') : _t('tt.consumed')}: <b>${fmtVal(consumed, true)}</b>`;
        if (budget != null) {
          const pct = (consumed / budget * 100).toFixed(1);
          html += `<br>${_t('ch.budget')}: ${fmtVal(budget, true)} (${pct}% ${_t('tt.utilized')})`;
        }
        if (!d.is_registered) html += `<br><span style="color:${_cssVar('--amber')}">${_t('tt.pep_not_reg')}</span>`;
        return html;
      },
    },
    series: [{
      type: 'treemap',
      roam: false,
      width: '100%',
      height: '100%',
      breadcrumb: { show: false },
      label: {
        show: true, fontSize: 11, color: '#f1f5f9',
        formatter: params => {
          const d = health.find(x => x.pep_wbs === params.name);
          const val = d ? (evmMode ? d.actual_cost * _currencyFactor : d.consumed_hours) : 0;
          const valStr = evmMode
            ? _currencySymbol + (val / 1000 >= 1 ? (val / 1000).toFixed(0) + 'k' : val.toFixed(0))
            : val.toFixed(0) + 'h';
          const nm = params.name.length > 16 ? params.name.slice(0, 15) + '…' : params.name;
          return `${nm}\n${valStr}${d && !d.is_registered ? '\n⚠' : ''}`;
        },
      },
      itemStyle: { gapWidth: 2, borderRadius: 4 },
      levels: [{
        itemStyle: { borderWidth: 0, gapWidth: 4 },
        upperLabel: { show: false },
      }],
      data: health.map(d => {
        const consumed = evmMode ? d.actual_cost * _currencyFactor : d.consumed_hours;
        const budget   = evmMode ? (d.budget_cost ?? null) && d.budget_cost * _currencyFactor : d.budget_hours;
        return {
          name: d.pep_wbs,
          value: consumed,
          itemStyle: {
            color: !d.is_registered
              ? _cssVar('--text-3')
              : budget != null && consumed / budget >= _budgetCritical
                ? _cssVar('--red')
                : budget != null && consumed / budget >= _budgetWarning
                  ? _cssVar('--amber')
                  : _cssVar('--primary'),
            borderColor: _cssVar('--bg'),
          },
        };
      }),
    }],
  };
}

function _buildBulletOption(withBudget, evmMode = false) {
  const labels  = withBudget.map(d => d.pep_wbs + (d.name ? `\n${d.name.slice(0, 28)}` : ''));
  const budgets = withBudget.map(d => (evmMode ? (d.budget_cost || 0) * _currencyFactor : d.budget_hours) || 0);
  const actuals = withBudget.map((d, i) => {
    const consumed = evmMode ? (d.actual_cost || 0) * _currencyFactor : d.consumed_hours;
    const pct = budgets[i] > 0 ? consumed / budgets[i] : 0;
    const color = pct >= _budgetCritical ? _cssVar('--red') : pct >= _budgetWarning ? _cssVar('--amber') : _cssVar('--primary');
    return { value: +consumed.toFixed(2), itemStyle: { color, borderRadius: [0, 2, 2, 0] } };
  });
  const unit = evmMode ? _currencySymbol : 'h';
  const fmtAx = evmMode
    ? v => v >= 1000 ? `${_currencySymbol}${(v/1000).toFixed(0)}k` : `${_currencySymbol}${v.toFixed(0)}`
    : v => `${v}h`;
  return {
    backgroundColor: 'transparent',
    toolbox: _toolbox({}, 'PMAS-Bullet'),
    grid: { top: 46, right: '10%', bottom: 16, left: '2%', containLabel: true },
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'none' },
      backgroundColor: _cssVar('--card'), borderColor: _cssVar('--border'), textStyle: { color: _cssVar('--text') },
      formatter: params => {
        const b = budgets[params[0].dataIndex];
        const a = params.find(p => p.seriesName === _t('ch.actual'))?.value ?? 0;
        const pct = b > 0 ? `${(a / b * 100).toFixed(1)}%` : '—';
        const fmtV = v => evmMode ? _fmtCost(v / _currencyFactor) : v.toFixed(1) + 'h';
        let html = `<b>${escHtml(params[0].axisValue.replace('\n', ' '))}</b><br>`;
        html += `${_t('ch.budget')}: <b>${fmtV(b)}</b><br>${_t('ch.actual')}: <b>${fmtV(a)}</b><br>`;
        html += `${_t('tt.utilization')}: <b>${pct}</b>`;
        if (b > 0 && a > b) html += `<br><span style="color:${_cssVar('--red')}">⚠ ${_t('tt.over_budget')}</span>`;
        return html;
      },
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: _cssVar('--text-3'), fontSize: 10, formatter: fmtAx },
      splitLine: { lineStyle: { color: _cssVar('--border') } },
    },
    yAxis: {
      type: 'category', data: labels,
      axisTick: { show: false },
      axisLabel: { color: _cssVar('--text'), fontSize: 10, lineHeight: 16 },
    },
    series: [
      {
        name: _t('ch.budget'),
        type: 'bar',
        barMaxWidth: 48,
        barGap: '-100%',
        z: 1,
        data: budgets.map(b => ({
          value: b,
          itemStyle: {
            color: 'rgba(148,163,184,0.18)',
            borderColor: 'rgba(148,163,184,0.35)',
            borderWidth: 1,
            borderRadius: [0, 3, 3, 0],
          },
        })),
      },
      {
        name: _t('ch.actual'),
        type: 'bar',
        barMaxWidth: 28,
        barGap: '-100%',
        z: 2,
        data: actuals,
        label: {
          show: true,
          position: 'right',
          fontSize: 10,
          color: _cssVar('--text'),
          formatter: params => {
            const b = budgets[params.dataIndex];
            return b > 0 ? `${(params.value / b * 100).toFixed(0)}%` : '';
          },
        },
      },
    ],
  };
}

// ---------------------------------------------------------------------------
// Collaborator Inline Detail Panel
// ---------------------------------------------------------------------------
function _closeCollabDetail() {
  _selectedCollaborator = null;
  document.getElementById('collabDetailPanel').hidden = true;
  // dispose inline charts
  ['collabInlineTimelineChart','collabCalendarChart'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    const c = echarts.getInstanceByDom(el);
    if (c && !c.isDisposed()) c.dispose();
  });
  // remove highlight from effort chart
  const effEl = document.getElementById('effortChart');
  if (effEl) { const c = echarts.getInstanceByDom(effEl); if (c) c.dispatchAction({ type: 'downplay' }); }
}

async function _openCollabDetail(name) {
  _selectedCollaborator = name;

  // highlight bar in effort chart
  const effEl = document.getElementById('effortChart');
  if (effEl) {
    const c = echarts.getInstanceByDom(effEl);
    if (c) {
      c.dispatchAction({ type: 'downplay' });
      c.dispatchAction({ type: 'highlight', name });
    }
  }

  // show panel, set title
  const panel = document.getElementById('collabDetailPanel');
  panel.hidden = false;
  document.getElementById('collabDetailName').textContent = name;

  // scroll panel into view smoothly
  panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

  // Section 1: cycle timeline
  await _renderCollabTimeline(name);

  // Section 2: calendar heatmap — use current calendar month
  _calYear  = new Date().getFullYear();
  _calMonth = new Date().getMonth() + 1;
  await _renderCollabCalendar(name, _calYear, _calMonth);
}

async function _renderCollabTimeline(name) {
  const emptyEl = document.getElementById('collabInlineTimelineEmpty');
  const chartEl = document.getElementById('collabInlineTimelineChart');

  // reuse existing filters from the main filter bar
  const pepCodes = pepMs.getValues();
  const pepDescs = pepDescMs.getValues();
  const dateFrom = document.getElementById('dateFromInput').value;
  const dateTo   = document.getElementById('dateToInput').value;

  const p = new URLSearchParams();
  p.set('collaborator_name', name);
  pepCodes.forEach(c => p.append('pep_code', c));
  pepDescs.forEach(d => p.append('pep_description', d));
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to',   dateTo);

  let rows = [];
  try { rows = await apiFetch(`/api/dashboard/collaborator-timeline?${p}`); }
  catch (e) { notify('Erro ao carregar timeline.', 'error'); return; }

  // dispose old chart
  const existing = echarts.getInstanceByDom(chartEl);
  if (existing && !existing.isDisposed()) existing.dispose();

  if (!rows.length) {
    emptyEl.hidden = false;
    chartEl.style.visibility = 'hidden';
    return;
  }
  emptyEl.hidden = true;
  chartEl.style.visibility = '';

  const tc = echarts.init(chartEl, 'dark', { renderer: 'svg' });
  _charts['collabInlineTimelineChart'] = tc;
  tc.setOption(_buildHoursBarOption({
    data: rows, categoryKey: 'cycle_name',
    orientation: 'vertical', stacked: true,
    showTotal: true, richLabel: false,
    maxItems: 40, toolboxName: 'PMAS-CollabTimeline',
  }), true);

  // Click a cycle bar → jump the calendar to that cycle's start month
  tc.off('click');
  tc.on('click', async (params) => {
    if (!params?.name) return;
    const rec = rows.find(r => r.cycle_name === params.name);
    if (!rec?.cycle_start) return;
    const [y, m] = rec.cycle_start.split('-').map(Number);
    _calYear  = y;
    _calMonth = m;
    await _renderCollabCalendar(_selectedCollaborator, _calYear, _calMonth);
    document.getElementById('collabCalendarChart')
      .scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });
}

async function _renderCollabCalendar(name, year, month) {
  const emptyEl  = document.getElementById('collabCalendarEmpty');
  const chartEl  = document.getElementById('collabCalendarChart');
  const statsEl  = document.getElementById('collabCalendarStats');
  const inputEl  = document.getElementById('calMonthInput');

  const nowDate  = new Date();
  inputEl.max    = `${nowDate.getFullYear()}-${String(nowDate.getMonth()+1).padStart(2,'0')}`;
  inputEl.value  = `${year}-${String(month).padStart(2,'0')}`;

  let data = [];
  try {
    data = await apiFetch(`/api/dashboard/collaborator-daily?collaborator_name=${encodeURIComponent(name)}&year=${year}&month=${month}`);
  } catch(e) { notify('Erro ao carregar dados diários.', 'error'); return; }

  // dispose old
  const existing = echarts.getInstanceByDom(chartEl);
  if (existing && !existing.isDisposed()) existing.dispose();

  const workPoints = data.filter(d => d.hours > 0);
  const quarantineDates = new Set(data.filter(d => d.has_quarantine).map(d => d.date));
  // include quarantine-only days so tooltip can show ⚠ even when hours=0
  const calPoints = data.filter(d => d.hours > 0 || d.has_quarantine);

  const dayHeaderEl = document.getElementById('calDayHeader');
  if (!calPoints.length) {
    emptyEl.hidden = false;
    chartEl.style.visibility = 'hidden';
    if (dayHeaderEl) dayHeaderEl.style.display = 'none';
    statsEl.innerHTML = '';
    return;
  }
  emptyEl.hidden = true;
  chartEl.style.visibility = '';
  if (dayHeaderEl) dayHeaderEl.style.display = 'flex';

  // data: [date, total, normal, extra, standby]
  // All days in the month — inactive days use value=-1 so visualMap.outOfRange
  // applies a neutral background while the label still shows the day number.
  const lastDay    = new Date(year, month, 0).getDate();
  const allDaysData = [];
  for (let d = 1; d <= lastDay; d++) {
    const dateStr = `${year}-${String(month).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
    const rec = data.find(r => r.date === dateStr);
    if (rec) {
      allDaysData.push([dateStr, rec.hours, rec.normal_hours || 0, rec.extra_hours || 0, rec.standby_hours || 0]);
    } else {
      allDaysData.push([dateStr, -1, 0, 0, 0]);
    }
  }

  const rangeStart = `${year}-${String(month).padStart(2,'0')}-01`;
  const rangeEnd   = `${year}-${String(month).padStart(2,'0')}-${String(lastDay).padStart(2,'0')}`;
  // maxHours removed — visualMap now uses discrete pieces, no continuous scale needed

  // Read theme CSS variables so the chart adapts to Admin > Aparência settings
  const primaryColor  = _cssVar('--primary')    || '#4f8ef7';
  const accentColor   = _cssVar('--accent')     || '#07b3d7';
  const cardColor     = _cssVar('--card')       || '#0e2038';
  const borderColor   = _cssVar('--border-hi')  || '#1d4068';
  const inactiveText  = _cssVar('--text-3')     || '#3d6080';
  const activeText    = _cssVar('--text')       || '#e0e0e0';
  const textMuted     = _cssVar('--text-2')     || '#94a3b8';
  const pal           = _getPalette();

  // Square cell size — compute from container, then force chart width to match exactly
  const containerW = chartEl.parentElement?.offsetWidth || chartEl.offsetWidth || 560;
  const cellW      = Math.min(Math.max(Math.floor((containerW - 16) / 7), 44), 80);
  const calWidth   = cellW * 7;
  chartEl.style.width  = `${calWidth + 8}px`;
  chartEl.style.maxWidth = '100%';
  chartEl.style.margin = '0 auto';

  // Day-of-week header row rendered in HTML (ECharts vertical orient puts dayLabel on left)
  const dayHeader = document.getElementById('calDayHeader');
  if (dayHeader) {
    const dayNames = _t('cal.day_names');
    dayHeader.style.cssText = `display:flex;width:${calWidth + 8}px;max-width:100%;margin:0 auto 2px`;
    dayHeader.innerHTML = dayNames.map(n =>
      `<div style="flex:0 0 ${cellW}px;text-align:center;font-size:10px;font-weight:600;color:${textMuted}">${n}</div>`
    ).join('');
  }

  // Dynamic height: weeks
  const firstDow  = new Date(year, month - 1, 1).getDay(); // 0=Sun
  const numWeeks  = Math.ceil((firstDow + lastDay) / 7);
  chartEl.style.height = `${numWeeks * cellW + 8}px`;

  const cc = echarts.init(chartEl, 'dark', { renderer: 'svg' });
  _charts['collabCalendarChart'] = cc;
  cc.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      formatter(p) {
        if (!p.value || p.value[1] < 0) return '';
        const [d_date, , n, e, s] = p.value;
        const q = quarantineDates.has(d_date) ? ' ⚠' : '';
        let tip = `<b>${d_date}</b>${q}`;
        if (n > 0) tip += `<br/>Normal: ${n.toFixed(1)}h`;
        if (e > 0) tip += `<br/>Extra: ${e.toFixed(1)}h`;
        if (s > 0) tip += `<br/>Sobreaviso: ${s.toFixed(1)}h`;
        return tip;
      },
    },
    visualMap: {
      show: false,
      type: 'piecewise',
      // 6 discrete bands matching the blue scale in the reference legend.
      // Values 0 and -1 (inactive / zero-hour days) fall through to outOfRange.
      pieces: [
        { gte:  1, lte:  3, color: '#d4e3f5' },
        { gte:  4, lte:  6, color: '#96bcdf' },
        { gte:  7, lte:  9, color: '#5490c8' },
        { gte: 10, lte: 12, color: '#2662ae' },
        { gte: 13, lte: 15, color: '#103c8c' },
        { gt:  15,           color: '#071e60' },
      ],
      outOfRange: { color: [cardColor] },
    },
    calendar: {
      orient: 'vertical',
      top: 4, left: 4, right: 4, bottom: 4,
      width: calWidth,
      range: [rangeStart, rangeEnd],
      cellSize: [cellW, cellW],
      dayLabel: { show: false },
      monthLabel: { show: false },
      yearLabel:  { show: false },
      itemStyle:  { color: cardColor, borderColor: borderColor, borderWidth: 2 },
      splitLine:  { show: false },
    },
    series: [{
      type: 'heatmap',
      coordinateSystem: 'calendar',
      data: allDaysData,
      label: {
        show: true,
        formatter(params) {
          const [d_date, total, n, e, s] = params.data;
          const day = parseInt(d_date.split('-')[2], 10);
          if (total < 0) return `{inactive|${day}}`;
          const isQ = quarantineDates.has(d_date);
          const dayStr = isQ ? `{qday|${day}⚠}` : `{day|${day}}`;
          const lines = [dayStr];
          if (n > 0) lines.push(`{n|${n.toFixed(1)}}`);
          if (e > 0) lines.push(`{e|${e.toFixed(1)}}`);
          if (s > 0) lines.push(`{s|${s.toFixed(1)}}`);
          return lines.join('\n');
        },
        rich: {
          inactive: { fontSize: 9, color: inactiveText,  lineHeight: 14, align: 'center' },
          day:      { fontSize: 9, fontWeight: 'bold', color: activeText, lineHeight: 14, align: 'center' },
          qday:     { fontSize: 9, fontWeight: 'bold', color: '#f59e0b',  lineHeight: 14, align: 'center' },
          n:    { fontSize: 9, color: pal[0] || '#4f8ef7', lineHeight: 13, align: 'center' },
          e:    { fontSize: 9, color: pal[1] || '#d9b273', lineHeight: 13, align: 'center' },
          s:    { fontSize: 9, color: pal[2] || '#a78bfa', lineHeight: 13, align: 'center' },
        },
      },
      emphasis: { itemStyle: { shadowBlur: 8, shadowColor: primaryColor } },
    }],
  }, true);

  // stats row
  const totalHours = workPoints.reduce((s, d) => s + d.hours, 0);
  const workDays   = workPoints.length;
  const avgPerDay  = workDays > 0 ? totalHours / workDays : 0;
  const peak       = workPoints.length ? workPoints.reduce((m, d) => d.hours > m.hours ? d : m, workPoints[0]) : null;

  const stat = (lbl, val) =>
    `<div style="display:flex;flex-direction:column;gap:.15rem">
       <span style="font-size:.7rem;color:var(--text-3);text-transform:uppercase;letter-spacing:.04em">${lbl}</span>
       <span style="font-size:.88rem;font-weight:600;color:var(--text)">${val}</span>
     </div>`;

  statsEl.innerHTML =
    stat(_t('cal.stat.total'), `${totalHours.toFixed(1)}h`) +
    stat(_t('cal.stat.active_days'), workDays) +
    stat(_t('cal.stat.avg_day'), `${avgPerDay.toFixed(1)}h`) +
    (peak ? stat(_t('cal.stat.peak'), `${peak.hours.toFixed(1)}h (${peak.date})`) : '') +
    (quarantineDates.size ? stat(_t('cal.stat.quarantine'), quarantineDates.size) : '');
}

// ---------------------------------------------------------------------------
// (cpiChart removed — IDP por ciclo merged into trends; see _buildHoursBarOption)
// ---------------------------------------------------------------------------
function _buildCpiOption_unused(trends) {
  const cats = trends.map(d => d.cycle_name);
  const cpiSeries = trends.map(d => d.cpi != null ? +d.cpi.toFixed(3) : null);
  return {
    backgroundColor: 'transparent',
    toolbox: _toolbox({
      dataZoom: { title: { zoom: _t('toolbox.zoom'), back: _t('toolbox.zoom_back') } },
    }, 'PMAS-Previsao'),
    tooltip: {
      trigger: 'axis',
      formatter: params => {
        const p = params[0];
        if (p.value == null) return `${p.name}<br/>IDP: —`;
        const color = p.value >= 1 ? _cssVar('--primary') : p.value >= 0.9 ? _cssVar('--amber') : _cssVar('--red');
        return `${p.name}<br/>IDP: <b style="color:${color}">${p.value.toFixed(3)}</b>`;
      },
    },
    grid: { left: 60, right: 20, top: 20, bottom: 50 },
    xAxis: { type: 'category', data: cats, axisLabel: { color: _cssVar('--text-3'), fontSize: 10, rotate: 30 } },
    yAxis: {
      type: 'value',
      axisLabel: { color: _cssVar('--text-3'), fontSize: 10 },
      splitLine: { lineStyle: { color: _cssVar('--surface') } },
    },
    series: [{
      type: 'line',
      data: cpiSeries,
      connectNulls: true,
      smooth: false,
      lineStyle: { color: _cssVar('--primary'), width: 2 },
      itemStyle: {
        color: params => {
          const v = params.value;
          if (v == null) return _cssVar('--primary');
          return v >= 1 ? _cssVar('--primary') : v >= 0.9 ? _cssVar('--amber') : _cssVar('--red');
        },
      },
      label: {
        show: true,
        position: 'top',
        fontSize: 10,
        fontWeight: 600,
        formatter: params => {
          if (params.value == null) return '';
          const v = params.value;
          const style = v >= 1 ? 'good' : v >= 0.9 ? 'amber' : 'red';
          return `{${style}|${v.toFixed(2)}}`;
        },
        rich: {
          good: { color: _cssVar('--primary'), fontWeight: 700, fontSize: 10 },
          amber: { color: _cssVar('--amber'), fontWeight: 700, fontSize: 10 },
          red:   { color: _cssVar('--red'), fontWeight: 700, fontSize: 10 },
        },
      },
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { color: _cssVar('--text-3'), type: 'dashed', width: 1 },
        label: { formatter: 'IDP = 1.0', color: _cssVar('--text-3'), fontSize: 10 },
        data: [{ yAxis: 1.0 }],
      },
    }],
  };
}

function _buildPepCpiOption(peps, allCycleNames) {
  const series = peps.map(([wbs, { desc, points }], i) => {
    const dataMap = Object.fromEntries(points.map(p => [p.cycleName, p.cpi]));
    const data    = allCycleNames.map(n => dataMap[n] ?? null);
    const pal     = _getPalette();
    const color   = pal[i % pal.length];
    return {
      name: `${wbs} — ${desc}`,
      type: 'line',
      data,
      connectNulls: false,
      smooth: false,
      symbol: 'circle', symbolSize: 7,
      lineStyle: { color, width: 2.5 },
      itemStyle: { color },
      emphasis: { focus: 'series' },
    };
  });

  return {
    backgroundColor: 'transparent',
    toolbox: _toolbox({}, 'PMAS-CPI-PEP'),
    title: {
      text: _t('pepcpi.title'),
      textStyle: { color: _cssVar('--text'), fontSize: 14, fontWeight: 600 },
      left: 'center', top: 8,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: _cssVar('--card'),
      borderColor: _cssVar('--border'),
      textStyle: { color: _cssVar('--text'), fontSize: 12 },
      formatter: params => {
        const header = `<b>${escHtml(params[0]?.axisValue)}</b><br/>`;
        const lines  = params
          .filter(p => p.value != null)
          .map(p => {
            const cpiVal = p.value;
            const color  = cpiVal >= 1.0 ? _cssVar('--primary') : cpiVal >= 0.9 ? _cssVar('--amber') : _cssVar('--red');
            const dot    = `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${p.color};margin-right:4px"></span>`;
            return `${dot}${escHtml(p.seriesName)}: <b style="color:${color}">${cpiVal.toFixed(2)}</b>`;
          })
          .join('<br/>');
        return header + lines;
      },
    },
    legend: {
      bottom: 0,
      textStyle: { color: _cssVar('--text-3'), fontSize: 10 },
      itemWidth: 14, itemHeight: 3,
    },
    grid: { top: 48, bottom: 64, left: 48, right: 16, containLabel: true },
    xAxis: {
      type: 'category',
      data: allCycleNames,
      axisLabel: { color: _cssVar('--text-3'), fontSize: 10, rotate: allCycleNames.length > 6 ? 30 : 0 },
      axisLine:  { lineStyle: { color: _cssVar('--border') } },
      splitLine: { show: false },
    },
    yAxis: {
      name: 'CPI',
      nameTextStyle: { color: _cssVar('--text-3'), fontSize: 11 },
      axisLabel: { color: _cssVar('--text-3'), formatter: v => v.toFixed(2) },
      axisLine:  { lineStyle: { color: _cssVar('--border') } },
      splitLine: { lineStyle: { color: _cssVar('--surface') } },
      min: v => Math.max(0, +(v.min - 0.15).toFixed(1)),
      max: v => +(v.max + 0.15).toFixed(1),
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { color: _cssVar('--text-3'), type: 'dashed', width: 1.5 },
        data: [{ yAxis: 1.0, label: { formatter: 'CPI = 1.0', color: _cssVar('--text-3'), fontSize: 10 } }],
      },
    },
    series: series.map((s, i) => i > 0 ? s : {
      ...s,
      markArea: {
        silent: true,
        data: [
          [{ yAxis: 0,   itemStyle: { color: (_cssVar('--red')   || '#ef4444') + '18' },
             label: { show: true, position: 'insideTopLeft', formatter: _t('cpi.zone_critical'),
               color: _cssVar('--red')   || '#ef4444', fontSize: 9 } },
           { yAxis: 0.9 }],
          [{ yAxis: 0.9, itemStyle: { color: (_cssVar('--amber') || '#f59e0b') + '14' },
             label: { show: true, position: 'insideTopLeft', formatter: _t('cpi.zone_warning'),
               color: _cssVar('--amber') || '#f59e0b', fontSize: 9 } },
           { yAxis: 1.0 }],
        ],
      },
    }),
  };
}

// ---------------------------------------------------------------------------
// Stats row (effort tab)
// ---------------------------------------------------------------------------
function _buildStatsRow(data, budgetData = []) {
  let normal = 0, extra = 0, standby = 0;
  data.forEach(r => { normal += r.normal_hours; extra += r.extra_hours; standby += r.standby_hours; });
  const total = normal + extra + standby;
  const row   = document.createElement('div'); row.className = 'stats-row';
  const cards = [
    { val: fmt(normal),  lbl: _t('stat.normal_h'),  cls: 'blue'    },
    { val: fmt(extra),   lbl: _t('stat.extra_h'),   cls: 'amber'   },
    { val: fmt(standby), lbl: _t('stat.standby_h'), cls: 'violet'  },
    { val: fmt(total),   lbl: _t('stat.total'),     cls: 'green'   },
    { val: data.length,  lbl: _t('stat.collabs'),   cls: 'neutral' },
  ];
  if (budgetData.length > 0) {
    const totalBudget = budgetData.reduce((s, d) => s + d.budget_hours, 0);
    const totalActual = budgetData.reduce((s, d) => s + d.actual_hours, 0);
    const pct  = totalBudget > 0 ? (totalActual / totalBudget * 100).toFixed(1) : '—';
    const over = totalBudget > 0 && totalActual > totalBudget;
    cards.push(
      { val: fmt(totalBudget), lbl: _t('stat.budgeted'),   cls: 'neutral' },
      { val: `${pct}%`,        lbl: _t('stat.vs_budget'),  cls: over ? 'red' : 'green' },
    );
  }
  cards.forEach(({ val, lbl, cls }) => {
    const card = document.createElement('div'); card.className = `stat-card ${cls}`;
    card.innerHTML = `<div class="val">${val}</div><div class="lbl">${lbl}</div>`;
    row.appendChild(card);
  });
  return row;
}

// ---------------------------------------------------------------------------
// Stats row (portfolio tab) — KPIs de custo proporcional
// ---------------------------------------------------------------------------
function _buildPortfolioStatsRow(health, trends) {
  const totalCost   = health.reduce((s, d) => s + (d.actual_cost || 0), 0);
  const totalBudget = health
    .filter(d => d.budget_cost != null)
    .reduce((s, d) => s + d.budget_cost, 0);
  const pepsActive  = health.filter(d => d.consumed_hours > 0).length;

  let normalH = 0, extraH = 0, standbyH = 0;
  (trends || []).forEach(r => {
    normalH  += r.normal_hours  || 0;
    extraH   += r.extra_hours   || 0;
    standbyH += r.standby_hours || 0;
  });
  const totalH = normalH + extraH + standbyH;

  const costNormal  = totalH > 0 ? totalCost * (normalH  / totalH) : 0;
  const costExtra   = totalH > 0 ? totalCost * (extraH   / totalH) : 0;
  const costStandby = totalH > 0 ? totalCost * (standbyH / totalH) : 0;

  const pct  = totalBudget > 0 ? (totalCost / totalBudget * 100).toFixed(1) : '—';
  const over = totalBudget > 0 && totalCost > totalBudget;

  const cards = [
    { val: _fmtCost(costNormal),  lbl: _t('stat.cost_normal'),    cls: 'blue'    },
    { val: _fmtCost(costExtra),   lbl: _t('stat.cost_extra'),     cls: 'amber'   },
    { val: _fmtCost(costStandby), lbl: _t('stat.cost_standby'),   cls: 'violet'  },
    { val: _fmtCost(totalCost),   lbl: _t('stat.cost_total'),     cls: 'green'   },
    { val: pepsActive,            lbl: _t('stat.peps_active'),    cls: 'neutral' },
  ];
  if (totalBudget > 0) {
    cards.push(
      { val: _fmtCost(totalBudget),             lbl: _t('stat.budget_cost'),    cls: 'neutral'             },
      { val: pct !== '—' ? `${pct}%` : '—',    lbl: _t('stat.vs_budget_cost'), cls: over ? 'red' : 'green' },
    );
  }

  const row = document.createElement('div');
  row.className = 'stats-row';
  cards.forEach(({ val, lbl, cls }) => {
    const card = document.createElement('div');
    card.className = `stat-card ${cls}`;
    card.innerHTML = `<div class="val">${val}</div><div class="lbl">${lbl}</div>`;
    row.appendChild(card);
  });
  return row;
}

// ---------------------------------------------------------------------------
// Cycles management
// ---------------------------------------------------------------------------
let _cycleEditId = null;
let _allCycles   = [];

async function loadCyclesTable() {
  const showArchived = document.getElementById('showArchivedCycles')?.checked;
  const url = showArchived ? '/api/cycles?include_archived=true' : '/api/cycles';
  try {
    _allCycles = await apiFetch(url);
    _renderCyclesTable(_applySort('cyclesTable', _allCycles));
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

function _renderCyclesTable(cycles) {
  const tbody = document.getElementById('cyclesBody');
  if (!cycles.length) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#475569;padding:2rem">${_t('no_cycles')}</td></tr>`;
    return;
  }
  const admin = _isAdmin();
  tbody.innerHTML = cycles.map(c => `
    <tr style="${!c.is_active ? 'opacity:.5' : ''}">
      <td>${escHtml(c.name)}${!c.is_active ? ' <em style="color:#64748b;font-size:.8rem">(arquivado)</em>' : ''}</td>
      <td>${c.start_date}</td>
      <td>${c.end_date}</td>
      <td><span class="badge-status ativo">${_t('badge.regular')}</span></td>
      <td style="text-align:right">${c.record_count.toLocaleString('pt-BR')}</td>
      <td><div class="actions">
        ${admin ? `<button class="btn btn-sm ${c.is_closed ? 'btn-warning' : 'btn-secondary'}" onclick="toggleCycleLock(${c.id}, ${c.is_closed})" title="${c.is_closed ? _t('title.unlock') : _t('title.lock')}">${c.is_closed ? '🔒' : '🔓'}</button>` : ''}
        ${admin ? `<button class="btn btn-sm btn-secondary" onclick="toggleCycleArchive(${c.id}, ${c.is_active})" title="${c.is_active ? _t('title.archive') : _t('title.restore')}">${c.is_active ? '📦' : '↩'}</button>` : ''}
        <button class="btn btn-secondary btn-sm" onclick="openCycleModal(${c.id})">${_t('btn.edit')}</button>
        <button class="btn btn-danger btn-sm" onclick="deleteCycle(${c.id}, ${escHtml(JSON.stringify(c.name))}, ${c.record_count})">${_t('btn.delete')}</button>
      </div></td>
    </tr>`).join('');
}

async function toggleCycleLock(id, isClosed) {
  if (!confirm(_t(isClosed ? 'confirm.unlock_cycle' : 'confirm.lock_cycle'))) return;
  try {
    await apiFetchJSON(`/api/cycles/${id}/toggle-status`, 'PATCH');
    loadCyclesTable();
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

async function toggleCycleArchive(id, isActive) {
  if (!confirm(_t(isActive ? 'confirm.archive_cycle' : 'confirm.restore_cycle'))) return;
  try {
    await apiFetchJSON(`/api/cycles/${id}/toggle-archive`, 'PATCH');
    loadCyclesTable();
    loadDashboardCycles();
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

document.getElementById('showArchivedCycles').addEventListener('change', loadCyclesTable);

function openCycleModal(id = null) {
  _cycleEditId = id;
  document.getElementById('cycleModalTitle').textContent = id ? _t('cm.title_edit') : _t('cm.title_new');
  document.getElementById('cycleError').textContent = '';
  if (id) {
    const c = _allCycles.find(x => x.id === id);
    if (c) {
      document.getElementById('cycleNameInput').value  = c.name;
      document.getElementById('cycleStartInput').value = c.start_date;
      document.getElementById('cycleEndInput').value   = c.end_date;
    }
  } else {
    document.getElementById('cycleNameInput').value  = '';
    document.getElementById('cycleStartInput').value = '';
    document.getElementById('cycleEndInput').value   = '';
  }
  document.getElementById('cycleModal').hidden = false;
}

function closeCycleModal() { document.getElementById('cycleModal').hidden = true; }

document.getElementById('cycleSaveBtn').addEventListener('click', async () => {
  const body = {
    name:       document.getElementById('cycleNameInput').value.trim(),
    start_date: document.getElementById('cycleStartInput').value,
    end_date:   document.getElementById('cycleEndInput').value,
  };
  if (!body.name || !body.start_date || !body.end_date) {
    document.getElementById('cycleError').textContent = _t('msg.fields_required');
    return;
  }
  try {
    if (_cycleEditId) {
      await apiFetchJSON(`/api/cycles/${_cycleEditId}`, 'PUT', body);
    } else {
      await apiFetchJSON('/api/cycles', 'POST', body);
    }
    closeCycleModal();
    loadCyclesTable();
    loadDashboardCycles();
  } catch (e) {
    document.getElementById('cycleError').textContent = e.message;
  }
});

document.getElementById('cycleCancelBtn').addEventListener('click', closeCycleModal);
document.getElementById('cycleModalClose').addEventListener('click', closeCycleModal);
document.getElementById('newCycleBtn').addEventListener('click', () => openCycleModal());

document.getElementById('cycleSearch').addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  const filtered = q ? _allCycles.filter(c => c.name.toLowerCase().includes(q)) : _allCycles;
  _renderCyclesTable(_applySort('cyclesTable', filtered));
});

async function deleteCycle(id, name, count) {
  if (count > 0) { notify(`Ciclo "${name}" possui ${count} registro(s) e não pode ser excluído.`, 'error'); return; }
  if (!confirm(_t('confirm.delete_cycle'))) return;
  try { await apiFetchJSON(`/api/cycles/${id}`, 'DELETE'); loadCyclesTable(); loadDashboardCycles(); }
  catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

document.getElementById('exportCyclesBtn').addEventListener('click', () => {
  if (!_allCycles.length) { notify(_t('msg.no_cycles_export'), 'info'); return; }
  const header = 'name,start_date,end_date,is_closed,record_count';
  const rows = _allCycles.map(c =>
    `"${c.name}",${c.start_date},${c.end_date},${c.is_closed},${c.record_count}`
  );
  const blob = new Blob(['﻿' + [header, ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement('a'), { href: url, download: 'ciclos.csv' });
  a.click();
  URL.revokeObjectURL(url);
});

document.getElementById('importCyclesInput').addEventListener('change', async e => {
  const file = e.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch('/api/cycles/import', { method: 'POST', headers: _authHeaders(), body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || res.statusText);
    const msg = `${_t('msg.import_done')}: ${data.created} ${_t('msg.created_n')}` +
      (data.errors.length ? `; ${data.errors.length} ${_t('msg.errors_n')}: ${data.errors.slice(0,3).join('; ')}` : '');
    notify(msg, data.errors.length ? 'error' : 'success');
    loadCyclesTable();
    loadDashboardCycles();
  } catch (err) { notify(`Erro na importação: ${err.message}`, 'error'); }
  e.target.value = '';
});

// ---------------------------------------------------------------------------
// Projects management
// ---------------------------------------------------------------------------
let _projectEditId  = null;
let _allProjects    = [];
let _consumedByPep  = {};

async function loadProjectsTable() {
  try {
    const [projects, health] = await Promise.all([
      apiFetch('/api/projects'),
      apiFetch('/api/portfolio-health').catch(() => []),
    ]);
    _allProjects   = projects;
    _consumedByPep = Object.fromEntries(health.map(h => [h.pep_wbs, h.consumed_hours]));
    _renderProjectsTable(_applySort('projectsTable', projects));
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

function _buildBudgetCell(p) {
  if (p.budget_hours == null) return '—';
  const consumed = _consumedByPep[p.pep_wbs];
  const budgetStr = p.budget_hours.toLocaleString('pt-BR') + 'h';
  if (!consumed) return budgetStr;
  const pct = consumed / p.budget_hours;
  const wPct = Math.round(_budgetWarning * 100);
  if (pct >= _budgetCritical) return `${budgetStr}<span class="badge-budget critical" title="${consumed.toFixed(1)}h consumidas">${_t('budget.exceeded')}</span>`;
  if (pct >= _budgetWarning)  return `${budgetStr}<span class="badge-budget warning" title="${consumed.toFixed(1)}h consumidas">${_t('budget.warning')} ≥${wPct}%</span>`;
  return budgetStr;
}

function _renderProjectsTable(projects) {
  const tbody = document.getElementById('projectsBody');
  if (!projects.length) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:#475569;padding:2rem">${_t('no_projects')}</td></tr>`;
    return;
  }
  tbody.innerHTML = projects.map(p => `
    <tr>
      <td><code>${escHtml(p.pep_wbs)}</code></td>
      <td>${escHtml(p.name || '—')}</td>
      <td>${escHtml(p.client || '—')}</td>
      <td>${escHtml(p.manager || '—')}</td>
      <td style="text-align:right">${_buildBudgetCell(p)}</td>
      <td><span class="badge-status ${p.status}">${p.status}</span></td>
      <td><div class="actions">
        <button class="btn btn-secondary btn-sm" onclick="openProjectModal(${p.id})">${_t('btn.edit')}</button>
        ${_isAdmin() ? `<button class="btn btn-secondary btn-sm" onclick="_openAclModal(${p.id}, ${escHtml(JSON.stringify(p.pep_wbs))})">🔑 Acesso</button>` : ''}
        <button class="btn btn-danger btn-sm" onclick="deleteProject(${p.id}, ${escHtml(JSON.stringify(p.pep_wbs))})">${_t('btn.delete')}</button>
      </div></td>
    </tr>`).join('');
}

function openProjectModal(id = null) {
  _projectEditId = id;
  document.getElementById('projectModalTitle').textContent = id ? _t('pm.title_edit') : _t('pm.title_new');
  document.getElementById('projectError').textContent = '';
  if (id) {
    const p = _allProjects.find(x => x.id === id);
    if (p) {
      document.getElementById('projectPepInput').value         = p.pep_wbs;
      document.getElementById('projectNameInput').value        = p.name    || '';
      document.getElementById('projectClientInput').value      = p.client  || '';
      document.getElementById('projectManagerInput').value     = p.manager || '';
      document.getElementById('projectBudgetInput').value      = p.budget_hours ?? '';
      document.getElementById('projectBudgetCostInput').value  = p.budget_cost ?? '';
      document.getElementById('projectStatusInput').value      = p.status;
    }
  } else {
    ['projectPepInput','projectNameInput','projectClientInput','projectManagerInput','projectBudgetInput','projectBudgetCostInput']
      .forEach(fid => { document.getElementById(fid).value = ''; });
    document.getElementById('projectStatusInput').value = 'ativo';
  }
  document.getElementById('projectModal').hidden = false;
}

function closeProjectModal() { document.getElementById('projectModal').hidden = true; }

document.getElementById('projectSaveBtn').addEventListener('click', async () => {
  const pep = document.getElementById('projectPepInput').value.trim();
  if (!pep) { document.getElementById('projectError').textContent = _t('msg.pep_required'); return; }
  const budget     = document.getElementById('projectBudgetInput').value;
  const budgetCost = document.getElementById('projectBudgetCostInput').value;
  const body = {
    pep_wbs:      pep,
    name:         document.getElementById('projectNameInput').value.trim()    || null,
    client:       document.getElementById('projectClientInput').value.trim()  || null,
    manager:      document.getElementById('projectManagerInput').value.trim() || null,
    budget_hours: budget     !== '' ? parseFloat(budget)     : null,
    budget_cost:  budgetCost !== '' ? parseFloat(budgetCost) : null,
    status:       document.getElementById('projectStatusInput').value,
  };
  try {
    if (_projectEditId) {
      await apiFetchJSON(`/api/projects/${_projectEditId}`, 'PUT', body);
    } else {
      await apiFetchJSON('/api/projects', 'POST', body);
    }
    closeProjectModal();
    loadProjectsTable();
  } catch (e) {
    document.getElementById('projectError').textContent = e.message;
  }
});

document.getElementById('projectCancelBtn').addEventListener('click', closeProjectModal);
document.getElementById('projectModalClose').addEventListener('click', closeProjectModal);
document.getElementById('newProjectBtn').addEventListener('click', () => openProjectModal());

document.getElementById('projectSearch').addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  const filtered = q ? _allProjects.filter(p =>
    (p.pep_wbs || '').toLowerCase().includes(q) ||
    (p.name    || '').toLowerCase().includes(q) ||
    (p.client  || '').toLowerCase().includes(q)
  ) : _allProjects;
  _renderProjectsTable(_applySort('projectsTable', filtered));
});

async function deleteProject(id, pep) {
  if (!confirm(_t('confirm.delete_project'))) return;
  try { await apiFetchJSON(`/api/projects/${id}`, 'DELETE'); loadProjectsTable(); }
  catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

// ---------------------------------------------------------------------------
// ACL de projetos — controle de acesso por PEP (item 3)
// ---------------------------------------------------------------------------
let _aclProjectId = null;

async function _openAclModal(projectId, pepWbs) {
  _aclProjectId = projectId;
  document.getElementById('aclModalTitle').textContent = _t('msg.acl_title') + pepWbs;
  document.getElementById('aclError').textContent = '';
  document.getElementById('aclModal').hidden = false;
  await Promise.all([_loadAclEntries(), _populateAclUserSelect()]);
}

async function _loadAclEntries() {
  const tbody = document.getElementById('aclEntriesBody');
  tbody.innerHTML = `<tr><td colspan="2" style="text-align:center;color:#475569;padding:.75rem">${_t('loading')}</td></tr>`;
  try {
    const entries = await apiFetch(`/api/projects/${_aclProjectId}/access`);
    if (!entries.length) {
      tbody.innerHTML = `<tr><td colspan="2" style="text-align:center;color:#475569;padding:.75rem">${_t('msg.no_access_granted')}</td></tr>`;
      return;
    }
    tbody.innerHTML = entries.map(e => `
      <tr>
        <td>${escHtml(e.username)}</td>
        <td style="text-align:right">
          <button class="btn btn-danger btn-sm" onclick="_revokeAccess(${e.user_id})">${_t('btn.revoke')}</button>
        </td>
      </tr>`).join('');
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

async function _populateAclUserSelect() {
  const sel = document.getElementById('aclUserSelect');
  try {
    const users = await apiFetch('/api/users');
    sel.innerHTML = `<option value="">${_t('ms.select_ph')}</option>` +
      users.filter(u => u.role !== 'admin').map(u =>
        `<option value="${u.id}">${escHtml(u.username)}</option>`
      ).join('');
  } catch (_) {}
}

document.getElementById('aclGrantBtn')?.addEventListener('click', async () => {
  const sel = document.getElementById('aclUserSelect');
  const userId = parseInt(sel.value);
  const errEl  = document.getElementById('aclError');
  if (!userId) { errEl.textContent = _t('msg.select_user'); return; }
  errEl.textContent = '';
  try {
    await apiFetchJSON(`/api/projects/${_aclProjectId}/access`, 'POST', { user_id: userId });
    sel.value = '';
    await _loadAclEntries();
  } catch (e) { errEl.textContent = e.message; }
});

async function _revokeAccess(userId) {
  if (!confirm(_t('confirm.revoke_access'))) return;
  try {
    await apiFetchJSON(`/api/projects/${_aclProjectId}/access/${userId}`, 'DELETE');
    await _loadAclEntries();
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

document.getElementById('aclModalClose')?.addEventListener('click', () => { document.getElementById('aclModal').hidden = true; });
document.getElementById('aclModalCloseBtn')?.addEventListener('click', () => { document.getElementById('aclModal').hidden = true; });

document.getElementById('exportProjectsBtn').addEventListener('click', () => {
  if (!_allProjects.length) { notify(_t('msg.no_projects_export'), 'info'); return; }
  const header = 'pep_wbs,name,client,manager,budget_hours,budget_cost,status';
  const esc = v => (v == null ? '' : `"${String(v).replace(/"/g, '""')}"`);
  const rows = _allProjects.map(p =>
    `${esc(p.pep_wbs)},${esc(p.name)},${esc(p.client)},${esc(p.manager)},${p.budget_hours ?? ''},${p.budget_cost ?? ''},${p.status}`
  );
  const blob = new Blob(['﻿' + [header, ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement('a'), { href: url, download: 'projetos.csv' });
  a.click();
  URL.revokeObjectURL(url);
});

document.getElementById('importProjectsInput').addEventListener('change', async e => {
  const file = e.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch('/api/projects/import', { method: 'POST', headers: _authHeaders(), body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || res.statusText);
    const msg = `${_t('msg.import_done')}: ${data.created} ${_t('msg.created_n')}, ${data.updated} ${_t('msg.updated_n')}` +
      (data.errors.length ? `; ${data.errors.length} ${_t('msg.errors_n')}: ${data.errors.slice(0,3).join('; ')}` : '');
    notify(msg, data.errors.length ? 'error' : 'success');
    loadProjectsTable();
  } catch (err) { notify(`Erro na importação: ${err.message}`, 'error'); }
  e.target.value = '';
});

// ---------------------------------------------------------------------------
// Team / RateCard management
// ---------------------------------------------------------------------------
let _allSeniorityLevels = [];
let _allRateCards       = [];
let _allTeam            = [];
let _seniorityEditId    = null;
let _rateCardEditId     = null;
let _assignCollabId     = null;

async function loadTeamTab() {
  await Promise.all([loadSeniorityLevels(), loadRateCards(), loadGlobalConfig()]);
  await loadTeamTable();
}

function _renderSeniorityTable(rows) {
  const tbody = document.getElementById('seniorityBody');
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="2" style="text-align:center;color:#475569;padding:1.5rem">${_t('no_seniority')}</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map(l => `
    <tr>
      <td>${escHtml(l.name)}</td>
      <td><div class="actions">
        <button class="btn btn-secondary btn-sm" onclick="openSeniorityModal(${l.id})">${_t('btn.edit')}</button>
        <button class="btn btn-danger btn-sm" onclick="deleteSeniorityLevel(${l.id}, ${escHtml(JSON.stringify(l.name))})">${_t('btn.delete')}</button>
      </div></td>
    </tr>`).join('');
}

async function loadSeniorityLevels() {
  try {
    _allSeniorityLevels = await apiFetch('/api/seniority-levels');
    _renderSeniorityTable(_applySort('seniorityTable', _allSeniorityLevels));
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

function _renderRateCardsTable(rows) {
  const tbody = document.getElementById('rateCardBody');
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:#475569;padding:1.5rem">${_t('no_rates')}</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map(c => `
    <tr>
      <td>${escHtml(c.seniority_level_name)}</td>
      <td style="text-align:right">R$ ${Number(c.hourly_rate).toLocaleString('pt-BR', {minimumFractionDigits:2})}</td>
      <td>${c.valid_from}</td>
      <td>${c.valid_to ?? '—'}</td>
      <td><div class="actions">
        <button class="btn btn-secondary btn-sm" onclick="openRateCardModal(${c.id})">${_t('btn.edit')}</button>
        <button class="btn btn-danger btn-sm" onclick="deleteRateCard(${c.id})">${_t('btn.delete')}</button>
      </div></td>
    </tr>`).join('');
}

async function loadRateCards() {
  try {
    _allRateCards = await apiFetch('/api/rate-cards');
    _renderRateCardsTable(_applySort('rateCardTable', _allRateCards));
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

function _renderTeamTable(rows) {
  const tbody = document.getElementById('teamBody');
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:#475569;padding:1.5rem">${_t('no_team')}</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map(m => `
    <tr>
      <td>${escHtml(m.name)}</td>
      <td>${m.seniority_level_name ? escHtml(m.seniority_level_name) : '<span style="color:#475569">—</span>'}</td>
      <td style="text-align:right">${m.current_hourly_rate != null ? 'R$ ' + Number(m.current_hourly_rate).toLocaleString('pt-BR', {minimumFractionDigits:2}) : '—'}</td>
      <td><button class="btn btn-secondary btn-sm" onclick="openAssignSeniority(${m.id}, ${escHtml(JSON.stringify(m.name))}, ${m.seniority_level_id ?? 'null'})">${_t('btn.assign')}</button></td>
    </tr>`).join('');
}

async function loadTeamTable() {
  try {
    _allTeam = await apiFetch('/api/team');
    _renderTeamTable(_applySort('teamTable', _allTeam));
    // Populate bulk seniority select
    const bulkSel = document.getElementById('bulkSenioritySelect');
    bulkSel.innerHTML = `<option value="">${_t('as.none_opt')}</option>` +
      _allSeniorityLevels.map(l => `<option value="${l.id}">${escHtml(l.name)}</option>`).join('');
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

// Seniority level modal
function openSeniorityModal(id = null) {
  _seniorityEditId = id;
  document.getElementById('seniorityModalTitle').textContent = id ? _t('sm.title_edit') : _t('sm.title_new');
  document.getElementById('seniorityError').textContent = '';
  const l = id ? _allSeniorityLevels.find(x => x.id === id) : null;
  document.getElementById('seniorityNameInput').value = l ? l.name : '';
  document.getElementById('seniorityModal').hidden = false;
}
function closeSeniorityModal() { document.getElementById('seniorityModal').hidden = true; }

document.getElementById('senioritySaveBtn').addEventListener('click', async () => {
  const name = document.getElementById('seniorityNameInput').value.trim();
  if (!name) { document.getElementById('seniorityError').textContent = _t('msg.name_required'); return; }
  try {
    if (_seniorityEditId) {
      await apiFetchJSON(`/api/seniority-levels/${_seniorityEditId}`, 'PUT', { name });
    } else {
      await apiFetchJSON('/api/seniority-levels', 'POST', { name });
    }
    closeSeniorityModal();
    await loadSeniorityLevels();
  } catch (e) { document.getElementById('seniorityError').textContent = e.message; }
});
document.getElementById('seniorityCancelBtn').addEventListener('click', closeSeniorityModal);
document.getElementById('seniorityModalClose').addEventListener('click', closeSeniorityModal);
document.getElementById('newSeniorityBtn').addEventListener('click', () => openSeniorityModal());

document.getElementById('exportSeniorityBtn').addEventListener('click', () => {
  if (!_allSeniorityLevels.length) { notify(_t('msg.no_levels_export'), 'info'); return; }
  const rows = _allSeniorityLevels.map(l => `"${l.name.replace(/"/g, '""')}"`);
  const blob = new Blob(['﻿' + ['name', ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  Object.assign(document.createElement('a'), { href: url, download: 'senioridade.csv' }).click();
  URL.revokeObjectURL(url);
});

document.getElementById('importSeniorityInput').addEventListener('change', async e => {
  const file = e.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch('/api/seniority-levels/import', { method: 'POST', headers: _authHeaders(), body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || res.statusText);
    const msg = `${_t('msg.import_done')}: ${data.created} ${_t('msg.created_n')}` +
      (data.errors.length ? `; ${data.errors.length} ${_t('msg.errors_n')}: ${data.errors.slice(0, 3).join('; ')}` : '');
    notify(msg, data.errors.length ? 'error' : 'success');
    await loadTeamTab();
  } catch (err) { notify(`Erro na importação: ${err.message}`, 'error'); }
  e.target.value = '';
});

async function deleteSeniorityLevel(id, name) {
  if (!confirm(_t('confirm.delete_level'))) return;
  try { await apiFetchJSON(`/api/seniority-levels/${id}`, 'DELETE'); await loadSeniorityLevels(); }
  catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

// Rate card modal
function _populateLevelSelect(selectId, selectedId = null) {
  const sel = document.getElementById(selectId);
  sel.innerHTML = _allSeniorityLevels.map(l =>
    `<option value="${l.id}" ${l.id === selectedId ? 'selected' : ''}>${escHtml(l.name)}</option>`
  ).join('');
}

function openRateCardModal(id = null) {
  _rateCardEditId = id;
  document.getElementById('rateCardModalTitle').textContent = id ? _t('rm.title_edit') : _t('rm.title_new');
  document.getElementById('rateCardError').textContent = '';
  const c = id ? _allRateCards.find(x => x.id === id) : null;
  _populateLevelSelect('rateCardLevelInput', c?.seniority_level_id ?? null);
  document.getElementById('rateCardRateInput').value = c ? c.hourly_rate : '';
  document.getElementById('rateCardFromInput').value = c ? c.valid_from : '';
  document.getElementById('rateCardToInput').value   = c ? (c.valid_to ?? '') : '';
  document.getElementById('rateCardModal').hidden = false;
}
function closeRateCardModal() { document.getElementById('rateCardModal').hidden = true; }

document.getElementById('rateCardSaveBtn').addEventListener('click', async () => {
  const rate = document.getElementById('rateCardRateInput').value;
  const from = document.getElementById('rateCardFromInput').value;
  if (!rate || !from) { document.getElementById('rateCardError').textContent = _t('msg.fields_required'); return; }
  const to = document.getElementById('rateCardToInput').value;
  const body = {
    seniority_level_id: parseInt(document.getElementById('rateCardLevelInput').value),
    hourly_rate: parseFloat(rate),
    valid_from: from,
    valid_to: to || null,
  };
  try {
    if (_rateCardEditId) {
      await apiFetchJSON(`/api/rate-cards/${_rateCardEditId}`, 'PUT', body);
    } else {
      await apiFetchJSON('/api/rate-cards', 'POST', body);
    }
    closeRateCardModal();
    await loadRateCards();
    await loadTeamTable();
  } catch (e) { document.getElementById('rateCardError').textContent = e.message; }
});
document.getElementById('rateCardCancelBtn').addEventListener('click', closeRateCardModal);
document.getElementById('rateCardModalClose').addEventListener('click', closeRateCardModal);
document.getElementById('newRateCardBtn').addEventListener('click', () => openRateCardModal());

document.getElementById('exportRateCardBtn').addEventListener('click', () => {
  if (!_allRateCards.length) { notify(_t('msg.no_rates_export'), 'info'); return; }
  const esc = v => (v == null || v === '') ? '' : `"${String(v).replace(/"/g, '""')}"`;
  const rows = _allRateCards.map(r =>
    `${esc(r.seniority_level_name)},${r.valid_from},${r.valid_to ?? ''},${r.hourly_rate}`
  );
  const blob = new Blob(['﻿' + ['seniority_level,valid_from,valid_to,hourly_rate', ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  Object.assign(document.createElement('a'), { href: url, download: 'rate_cards.csv' }).click();
  URL.revokeObjectURL(url);
});

document.getElementById('importRateCardInput').addEventListener('change', async e => {
  const file = e.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch('/api/rate-cards/import', { method: 'POST', headers: _authHeaders(), body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || res.statusText);
    const msg = `${_t('msg.import_done')}: ${data.created} ${_t('msg.created_n')}, ${data.updated} ${_t('msg.updated_n')}` +
      (data.errors.length ? `; ${data.errors.length} ${_t('msg.errors_n')}: ${data.errors.slice(0, 3).join('; ')}` : '');
    notify(msg, data.errors.length ? 'error' : 'success');
    await loadTeamTab();
  } catch (err) { notify(`Erro na importação: ${err.message}`, 'error'); }
  e.target.value = '';
});

async function deleteRateCard(id) {
  if (!confirm('Excluir esta taxa?')) return;
  try { await apiFetchJSON(`/api/rate-cards/${id}`, 'DELETE'); await loadRateCards(); await loadTeamTable(); }
  catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

// Assign seniority modal
function openAssignSeniority(collabId, name, currentLevelId) {
  _assignCollabId = collabId;
  document.getElementById('assignSeniorityTitle').textContent = _t('msg.seniority_title') + name;
  document.getElementById('assignSeniorityError').textContent = '';
  const sel = document.getElementById('assignSenioritySelect');
  sel.innerHTML = `<option value="">${_t('as.none_opt')}</option>` +
    _allSeniorityLevels.map(l =>
      `<option value="${l.id}" ${l.id === currentLevelId ? 'selected' : ''}>${escHtml(l.name)}</option>`
    ).join('');
  document.getElementById('assignSeniorityModal').hidden = false;
}
function closeAssignSeniority() { document.getElementById('assignSeniorityModal').hidden = true; }

document.getElementById('assignSenioritySaveBtn').addEventListener('click', async () => {
  const val = document.getElementById('assignSenioritySelect').value;
  const body = { seniority_level_id: val ? parseInt(val) : null };
  try {
    await apiFetchJSON(`/api/team/${_assignCollabId}/seniority`, 'PUT', body);
    closeAssignSeniority();
    await loadTeamTable();
  } catch (e) { document.getElementById('assignSeniorityError').textContent = e.message; }
});
document.getElementById('assignSeniorityCancelBtn').addEventListener('click', closeAssignSeniority);
document.getElementById('assignSeniorityClose').addEventListener('click', closeAssignSeniority);

// Bulk assign seniority
document.getElementById('bulkSeniorityBtn').addEventListener('click', async () => {
  const val = document.getElementById('bulkSenioritySelect').value;
  const label = val
    ? _allSeniorityLevels.find(l => l.id === parseInt(val))?.name
    : _t('as.none_opt');
  if (!confirm(_t('confirm.assign_all'))) return;
  try {
    const body = { seniority_level_id: val ? parseInt(val) : null };
    await apiFetchJSON('/api/team/bulk-seniority', 'PUT', body);
    await loadTeamTable();
    notify(`Senioridade "${label}" atribuída a todos.`, 'success');
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
});

// Global config (multipliers)
let _anomalyMaxHours = 24;
let _budgetWarning  = 0.9;
let _budgetCritical = 1.0;

function _updateBulletLegend() {
  const wPct = Math.round(_budgetWarning  * 100);
  const cPct = Math.round(_budgetCritical * 100);
  const okEl   = document.getElementById('bulletOkLabel');
  const warnEl = document.getElementById('bulletWarnLabel');
  const critEl = document.getElementById('bulletCritLabel');
  if (okEl)   okEl.textContent   = `< ${wPct}%`;
  if (warnEl) warnEl.textContent = `${wPct}–${cPct - 1}%`;
  if (critEl) critEl.textContent = `≥ ${cPct}%`;
}

async function loadGlobalConfig() {
  try {
    const cfg = await apiFetch('/api/config');
    document.getElementById('extraMultiplierInput').value   = cfg.extra_hours_multiplier;
    document.getElementById('standbyMultiplierInput').value = cfg.standby_hours_multiplier;
    if (cfg.anomaly_max_daily_hours) _anomalyMaxHours = cfg.anomaly_max_daily_hours;
    if (cfg.timezone) document.getElementById('timezoneSelect').value = cfg.timezone;
    if (cfg.budget_warning_threshold  != null) { _budgetWarning  = cfg.budget_warning_threshold;  document.getElementById('budgetWarningInput').value  = cfg.budget_warning_threshold; }
    if (cfg.budget_critical_threshold != null) { _budgetCritical = cfg.budget_critical_threshold; document.getElementById('budgetCriticalInput').value = cfg.budget_critical_threshold; }
    _updateBulletLegend();
  } catch (e) { _updateBulletLegend(); /* use defaults */ }
}

document.getElementById('saveConfigBtn').addEventListener('click', async () => {
  const em  = parseFloat(document.getElementById('extraMultiplierInput').value);
  const sm  = parseFloat(document.getElementById('standbyMultiplierInput').value);
  const tz  = document.getElementById('timezoneSelect').value;
  const wt  = parseFloat(document.getElementById('budgetWarningInput').value);
  const ct  = parseFloat(document.getElementById('budgetCriticalInput').value);
  const msg = document.getElementById('configMsg');
  if (isNaN(em) || isNaN(sm) || em <= 0 || sm <= 0 || isNaN(wt) || isNaN(ct) || wt <= 0 || ct <= 0) {
    msg.style.color = _cssVar('--red');
    msg.textContent = _t('msg.positive_numbers');
    return;
  }
  try {
    await apiFetchJSON('/api/config', 'PUT', {
      extra_hours_multiplier: em,
      standby_hours_multiplier: sm,
      anomaly_max_daily_hours: _anomalyMaxHours,
      timezone: tz,
      budget_warning_threshold: wt,
      budget_critical_threshold: ct,
    });
    _budgetWarning  = wt;
    _budgetCritical = ct;
    _updateBulletLegend();
    msg.style.color = _cssVar('--green');
    msg.textContent = _t('msg.config_saved');
    setTimeout(() => { msg.textContent = ''; }, 3000);
  } catch (e) {
    msg.style.color = _cssVar('--red');
    msg.textContent = e.message;
  }
});

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------
function _authHeaders(extra = {}) {
  const token = sessionStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}`, ...extra } : extra;
}

function _getTokenPayload() {
  const token = sessionStorage.getItem('access_token');
  if (!token) return null;
  try { return JSON.parse(atob(token.split('.')[1])); } catch (_) { return null; }
}

function _isAdmin() {
  const p = _getTokenPayload();
  return p ? p.role === 'admin' : false;
}

function _handleUnauthorized() {
  sessionStorage.removeItem('access_token');
  document.getElementById('appShell').hidden = true;
  document.getElementById('loginOverlay').removeAttribute('hidden');
}

async function apiFetch(url) {
  const res = await fetch(url, { headers: _authHeaders() });
  if (res.status === 401) { _handleUnauthorized(); return; }
  if (!res.ok) {
    const j = await res.json().catch(() => ({}));
    throw new Error(j.detail ?? res.statusText);
  }
  return res.json();
}

async function apiFetchJSON(url, method, body) {
  const res = await fetch(url, {
    method,
    headers: _authHeaders({ 'Content-Type': 'application/json' }),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401) { _handleUnauthorized(); return; }
  if (!res.ok) {
    const j = await res.json().catch(() => ({}));
    throw new Error(j.detail ?? res.statusText);
  }
  return res.status === 204 ? null : res.json();
}

function notify(msg, type = 'info') {
  const el = document.getElementById('notification');
  el.textContent = msg; el.className = type; el.style.display = 'block';
  setTimeout(() => { el.style.display = 'none'; }, 6000);
}

function fmt(h) {
  return Number(h).toLocaleString(_locale === 'pt' ? 'pt-BR' : 'en-US', {
    minimumFractionDigits: 1, maximumFractionDigits: 1,
  });
}

function escHtml(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

// ---------------------------------------------------------------------------
// Login form
// ---------------------------------------------------------------------------
document.getElementById('loginForm').addEventListener('submit', async e => {
  e.preventDefault();
  const username = document.getElementById('loginUsername').value.trim();
  const password = document.getElementById('loginPassword').value;
  const errEl    = document.getElementById('loginError');
  errEl.textContent = '';
  try {
    const res = await fetch('/api/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username, password }),
    });
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      errEl.textContent = j.detail ?? _t('msg.invalid_credentials');
      return;
    }
    const { access_token } = await res.json();
    sessionStorage.setItem('access_token', access_token);
    sessionStorage.setItem('username', username);
    document.getElementById('loginOverlay').setAttribute('hidden', '');
    document.getElementById('appShell').removeAttribute('hidden');
    _bootApp();
  } catch (_) {
    errEl.textContent = _t('msg.connection_error');
  }
});

document.getElementById('logoutBtn').addEventListener('click', () => {
  sessionStorage.removeItem('access_token');
  sessionStorage.removeItem('username');
  sessionStorage.removeItem('role');
  document.getElementById('appShell').hidden = true;
  document.getElementById('loginOverlay').removeAttribute('hidden');
});

document.getElementById('collabDetailClose').addEventListener('click', _closeCollabDetail);
document.getElementById('calPrevMonth').addEventListener('click', async () => {
  if (!_selectedCollaborator) return;
  _calMonth--;
  if (_calMonth < 1) { _calMonth = 12; _calYear--; }
  await _renderCollabCalendar(_selectedCollaborator, _calYear, _calMonth);
});
document.getElementById('calNextMonth').addEventListener('click', async () => {
  if (!_selectedCollaborator) return;
  const now = new Date();
  if (_calYear > now.getFullYear() || (_calYear === now.getFullYear() && _calMonth >= now.getMonth() + 1)) return;
  _calMonth++;
  if (_calMonth > 12) { _calMonth = 1; _calYear++; }
  await _renderCollabCalendar(_selectedCollaborator, _calYear, _calMonth);
});
document.getElementById('calMonthInput').addEventListener('change', async () => {
  if (!_selectedCollaborator) return;
  const val = document.getElementById('calMonthInput').value;
  if (!val) return;
  const [y, m] = val.split('-').map(Number);
  _calYear = y; _calMonth = m;
  await _renderCollabCalendar(_selectedCollaborator, _calYear, _calMonth);
});

// ---------------------------------------------------------------------------
// Users management (Admin tab)
// ---------------------------------------------------------------------------
let _allUsers = [];

async function loadUsersTable() {
  try {
    _allUsers = await apiFetch('/api/users');
    _renderUsersTable(_applySort('usersTable', _allUsers));
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

function _renderUsersTable(users) {
  const tbody = document.getElementById('usersBody');
  if (!users.length) {
    tbody.innerHTML = `<tr><td colspan="3" style="text-align:center;color:#475569;padding:2rem">${_t('no_users')}</td></tr>`;
    return;
  }
  const payload = _getTokenPayload();
  const selfId  = payload ? payload.sub : null;
  tbody.innerHTML = users.map(u => `
    <tr>
      <td>${escHtml(u.username)}</td>
      <td><span class="badge-status ${u.role === 'admin' ? 'ativo' : 'quarantine'}">${u.role === 'admin' ? _t('lbl.admin') : _t('lbl.user')}</span></td>
      <td><div class="actions">
        <button class="btn btn-secondary btn-sm" onclick="openPwdModal(${u.id})">${_t('btn.pwd')}</button>
        ${u.username !== selfId ? `<button class="btn btn-danger btn-sm" onclick="deleteUser(${u.id}, ${escHtml(JSON.stringify(u.username))})">${_t('btn.delete')}</button>` : ''}
      </div></td>
    </tr>`).join('');
}

document.getElementById('newUserBtn').addEventListener('click', () => {
  document.getElementById('userUsernameInput').value = '';
  document.getElementById('userPasswordInput').value = '';
  document.getElementById('userRoleSelect').value    = 'user';
  document.getElementById('userError').textContent   = '';
  document.getElementById('userModal').hidden = false;
});

document.getElementById('userModalClose').addEventListener('click',  () => { document.getElementById('userModal').hidden = true; });
document.getElementById('userCancelBtn').addEventListener('click',   () => { document.getElementById('userModal').hidden = true; });

document.getElementById('userSaveBtn').addEventListener('click', async () => {
  const username = document.getElementById('userUsernameInput').value.trim();
  const password = document.getElementById('userPasswordInput').value;
  const role     = document.getElementById('userRoleSelect').value;
  const errEl    = document.getElementById('userError');
  errEl.textContent = '';
  if (!username || !password) { errEl.textContent = _t('msg.fields_required'); return; }
  try {
    await apiFetchJSON('/api/users', 'POST', { username, password, role });
    document.getElementById('userModal').hidden = true;
    loadUsersTable();
    notify(_t('msg.user_created'), 'success');
  } catch (e) { errEl.textContent = e.message; }
});

function openPwdModal(userId) {
  document.getElementById('pwdTargetId').value  = userId;
  document.getElementById('pwdNewInput').value  = '';
  document.getElementById('pwdError').textContent = '';
  document.getElementById('pwdModal').hidden = false;
}

document.getElementById('pwdModalClose').addEventListener('click', () => { document.getElementById('pwdModal').hidden = true; });
document.getElementById('pwdCancelBtn').addEventListener('click',  () => { document.getElementById('pwdModal').hidden = true; });

document.getElementById('pwdSaveBtn').addEventListener('click', async () => {
  const userId      = document.getElementById('pwdTargetId').value;
  const new_password = document.getElementById('pwdNewInput').value;
  const errEl       = document.getElementById('pwdError');
  errEl.textContent = '';
  if (!new_password) { errEl.textContent = _t('msg.pwd_field_required'); return; }
  try {
    await apiFetchJSON(`/api/users/${userId}/password`, 'PATCH', { new_password });
    document.getElementById('pwdModal').hidden = true;
    notify(_t('msg.pwd_changed'), 'success');
  } catch (e) { errEl.textContent = e.message; }
});

async function deleteUser(id, username) {
  if (!confirm(_t('confirm.delete_user'))) return;
  try {
    await apiFetchJSON(`/api/users/${id}`, 'DELETE');
    loadUsersTable();
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

// ---------------------------------------------------------------------------
// Audit Log (Admin tab)
// ---------------------------------------------------------------------------

let _auditLogCache = [];

async function loadAuditLog() {
  const entity = document.getElementById('auditEntityFilter').value;
  const action = document.getElementById('auditActionFilter').value;
  const params = new URLSearchParams({ limit: 200 });
  if (entity) params.set('entity', entity);
  if (action) params.set('action', action);
  try {
    _auditLogCache = await apiFetch(`/api/audit-log?${params}`);
    _renderAuditLog(_applySort('auditTable', _auditLogCache));
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

function _renderAuditLog(rows) {
  const tbody = document.getElementById('auditBody');
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#475569;padding:2rem">${_t('no_audit')}</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map(r => {
    const when = new Date(r.timestamp).toLocaleString(_locale === 'pt' ? 'pt-BR' : 'en-US', { timeZone: 'America/Sao_Paulo', dateStyle: 'short', timeStyle: 'short' });
    let detail = '';
    if (r.detail) {
      try {
        const obj = JSON.parse(r.detail);
        detail = Object.entries(obj).map(([k, v]) => `${k}: ${v}`).join(', ');
      } catch { detail = r.detail; }
    }
    return `<tr>
      <td style="white-space:nowrap">${escHtml(when)}</td>
      <td>${escHtml(r.username || '—')}</td>
      <td><code>${escHtml(r.action)}</code></td>
      <td>${escHtml(r.entity)}</td>
      <td style="text-align:right">${r.entity_id ?? '—'}</td>
      <td style="font-size:.78rem;color:#94a3b8;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escHtml(detail)}">${escHtml(detail)}</td>
    </tr>`;
  }).join('');
}

document.getElementById('auditRefreshBtn').addEventListener('click', loadAuditLog);
document.getElementById('auditEntityFilter').addEventListener('change', loadAuditLog);
document.getElementById('auditActionFilter').addEventListener('change', loadAuditLog);

// ---------------------------------------------------------------------------
// Chart series names (for color picker UI)
// ---------------------------------------------------------------------------
const _CHART_SERIES_NAMES = {
  effortChart:   ['Horas Normais', 'Hora Extra', 'Sobreaviso'],
  trendsChart:   ['Horas Normais', 'Hora Extra', 'Sobreaviso'],
  treemapChart:  [],
  bulletChart:   ['Planejado', 'Realizado'],
  scatterChart:  [],
  forecastChart: ['Realizado', 'Previsto', 'Orçamento'],
};

// ---------------------------------------------------------------------------
// Theme presets
// ---------------------------------------------------------------------------
const _THEME_PRESETS = {
  pmas: {
    color_primary: '#4f8ef7', color_background: '#081122',
    color_surface: '#0e2038', color_accent: '#07b3d7',
    color_success: '#5ad388', color_warning: '#d9b273',
    color_danger:  '#c56d76', color_text: '#e0e0e0',
    color_text_muted: '#818998', density: 'normal',
    chart_palette: ['#4f8ef7','#d9b273','#a78bfa','#35a1f3','#5ad388','#01c1b9'],
  },
  corporate: {
    color_primary: '#0070f3', color_background: '#0a0a23',
    color_surface: '#111133', color_accent: '#00d4ff',
    color_success: '#00c853', color_warning: '#ffab00',
    color_danger:  '#ff1744', color_text: '#f0f4ff',
    color_text_muted: '#7986cb', density: 'normal',
    chart_palette: ['#0070f3','#00d4ff','#00c853','#ffab00','#7c4dff','#26c6da'],
  },
  high_contrast: {
    color_primary: '#ffffff', color_background: '#000000',
    color_surface: '#111111', color_accent: '#ffff00',
    color_success: '#00ff00', color_warning: '#ff8800',
    color_danger:  '#ff0000', color_text: '#ffffff',
    color_text_muted: '#aaaaaa', density: 'relaxed',
    chart_palette: ['#ffffff','#ffff00','#00ff00','#ff8800','#00ffff','#ff00ff'],
  },
};

// ---------------------------------------------------------------------------
// User preferences — populated at login, used by layout + color pickers
// ---------------------------------------------------------------------------
let _userPrefs = null;

async function _loadPreferences() {
  try {
    _userPrefs = await apiFetch('/api/my/preferences');
  } catch {
    _userPrefs = { dashboard: { grid_cols: 2, charts: [] } };
  }
}

// ---------------------------------------------------------------------------
// Theme loader (public endpoint — no auth required)
// ---------------------------------------------------------------------------
const _DENSITY_MAP = {
  compact:  { spacing: '0.45rem', fontSize: '0.78rem' },
  normal:   { spacing: '0.875rem', fontSize: '0.875rem' },
  relaxed:  { spacing: '1.35rem', fontSize: '1rem' },
};

function _getPalette() {
  return window._CHART_PALETTE || ['#4f8ef7','#e94560','#2ecc71','#f39c12','#9b59b6','#1abc9c'];
}

function _resolveSeriesColor(chartId, seriesName, fallbackIndex) {
  const prefs = window._userPrefs?.dashboard?.charts?.find(c => c.id === chartId);
  const custom = prefs?.options?.series_colors?.[seriesName];
  if (custom) return custom;
  const palette = _getPalette();
  return palette[fallbackIndex % palette.length] || '#4f8ef7';
}

async function _loadTheme() {
  try {
    const t = await fetch('/api/theme').then(r => r.json());
    const root = document.documentElement;

    const primary   = t.color_primary    || '#4f8ef7';
    const bg        = t.color_background || '#1a1a2e';
    const surface   = t.color_surface    || '#16213e';
    const accent    = t.color_accent     || '#e94560';
    const success   = t.color_success    || '#2ecc71';
    const warning   = t.color_warning    || '#f39c12';
    const danger    = t.color_danger     || '#e74c3c';
    const text      = t.color_text       || '#e0e0e0';
    const textMuted = t.color_text_muted || '#8892a4';

    // Standard --color-* vars (new CSS)
    root.style.setProperty('--color-primary',    primary);
    root.style.setProperty('--color-background', bg);
    root.style.setProperty('--color-surface',    surface);
    root.style.setProperty('--color-accent',     accent);
    root.style.setProperty('--color-success',    success);
    root.style.setProperty('--color-warning',    warning);
    root.style.setProperty('--color-danger',     danger);
    root.style.setProperty('--color-text',       text);
    root.style.setProperty('--color-text-muted', textMuted);

    // --theme-* aliases (gradient bar, tooltips)
    root.style.setProperty('--theme-primary',    primary);
    root.style.setProperty('--theme-bg',         bg);
    root.style.setProperty('--theme-surface',    surface);
    root.style.setProperty('--theme-accent',     accent);
    root.style.setProperty('--theme-success',    success);
    root.style.setProperty('--theme-warning',    warning);
    root.style.setProperty('--theme-danger',     danger);
    root.style.setProperty('--theme-text',       text);
    root.style.setProperty('--theme-text-muted', textMuted);

    // Original legacy vars — the ones the existing stylesheet actually uses
    // (--bg 3×, --surface 8×, --card 8×, --text 12×, --primary 10×, etc.)
    root.style.setProperty('--bg',        bg);
    root.style.setProperty('--surface',   surface);
    root.style.setProperty('--card',      surface);
    root.style.setProperty('--card-alt',  bg);
    root.style.setProperty('--text',      text);
    root.style.setProperty('--text-2',    textMuted);
    root.style.setProperty('--text-3',    textMuted);
    root.style.setProperty('--primary',   primary);
    root.style.setProperty('--primary-d', primary);
    root.style.setProperty('--primary-g', `linear-gradient(135deg, ${primary} 0%, ${accent} 100%)`);
    root.style.setProperty('--green',     success);
    root.style.setProperty('--amber',     warning);
    root.style.setProperty('--red',       danger);
    root.style.setProperty('--cyan',      accent);

    // Density
    const density = _DENSITY_MAP[t.density] || _DENSITY_MAP.normal;
    root.style.setProperty('--density-spacing',   density.spacing);
    root.style.setProperty('--density-font-size', density.fontSize);

    // Font family
    if (t.font_family) root.style.setProperty('--font-family', t.font_family);

    // Chart palette
    window._CHART_PALETTE = t.chart_palette?.length ? t.chart_palette : undefined;

    // App name
    const appName = t.app_name || 'PMAS';
    document.title = `${appName} — Dashboard`;
    document.querySelectorAll('[data-app-name]').forEach(el => { el.textContent = appName; });

    // Logo
    if (t.logo_url) {
      document.querySelectorAll('[data-app-logo]').forEach(el => { el.src = escHtml(t.logo_url); });
      const box = document.getElementById('headerLogoBox');
      if (box) box.innerHTML = `<img src="${escHtml(t.logo_url)}" class="header-logo-img" alt="Logo" data-app-logo />`;
    }
  } catch (_) { /* silently ignore — not critical */ }
}

// ---------------------------------------------------------------------------
// My Area tab
// ---------------------------------------------------------------------------
let _currentUserInfo = null;

function _switchMyTab(tabId) {
  document.querySelectorAll('.my-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.myTab === tabId);
  });
  document.querySelectorAll('.my-tab-section').forEach(el => {
    el.hidden = el.id !== `my-tab-${tabId}`;
  });
  if (tabId === 'upload') { loadMyHistory(); loadMyQr(); }
}

document.querySelectorAll('.my-tab-btn').forEach(btn => {
  btn.addEventListener('click', () => _switchMyTab(btn.dataset.myTab));
});

function _initMyArea() {
  const usernameEl = document.getElementById('myProfileUsername');
  if (usernameEl) {
    const payload = _getTokenPayload() || {};
    const stored  = sessionStorage.getItem('username') || payload.sub || '—';
    const role    = payload.role || '';
    usernameEl.textContent = `${stored} (${role})`;
    _currentUserInfo = { username: stored, role };
  }
  _initChartLayout();
  _loadMyPreferences();
}

// Chart layout drag-drop
let _sortableLayout = null;
function _initChartLayout() {
  const list = document.getElementById('chartLayoutList');
  if (!list || typeof Sortable === 'undefined') return;
  if (_sortableLayout) _sortableLayout.destroy();
  _sortableLayout = Sortable.create(list, { animation: 150, handle: '.sortable-handle' });
}

async function _loadMyPreferences() {
  try {
    _userPrefs = await apiFetch('/api/my/preferences');
    _applyLayoutPreferences();
    const order = _userPrefs?.dashboard?.chart_order;
    if (Array.isArray(order)) {
      const list = document.getElementById('chartLayoutList');
      if (list) {
        const items = [...list.querySelectorAll('.sortable-item')];
        order.forEach(chartId => {
          const item = items.find(i => i.dataset.chart === chartId);
          if (item) list.appendChild(item);
        });
      }
    }
  } catch (_) {}
}

function _applyLayoutPreferences() {
  const prefs = _userPrefs?.dashboard;
  if (!prefs) return;

  // Sub-tab order (reorder nav buttons + sections)
  const order = prefs.chart_order;
  if (Array.isArray(order) && order.length) {
    const nav = document.querySelector('.analytics-tabs');
    const firstSection = document.querySelector('.atab-section');
    const parent = firstSection?.parentElement;
    order.forEach(tabId => {
      const btn = nav?.querySelector(`[data-atab="${tabId}"]`);
      if (btn) nav.appendChild(btn);
      const section = document.getElementById(`atab-${tabId}`);
      if (section && parent) parent.appendChild(section);
    });
  }

  // Grid columns — apply to each visible atab-section
  if (prefs.grid_cols && prefs.grid_cols > 1) {
    document.querySelectorAll('.atab-section').forEach(s => {
      s.dataset.cols = prefs.grid_cols;
    });
  } else {
    document.querySelectorAll('.atab-section').forEach(s => {
      delete s.dataset.cols;
    });
  }

  // Per-chart size and order (visibility stays under business-logic control)
  (prefs.charts || []).forEach(cp => {
    const panel = document.querySelector(`[data-chart-id="${cp.id}"]`);
    if (!panel) return;
    if (cp.size) panel.dataset.size = cp.size;
    if (cp.order != null) panel.style.order = cp.order;
  });

  Object.values(_charts).forEach(c => {
    try { if (!c.isDisposed()) c.resize(); } catch (_) {}
  });
}

document.getElementById('saveLayoutBtn')?.addEventListener('click', async () => {
  const list = document.getElementById('chartLayoutList');
  if (!list) return;
  const order = [...list.querySelectorAll('.sortable-item')].map(i => i.dataset.chart);
  try {
    _userPrefs = await apiFetchJSON('/api/my/preferences', 'PUT', { dashboard: { chart_order: order } });
    _applyLayoutPreferences();
    notify('Layout salvo.', 'success');
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
});

// My Area — change password
document.getElementById('myChangePwdBtn')?.addEventListener('click', () => {
  document.getElementById('myCurrentPwdInput').value = '';
  document.getElementById('myNewPwdInput').value = '';
  document.getElementById('myPwdError').textContent = '';
  document.getElementById('myPwdModal').removeAttribute('hidden');
});
document.getElementById('myPwdModalClose')?.addEventListener('click', () => {
  document.getElementById('myPwdModal').setAttribute('hidden', '');
});
document.getElementById('myPwdCancelBtn')?.addEventListener('click', () => {
  document.getElementById('myPwdModal').setAttribute('hidden', '');
});
document.getElementById('myPwdSaveBtn')?.addEventListener('click', async () => {
  const currentPwd = document.getElementById('myCurrentPwdInput').value.trim();
  const newPwd     = document.getElementById('myNewPwdInput').value.trim();
  const errEl      = document.getElementById('myPwdError');
  errEl.textContent = '';
  if (!currentPwd || !newPwd) { errEl.textContent = _t('msg.pwd_fill_all'); return; }
  try {
    const stored = sessionStorage.getItem('username') || '';
    // Find own user id first
    const users = await apiFetch('/api/users');
    const me = users.find(u => u.username === stored);
    if (!me) { errEl.textContent = _t('msg.user_not_found'); return; }
    await apiFetchJSON(`/api/users/${me.id}/password`, 'PATCH', {
      new_password: newPwd,
      current_password: currentPwd,
    });
    document.getElementById('myPwdModal').setAttribute('hidden', '');
    notify(_t('msg.pwd_changed'), 'success');
  } catch (e) { errEl.textContent = e.message; }
});

// ---------------------------------------------------------------------------
// My Area — Upload sub-tab
// ---------------------------------------------------------------------------
document.getElementById('myAreaCsvInput')?.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const resultEl = document.getElementById('myAreaUploadResult');
  resultEl.textContent = _t('loading');
  try {
    const fd = new FormData();
    fd.append('file', file);
    const resp = await fetch('/api/upload-timesheet', {
      method: 'POST',
      headers: _authHeaders(),
      body: fd,
    });
    const json = await resp.json();
    if (!resp.ok) throw new Error(json.detail || resp.statusText);
    _showIngestResult(json, file.name);
    const msg = `✅ ${json.records_inserted} ${_t('upload.inserted')}${json.quarantine_records_added ? ` · ⚠ ${json.quarantine_records_added} ${_t('upload.quarantine')}` : ''}`;
    resultEl.textContent = msg;
    notify(msg, json.quarantine_records_added ? 'warning' : 'success');
    _refreshTabBadges();
    loadMyHistory();
    loadMyQr();
  } catch (e) {
    resultEl.textContent = `Erro: ${e.message}`;
    notify(e.message, 'error');
  }
  e.target.value = '';
});

// ---------------------------------------------------------------------------
// My Area — Histórico sub-tab
// ---------------------------------------------------------------------------
let _myHistoryCache = [];

async function loadMyHistory() {
  try {
    _myHistoryCache = await apiFetch('/api/upload-history');
    _renderMyHistory(_applySort('myHistoryTable', _myHistoryCache));
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

function _renderMyHistory(rows) {
  const tbody = document.getElementById('myHistoryBody');
  if (!tbody) return;
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;color:#475569;padding:2rem">${_t('msg.no_import_sessions')}</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map(r => {
    const when = new Date(r.uploaded_at).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo', dateStyle: 'short', timeStyle: 'short' });
    const statusKey = r.status === 'ok' ? 'history.status.ok'
      : r.status === 'warnings' ? 'history.status.warnings'
      : r.status === 'quarantine' ? 'history.status.quarantine'
      : 'history.status.rejected';
    const warnCell = r.warning_count > 0 ? `<strong style="color:${_cssVar('--amber')}">${r.warning_count}</strong>` : '0';
    const infoCell = r.info_count    > 0 ? `<strong style="color:${_cssVar('--primary')}">${r.info_count}</strong>`    : '0';
    return `<tr style="cursor:pointer" onclick="_openSessionDetail(${r.id})" title="Clique para ver detalhes">
      <td style="white-space:nowrap;font-size:.78rem">${escHtml(when)}</td>
      <td style="font-size:.78rem">${escHtml(r.source_file)}</td>
      <td style="font-size:.78rem">${escHtml(r.uploaded_by_username)}</td>
      <td style="text-align:right">${r.records_inserted}</td>
      <td style="text-align:right">${r.records_skipped}</td>
      <td style="text-align:right">${r.quarantine_added > 0 ? `<strong style="color:${_cssVar('--red')}">${r.quarantine_added}</strong>` : '0'}</td>
      <td style="text-align:right">${warnCell}</td>
      <td style="text-align:right">${infoCell}</td>
      <td>${escHtml(_t(statusKey))}</td>
    </tr>`;
  }).join('');
}

document.getElementById('myHistoryRefreshBtn')?.addEventListener('click', loadMyHistory);

// ---------------------------------------------------------------------------
// My Area — Quarentena sub-tab
// ---------------------------------------------------------------------------
let _myQrCache = [];
let _qrPage = 0;
const _QR_PAGE_SIZE = 50;

async function loadMyQr() {
  _qrPage = 0;
  const filter = document.getElementById('myQrFilter')?.value;
  const params = new URLSearchParams({ limit: 500 });
  if (filter === 'pending')   params.set('review_status', 'pending');
  if (filter === 'approved')  params.set('review_status', 'approved');
  if (filter === 'rejected')  params.set('review_status', 'rejected');
  try {
    _myQrCache = await apiFetch(`/api/quarantine?${params}`);
    _qrCache = _myQrCache;
    _renderMyQrTable(_applySort('myQrTable', _myQrCache));
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

function _renderMyQrTable(rows) {
  const tbody = document.getElementById('myQrBody');
  if (!tbody) return;
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:#475569;padding:2rem">${_t('msg.no_quarantine')}</td></tr>`;
    const pg = document.getElementById('myQrPagination');
    if (pg) pg.hidden = true;
    return;
  }
  const totalPages = Math.ceil(rows.length / _QR_PAGE_SIZE);
  _qrPage = Math.min(_qrPage, totalPages - 1);
  const pageRows = rows.slice(_qrPage * _QR_PAGE_SIZE, (_qrPage + 1) * _QR_PAGE_SIZE);
  tbody.innerHTML = pageRows.map(r => {
    const raw  = r.raw_data || {};
    const when = new Date(r.ingested_at).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo', dateStyle: 'short', timeStyle: 'short' });
    return `<tr style="cursor:pointer" onclick="_openQRDetail(${r.id})">
      <td style="font-size:.78rem;white-space:nowrap">${escHtml(when)}</td>
      <td>${escHtml(raw['Colaborador'] || '—')}</td>
      <td style="font-size:.78rem">${escHtml(raw['Data'] || '—')}</td>
      <td style="text-align:right">${raw['Horas totais (decimal)'] ?? '—'}</td>
      <td style="font-size:.78rem">${escHtml(raw['Código PEP'] || '—')}</td>
      <td style="font-size:.78rem;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
          title="${escHtml(r.quarantine_reason)}">${escHtml(r.quarantine_reason)}</td>
      <td>${_qrStatusBadge(r.review_status)}</td>
    </tr>`;
  }).join('');
  const pg = document.getElementById('myQrPagination');
  if (pg) {
    pg.hidden = totalPages <= 1;
    if (!pg.hidden) {
      pg.style.display = 'flex';
      document.getElementById('myQrPageLabel').textContent = `${_t('page.label')} ${_qrPage + 1} ${_t('page.of')} ${totalPages}`;
      document.getElementById('myQrPrevBtn').disabled = _qrPage === 0;
      document.getElementById('myQrNextBtn').disabled = _qrPage >= totalPages - 1;
    }
  }
}

document.getElementById('myQrRefreshBtn')?.addEventListener('click', loadMyQr);
document.getElementById('myQrFilter')?.addEventListener('change', loadMyQr);
document.getElementById('myQrPrevBtn')?.addEventListener('click', () => {
  if (_qrPage > 0) { _qrPage--; _renderMyQrTable(_applySort('myQrTable', _myQrCache)); }
});
document.getElementById('myQrNextBtn')?.addEventListener('click', () => {
  const totalPages = Math.ceil(_myQrCache.length / _QR_PAGE_SIZE);
  if (_qrPage < totalPages - 1) { _qrPage++; _renderMyQrTable(_applySort('myQrTable', _myQrCache)); }
});

// ---------------------------------------------------------------------------
// My Area — Exportar quarentena (item 5)
// ---------------------------------------------------------------------------
document.getElementById('myQrExportBtn')?.addEventListener('click', async () => {
  try {
    const resp = await fetch('/api/my/quarantine/export', { headers: _authHeaders() });
    if (!resp.ok) { notify('Erro ao exportar quarentena.', 'error'); return; }
    const blob = await resp.blob();
    const cd   = resp.headers.get('Content-Disposition') || '';
    const name = cd.match(/filename="([^"]+)"/)?.[1] || 'quarantine_export.csv';
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), { href: url, download: name });
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
});


// ---------------------------------------------------------------------------
// Validation Rules (Admin tab)
// ---------------------------------------------------------------------------
let _rules = [];
let _rulesSortable = null;
let _editingRuleId = null;

async function loadRulesList() {
  try {
    _rules = await apiFetch('/api/validation-rules');
    _renderRulesList();
  } catch (e) { notify(`Erro ao carregar regras: ${e.message}`, 'error'); }
}

function _renderRulesList() {
  const ul = document.getElementById('rulesList');
  if (!ul) return;
  if (!_rules.length) {
    ul.innerHTML = `<li style="text-align:center;color:#475569;padding:1rem;font-size:.85rem">${_t('vr.empty')}</li>`;
    return;
  }
  ul.innerHTML = _rules.map(r => {
    const actionBadge = `<span class="rule-badge ${r.action}">${r.action}</span>`;
    const systemBadge = r.is_system ? `<span class="rule-badge system">🔒 ${_t('vr.badge.system')}</span>` : '';
    const activeClass = r.is_active ? '' : 'rule-inactive';
    const editBtn  = r.is_system ? '' :
      `<button class="btn btn-secondary btn-sm" onclick="openEditRule(${r.id})">✎</button>`;
    const delBtn = r.is_system ? '' :
      `<button class="btn btn-danger btn-sm" onclick="deleteRule(${r.id})">✕</button>`;
    const toggleTitle = _t(r.is_active ? 'vr.btn.deactivate' : 'vr.btn.activate');
    return `<li class="sortable-item ${activeClass}" data-rule-id="${r.id}">
      <span class="sortable-handle">⠿</span>
      <span class="sortable-item-label">
        <strong>${escHtml(r.field)}</strong>
        <span style="color:#64748b;font-size:.75rem;margin:0 .3rem">${escHtml(r.operator)}</span>
        <span style="color:#e2e8f0">${escHtml(r.value || '—')}</span>
        ${r.description ? `<span style="color:#64748b;font-size:.75rem;margin-left:.5rem">— ${escHtml(r.description)}</span>` : ''}
      </span>
      ${actionBadge}${systemBadge}
      <div class="sortable-item-actions">
        <button class="btn btn-secondary btn-sm" title="${toggleTitle}" onclick="toggleRule(${r.id})">${r.is_active ? '⏸' : '▶'}</button>
        ${editBtn}${delBtn}
      </div>
    </li>`;
  }).join('');

  // Init SortableJS on rules list (non-system rules can be reordered)
  if (_rulesSortable) _rulesSortable.destroy();
  _rulesSortable = Sortable.create(ul, {
    animation: 150,
    handle: '.sortable-handle',
    onEnd: async () => {
      const items = [...ul.querySelectorAll('[data-rule-id]')];
      const orderMap = {};
      items.forEach((el, idx) => { orderMap[el.dataset.ruleId] = idx + 1; });
      try {
        await apiFetchJSON('/api/validation-rules/reorder', 'POST', orderMap);
        loadRulesList();
      } catch (e) { notify(`${_t('msg.rule_reorder_error')}: ${e.message}`, 'error'); }
    },
  });
}

const _AGGREGATE_RULE_FIELDS = new Set(['soma_diaria', 'soma_semanal']);

function _updateRuleActionOptions() {
  const field     = document.getElementById('ruleFieldInput')?.value;
  const actionSel = document.getElementById('ruleActionInput');
  const hintEl    = document.getElementById('ruleAggregateHint');
  if (!actionSel) return;
  const isAgg = _AGGREGATE_RULE_FIELDS.has(field);
  [...actionSel.options].forEach(opt => {
    if (opt.value === 'quarentena' || opt.value === 'descarte') {
      opt.disabled = isAgg;
    }
  });
  if (isAgg && (actionSel.value === 'quarentena' || actionSel.value === 'descarte')) {
    actionSel.value = 'warning';
  }
  if (hintEl) hintEl.hidden = !isAgg;
}

function _openRuleModal(rule = null) {
  _editingRuleId = rule ? rule.id : null;
  document.getElementById('ruleModalTitle').textContent = _t(rule ? 'vr.modal.edit' : 'vr.modal.new');
  document.getElementById('ruleFieldInput').value    = rule?.field    || 'horas_individuais';
  document.getElementById('ruleOperatorInput').value = rule?.operator || 'gt';
  document.getElementById('ruleValueInput').value    = rule?.value    || '';
  document.getElementById('ruleActionInput').value   = rule?.action   || 'warning';
  document.getElementById('ruleOrderInput').value    = rule?.order    || 10;
  document.getElementById('ruleActiveInput').value   = rule ? (rule.is_active ? 'true' : 'false') : 'true';
  document.getElementById('ruleDescInput').value     = rule?.description || '';
  document.getElementById('ruleError').textContent   = '';
  _updateRuleActionOptions();
  document.getElementById('ruleModal').removeAttribute('hidden');
}

function openEditRule(id) {
  const rule = _rules.find(r => r.id === id);
  if (rule) _openRuleModal(rule);
}

document.getElementById('ruleFieldInput')?.addEventListener('change', _updateRuleActionOptions);
document.getElementById('newRuleBtn')?.addEventListener('click', () => _openRuleModal());
document.getElementById('ruleModalClose')?.addEventListener('click',  () => document.getElementById('ruleModal').setAttribute('hidden', ''));
document.getElementById('ruleCancelBtn')?.addEventListener('click',   () => document.getElementById('ruleModal').setAttribute('hidden', ''));

document.getElementById('ruleSaveBtn')?.addEventListener('click', async () => {
  const errEl = document.getElementById('ruleError');
  errEl.textContent = '';
  const payload = {
    field:       document.getElementById('ruleFieldInput').value,
    operator:    document.getElementById('ruleOperatorInput').value,
    value:       document.getElementById('ruleValueInput').value || null,
    action:      document.getElementById('ruleActionInput').value,
    order:       parseInt(document.getElementById('ruleOrderInput').value) || 10,
    is_active:   document.getElementById('ruleActiveInput').value === 'true',
    description: document.getElementById('ruleDescInput').value || null,
  };
  try {
    if (_editingRuleId) {
      await apiFetchJSON(`/api/validation-rules/${_editingRuleId}`, 'PUT', payload);
    } else {
      await apiFetchJSON('/api/validation-rules', 'POST', payload);
    }
    document.getElementById('ruleModal').setAttribute('hidden', '');
    loadRulesList();
    notify(_t('vr.saved'), 'success');
  } catch (e) { errEl.textContent = e.message; }
});

async function toggleRule(id) {
  try {
    await apiFetchJSON(`/api/validation-rules/${id}/toggle`, 'PATCH');
    loadRulesList();
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

async function deleteRule(id) {
  if (!confirm('Excluir esta regra?')) return;
  try {
    await apiFetchJSON(`/api/validation-rules/${id}`, 'DELETE');
    loadRulesList();
    notify('Regra excluída.', 'success');
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

// ---------------------------------------------------------------------------
// Quarantine helpers (shared by My Area)
// ---------------------------------------------------------------------------
let _qrCache = [];

function _qrStatusBadge(status) {
  const cls = status === 'approved' ? 'ativo' : status === 'rejected' ? 'rejected' : 'suspenso';
  return `<span class="badge-status ${cls}">${_t('qr.status.' + status)}</span>`;
}

function _openQRDetail(id) {
  const r = _qrCache.find(x => x.id === id);
  if (!r) return;
  const raw = r.raw_data || {};

  document.getElementById('qrModalTitle').textContent = _t('qr.modal.title') + r.id;
  document.getElementById('qrDCollab').textContent    = raw['Colaborador'] || '—';
  document.getElementById('qrDDate').textContent      = raw['Data'] || '—';
  document.getElementById('qrDHours').textContent     = raw['Horas totais (decimal)'] ?? '—';
  document.getElementById('qrDPep').textContent       = (raw['Código PEP'] ? `${raw['Código PEP']} — ${raw['PEP'] || ''}` : '—');
  document.getElementById('qrDExtra').textContent     = raw['Hora extra'] || '—';
  document.getElementById('qrDStandby').textContent   = raw['Hora sobreaviso'] || '—';
  document.getElementById('qrDReason').textContent    = r.quarantine_reason;
  document.getElementById('qrDRule').textContent      = r.rule_description || (r.rule_id ? `Regra #${r.rule_id}` : '—');
  document.getElementById('qrDSession').textContent   = r.upload_session_id ?? '—';
  document.getElementById('qrDStatus').innerHTML      = _qrStatusBadge(r.review_status);
  document.getElementById('qrDReviewedBy').textContent = r.reviewed_by
    ? `${r.reviewed_by} em ${new Date(r.reviewed_at).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo', dateStyle:'short', timeStyle:'short' })}`
    : '—';
  document.getElementById('qrDRawData').textContent   = JSON.stringify(raw, null, 2);

  const isPending = r.review_status === 'pending';
  document.getElementById('qrApproveBtn').hidden = !isPending || !_isAdmin();
  document.getElementById('qrRejectBtn').hidden  = !isPending || !_isAdmin();

  document.getElementById('qrApproveBtn').onclick = () => _doQRAction(id, 'approve');
  document.getElementById('qrRejectBtn').onclick  = () => _doQRAction(id, 'reject');

  document.getElementById('qrDetailModal').removeAttribute('hidden');
}

async function _doQRAction(id, action) {
  try {
    await apiFetchJSON(`/api/quarantine/${id}/${action}`, 'POST', {});
    document.getElementById('qrDetailModal').setAttribute('hidden', '');
    notify(_t(action === 'approve' ? 'msg.qr_approved' : 'msg.qr_rejected'), 'success');
    _refreshTabBadges();
    loadMyQr();
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

document.getElementById('qrModalClose')?.addEventListener('click',    () => document.getElementById('qrDetailModal').setAttribute('hidden', ''));
document.getElementById('qrModalCloseBtn')?.addEventListener('click', () => document.getElementById('qrDetailModal').setAttribute('hidden', ''));


// ---------------------------------------------------------------------------
// Session detail modal
// ---------------------------------------------------------------------------
async function _openSessionDetail(sessionId) {
  try {
    const endpoint = `/api/upload-history/${sessionId}`;
    const r = await apiFetch(endpoint);
    const modal  = document.getElementById('sessionDetailModal');
    const title  = document.getElementById('sessionDetailTitle');
    const meta   = document.getElementById('sessionDetailMeta');
    const counts = document.getElementById('sessionDetailCounts');
    const wDiv   = document.getElementById('sessionDetailWarnings');
    const wList  = document.getElementById('sessionDetailWarningsList');
    const iDiv   = document.getElementById('sessionDetailInfos');
    const iList  = document.getElementById('sessionDetailInfosList');

    const when = new Date(r.uploaded_at).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo', dateStyle: 'short', timeStyle: 'short' });
    title.textContent = `Importação — ${r.source_file}`;
    meta.innerHTML = [
      `<span style="color:#64748b">Data</span><span>${escHtml(when)}</span>`,
      `<span style="color:#64748b">Usuário</span><span>${escHtml(r.uploaded_by_username)}</span>`,
      `<span style="color:#64748b">Arquivo</span><span style="word-break:break-all">${escHtml(r.source_file)}</span>`,
      `<span style="color:#64748b">Status</span><span>${escHtml(r.status)}</span>`,
    ].join('');

    const chip = (label, val, color) =>
      `<span style="background:${color}22;color:${color};border:1px solid ${color}44;border-radius:.3rem;padding:.15rem .6rem;font-size:.78rem">${label}: <strong>${val}</strong></span>`;
    counts.innerHTML =
      chip('Inseridos',  r.records_inserted,        '#2ecc71') +
      chip('Ignorados',  r.records_skipped,          '#94a3b8') +
      chip('Quarentena', r.quarantine_added,         _cssVar('--red')) +
      chip('Avisos',     r.warning_count,            _cssVar('--amber')) +
      chip('Infos',      r.info_count,               '#60a5fa');

    const _exportDetailCsv = (items, label) => {
      const header = 'tipo,mensagem\n';
      const body = items.map(m => `"${label}","${String(m).replace(/"/g, '""')}"`).join('\n');
      const blob = new Blob([header + body], { type: 'text/csv' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `${label.toLowerCase()}_${r.source_file.replace(/\.[^.]+$/, '')}.csv`;
      a.click();
      URL.revokeObjectURL(a.href);
    };

    if (r.warnings_detail?.length) {
      wList.innerHTML = r.warnings_detail.map(w => `<li>${escHtml(w)}</li>`).join('');
      document.getElementById('sessionDetailWarningsHeader').innerHTML =
        `<p style="font-size:.78rem;font-weight:600;color:#f59e0b;margin:0">⚠ Avisos</p>
         <button type="button" id="sdWarnCsvBtn" class="btn btn-secondary btn-sm" style="font-size:.7rem;padding:.1rem .45rem;margin-left:auto">⬇ CSV</button>`;
      setTimeout(() => document.getElementById('sdWarnCsvBtn')?.addEventListener('click', () =>
        _exportDetailCsv(r.warnings_detail, 'Avisos')), 0);
      wDiv.hidden = false;
    } else {
      document.getElementById('sessionDetailWarningsHeader').innerHTML =
        `<p style="font-size:.78rem;font-weight:600;color:#f59e0b;margin:0">⚠ Avisos</p>`;
      wDiv.hidden = true;
    }
    if (r.infos_detail?.length) {
      iList.innerHTML = r.infos_detail.map(i => `<li>${escHtml(i)}</li>`).join('');
      document.getElementById('sessionDetailInfosHeader').innerHTML =
        `<p style="font-size:.78rem;font-weight:600;color:#60a5fa;margin:0">ℹ Informações</p>
         <button type="button" id="sdInfoCsvBtn" class="btn btn-secondary btn-sm" style="font-size:.7rem;padding:.1rem .45rem;margin-left:auto">⬇ CSV</button>`;
      setTimeout(() => document.getElementById('sdInfoCsvBtn')?.addEventListener('click', () =>
        _exportDetailCsv(r.infos_detail, 'Informações')), 0);
      iDiv.hidden = false;
    } else {
      document.getElementById('sessionDetailInfosHeader').innerHTML =
        `<p style="font-size:.78rem;font-weight:600;color:#60a5fa;margin:0">ℹ Informações</p>`;
      iDiv.hidden = true;
    }

    modal.hidden = false;
  } catch (e) { notify(`Erro ao carregar detalhes: ${e.message}`, 'error'); }
}

// ---------------------------------------------------------------------------
// Theme editor (Admin tab)
// ---------------------------------------------------------------------------
const _THEME_FIELDS = [
  { key: 'color_primary',     label: 'Cor primária' },
  { key: 'color_background',  label: 'Fundo' },
  { key: 'color_surface',     label: 'Superfície' },
  { key: 'color_accent',      label: 'Destaque' },
  { key: 'color_success',     label: 'Sucesso' },
  { key: 'color_warning',     label: 'Alerta' },
  { key: 'color_danger',      label: 'Perigo' },
  { key: 'color_text',        label: 'Texto' },
  { key: 'color_text_muted',  label: 'Texto muted' },
];

let _currentTheme = {};

async function _loadThemeEditor() {
  try {
    _currentTheme = await fetch('/api/theme').then(r => r.json());
    _renderThemeEditor();
  } catch (e) { notify(`Erro ao carregar tema: ${e.message}`, 'error'); }
}

function _applyThemePreset(key) {
  const preset = _THEME_PRESETS[key];
  if (!preset) return;
  _THEME_FIELDS.forEach(f => {
    if (preset[f.key]) {
      const picker = document.getElementById(`themeColor_${f.key}`);
      const txt    = document.getElementById(`themeColorTxt_${f.key}`);
      if (picker) picker.value = preset[f.key];
      if (txt)    txt.value   = preset[f.key];
    }
  });
  if (preset.density) {
    document.querySelectorAll('.theme-density-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.density === preset.density);
    });
    const d = _DENSITY_MAP[preset.density] || _DENSITY_MAP.normal;
    document.documentElement.style.setProperty('--density-spacing',   d.spacing);
    document.documentElement.style.setProperty('--density-font-size', d.fontSize);
  }
  if (preset.chart_palette) {
    preset.chart_palette.forEach((c, i) => {
      const picker = document.getElementById(`themePalColor_${i}`);
      const txt    = document.getElementById(`themePalTxt_${i}`);
      if (picker) picker.value = c;
      if (txt)    txt.value   = c;
    });
  }
}

function _renderThemeEditor() {
  const grid = document.getElementById('themeColorGrid');
  if (!grid) return;
  const t   = _currentTheme;
  const pal = t.chart_palette?.length ? t.chart_palette : _THEME_PRESETS.pmas.chart_palette;

  // Section: app name + density
  const densitySection = `
    <div class="form-group full" style="margin-bottom:.25rem">
      <label style="font-size:.75rem;font-weight:600;color:#cbd5e1">${_t('appearance.app_name')}</label>
      <input type="text" id="themeAppName" value="${escHtml(t.app_name || 'PMAS')}"
        style="max-width:240px;margin-top:.25rem" />
    </div>
    <div class="form-group full" style="margin-bottom:.5rem">
      <label style="font-size:.75rem;font-weight:600;color:#cbd5e1">${_t('appearance.density')}</label>
      <div style="display:flex;gap:.5rem;margin-top:.25rem">
        ${['compact','normal','relaxed'].map(d => `
          <button class="btn btn-secondary btn-sm theme-density-btn${(t.density || 'normal') === d ? ' active' : ''}"
            data-density="${d}" type="button">${_t('appearance.density.'+d)}</button>
        `).join('')}
      </div>
    </div>`;

  // Section: presets
  const presetsSection = `
    <div class="form-group full" style="margin-bottom:.5rem">
      <label style="font-size:.75rem;font-weight:600;color:#cbd5e1">${_t('appearance.presets')}</label>
      <div style="display:flex;gap:.5rem;flex-wrap:wrap;margin-top:.25rem">
        ${Object.keys(_THEME_PRESETS).map(k => `
          <button class="btn btn-secondary btn-sm" type="button"
            onclick="_applyThemePreset('${k}')">${_t('appearance.preset.'+k)}</button>
        `).join('')}
      </div>
    </div>`;

  // Section: colors
  const colorSection = `
    <div class="form-group full" style="margin-bottom:.25rem">
      <label style="font-size:.75rem;font-weight:600;color:#cbd5e1">${_t('appearance.colors')}</label>
    </div>
    ${_THEME_FIELDS.map(f => `
      <div class="form-group">
        <label style="font-size:.7rem;color:#94a3b8">${escHtml(f.label)}</label>
        <div class="theme-swatch-row">
          <input type="color" id="themeColor_${f.key}" value="${escHtml(t[f.key] || '#000000')}" />
          <input type="text" id="themeColorTxt_${f.key}" value="${escHtml(t[f.key] || '')}"
            style="flex:1;font-size:.8rem" />
        </div>
      </div>
    `).join('')}`;

  // Section: chart palette
  const paletteSection = `
    <div class="form-group full" style="margin:.5rem 0 .25rem">
      <label style="font-size:.75rem;font-weight:600;color:#cbd5e1">${_t('appearance.palette')}</label>
    </div>
    ${Array.from({ length: 6 }, (_, i) => `
      <div class="form-group">
        <label style="font-size:.7rem;color:#94a3b8">Cor ${i + 1}</label>
        <div class="theme-swatch-row">
          <input type="color" id="themePalColor_${i}" value="${escHtml(pal[i] || '#4f8ef7')}" />
          <input type="text" id="themePalTxt_${i}" value="${escHtml(pal[i] || '')}"
            style="flex:1;font-size:.8rem" />
        </div>
      </div>
    `).join('')}`;

  grid.innerHTML = densitySection + presetsSection + colorSection + paletteSection;

  // Wire color pickers ↔ text inputs
  _THEME_FIELDS.forEach(f => {
    const picker = document.getElementById(`themeColor_${f.key}`);
    const txt    = document.getElementById(`themeColorTxt_${f.key}`);
    picker?.addEventListener('input', () => { txt.value = picker.value; });
    txt?.addEventListener('change',  () => { if (/^#[0-9a-f]{6}$/i.test(txt.value)) picker.value = txt.value; });
  });
  Array.from({ length: 6 }, (_, i) => {
    const picker = document.getElementById(`themePalColor_${i}`);
    const txt    = document.getElementById(`themePalTxt_${i}`);
    picker?.addEventListener('input', () => { txt.value = picker.value; });
    txt?.addEventListener('change',  () => { if (/^#[0-9a-f]{6}$/i.test(txt.value)) picker.value = txt.value; });
  });

  // Density button toggle — apply preview immediately
  grid.querySelectorAll('.theme-density-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      grid.querySelectorAll('.theme-density-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const d = _DENSITY_MAP[btn.dataset.density] || _DENSITY_MAP.normal;
      document.documentElement.style.setProperty('--density-spacing',   d.spacing);
      document.documentElement.style.setProperty('--density-font-size', d.fontSize);
    });
  });
}

document.getElementById('saveThemeBtn')?.addEventListener('click', async () => {
  const payload = { ..._currentTheme };
  _THEME_FIELDS.forEach(f => {
    const txt = document.getElementById(`themeColorTxt_${f.key}`);
    if (txt) payload[f.key] = txt.value;
  });
  const appNameEl = document.getElementById('themeAppName');
  if (appNameEl) payload.app_name = appNameEl.value.trim() || 'PMAS';
  const activeBtn = document.querySelector('.theme-density-btn.active');
  if (activeBtn) payload.density = activeBtn.dataset.density;
  payload.chart_palette = Array.from({ length: 6 }, (_, i) => {
    return document.getElementById(`themePalTxt_${i}`)?.value || _THEME_PRESETS.pmas.chart_palette[i];
  });
  try {
    _currentTheme = await apiFetchJSON('/api/theme', 'PUT', payload);
    _loadTheme();
    notify(_t('appearance.saved'), 'success');
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
});

document.getElementById('restoreDefaultThemeBtn')?.addEventListener('click', () => {
  _applyThemePreset('pmas');
});

document.getElementById('logoUploadInput')?.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  try {
    const resp = await fetch('/api/theme/logo', {
      method: 'POST',
      headers: _authHeaders(),
      body: fd,
    });
    if (!resp.ok) throw new Error((await resp.json()).detail || resp.statusText);
    _currentTheme = await resp.json();
    _loadTheme();
    notify('Logo atualizado.', 'success');
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
  e.target.value = '';
});

document.getElementById('deleteLogoBtn')?.addEventListener('click', async () => {
  if (!confirm('Remover logo personalizado?')) return;
  try {
    _currentTheme = await apiFetchJSON('/api/theme/logo', 'DELETE');
    _loadTheme();
    notify('Logo removido.', 'success');
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
});

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
function _updateHeaderUser() {
  const el = document.getElementById('headerUserInfo');
  if (!el) return;
  const username = sessionStorage.getItem('username') || _getTokenPayload()?.sub || '';
  el.textContent = username || 'PMAS';
}

async function loadSemaphore() {
  const bar = document.getElementById('semaphoreBar');
  if (!bar) return;
  try {
    const data = await apiFetch('/api/portfolio-health');
    if (!data.length) {
      bar.style.display = 'none';
      const hdr = document.getElementById('headerSemaphore');
      if (hdr) hdr.style.display = 'none';
      return;
    }

    const classify = p => {
      if (!p.budget_hours && !p.budget_cost) return 'grey';
      const pctH = p.budget_hours ? p.consumed_hours / p.budget_hours : 0;
      const pctC = p.budget_cost  ? p.actual_cost    / p.budget_cost  : 0;
      const max  = Math.max(pctH, pctC);
      return max >= _budgetCritical ? 'red' : max >= _budgetWarning ? 'yellow' : 'green';
    };

    const wPct = Math.round(_budgetWarning  * 100);
    const cPct = Math.round(_budgetCritical * 100);

    const counts = { green: 0, yellow: 0, red: 0, grey: 0 };
    const pills  = data.map(p => {
      const s = classify(p);
      counts[s]++;
      const pH = p.budget_hours ? (p.consumed_hours / p.budget_hours * 100).toFixed(0) + '% h' : '— h';
      const pC = p.budget_cost  ? (p.actual_cost    / p.budget_cost  * 100).toFixed(0) + '% R$': '— R$';
      const tip = `${p.pep_wbs}: ${pH} · ${pC} — clique para detalhar`;
      return `<span class="sem-project ${s}" data-pep="${escHtml(p.pep_wbs)}" title="${escHtml(tip)}">${escHtml(p.pep_wbs)}</span>`;
    });

    const dot = (cls, label) => counts[cls]
      ? `<span class="sem-count" title="${label}"><span class="sem-dot ${cls}"></span>${counts[cls]}</span>`
      : '';

    const summaryHtml =
      `<span class="sem-title">Portfólio</span>
      ${dot('green',  `OK — abaixo de ${wPct}% do budget`)}
      ${dot('yellow', `Atenção — ≥ ${wPct}% do budget`)}
      ${dot('red',    `Estourado — ≥ ${cPct}% do budget`)}
      ${dot('grey',   'Sem budget definido')}`;

    bar.innerHTML =
      `<div class="sem-summary">${summaryHtml}</div>
      <div class="sem-divider"></div>
      <div class="sem-projects">${pills.join('')}</div>`;
    bar.style.display = 'flex';

    const hdr = document.getElementById('headerSemaphore');
    if (hdr) { hdr.innerHTML = summaryHtml; hdr.style.display = 'flex'; }
  } catch (_) {
    bar.style.display = 'none';
    const hdr = document.getElementById('headerSemaphore');
    if (hdr) hdr.style.display = 'none';
  }
}

// ---------------------------------------------------------------------------
// Semaphore drill-down: click a pill → filter Portfolio tab by that PEP
// ---------------------------------------------------------------------------
document.getElementById('semaphoreBar').addEventListener('click', e => {
  const pill = e.target.closest('[data-pep]');
  if (pill) _drillDownToPep(pill.dataset.pep);
});

async function _drillDownToPep(pepCode) {
  // Navigate to Dashboard tab
  document.querySelector('.tab-btn[data-tab="dashboard"]')?.click();

  // Reset all filters so we fetch the full PEP list, then pin to target PEP
  cycleMs.clear(); pepMs.clear(); pepDescMs.clear(); collaboratorMs.clear();
  document.getElementById('dateFromInput').value = '';
  document.getElementById('dateToInput').value   = '';
  await refreshPeps();
  if (!pepMs.items.some(i => String(i.value) === String(pepCode))) {
    notify(_t('msg.pep_not_available'), 'warning');
    return;
  }
  pepMs.selectOnly(pepCode);
  refreshPepDescriptions();

  // Switch to portfolio sub-tab programmatically and render
  _disposeTabCharts(_activeATab);
  document.querySelectorAll('.atab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.atab-section').forEach(s => { s.hidden = true; });
  const portfolioBtn = document.querySelector('.atab-btn[data-atab="portfolio"]');
  if (portfolioBtn) portfolioBtn.classList.add('active');
  _activeATab = 'portfolio';
  document.getElementById('atab-portfolio').hidden = false;

  await _renderPortfolioTab();
  document.getElementById('runwayPanel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ---------------------------------------------------------------------------
// Tab badges — pending quarantine indicators
// ---------------------------------------------------------------------------
async function _refreshTabBadges() {
  // Admin badge — pending quarantine records (admin only)
  if (_isAdmin()) {
    try {
      const rows = await apiFetch('/api/quarantine?review_status=pending');
      const badge = document.getElementById('adminTabBadge');
      if (badge) {
        const n = rows.length;
        if (n > 0) { badge.textContent = n > 99 ? '99+' : n; badge.removeAttribute('hidden'); }
        else badge.setAttribute('hidden', '');
      }
    } catch (_) {}
  }
  // Minha Área badge — user's own pending quarantine records
  try {
    const rows = await apiFetch('/api/my/quarantine');
    const pending = rows.filter(r => r.review_status === 'pending');
    const badge = document.getElementById('myTabBadge');
    if (badge) {
      const n = pending.length;
      if (n > 0) { badge.textContent = n > 99 ? '99+' : n; badge.removeAttribute('hidden'); }
      else badge.setAttribute('hidden', '');
    }
  } catch (_) {}
}

// ---------------------------------------------------------------------------
// Wire up sortable column headers
// ---------------------------------------------------------------------------
_makeSortable('cyclesTable',
  [{key:'name',type:'str'}, {key:'start_date',type:'date'}, {key:'end_date',type:'date'}, null, {key:'record_count',type:'num'}, null],
  () => { const q = document.getElementById('cycleSearch')?.value?.toLowerCase(); return q ? _allCycles.filter(c => c.name.toLowerCase().includes(q)) : _allCycles; },
  _renderCyclesTable
);
_makeSortable('projectsTable',
  [{key:'pep_wbs',type:'str'}, {key:'name',type:'str'}, {key:'client',type:'str'}, {key:'manager',type:'str'}, {key:'budget_hours',type:'num'}, {key:'status',type:'str'}, null],
  () => { const q = document.getElementById('projectSearch')?.value?.toLowerCase(); return q ? _allProjects.filter(p => (p.pep_wbs||'').toLowerCase().includes(q) || (p.name||'').toLowerCase().includes(q) || (p.client||'').toLowerCase().includes(q)) : _allProjects; },
  _renderProjectsTable
);
_makeSortable('seniorityTable',   [{key:'name',type:'str'}, null], () => _allSeniorityLevels, _renderSeniorityTable);
_makeSortable('rateCardTable',    [{key:'seniority_level_name',type:'str'}, {key:'hourly_rate',type:'num'}, {key:'valid_from',type:'date'}, {key:'valid_to',type:'date'}, null], () => _allRateCards, _renderRateCardsTable);
_makeSortable('teamTable',        [{key:'name',type:'str'}, {key:'seniority_level_name',type:'str'}, {key:'current_hourly_rate',type:'num'}, null], () => _allTeam, _renderTeamTable);
_makeSortable('usersTable',       [{key:'username',type:'str'}, {key:'role',type:'str'}, null], () => _allUsers, _renderUsersTable);
_makeSortable('auditTable',       [{key:'timestamp',type:'date'}, {key:'username',type:'str'}, {key:'action',type:'str'}, {key:'entity',type:'str'}, {key:'entity_id',type:'num'}, null], () => _auditLogCache, _renderAuditLog);
_makeSortable('myHistoryTable',   [{key:'uploaded_at',type:'date'}, {key:'source_file',type:'str'}, {key:'uploaded_by_username',type:'str'}, {key:'records_inserted',type:'num'}, {key:'records_skipped',type:'num'}, {key:'quarantine_added',type:'num'}, {key:'warning_count',type:'num'}, {key:'info_count',type:'num'}, {key:'status',type:'str'}], () => _myHistoryCache, _renderMyHistory);
_makeSortable('myQrTable',        [{key:'ingested_at',type:'date'}, null, null, null, null, {key:'quarantine_reason',type:'str'}, {key:'review_status',type:'str'}], () => _myQrCache, _renderMyQrTable);
_makeSortable('runwayTable',      [{key:'pep_wbs',type:'str'}, {key:'name',type:'str'}, {key:'consumed_hours',type:'num'}, null, {key:'avg_hours_per_cycle',type:'num'}, {key:'cycles_to_complete',type:'num'}, {key:'estimated_completion_cycle',type:'str'}, {key:'spi',type:'num'}, {key:'schedule_status',type:'str'}, {key:'cpi',type:'num'}], () => (_lastRunwayData||[]).filter(r => r.budget_hours != null), _drawRunwayRows);

function _bootApp() {
  if (_isAdmin()) document.getElementById('adminTabBtn').removeAttribute('hidden');
  document.getElementById('langToggleBtn').textContent = _t('btn.lang');
  _applyI18n();
  _loadTheme();
  _loadPreferences().then(() => _applyLayoutPreferences());
  _updateHeaderUser();
  loadDashboardCycles();
  loadSemaphore();
  loadGlobalConfig();
  _refreshTabBadges();
  _renderActiveTab();
}

if (sessionStorage.getItem('access_token')) {
  document.getElementById('loginOverlay').setAttribute('hidden', '');
  document.getElementById('appShell').removeAttribute('hidden');
  _bootApp();
}
