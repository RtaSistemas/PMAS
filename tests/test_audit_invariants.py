"""Data-invariant audit (cycle 3): seeded random data through the real API.

The generator builds cycles, projects, collaborators, rate cards and messy
timesheet files.  After each upload the checks compare summary tables with
raw rows and compare the analytics endpoints with each other.
"""
from __future__ import annotations

import calendar
import io
import math
import random
from collections import defaultdict
from datetime import date, timedelta

import pandas as pd
import pytest

from backend.app.models import (
    CollaboratorCycleSummary, PepCycleSummary, TimesheetRecord,
)

COLS = ["Colaborador", "Data", "Horas totais (decimal)", "Hora extra",
        "Hora sobreaviso", "Código PEP", "PEP"]


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class World:
    def __init__(self, client, seed, n_cycles=3, n_peps=4, n_collabs=5):
        self.c = client
        self.rng = random.Random(seed)
        self.year = 2025
        self.cycles = []
        for m in range(1, n_cycles + 1):
            last = calendar.monthrange(self.year, m)[1]
            r = client.post("/api/cycles", json={
                "name": f"M{m:02d}/{self.year}",
                "start_date": f"{self.year}-{m:02d}-01",
                "end_date": f"{self.year}-{m:02d}-{last:02d}"})
            assert r.status_code == 201, r.text
            self.cycles.append((m, r.json()["id"]))
        self.peps = []
        for i in range(n_peps):
            pep = f"60IT-{100 + i}-01"
            body = {"pep_wbs": pep, "name": f"Proj {i}"}
            if i % 4 != 3:  # some without budget
                body["budget_hours"] = 400.0 + 100 * i
                body["budget_cost"] = 40000.0 + 10000 * i
            r = client.post("/api/projects", json=body)
            assert r.status_code == 201, r.text
            self.peps.append((pep, r.json()["id"]))
        self.levels = []
        for k, nm in enumerate(["Pleno", "Senior"]):
            r = client.post("/api/seniority-levels", json={"name": nm})
            assert r.status_code == 201, r.text
            lvl = r.json()["id"]
            self.levels.append(lvl)
            r = client.post("/api/rate-cards", json={
                "seniority_level_id": lvl, "hourly_rate": 80.0 + 40 * k,
                "valid_from": f"{self.year}-01-01"})
            assert r.status_code == 201, r.text
        self.collabs = [f"Pessoa {chr(65 + i)}" for i in range(n_collabs)]

    def assign_seniority(self):
        team = self.c.get("/api/team").json()
        for i, t in enumerate(team):
            if i % 5 == 4:
                continue  # one without seniority -> cost 0
            r = self.c.put(f"/api/team/{t['id']}/seniority",
                           json={"seniority_level_id": self.levels[i % 2]})
            assert r.status_code == 200, r.text

    def make_file(self, peps, months, fmt=None, messy=True, tag=""):
        """Return (bytes, filename, expected) where expected counts rows."""
        rng = self.rng
        fmt = fmt or rng.choice(["csv", "csv_semi", "xlsx"])
        rows = []
        exp = defaultdict(int)
        seen = set()
        for pep in peps:
            for m in months:
                days = rng.sample(range(1, calendar.monthrange(self.year, m)[1] + 1), 6)
                for d in days:
                    for cname in rng.sample(self.collabs, 3):
                        key = (cname, m, d, pep)
                        if key in seen:
                            continue
                        seen.add(key)
                        h = round(rng.choice([0.5, 1, 2, 4, 6, 7.5, 8]), 2)
                        rows.append(self._row(cname, m, d, h, pep, fmt, rng))
                        exp["ok"] += 1
        if messy:
            kinds = ["future", "bad_date", "bad_hours", "over24", "neg",
                     "no_cycle", "blank_name", "empty_hours"]
            for kind in rng.sample(kinds, 5):
                pep = rng.choice(peps)
                if kind == "future":
                    dt = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
                    rows.append([self.collabs[0], dt, "8", "", "", pep, "d"])
                elif kind == "bad_date":
                    rows.append([self.collabs[0], "31/02/2025x", "8", "", "", pep, "d"])
                elif kind == "bad_hours":
                    rows.append([self.collabs[0], f"{self.year}-01-20", "abc", "", "", pep, "d"])
                elif kind == "over24":
                    rows.append([self.collabs[1], f"{self.year}-01-21", "30", "", "", pep, "d"])
                elif kind == "neg":
                    rows.append([self.collabs[1], f"{self.year}-01-22", "-3", "", "", pep, "d"])
                elif kind == "no_cycle":
                    rows.append([self.collabs[1], "2019-05-14", "8", "", "", pep, "d"])
                elif kind == "blank_name":
                    rows.append(["", f"{self.year}-01-23", "8", "", "", pep, "d"])
                elif kind == "empty_hours":
                    rows.append([self.collabs[2], f"{self.year}-01-24", "", "", "", pep, "d"])
            exp["bad"] = 5
        rng.shuffle(rows)
        exp["rows"] = len(rows)
        name = f"f{tag}.{'xlsx' if fmt == 'xlsx' else 'csv'}"
        df = pd.DataFrame(rows, columns=COLS)
        if fmt == "xlsx":
            buf = io.BytesIO()
            df.to_excel(buf, index=False)
            return buf.getvalue(), name, exp
        if fmt == "csv_semi":
            return df.to_csv(index=False, sep=";").encode("utf-8"), name, exp
        return df.to_csv(index=False).encode("utf-8"), name, exp

    def _row(self, cname, m, d, h, pep, fmt, rng):
        dt = date(self.year, m, d)
        if fmt == "csv_semi":
            ds = dt.strftime("%d/%m/%Y") if d > 12 else dt.isoformat()
            hs = str(h).replace(".", ",")
        elif fmt == "xlsx":
            ds, hs = dt.isoformat(), h
        else:
            ds = dt.isoformat() if rng.random() < .5 else (
                dt.strftime("%d/%m/%Y") if d > 12 else dt.isoformat())
            hs = str(h)
        extra = "Sim" if rng.random() < .1 else ""
        stand = "Sim" if (not extra and rng.random() < .05) else ""
        return [cname, ds, hs, extra, stand, pep, f"{pep} desc"]

    def upload(self, data, name, expect=200):
        r = self.c.post("/api/upload-timesheet", files={"file": (name, data)})
        assert r.status_code == expect, (r.status_code, r.text[:300])
        return r.json()


