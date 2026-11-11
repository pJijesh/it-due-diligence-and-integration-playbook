"""Checks on the written material: no long dashes, working relative links, diagrams present."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "build", "dist"}
TEXT_SUFFIXES = {".md", ".py", ".csv", ".json", ".yml", ".yaml", ".toml", ".mmd", ".txt", ".svg", ""}
LONG_DASHES = (chr(0x2014), chr(0x2013))


def text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or SKIP_DIRS & set(path.relative_to(ROOT).parts):
            continue
        if path.suffix in TEXT_SUFFIXES and not path.name.endswith(".egg-info"):
            yield path


def test_no_long_dashes_anywhere():
    bad = []
    for path in text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(d in text for d in LONG_DASHES):
            bad.append(str(path.relative_to(ROOT)))
    assert not bad, f"long dashes found in: {bad}"


def test_markdown_relative_links_resolve():
    link = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
    problems = []
    for path in ROOT.rglob("*.md"):
        if SKIP_DIRS & set(path.relative_to(ROOT).parts):
            continue
        for target in link.findall(path.read_text(encoding="utf-8")):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            target = target.split("#")[0]
            if target and not (path.parent / target).exists():
                problems.append(f"{path.relative_to(ROOT)} -> {target}")
    assert not problems, problems


def test_diagrams_have_source_and_render():
    for name in ("workflow", "100-day-timeline"):
        assert (ROOT / "docs" / "images" / f"{name}.mmd").is_file()
        svg = (ROOT / "docs" / "images" / f"{name}.svg").read_text(encoding="utf-8")
        assert svg.lstrip().startswith("<svg")


def test_required_docs_exist():
    for name in (
        "due-diligence-guide.md",
        "integration-guide.md",
        "risk-and-red-flags.md",
        "synergy-and-cost-model.md",
        "day-1-checklist.md",
    ):
        assert (ROOT / "docs" / name).is_file(), name


def test_counts_quoted_in_prose_match_the_data():
    import csv

    with open(ROOT / "data" / "integration-plan.csv", newline="", encoding="utf-8") as fh:
        n_tasks = len(list(csv.DictReader(fh)))
    with open(ROOT / "data" / "question-bank.csv", newline="", encoding="utf-8") as fh:
        bank = list(csv.DictReader(fh))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    guide = (ROOT / "docs" / "integration-guide.md").read_text(encoding="utf-8")
    dd = (ROOT / "docs" / "due-diligence-guide.md").read_text(encoding="utf-8")
    assert f"{n_tasks} tasks" in readme and f"{n_tasks} tasks" in guide
    assert f"{len(bank)} questions" in readme or f"{len(bank)}-question" in readme
    w5 = sum(1 for r in bank if r["weight"] == "5")
    w45 = sum(1 for r in bank if r["weight"] in ("4", "5"))
    assert f"| {w5} |" in dd and f"| {w45} |" in dd and f"| {len(bank)} |" in dd
