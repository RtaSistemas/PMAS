"""CSV formula injection (WO-001 T4).

A cell that starts with = + - @ tab or CR runs as a formula when Excel opens the file.
Every server export prefixes such a text cell with a single quote. An import removes that quote.
"""
from __future__ import annotations

import csv
import io
import re
from pathlib import Path

import pytest

from backend.app.utils import csv_safe, csv_unsafe, safe_row

ROUTERS = Path(__file__).resolve().parent.parent / "backend" / "app" / "routers"
TRIGGERS = ["=", "+", "-", "@", "\t", "\r"]


class TestCsvSafe:
    @pytest.mark.parametrize("trigger", TRIGGERS)
    def test_trigger_characters_get_a_quote(self, trigger):
        assert csv_safe(f"{trigger}cmd") == f"'{trigger}cmd"

    @pytest.mark.parametrize("text", ["Ana Souza", "A=B", "João-Pedro", "x@y", "", " =x"])
    def test_other_text_is_unchanged(self, text):
        assert csv_safe(text) == text

    def test_none_and_numbers_are_unchanged(self):
        assert csv_safe(None) is None
        assert csv_safe(-5) == -5
        assert csv_safe(-5.5) == -5.5
        assert csv_safe(True) is True

    def test_safe_row_changes_only_text_cells(self):
        assert safe_row(["=A1", -3, None, "ok", "-x"]) == ["'=A1", -3, None, "ok", "'-x"]


class TestCsvUnsafe:
    @pytest.mark.parametrize("trigger", TRIGGERS)
    def test_round_trip_for_each_trigger(self, trigger):
        original = f"{trigger}HYPERLINK(\"x\")"
        assert csv_unsafe(csv_safe(original)) == original

    def test_quote_before_a_normal_character_stays(self):
        assert csv_unsafe("'Maria") == "'Maria"
        assert csv_unsafe("'") == "'"

    def test_none_and_non_text_are_unchanged(self):
        assert csv_unsafe(None) is None
        assert csv_unsafe(5) == 5


class TestEveryCsvRouteUsesTheHelper:
    def test_each_module_that_returns_text_csv_calls_the_helper(self):
        modules = [p for p in ROUTERS.rglob("*.py") if 'media_type="text/csv"' in p.read_text(encoding="utf-8")]
        assert modules, "no CSV route found: the check is broken"
        missing = [p.name for p in modules
                   if not re.search(r"\b(safe_row|csv_safe)\(", p.read_text(encoding="utf-8"))]
        assert missing == []

    def test_no_writerow_in_a_csv_module_skips_the_helper(self):
        """Every data writerow([...]) must wrap its cells; header rows are plain string lists."""
        offenders = []
        for p in ROUTERS.rglob("*.py"):
            src = p.read_text(encoding="utf-8")
            if 'media_type="text/csv"' not in src:
                continue
            for m in re.finditer(r"writerow\(\s*(\[)", src):
                line_no = src[: m.start()].count("\n") + 1
                # A row of plain header literals starts with a quote right after the bracket.
                if not re.match(r"\[\s*[\"']", src[m.start(1):m.start(1) + 40]):
                    offenders.append(f"{p.name}:{line_no}")
        assert offenders == []


class TestExportsAreSafeAndRoundTrip:
    def test_seniority_export_is_safe_and_reimports_to_the_same_name(self, client, db_session):
        from backend.app.models import SeniorityLevel
        db_session.add(SeniorityLevel(name='=HYPERLINK("x")'))
        db_session.commit()
        body = client.get("/api/seniority-levels/export").text
        cells = [row[0] for row in csv.reader(io.StringIO(body))][1:]
        assert cells == ["'=HYPERLINK(\"x\")"]

        db_session.query(SeniorityLevel).delete()
        db_session.commit()
        res = client.post("/api/seniority-levels/import", files={"file": ("s.csv", body.encode(), "text/csv")})
        assert res.status_code == 200 and res.json()["created"] == 1
        assert [lv.name for lv in db_session.query(SeniorityLevel)] == ['=HYPERLINK("x")']

    def test_rate_card_export_prefixes_the_level_name(self, client, db_session):
        from datetime import date
        from backend.app.models import RateCard, SeniorityLevel
        level = SeniorityLevel(name="-Senior")
        db_session.add(level)
        db_session.flush()
        db_session.add(RateCard(seniority_level_id=level.id, hourly_rate=100.0, valid_from=date(2026, 1, 1)))
        db_session.commit()
        rows = list(csv.reader(io.StringIO(client.get("/api/rate-cards/export").text)))
        assert rows[1][0] == "'-Senior"
        assert rows[1][3] == "100.0"           # numbers stay numbers

    def test_plan_export_prefixes_the_cycle_name_and_reimports(self, client, db_session):
        from datetime import date
        from backend.app.models import Cycle, Project, ProjectCyclePlan
        project = Project(pep_wbs="AB-0001", name="P")
        cycle = Cycle(name="=Ciclo 1", start_date=date(2026, 1, 1), end_date=date(2026, 1, 31))
        db_session.add_all([project, cycle])
        db_session.flush()
        db_session.add(ProjectCyclePlan(project_id=project.id, cycle_id=cycle.id, planned_hours=10.0))
        db_session.commit()
        body = client.get(f"/api/projects/{project.id}/plans/export").text
        rows = list(csv.reader(io.StringIO(body)))
        assert rows[1][1] == "'=Ciclo 1"

        db_session.query(ProjectCyclePlan).delete()
        db_session.commit()
        res = client.post("/api/projects/plans/import", files={"file": ("p.csv", body.encode(), "text/csv")})
        assert res.status_code == 200 and res.json()["created"] == 1

    def test_preset_export_is_safe_and_reimports_to_the_same_name(self, client, db_session):
        from backend.app.models import ThemePreset
        db_session.add(ThemePreset(name="@preset", is_builtin=False, config={}))
        db_session.commit()
        body = client.get("/api/theme/presets/export").text
        rows = list(csv.reader(io.StringIO(body)))
        assert rows[-1][0] == "'@preset"

        db_session.query(ThemePreset).delete()
        db_session.commit()
        client.post("/api/theme/presets/import", files={"file": ("t.csv", body.encode(), "text/csv")})
        assert [p.name for p in db_session.query(ThemePreset)] == ["@preset"]


class TestImportsRemoveTheQuote:
    def test_project_import_restores_the_text(self, client, db_session):
        from backend.app.models import Project
        csv_text = "pep_wbs,name,client,manager\nAB-0002,'=HYPERLINK(\"x\"),'-Cliente,Maria\n"
        res = client.post("/api/projects/import", files={"file": ("p.csv", csv_text.encode(), "text/csv")})
        assert res.status_code == 200 and res.json()["created"] == 1
        p = db_session.query(Project).filter_by(pep_wbs="AB-0002").one()
        assert (p.name, p.client, p.manager) == ('=HYPERLINK("x")', "-Cliente", "Maria")

    def test_cycle_import_restores_the_text(self, client, db_session):
        from backend.app.models import Cycle
        csv_text = "name,start_date,end_date\n'=Jan,2026-01-01,2026-01-31\n"
        res = client.post("/api/cycles/import", files={"file": ("c.csv", csv_text.encode(), "text/csv")})
        assert res.status_code == 200 and res.json()["created"] == 1
        assert db_session.query(Cycle).one().name == "=Jan"