# ---------------------------------------------------------------------------
# Invariant checks (return a list of violation strings)
# ---------------------------------------------------------------------------

def _close(a, b, tol=1e-6):
    return abs((a or 0) - (b or 0)) <= tol * max(1.0, abs(a or 0), abs(b or 0))


def check_summaries(db):
    v = []
    raw = defaultdict(lambda: [0.0, 0.0])
    rawc = defaultdict(lambda: [0.0, 0.0])
    for r in db.query(TimesheetRecord).all():
        h = (r.normal_hours or 0) + (r.extra_hours or 0) + (r.standby_hours or 0)
        c = (r.normal_cost or 0) + (r.extra_cost or 0) + (r.standby_cost or 0)
        raw[(r.pep_wbs, r.cycle_id)][0] += h
        raw[(r.pep_wbs, r.cycle_id)][1] += c
        rawc[(r.collaborator_id, r.cycle_id)][0] += h
        rawc[(r.collaborator_id, r.cycle_id)][1] += c
    summ = {(s.pep_wbs, s.cycle_id): (s.total_hours, s.total_cost)
            for s in db.query(PepCycleSummary).all()}
    for k in set(raw) | set(summ):
        if k[0] is None:
            continue
        rh, rc = raw.get(k, (0, 0))
        sh, sc = summ.get(k, (0, 0))
        if not (_close(rh, sh) and _close(rc, sc)):
            v.append(f"PepCycleSummary {k}: raw={rh:.4f}/{rc:.2f} summ={sh:.4f}/{sc:.2f}")
    csum = {(s.collaborator_id, s.cycle_id): (s.total_hours, s.total_cost)
            for s in db.query(CollaboratorCycleSummary).all()}
    for k in set(rawc) | set(csum):
        rh, rc = rawc.get(k, (0, 0))
        sh, sc = csum.get(k, (0, 0))
        if not (_close(rh, sh) and _close(rc, sc)):
            v.append(f"CollabCycleSummary {k}: raw={rh:.4f}/{rc:.2f} summ={sh:.4f}/{sc:.2f}")
    return v


