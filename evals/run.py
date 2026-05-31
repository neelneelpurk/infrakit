#!/usr/bin/env python3
"""Run the InfraKit eval suite and print a scorecard.

    python evals/run.py                 # score the committed example deliverables
    python evals/run.py --verbose       # show every check
    python evals/run.py --generator llm # (hook) generate fresh output, then score

Exit code is non-zero if any case misses its bar, so this is CI-usable.

Two halves of an eval:

* **generator** — produces the IaC to score. The default ``committed`` generator
  scores the example deliverables checked into the repo (deterministic, offline,
  free — this is what CI runs). The ``llm`` generator is the hook for the real
  thing: drive the InfraKit pipeline with an actual agent against each case's
  requirement and score whatever it writes. That needs an API key / agent and is
  non-deterministic, so it is intentionally not wired into CI.
* **scorer** — the mechanical, deterministic part (``scorer.py``). It is the same
  for both generators; that's the point.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cases as cases_mod  # noqa: E402
import scorer  # noqa: E402

_STATUS_ICON = {"pass": "✅", "fail": "❌", "na": "➖"}


def _case_passes(case, summary) -> bool:
    if case.kind == "negative":
        return summary["pct"] <= case.max_pct_if_negative
    return summary["failed"] == 0  # golden: every applicable check must pass


def run(generator: str = "committed", verbose: bool = False) -> int:
    if generator == "llm":
        raise NotImplementedError(
            "The 'llm' generator is a hook, not yet wired. Implement it by driving "
            "the InfraKit pipeline (create_* → plan → implement) with an agent "
            "against each case's requirement, writing output to a temp dir, then "
            "calling scorer.score(case.iac, temp_dir, case.checks). The scorer "
            "below is identical for both generators."
        )

    all_pass = True
    print(f"InfraKit evals — generator={generator}\n")
    for case in cases_mod.ALL_CASES:
        if not case.path.exists():
            print(f"❌ {case.id}: path not found ({case.path})")
            all_pass = False
            continue
        results = scorer.score(case.iac, case.path, case.checks)
        summary = scorer.summarize(results)
        ok = _case_passes(case, summary)
        all_pass = all_pass and ok
        bar = "≤%.0f%%" % case.max_pct_if_negative if case.kind == "negative" else "100%"
        verdict = "PASS" if ok else "FAIL"
        print(
            f"{'✅' if ok else '❌'} [{case.kind:<8}] {case.id:<42} "
            f"{summary['passed']}/{summary['applicable']} checks "
            f"({summary['pct']:.0f}%, target {bar}) — {verdict}"
        )
        if verbose or not ok:
            for r in results:
                extra = f"  ({r.detail})" if r.detail else ""
                print(f"      {_STATUS_ICON[r.status]} {r.check}{extra}")
    total_checks = sum(
        scorer.summarize(scorer.score(c.iac, c.path, c.checks))["applicable"]
        for c in cases_mod.ALL_CASES if c.path.exists()
    )
    print(f"\n{total_checks} scored checks across {len(cases_mod.ALL_CASES)} cases.")
    print("RESULT:", "ALL CASES PASS ✅" if all_pass else "FAILURES ❌")
    return 0 if all_pass else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Run the InfraKit eval suite.")
    ap.add_argument("--generator", default="committed", choices=["committed", "llm"])
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    return run(generator=args.generator, verbose=args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
