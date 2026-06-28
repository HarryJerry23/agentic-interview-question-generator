"""Source-health diagnostic for the mock_interview workflow (Feature 11 / Part 7).

For a sample set of outcomes it exercises EVERY configured source and reports per-source yield, so we
can confirm GitHub is connected and see which Tavily-allowlist domains actually return interview
questions (and which are dead/blocked → candidates to prune).

Run:  PYTHONPATH=. python scripts/check_sources.py [outcome ...]

It does NOT modify anything. GitHub uses settings.github_token if set (else the 60/hr unauthenticated
limit applies). Each allowlist domain costs one Tavily search — a one-off diagnostic, not a per-run cost.
"""
from __future__ import annotations

import sys

from backend.agent.sources.base import domain as _domain
from backend.agent.sources.github_repo import GithubRepoConnector
from backend.agent.sources.tavily_search import _client, _on_allowlist, _records_from_results, _search
from backend.settings import settings

SAMPLE_OUTCOMES = ["prompt_engineering_techniques", "rag_evaluation_metrics", "llm_hallucination_problem"]


def _check_github(outcomes):
    print("\n=== GitHub repos connector ===")
    print(f"github_token: {'SET (5000/hr)' if settings.github_token else 'ABSENT → unauthenticated 60/hr (slow, may rate-limit)'}")
    print(f"enabled: {settings.interview_src_github_enabled} · repos configured: {len(settings.interview_github_repos)}")
    if not settings.interview_src_github_enabled:
        print("  (disabled — skipping)")
        return
    try:
        recs = GithubRepoConnector().fetch(outcomes)
    except Exception as exc:  # noqa: BLE001
        print(f"  ERROR: {exc}")
        return
    by_repo: dict[str, int] = {}
    for r in recs:
        by_repo[r.source_type] = by_repo.get(r.source_type, 0) + 1
    print(f"  total candidates: {len(recs)} across {len(by_repo)} repo files")
    if not recs:
        print("  ⚠ 0 candidates — likely rate-limited (add GITHUB_TOKEN) or repos changed.")


def _check_tavily_domains(outcomes):
    print("\n=== Tavily allowlist domains (per-domain yield) ===")
    if not settings.tavily_api_key:
        print("  TAVILY_API_KEY absent — skipping web sources.")
        return
    allow = set(settings.interview_source_allowlist or [])
    client = _client()
    query = " / ".join(o.replace("_", " ") for o in outcomes) + " interview questions"
    productive, zero = [], []
    for dom in sorted(allow):
        results = _search(client, query, include_domains=[dom])
        on_dom = [r for r in results if _on_allowlist(_domain(r.get("url", "")), {dom})]
        recs = _records_from_results(on_dom, {dom}, set())
        n = len(recs)
        (productive if n else zero).append((dom, n))
        print(f"  {'✓' if n else '·'} {dom:<32} results={len(results):<3} questions={n}")
    print(f"\n  productive: {len(productive)}/{len(allow)} domains returned ≥1 question")
    if zero:
        print(f"  zero-yield ({len(zero)}): {', '.join(d for d, _ in zero)}")
        print("  (zero can mean dead/blocked OR just no hit for these sample outcomes — re-check before pruning.)")


def main():
    outcomes = sys.argv[1:] or SAMPLE_OUTCOMES
    print(f"Source-health check · sample outcomes: {outcomes}")
    _check_github(outcomes)
    _check_tavily_domains(outcomes)


if __name__ == "__main__":
    main()
