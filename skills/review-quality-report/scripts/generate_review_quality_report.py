#!/usr/bin/env python3
"""Generate a deterministic Republic review-quality debt report.

Read-only over company reviews/registry/evidence. Writes one markdown report under
~/brain/reports/republic-investing/.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HOME = Path.home()
BRAIN = HOME / "brain"
COMPANIES = BRAIN / "companies"
REGISTRY = COMPANIES / "investment_registry.json"
REPORT_DIR = BRAIN / "reports" / "republic-investing"

REVIEW_RE = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})_(?P<slug>.+?)_(?P<kind>review|evaluation)_v(?P<version>\d+(?:\.\d+)?)\.md$")
MATERIAL_TERMS_RE = re.compile(
    r"\b("
    r"funding|fundraise|raised|raise close|new investors?|series\s+[a-d]|"
    r"acquisition|acquired|ipo|exit|sale process|strategic review|"
    r"partnership|partners? with|major customer|retailer|license|licence|regulatory approval|"
    r"litigation|enforcement|insolvency|restatement"
    r")\b",
    re.I,
)
FRESHNESS_TABLE_TERMS = (
    "Discovery date",
    "Publisher date",
    "Resolved URL",
    "Freshness",
    "Confirmation",
)
RULE24_REQUIRED = (
    "type: review",
    "slug:",
    "date:",
    "version:",
    "fundamentals_score:",
    "signal_state:",
    "action:",
    "holding_active:",
    "cap_table:",
)
RULE24_VALUE_ALIASES = (
    ("fair_value_low_gbp:", "fairValue", "fair value"),
    ("fair_value_high_gbp:", "fairValue", "fair value"),
    ("target_entry_price_gbp:", "target_entry_price", "target entry"),
)


@dataclass(frozen=True)
class ReviewFile:
    path: Path
    folder: str
    date: str
    version: float
    version_raw: str
    kind: str


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(BRAIN))
    except ValueError:
        return str(path)


def load_registry() -> dict[str, dict]:
    if not REGISTRY.exists():
        return {}
    data = json.loads(REGISTRY.read_text())
    if isinstance(data, dict) and "companies" in data and isinstance(data["companies"], list):
        return {str(e.get("name") or e.get("slug") or i): e for i, e in enumerate(data["companies"]) if isinstance(e, dict)}
    if isinstance(data, dict):
        return {str(k): v for k, v in data.items() if isinstance(v, dict)}
    return {}


def scan_reviews() -> list[ReviewFile]:
    out: list[ReviewFile] = []
    for p in COMPANIES.glob("*/*.md"):
        m = REVIEW_RE.match(p.name)
        if not m:
            continue
        out.append(
            ReviewFile(
                path=p,
                folder=p.parent.name,
                date=m.group("date"),
                version=float(m.group("version")),
                version_raw=m.group("version"),
                kind=m.group("kind"),
            )
        )
    return out


def frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return ""
    return parts[1]


def has_section20(text: str) -> bool:
    return bool(re.search(r"^#{2,4}\s+(?:Section\s+)?20\b|Self-Audit Log", text, re.I | re.M))


def latest_by_folder(reviews: list[ReviewFile]) -> dict[str, ReviewFile]:
    grouped: dict[str, list[ReviewFile]] = defaultdict(list)
    for r in reviews:
        grouped[r.folder].append(r)
    return {folder: sorted(rows, key=lambda r: (r.version, r.date, r.path.name), reverse=True)[0] for folder, rows in grouped.items()}


def find_entry_for_folder(registry: dict[str, dict], folder: str) -> tuple[str, dict] | tuple[None, None]:
    for name, entry in registry.items():
        if entry.get("folderSlug") == folder:
            return name, entry
        lr = entry.get("latestReview") if isinstance(entry.get("latestReview"), dict) else {}
        p = lr.get("path") if isinstance(lr, dict) else None
        if isinstance(p, str) and p.startswith(f"companies/{folder}/"):
            return name, entry
    return None, None


def rule24_missing(r: ReviewFile, text: str) -> list[str]:
    # Rule applies to v2+ reviews dated post 2026-04-29.
    if r.date < "2026-04-29" or r.version < 2:
        return []
    fm = frontmatter(text)
    missing = [key for key in RULE24_REQUIRED if key not in fm]
    for required, *aliases in RULE24_VALUE_ALIASES:
        if required not in fm and not any(a in fm for a in aliases):
            missing.append(required)
    return missing


def has_freshness_table(text: str) -> bool:
    table_hits = sum(1 for term in FRESHNESS_TABLE_TERMS if term.lower() in text.lower())
    return table_hits >= 3


def status_of(entry: dict | None) -> str:
    if not entry:
        return "<no registry entry>"
    lr = entry.get("latestReview") if isinstance(entry.get("latestReview"), dict) else {}
    return str(lr.get("reviewStatus") or "<missing>")


def main() -> int:
    now = datetime.now(ZoneInfo("Europe/London"))
    registry = load_registry()
    reviews = scan_reviews()
    latest = latest_by_folder(reviews)

    issues: dict[str, list[str]] = {"P0": [], "P1": [], "P2": [], "P3": []}
    registry_path_missing: list[str] = []
    registry_pointer_stale: list[str] = []
    status_counts: Counter[str] = Counter()
    frontmatter_debt: list[str] = []
    material_news_risk: list[str] = []
    missing_evidence: list[str] = []
    missing_section20: list[str] = []
    orphan_latest_reviews: list[str] = []

    for name, entry in registry.items():
        lr = entry.get("latestReview") if isinstance(entry.get("latestReview"), dict) else {}
        status_counts[str(lr.get("reviewStatus") or "<missing>")] += 1
        p = lr.get("path") if isinstance(lr, dict) else None
        if p and not (BRAIN / p).exists():
            registry_path_missing.append(f"{name}: {p}")
        folder = entry.get("folderSlug")
        if not folder and isinstance(p, str) and p.startswith("companies/"):
            folder = Path(p).parts[1]
        if folder and folder in latest:
            latest_rel = rel(latest[folder].path)
            if p and p != latest_rel:
                registry_pointer_stale.append(f"{name}: registry {p} < latest root {latest_rel}")
        elif not p:
            issues["P2"].append(f"{name}: no latestReview.path")

    for folder, r in sorted(latest.items()):
        name, entry = find_entry_for_folder(registry, folder)
        if not entry:
            orphan_latest_reviews.append(rel(r.path))
        text = r.path.read_text(errors="replace")
        status = status_of(entry)
        if status == "<missing>":
            issues["P2"].append(f"{folder}: latestReview.reviewStatus missing")
        ev = COMPANIES / folder / "evidence" / "current"
        if not (ev / "manifest.json").exists():
            missing_evidence.append(f"{folder}: missing evidence/current/manifest.json")
        if not (ev / "historical_context.md").exists():
            missing_evidence.append(f"{folder}: missing evidence/current/historical_context.md")
        missing = rule24_missing(r, text)
        if missing:
            frontmatter_debt.append(f"{rel(r.path)}: missing {', '.join(missing[:6])}{'…' if len(missing) > 6 else ''}")
        if MATERIAL_TERMS_RE.search(text) and not has_freshness_table(text):
            material_news_risk.append(f"{rel(r.path)}: material-news terms found but no freshness table/equivalent")
        if not has_section20(text):
            missing_section20.append(rel(r.path))

    # Known contaminated review class: latest TransferGo v5 contains the false funding/stale-news issue.
    for folder, r in latest.items():
        if folder == "transfergo" and "2026-05-03_transfergo_review_v5.md" in r.path.name:
            issues["P0"].append(
                "TransferGo latest review is v5 and should be treated as contaminated until Jack's v6 correction replaces the false/stale Google News funding/partnership deltas."
            )

    for row in registry_path_missing:
        issues["P1"].append(f"Missing registry review path: {row}")
    for row in registry_pointer_stale[:20]:
        issues["P1"].append(f"Registry pointer stale: {row}")
    for row in missing_evidence[:20]:
        issues["P1"].append(row)
    for row in material_news_risk[:20]:
        issues["P1"].append(f"Rule 26 risk: {row}")
    for row in frontmatter_debt[:30]:
        issues["P2"].append(f"Rule 24 debt: {row}")
    for row in missing_section20[:20]:
        issues["P2"].append(f"No obvious Section 20/Self-Audit marker: {row}")
    for row in orphan_latest_reviews:
        issues["P2"].append(f"Latest review without registry entry: {row}")

    safeish = []
    for folder, r in sorted(latest.items()):
        name, entry = find_entry_for_folder(registry, folder)
        if status_of(entry) == "canonical_final" and r.path.exists():
            safeish.append(f"{name or folder}: {rel(r.path)}")

    title = "Republic review quality debt"
    report_name = f"{now:%Y-%m-%d-%H%M}_review_quality_debt.md"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORT_DIR / report_name

    lines: list[str] = []
    lines += [
        "---",
        f"title: {title}",
        "category: republic-investing",
        "type: report",
        f"date: {now:%Y-%m-%d}",
        f"time: {now:%H:%M %Z}",
        "---",
        "",
        f"# {title} — {now:%Y-%m-%d %H:%M %Z}",
        "",
        "## Summary",
        "",
        f"- Registry entries: {len(registry)}",
        f"- Review files scanned: {len(reviews)}",
        f"- Company folders with latest reviews: {len(latest)}",
        f"- Current evidence manifests present: {sum(1 for folder in latest if (COMPANIES / folder / 'evidence/current/manifest.json').exists())}/{len(latest)}",
        f"- P0 contaminated: {len(issues['P0'])}",
        f"- P1 blocking/high-risk: {len(issues['P1'])}",
        f"- P2 quality debt: {len(issues['P2'])}",
        f"- P3 cleanup: {len(issues['P3'])}",
        "",
        "## P0 / P1 issues",
        "",
    ]
    if issues["P0"]:
        lines += ["### P0 — contaminated / unsafe for strategy", ""]
        lines += [f"- {x}" for x in issues["P0"]]
        lines.append("")
    if issues["P1"]:
        lines += ["### P1 — blocking / high-risk", ""]
        lines += [f"- {x}" for x in issues["P1"]]
        lines.append("")
    if not issues["P0"] and not issues["P1"]:
        lines.append("None.\n")

    lines += ["## Registry integrity", ""]
    lines += [f"- Missing registry review paths: {len(registry_path_missing)}"]
    lines += [f"- Registry pointer stale vs latest root file: {len(registry_pointer_stale)}"]
    if registry_pointer_stale[:10]:
        lines += ["", "Examples:"] + [f"- {x}" for x in registry_pointer_stale[:10]]
    lines.append("")

    lines += ["## Review status coverage", ""]
    for status, count in status_counts.most_common():
        lines.append(f"- {status}: {count}")
    lines.append("")

    lines += ["## Evidence packet coverage", ""]
    if missing_evidence:
        lines += [f"- {x}" for x in missing_evidence[:50]]
    else:
        lines.append("- All latest-review folders have current manifest + historical_context.")
    lines.append("")

    lines += ["## Rule 24 frontmatter debt", ""]
    if frontmatter_debt:
        lines += [f"- {x}" for x in frontmatter_debt[:50]]
    else:
        lines.append("- No Rule 24 debt detected by heuristic.")
    lines.append("")

    lines += ["## Rule 26 material-news freshness risk", ""]
    if material_news_risk:
        lines += [f"- {x}" for x in material_news_risk[:50]]
    else:
        lines.append("- No material-news freshness risk detected by heuristic.")
    lines.append("")

    lines += ["## Section 20 / audit marker debt", ""]
    if missing_section20:
        lines += [f"- {x}" for x in missing_section20[:50]]
    else:
        lines.append("- All latest reviews show a Section 20 / Self-Audit marker.")
    lines.append("")

    lines += ["## Canonical-final reviews detected", ""]
    if safeish:
        lines += [f"- {x}" for x in safeish[:50]]
    else:
        lines.append("- None marked canonical_final in registry.")
    lines.append("")

    lines += ["## Recommended next actions", ""]
    recs = []
    if issues["P0"]:
        recs.append("Replace contaminated TransferGo v5 with Jack's v6 correction, then update registry latestReview to v6.")
    if material_news_risk:
        recs.append("Add Rule 26 freshness tables to latest reviews that use funding/partnership/exit/regulatory news as material deltas.")
    if frontmatter_debt:
        recs.append("Choose one Rule 24 frontmatter schema and backfill or relax the hard rule; do not leave the rule and files divergent.")
    if status_counts.get("<missing>"):
        recs.append("Backfill latestReview.reviewStatus on registry entries so signal/report consumers know canonical vs maintenance/limited state.")
    if registry_pointer_stale:
        recs.append("Update stale registry latestReview.path pointers to the latest root-level review where appropriate.")
    if not recs:
        recs.append("No high-priority metadata action detected; rerun after next review batch.")
    lines += [f"{i}. {x}" for i, x in enumerate(recs, 1)]
    lines.append("")

    lines += ["## Source files checked", ""]
    lines += [
        f"- {rel(REGISTRY)}",
        "- companies/*/*_review_v*.md",
        "- companies/*/*_evaluation_v*.md",
        "- companies/*/evidence/current/manifest.json",
        "- companies/*/evidence/current/historical_context.md",
        "",
    ]

    out.write_text("\n".join(lines))
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
