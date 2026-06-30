"""Build a precise per-session reading-material map.

Produces data/reading_materials/session_map.json, keyed by the CANONICAL session
names in data/course_structure.json, with each value being only that session's
reading-material text.

Why this exists
---------------
The two course reading-material files are monolithic. Their headings do NOT match
the canonical session names (e.g. "# Introduction" vs "Exploring Gen AI
Capabilities"), so the old fuzzy substring matching in data_loader fed the wrong
content into understand_session — the root cause of off-topic questions.

Two different layouts, handled explicitly:

  gen_ai_reading_material.md
    Exported from a sheet: each session starts with a quote-prefixed boundary
    (`"# ...`). There are exactly 18 such boundaries, mapped IN ORDER to sessions
    via GEN_AI_ORDER below (most boundaries are just titled "Introduction", so we
    can only map them by position + verified content).

  llm_applications_reading_material.md
    No quote boundaries. Sessions start at distinctive `# <Heading>` lines that DO
    match canonical names. We anchor on those exact headings (LLM_APPS_ANCHORS),
    which also avoids the code-comment false-headings (`# Getting weather data...`)
    that broke the old generic parser.

Sessions with no clean reading material (a few bleed/merge in the source files)
simply get no entry; understand_session then falls back to the knowledge graph.

Run: python scripts/build_session_reading_material.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import GEN_AI_RM, LLM_APPS_RM, DATA_DIR  # noqa: E402

OUT_PATH = DATA_DIR / "reading_materials" / "session_map.json"
MAX_CHARS = 12000  # generous per-session cap

# gen_ai: the 18 `"#` boundaries in file order map to these canonical sessions.
GEN_AI_ORDER = [
    "Exploring Gen AI Capabilities",
    "Productivity Power Up with AI Tools",
    "Prompt Engineering Fundamentals",
    "Building Social Media Content Automation Workflow",
    "Advanced Prompt Engineering",
    "Build Your Own AI News Summarizer | Part 1",
    "Build Your Own AI News Summarizer | Part 2",
    "Productivity Power-Up with AI Tools | Part 2",
    "Mastering Image Generation",
    "Setting Up Your Kaggle Environment",
    "Mastering Image Generation with Stable Diffusion",
    "Introduction to AI Agents",
    "Mastering AI Audio Generation",
    "Building No-Code Applications with AI",
    "Building a Learning Path Generator",
    "Mastering AI Audio Generation using F5-TTS",
    "Building an Agent with Memory",
    "Introduction to Model Context Protocol",
]

# llm_apps: canonical session name -> the exact `# <heading>` text that starts it.
LLM_APPS_ANCHORS = {
    "Introduction to Google Colab": "Introduction to Google Colab",
    "Introduction to Third Party Packages": "Introduction to Third-Party Packages in Python",
    "Introduction to Flask": "Introduction to Flask",
    "Building Rest APIs using Flask": "Building Rest APIs using Flask",
    "Integrating Flask APIs in Frontend": "Integrating Flask APIs in Frontend",
    "Building LLM Applications Using Python | Part 1": "Building LLM Applications using Python | Part 1",
    "Building LLM Applications Using Python | Part 2": "Building LLM Applications using Python | Part 2",
    "Building UI for LLM Applications": "Building UI for LLM Applications",
    "Deploying LLM Applications": "Deploying LLM Applications",
    "Understanding How LLMs Work | Part 1": "Understanding How LLMs Work | Part 1",
    "Understanding How LLMs Work | Part 2": "Understanding How LLMs Work | Part 2",
    "Tool use & Function Calling in LLMs": "Tool Use & Function Calling in LLMs",
    "Effective Prompting Techniques": "Effective Prompting Techniques",
    "Introduction to Langchain": "Introduction to LangChain",
    "Introduction to Retrieval-Augmented Generation | Part 1": "Introduction to Retrieval-Augmented Generation | Part 1",
    "Introduction to Retrieval-Augmented Generation | Part 2": "Introduction to Retrieval-Augmented Generation | Part 2",
    "Building AI Agents using Langchain": "Building AI Agents Using LangChain",
    "Building Memory Agents": "Building Memory Agent using Langchain",
    "AI in the Real World": "AI In The Real World",
    "Building an AI-Powered Conversational Interview Assistant | Part 1": "Building an AI-Powered Conversational Interview Assistant",
    "Building an AI-Powered Conversational Interview Assistant | Part 2": "Building an AI-Powered Conversational Interview Assistant | Part 2",
    "Introduction to Context Engineering": "Introduction to Context Engineering",
    "Integrating MCP": "Integrating MCP",
    "Building Multi Agent Systems Using Crew AI": "Building Multi Agent Systems Using Crew AI",
    "Building a Game Development Crew": "Building a Game Development Crew",
    "Introduction to LLM Evaluation | Part 1": "Introduction to LLM Application Evaluation | Part 1",
    "Introduction to LLM Evaluation | Part 2": "Introduction to LLM Application Evaluation | Part 2",
    "Running Models Locally": "Running Models Locally",
    "Fine-Tuning LLMs | Part 1": "Fine-Tuning LLMs",
}


def build_gen_ai(text: str) -> dict[str, str]:
    """Split on quote-prefixed `"#` boundaries; assign segments in order."""
    boundaries = [m.start() for m in re.finditer(r'^"#', text, re.MULTILINE)]
    if len(boundaries) != len(GEN_AI_ORDER):
        print(f"  WARNING: gen_ai has {len(boundaries)} boundaries but "
              f"{len(GEN_AI_ORDER)} mapped sessions — mapping by position anyway.")
    out: dict[str, str] = {}
    for i, start in enumerate(boundaries):
        if i >= len(GEN_AI_ORDER):
            break
        end = boundaries[i + 1] if i + 1 < len(boundaries) else len(text)
        out[GEN_AI_ORDER[i]] = text[start:end].strip()[:MAX_CHARS]
    return out


def build_llm_apps(text: str) -> dict[str, str]:
    """Anchor on exact `# <heading>` lines that match canonical session starts."""
    # Find the line position of each anchor heading (single `#`, optional quote).
    positions: list[tuple[int, str]] = []
    for session, heading in LLM_APPS_ANCHORS.items():
        pat = r'^"?#\s+' + re.escape(heading) + r'\s*$'
        m = re.search(pat, text, re.MULTILINE)
        if m:
            positions.append((m.start(), session))
        else:
            print(f"  WARNING: anchor not found for '{session}' ({heading!r})")
    positions.sort()
    out: dict[str, str] = {}
    for i, (start, session) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        out[session] = text[start:end].strip()[:MAX_CHARS]
    return out


def main():
    session_map: dict[str, str] = {}

    if GEN_AI_RM.exists():
        session_map.update(build_gen_ai(GEN_AI_RM.read_text(encoding="utf-8")))
    else:
        print(f"WARNING: {GEN_AI_RM} not found")

    if LLM_APPS_RM.exists():
        session_map.update(build_llm_apps(LLM_APPS_RM.read_text(encoding="utf-8")))
    else:
        print(f"WARNING: {LLM_APPS_RM} not found")

    OUT_PATH.write_text(json.dumps(session_map, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"\nWrote {len(session_map)} sessions → {OUT_PATH}")
    for name in session_map:
        print(f"  · {name}  ({len(session_map[name])} chars)")


if __name__ == "__main__":
    main()
