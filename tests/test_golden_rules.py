"""
Static-analysis tests enforcing PMAS Golden Rules and code quality invariants.

These tests scan source files for patterns that are FORBIDDEN by the
architectural constraints defined in CLAUDE.md. They catch silent bugs
(wrong locale, bypassed currency factor, EVM logic outside evm.py) that
unit/integration tests would miss because the behaviour only breaks at
runtime when specific settings are active.

GR-2: All EVM formulas live exclusively in services/evm.py.
GR-3: Chart data-series colors must use _getPalette() / _cssVar().
      Hardcoded hex literals in chart options are forbidden.
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
FRONTEND = ROOT / "frontend"
BACKEND_ROUTERS = ROOT / "backend" / "app" / "routers"

# ── helpers ───────────────────────────────────────────────────────────────────

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ── GR-2: No EVM formulas outside evm.py ─────────────────────────────────────

EVM_FORMULA_NAMES = [
    "compute_cpi",
    "compute_spi",
    "compute_eac",
    "compute_tcpi",
    "compute_vac",
    "compute_cv",
    "compute_sv",
    "compute_ev_capped",
    "compute_earned_schedule",
    "compute_spi_t",
    "compute_sv_t",
    "compute_ieac_t",
    "compute_eac_schedule",
]

_EVM_DEF_RE = re.compile(
    r"\bdef\s+(" + "|".join(EVM_FORMULA_NAMES) + r")\s*\("
)


def test_gr2_no_evm_formulas_in_routers():
    """GR-2: EVM formula implementations must not appear in any router."""
    violations = []
    for py_file in BACKEND_ROUTERS.rglob("*.py"):
        source = _read(py_file)
        for m in _EVM_DEF_RE.finditer(source):
            line_no = source[: m.start()].count("\n") + 1
            violations.append(f"{py_file.relative_to(ROOT)}:{line_no}: defines {m.group(1)}")

    assert not violations, (
        "GR-2 violation — EVM formula(s) defined outside services/evm.py:\n"
        + "\n".join(violations)
    )


def test_gr2_no_evm_formulas_in_frontend():
    """GR-2: EVM formula implementations must not appear in frontend JS."""
    _JS_EVM_DEF_RE = re.compile(
        r"\bfunction\s+(" + "|".join(EVM_FORMULA_NAMES) + r")\s*\("
    )
    violations = []
    for js_file in FRONTEND.rglob("*.js"):
        source = _read(js_file)
        for m in _JS_EVM_DEF_RE.finditer(source):
            line_no = source[: m.start()].count("\n") + 1
            violations.append(f"{js_file.relative_to(ROOT)}:{line_no}: defines {m.group(1)}")

    assert not violations, (
        "GR-2 violation — EVM formula(s) re-implemented in frontend JS:\n"
        + "\n".join(violations)
    )


# ── GR-3: No hardcoded hex in ECharts chart option color properties ───────────
#
# Detect `color: '#xxx'` or `color: "#xxx"` in JavaScript object property
# syntax (colon then space then quoted hex). This matches ECharts option
# objects. It does NOT match CSS inline styles (which use `color:#xxx`
# without a space before the hash).

_ECHARTS_HEX_RE = re.compile(
    r"(?:color|borderColor|shadowColor)\s*:\s+['\"]#[0-9A-Fa-f]{3,8}['\"]"
)


def test_gr3_no_hex_in_chart_color_properties():
    """GR-3: ECharts option color properties must not use hardcoded hex literals."""
    files_to_check = (
        [FRONTEND / "app.js"]
        + list((FRONTEND / "crud").glob("*.js"))
        + list((FRONTEND / "charts").glob("*.js"))
        + list((FRONTEND / "tabs").glob("*.js"))
    )
    violations = []
    for path in files_to_check:
        if not path.exists():
            continue
        source = _read(path)
        for m in _ECHARTS_HEX_RE.finditer(source):
            line_no = source[: m.start()].count("\n") + 1
            ctx = source[max(0, m.start() - 60) : m.end() + 60].replace("\n", " ")
            violations.append(f"{path.name}:{line_no}: …{ctx.strip()}…")

    assert not violations, (
        "GR-3 violation — hardcoded hex in ECharts color property "
        "(use _cssVar() or _getPalette()):\n"
        + "\n".join(violations)
    )


# ── GR-3 fallback: no `|| '#hex'` as color fallbacks ─────────────────────────
#
# _cssVar() always resolves from the configured theme CSS variables.  Using
# || '#hex' as a fallback bypasses the admin-configured palette and hardcodes
# a specific color.  The CSS variables are guaranteed to be defined by style.css,
# so fallbacks are unnecessary and violate GR-3.

_HEX_FALLBACK_RE = re.compile(r"\|\|\s*['\"]#[0-9A-Fa-f]{3,8}['\"]")


def test_gr3_no_hex_fallback_in_charts():
    """GR-3: No `|| '#hex'` fallback patterns in chart files."""
    charts_dir = FRONTEND / "charts"
    violations = []
    for path in charts_dir.glob("*.js"):
        if not path.exists():
            continue
        source = _read(path)
        for m in _HEX_FALLBACK_RE.finditer(source):
            line_no = source[: m.start()].count("\n") + 1
            ctx = source[max(0, m.start() - 60) : m.end() + 60].replace("\n", " ")
            violations.append(f"{path.name}:{line_no}: …{ctx.strip()}…")

    assert not violations, (
        "GR-3 violation — || '#hex' fallback in chart file "
        "(CSS variables are always defined; remove the fallback):\n"
        + "\n".join(violations)
    )


# ── Locale bypass: no hardcoded 'pt-BR' in number/date formatters ─────────────
#
# All .toLocaleString() calls must use the _locale variable so they respond
# to the user's language selection. Pattern: `.toLocaleString('pt-BR', ...)`
# Any remaining literal 'pt-BR' is a bypass.

_HARDCODED_PTBR_RE = re.compile(r"\.toLocaleString\(['\"]pt-BR['\"]")


def test_no_hardcoded_pt_br_locale_in_app_js():
    """All toLocaleString calls must use the _locale variable, not 'pt-BR'."""
    files_to_check = [
        FRONTEND / "app.js",
        FRONTEND / "crud" / "cycles.js",
        FRONTEND / "crud" / "projects.js",
    ]
    violations = []
    for path in files_to_check:
        if not path.exists():
            continue
        source = _read(path)
        for m in _HARDCODED_PTBR_RE.finditer(source):
            line_no = source[: m.start()].count("\n") + 1
            ctx = source[max(0, m.start() - 40) : m.end() + 40].replace("\n", " ")
            violations.append(f"{path.name}:{line_no}: …{ctx.strip()}…")

    assert not violations, (
        "Locale bypass — hardcoded 'pt-BR' in toLocaleString "
        "(use _locale === 'pt' ? 'pt-BR' : 'en-US'):\n"
        + "\n".join(violations)
    )


def test_no_hardcoded_pt_br_locale_in_utils_js():
    """formatCost in utils.js must use the locale parameter, not hardcode 'pt-BR'."""
    utils_js = FRONTEND / "utils.js"
    source = _read(utils_js)
    violations = []
    for m in _HARDCODED_PTBR_RE.finditer(source):
        line_no = source[: m.start()].count("\n") + 1
        ctx = source[max(0, m.start() - 40) : m.end() + 40].replace("\n", " ")
        violations.append(f"utils.js:{line_no}: …{ctx.strip()}…")

    assert not violations, (
        "Locale bypass in utils.js — toLocaleString must use the locale parameter:\n"
        + "\n".join(violations)
    )


# ── Currency: no hardcoded 'R$' currency symbol in string literals ────────────
#
# The literal string 'R$' or "R$" as a standalone value in rendering
# contexts bypasses _currencySymbol. Allowed: inside _LANG translation
# table, as default value in _currencySymbol = 'R$', inside CSS or HTML
# attribute comments, and as the symbol parameter default in utils.js.
#
# We specifically look for patterns where 'R$' appears in string concatenation
# or as a chart axis name — these are the real display bypass patterns.
# Allowed: `|| 'R$'` (safe fallback), inside _LANG block,
# `_currencySymbol = symbol || 'R$'` initialization.
#
# Patterns representing actual rendering bypasses:
#   name: 'R$'       — ECharts axis name (should be _currencySymbol)
#   + '% R$'         — concat with percent suffix
#   + '- R$'         — concat with dash suffix
_RS_RENDERING_RE = re.compile(
    r"name\s*:\s*['\"]R\$['\"]"
    r"|[+]\s*['\"]['%\-\u2014 ]*R\$['\"]"
    r"|['\"']R\$['%\-\u2014 ]*['\"]\s*[+]"
)

_RS_INIT_RE = re.compile(r"_currencySymbol\s*=")


def test_no_standalone_r_dollar_in_app_js():
    """Monetary display code must use _currencySymbol, not the literal 'R$'."""
    app_js = FRONTEND / "app.js"
    source = _read(app_js)

    # Allowed ranges: any _currencySymbol assignment context + the _LANG block
    allowed_ranges: list[tuple[int, int]] = []
    for m in _RS_INIT_RE.finditer(source):
        fn_end = source.find("\n}", m.start()) + 2
        allowed_ranges.append((max(0, m.start() - 300), fn_end))
    lang_start = source.find("const _LANG")
    lang_end   = source.find("\n};", lang_start) + 3 if lang_start != -1 else -1
    if lang_start != -1:
        allowed_ranges.append((lang_start, lang_end))

    def _in_allowed(pos: int) -> bool:
        return any(s <= pos <= e for s, e in allowed_ranges)

    violations = []
    for m in _RS_RENDERING_RE.finditer(source):
        if _in_allowed(m.start()):
            continue
        line_no = source[: m.start()].count("\n") + 1
        ctx = source[max(0, m.start() - 40) : m.end() + 40].replace("\n", " ")
        violations.append(f"app.js:{line_no}: ...{ctx.strip()}...")

    assert not violations, (
        "Currency bypass -- hardcoded 'R$' in rendering context "
        "(use _currencySymbol):\n" + "\n".join(violations)
    )


# ── _currencyFactor: monetary raw values must go through _fmtCost ─────────────
#
# A .toLocaleString() call with minimumFractionDigits:2 on a non-Date value
# bypasses _fmtCost and therefore ignores _currencyFactor.
# We exclude:
#   - the _fmtCost function body itself (which correctly calls toLocaleString)
#   - calls that use the _locale variable pattern (they're using the correct
#     locale but must still go through _fmtCost for the currency factor)
#
# NOTE: This pattern catches BOTH 'pt-BR' hardcoded AND _locale-variable
# monetary calls. All monetary display must route through _fmtCost().

_CURRENCY_BYPASS_RE = re.compile(
    r"\.toLocaleString\([^)]*minimumFractionDigits\s*:\s*2"
)


def test_no_currency_tolocalestring_bypass_in_app_js():
    """Monetary values must use _fmtCost(), not raw toLocaleString with decimals."""
    app_js = FRONTEND / "app.js"
    source = _read(app_js)

    # Exclude _fmtCost function body
    fmtcost_start = source.find("function _fmtCost(")
    fmtcost_end = source.find("\n}", fmtcost_start) + 2 if fmtcost_start != -1 else -1

    violations = []
    for m in _CURRENCY_BYPASS_RE.finditer(source):
        pos = m.start()
        if fmtcost_start != -1 and fmtcost_start <= pos <= fmtcost_end:
            continue
        line_no = source[:pos].count("\n") + 1
        ctx = source[max(0, pos - 60) : m.end() + 40].replace("\n", " ")
        violations.append(f"app.js:{line_no}: …{ctx.strip()}…")

    assert not violations, (
        "_currencyFactor bypass — use _fmtCost() instead of raw toLocaleString "
        "with minimumFractionDigits:2:\n" + "\n".join(violations)
    )
