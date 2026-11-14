#!/usr/bin/env python3
"""Check English text against the PMAS STE profile (see docs/STE-GUIDE.md).

Usage: python scripts/ste_check.py FILE [FILE ...] [--verbose]
Supports .md files and frontend/lang/en.js. Prints the share of passing sentences.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MAX_WORDS = 25
CONTRACTION = re.compile(r"\b\w+(?:n't|'re|'ve|'ll|'d|'s)\b", re.I)
FILLER = re.compile(r"\b(please|simply|just|etc\.?|e\.g\.|i\.e\.)(?=\W|$)", re.I)
VAGUE = re.compile(r"\b(should|might|may)\b", re.I)
PASSIVE = re.compile(
    r"\b(is|are|was|were|be|been|being)\s+"
    r"(\w+ed|shown|made|done|given|taken|seen|written|stored|set|sent|run|found|built|chosen)\b",
    re.I,
)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def _extract_md(text: str) -> list[str]:
    out, in_code = [], False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not s or s.startswith(("|", "#", ">", "---", "<", "title:", "version:")):
            continue
        s = re.sub(r"^([-*]|\d+\.)\s+", "", s)
        s = re.sub(r"`[^`]*`", "X", s)
        s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
        s = re.sub(r"[*_]{1,2}", "", s)
        out.append(s)
    return out


def _extract_lang(text: str) -> list[str]:
    values = re.findall(r"'[\w.\-]+'\s*:\s*'((?:[^'\\]|\\.)*)'", text)
    return [re.sub(r"<[^>]+>", "", v.replace("\\'", "'")) for v in values]


def _violations(sentence: str) -> list[str]:
    found = []
    if len(sentence.split()) > MAX_WORDS:
        found.append("length")
    if CONTRACTION.search(sentence):
        found.append("contraction")
    if FILLER.search(sentence):
        found.append("filler")
    if VAGUE.search(sentence):
        found.append("vague-verb")
    if PASSIVE.search(sentence):
        found.append("passive")
    return found


def check(path: Path, verbose: bool = False) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    chunks = _extract_lang(text) if path.suffix == ".js" else _extract_md(text)
    total = passed = 0
    for chunk in chunks:
        for sentence in SENTENCE_SPLIT.split(chunk):
            sentence = sentence.strip()
            if len(sentence.split()) < 3:
                continue
            total += 1
            problems = _violations(sentence)
            if problems:
                if verbose:
                    print(f"  [{','.join(problems)}] {sentence[:110]}")
            else:
                passed += 1
    return passed, total


def main(argv: list[str]) -> int:
    verbose = "--verbose" in argv
    files = [Path(a) for a in argv if not a.startswith("--")]
    if not files:
        print(__doc__)
        return 2
    for f in files:
        passed, total = check(f, verbose)
        pct = 100 * passed / total if total else 100.0
        print(f"{f}: {passed}/{total} sentences pass ({pct:.0f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