def raw_signature(db):
    return sorted(
        (r.collaborator_id, r.cycle_id, str(r.record_date), r.pep_wbs,
         round(r.normal_hours, 6), round(r.extra_hours, 6), round(r.standby_hours, 6),
         round(r.normal_cost, 6), round(r.extra_cost, 6), round(r.standby_cost, 6))
        for r in db.query(TimesheetRecord).all())


def walk_bad_numbers(obj, path="$"):
    out = []
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        out.append(path)
    elif isinstance(obj, dict):
        for k, x in obj.items():
            out += walk_bad_numbers(x, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, x in enumerate(obj):
            out += walk_bad_numbers(x, f"{path}[{i}]")
    return out


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

SEEDS = [1, 2, 3]


@pytest.mark.parametrize("seed", SEEDS)
def test_upload_sessions_account_for_every_row_and_summaries_match(client, db_session, seed):
    w = World(client, seed)
    peps = [p for p, _ in w.peps]
    w.upload(*w.make_file(peps, [1], tag="seed")[:2])  # creates collaborators
    w.assign_seniority()
    for step in range(5):
        sub = w.rng.sample(peps, w.rng.randint(1, 3))
        months = w.rng.sample([m for m, _ in w.cycles], w.rng.randint(1, 2))
        data, name, exp = w.make_file(sub, months, tag=f"{seed}_{step}")
        out = w.upload(data, name)
        total = out["records_inserted"] + out["records_skipped"] + out["quarantine_records_added"]
        assert total == exp["rows"], (step, out, dict(exp))
        db_session.expire_all()
        assert check_summaries(db_session) == []
        sig = raw_signature(db_session)
        out2 = w.upload(data, name)  # same file again: idempotent
        db_session.expire_all()
        assert raw_signature(db_session) == sig
        assert out2["records_inserted"] == out["records_inserted"]
        assert check_summaries(db_session) == []


def _raw_totals(db):
    rows = db.query(TimesheetRecord).all()
    h = sum(r.normal_hours + r.extra_hours + r.standby_hours for r in rows)
    c = sum(r.normal_cost + r.extra_cost + r.standby_cost for r in rows)
    return h, c


def _load(w, db):
    peps = [p for p, _ in w.peps]
    w.upload(*w.make_file(peps, [1], tag="seed")[:2])
    w.assign_seniority()
    for step in range(4):
        sub = w.rng.sample(peps, w.rng.randint(2, 4))
        months = w.rng.sample([m for m, _ in w.cycles], w.rng.randint(1, 3))
        w.upload(*w.make_file(sub, months, tag=f"L{step}")[:2])
    db.expire_all()


def _endpoint_totals(c, peps):
    g = lambda u: c.get(u)
    out = {}
    pf = g("/api/v2/portfolio").json()
    out["portfolio_h"] = sum(x["total_hours"] for x in pf)
    out["portfolio_c"] = sum(x["total_cost"] for x in pf)
    ef = g("/api/v2/effort").json()
    out["effort_h"] = sum(x["total_hours"] for x in ef)
    out["effort_c"] = sum(x["total_cost"] for x in ef)
    tr = g("/api/v2/trends").json()
    out["trends_h"] = sum(x["total_hours"] for x in tr)
    out["trends_c"] = sum(x["actual_cost"] for x in tr)
    rw = g("/api/v2/runway").json()
    out["runway_h"] = sum(x["consumed_hours"] for x in rw)
    out["runway_c"] = sum(x["actual_cost"] for x in rw)
    al = g("/api/v2/allocation").json()
    out["alloc_h"] = sum(x["total_hours"] for x in al)
    out["alloc_c"] = sum(x["total_cost"] for x in al)
    cc = g("/api/v2/concentration").json()
    out["conc_h"] = sum(x["total_hours"] for x in cc)
    out["conc_c"] = sum(x["total_cost"] for x in cc)
    fh = fc = 0.0
    for p in peps:
        f = g(f"/api/v2/forecast?pep_wbs={p}").json()
        fh += f["consumed_hours"] or 0
        fc += f["actual_cost"] or 0
    out["forecast_h"], out["forecast_c"] = fh, fc
    return out


@pytest.mark.parametrize("seed", SEEDS)
def test_endpoints_agree_on_totals_and_fast_path_equals_raw(client, db_session, seed):
    from backend.app.models import CollaboratorCycleSummary, PepCycleSummary
    w = World(client, seed)
    _load(w, db_session)
    peps = [p for p, _ in w.peps]
    rh, rc = _raw_totals(db_session)
    assert rc > 0
    fast = _endpoint_totals(client, peps)
    for k, v in fast.items():
        want = rh if k.endswith("_h") else rc
        assert abs(v - want) < 1e-3, (k, v, want)
    # fast path == raw fallback
    db_session.query(PepCycleSummary).delete()
    db_session.query(CollaboratorCycleSummary).delete()
    db_session.commit()
    slow = _endpoint_totals(client, peps)
    for k in fast:
        assert abs(fast[k] - slow[k]) < 1e-3, (k, fast[k], slow[k])


@pytest.mark.parametrize("seed", SEEDS)
def test_lifecycle_operations_keep_summaries_and_frozen_costs(client, db_session, seed):
    w = World(client, seed)
    _load(w, db_session)
    rng = w.rng
    frozen = raw_signature(db_session)
    # rate-card change must not alter frozen costs
    cards = client.get("/api/rate-cards").json()
    for cd in cards:
        r = client.put(f"/api/rate-cards/{cd['id']}", json={
            "seniority_level_id": cd["seniority_level_id"], "hourly_rate": cd["hourly_rate"] * 3,
            "valid_from": cd["valid_from"], "valid_to": cd.get("valid_to")})
        assert r.status_code == 200, r.text
    db_session.expire_all()
    assert raw_signature(db_session) == frozen
    q = client.get("/api/quarantine?limit=500").json()
    assert q, "generator must produce quarantine rows"
    for i, rec in enumerate(rng.sample(q, min(len(q), 12))):
        act = rng.choice(["approve", "reject", "delete", "approve"])
        if act == "delete":
            r = client.delete(f"/api/quarantine/{rec['id']}")
            assert r.status_code in (204, 404), r.text
        else:
            r = client.post(f"/api/quarantine/{rec['id']}/{act}")
            assert r.status_code in (200, 409, 422, 403), (act, r.status_code, r.text)
        db_session.expire_all()
        assert check_summaries(db_session) == [], (i, act)
    for m, cid in w.cycles:
        for op in ("toggle-status", "toggle-archive", "toggle-status", "toggle-archive"):
            r = client.patch(f"/api/cycles/{cid}/{op}")
            assert r.status_code == 200, r.text
        db_session.expire_all()
        assert check_summaries(db_session) == []
    # Renaming a project with history is blocked
    pep, pid = w.peps[0]
    r = client.put(f"/api/projects/{pid}", json={"pep_wbs": "60IT-999-99", "name": "x"})
    assert r.status_code in (409, 422), r.text
    db_session.expire_all()
    assert check_summaries(db_session) == []


@pytest.mark.parametrize("seed", SEEDS)
def test_evm_identities_and_no_nan_in_any_get(client, db_session, seed):
    w = World(client, seed)
    _load(w, db_session)
    pep0, pid0 = w.peps[0]
    r = client.post(f"/api/projects/{pid0}/baseline", json={"label": "B1"})
    assert r.status_code in (200, 201), r.text
    for m, cid in w.cycles:
        r = client.put(f"/api/projects/{pid0}/plans/{cid}",
                       json={"cycle_id": cid, "planned_hours": 100.0, "planned_cost": 10000.0})
        assert r.status_code == 200, r.text
    client.put(f"/api/projects/{w.peps[1][1]}", json={
        "pep_wbs": w.peps[1][0], "status": "encerrado", "completion_date": "2025-03-31",
        "start_date": "2025-01-01", "budget_hours": 500.0, "budget_cost": 50000.0})
    bad = []
    spec = client.get("/openapi.json").json()["paths"]
    for path, ops in spec.items():
        if "get" not in ops or "{" in path:
            continue
        params = ops["get"].get("parameters", [])
        if any(p["required"] for p in params):
            continue
        r = client.get(path)
        assert r.status_code in (200, 403, 404), (path, r.status_code, r.text[:200])
        if r.headers.get("content-type", "").startswith("application/json"):
            bad += [(path, b) for b in walk_bad_numbers(r.json())]
    checked = []
    for pep, _ in w.peps:
        f = client.get(f"/api/v2/forecast?pep_wbs={pep}").json()
        bad += [(pep, b) for b in walk_bad_numbers(f)]
        ac, bac = f.get("actual_cost"), f.get("budget_cost")
        ev = ac + f["cv"] if f.get("cv") is not None else None  # CV = EV - AC
        if f.get("cpi") is not None and ac and ev is not None:
            assert abs(f["cpi"] - ev / ac) < 2e-4 * max(1, f["cpi"]) + 1e-4, (pep, f["cpi"], ev, ac)
        if bac and ev is not None:
            assert ev <= bac + 0.01, (pep, ev, bac)
        if f.get("eac") is not None and f.get("vac") is not None and bac:
            assert abs(f["vac"] - (bac - f["eac"])) < 0.02, (pep, f["vac"], bac, f["eac"])
        if f.get("eac") is not None and f.get("remaining_cost") is not None and ac is not None \
                and not f.get("is_closed") and bac:
            assert abs(f["remaining_cost"] - (f["eac"] - ac)) < 0.02, (pep, f["remaining_cost"], f["eac"], ac)
        checked.append(pep) if ev is not None else None
    assert checked, "EVM identities were never exercised"
    assert bad == []


def _as_user(user):
    from contextlib import contextmanager
    from fastapi.testclient import TestClient
    from backend.app.database import get_db
    from backend.app.deps import get_current_user
    from backend.app.main import app
    from tests.conftest import _override_get_db

    @contextmanager
    def cm():
        saved = dict(app.dependency_overrides)
        try:
            app.dependency_overrides[get_db] = _override_get_db
            app.dependency_overrides[get_current_user] = lambda: user
            with TestClient(app, raise_server_exceptions=True) as c:
                yield c
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(saved)
    return cm()


@pytest.mark.parametrize("seed", SEEDS)
def test_acl_restricted_user_never_sees_other_peps(client, db_session, seed):
    from backend.app.models import Project, User, UserProjectAccess
    w = World(client, seed)
    _load(w, db_session)
    allowed = [w.peps[0][0], w.peps[1][0]]
    forbidden = [w.peps[2][0], w.peps[3][0]]
    u = User(username="restricted", hashed_password="x", role="user")
    db_session.add(u)
    db_session.commit()
    for pep in allowed:
        pid = db_session.query(Project).filter_by(pep_wbs=pep).one().id
        db_session.add(UserProjectAccess(user_id=u.id, project_id=pid))
    db_session.commit()
    rows = db_session.query(TimesheetRecord).filter(TimesheetRecord.pep_wbs.in_(allowed)).all()
    want_h = sum(r.normal_hours + r.extra_hours + r.standby_hours for r in rows)
    want_c = sum(r.normal_cost + r.extra_cost + r.standby_cost for r in rows)
    forbidden_tokens = forbidden + [f"Proj {i}" for i in (2, 3)] + [f"{p} desc" for p in forbidden]
    leaks = []
    with _as_user(u) as rc:
        urls = [p for p in [
            "/api/v2/portfolio", "/api/v2/portfolio/by-cycle", "/api/v2/effort", "/api/v2/trends",
            "/api/v2/runway", "/api/v2/allocation", "/api/v2/concentration",
            "/api/v2/over-allocation", "/api/v2/filters", "/api/projects",
            "/api/my/alerts", "/api/my/notifications/", "/api/my/upload-history",
            "/api/my/quarantine", "/api/my/quarantine/export", "/api/cycles",
            "/api/team", "/api/summaries/status",
        ]]
        for pep in forbidden:
            urls += [f"/api/v2/portfolio?pep_wbs={pep}", f"/api/v2/effort?pep_wbs={pep}",
                     f"/api/v2/trends?pep_wbs={pep}", f"/api/v2/runway?pep_wbs={pep}",
                     f"/api/v2/allocation?pep_wbs={pep}", f"/api/v2/concentration?pep_wbs={pep}",
                     f"/api/v2/forecast?pep_wbs={pep}", f"/api/v2/portfolio/by-cycle?pep_wbs={pep}",
                     f"/api/v2/runway?pep_description={pep}%20desc",
                     f"/api/v2/concentration?pep_description={pep}%20desc"]
        for url in urls:
            r = rc.get(url)
            assert r.status_code < 500, (url, r.status_code, r.text[:200])
            for tok in forbidden_tokens:
                if tok in r.text:
                    leaks.append((url, r.status_code, tok))
        # sums over allowed PEPs equal the restricted total
        def total(url, hkey, ckey):
            data = rc.get(url).json()
            return (sum(x[hkey] for x in data), sum(x[ckey] for x in data))
        for url, hk, ck in [("/api/v2/portfolio", "total_hours", "total_cost"),
                            ("/api/v2/effort", "total_hours", "total_cost"),
                            ("/api/v2/allocation", "total_hours", "total_cost"),
                            ("/api/v2/concentration", "total_hours", "total_cost"),
                            ("/api/v2/runway", "consumed_hours", "actual_cost"),
                            ("/api/v2/trends", "total_hours", "actual_cost")]:
            h, c = total(url, hk, ck)
            assert abs(h - want_h) < 1e-3 and abs(c - want_c) < 1e-2, (url, h, c, want_h, want_c)
        # summary rows deleted: the raw fallback must give the same for the restricted user
        from backend.app.models import CollaboratorCycleSummary, PepCycleSummary
        db_session.query(PepCycleSummary).delete()
        db_session.query(CollaboratorCycleSummary).delete()
        db_session.commit()
        for url, hk, ck in [("/api/v2/portfolio", "total_hours", "total_cost"),
                            ("/api/v2/effort", "total_hours", "total_cost"),
                            ("/api/v2/trends", "total_hours", "actual_cost")]:
            h, c = total(url, hk, ck)
            assert abs(h - want_h) < 1e-3 and abs(c - want_c) < 1e-2, ("raw", url, h, c)
        # collaborator drill-down must not include forbidden PEP hours
        some = db_session.query(TimesheetRecord).filter(TimesheetRecord.pep_wbs.in_(forbidden)).first()
        from backend.app.models import Collaborator
        name = db_session.get(Collaborator, some.collaborator_id).name
        for url in [f"/api/dashboard/collaborator-timeline?collaborator_name={name}",
                    f"/api/dashboard/collaborator-export?collaborator_name={name}",
                    f"/api/dashboard/collaborator-daily?collaborator_name={name}&year=2025&month=1"]:
            r = rc.get(url)
            for tok in forbidden:
                if tok in r.text:
                    leaks.append((url, tok))
        # forbidden ids
        for pid in [db_session.query(Project).filter_by(pep_wbs=forbidden[0]).one().id]:
            for url in (f"/api/v2/projects/{pid}/monte-carlo",):
                r = rc.get(url)
                assert r.status_code in (403, 404), (url, r.status_code)
            r = rc.post(f"/api/v2/projects/{pid}/simulate", json={})
            assert r.status_code in (403, 404, 422), (r.status_code, r.text[:200])
    assert leaks == []


@pytest.mark.parametrize("seed", [1])
def test_acl_per_project_reads_blocked_for_restricted_user(client, db_session, seed):
    from backend.app.models import Project, User, UserProjectAccess
    w = World(client, seed)
    _load(w, db_session)
    (ok_pep, ok_id), (_, bad_id) = w.peps[0], w.peps[2]
    client.post(f"/api/projects/{bad_id}/baseline", json={"label": "secret"})
    client.put(f"/api/projects/{bad_id}/plans/{w.cycles[0][1]}",
               json={"cycle_id": w.cycles[0][1], "planned_hours": 10.0, "planned_cost": 99.0})
    u = User(username="restricted", hashed_password="x", role="user")
    db_session.add(u)
    db_session.commit()
    db_session.add(UserProjectAccess(user_id=u.id, project_id=ok_id))
    db_session.commit()
    with _as_user(u) as rc:
        for suffix in ("plans", "plans/export", "baselines", "budget-history"):
            r = rc.get(f"/api/projects/{bad_id}/{suffix}")
            assert r.status_code in (403, 404), (suffix, r.status_code, r.text[:120])
            r = rc.get(f"/api/projects/{ok_id}/{suffix}")
            assert r.status_code == 200, (suffix, r.status_code)
