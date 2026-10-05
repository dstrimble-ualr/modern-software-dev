"""Print the numbers from the last `make coverage` run as a Markdown table.

CI appends this to the GitHub Actions job summary. Run it locally with
`make coverage-summary`. Reads coverage.json, written by --cov-report=json.

coverage.py computes one percentage per file:
    (covered statements + covered branch paths) / (statements + branch paths) * 100
The table shows the two counts that feed that formula.
"""
import json
import sys
from pathlib import Path

report = Path(__file__).resolve().parents[1] / "coverage.json"
if not report.exists():
    sys.exit("No coverage.json found. Run `make coverage` first.")

data = json.loads(report.read_text())


def row(label, s):
    statements = f"{s['covered_lines']}/{s['num_statements']}"
    branches = f"{s['covered_branches']}/{s['num_branches']}"
    return f"| {label} | {statements} | {branches} | {s['percent_covered']:.2f}% |"


print("| File | Statements covered | Branch paths covered | Coverage |")
print("|---|---|---|---|")
for path, info in sorted(data["files"].items()):
    print(row(path, info["summary"]))
print(row("**All files**", data["totals"]))
