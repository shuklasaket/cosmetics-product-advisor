---
name: developing-with-streamlit
description: "Develop, test, style, or debug this project's Streamlit UI using version-matched references from installed Streamlit. Use for widgets, forms, session state, caching, and AppTest; not general repository or non-UI Python changes."
---

> Project adaptation, 17 October 2026: narrowed discovery to Streamlit UI work, removed a Claude-specific tool declaration, and selected the repository uv environment. The upstream discovery script is unchanged.

Read the [project integration boundaries](../../../docs/skills.md#application-boundaries) before applying general examples.

# Developing with Streamlit

Streamlit (>=1.57) ships detailed reference documentation for building Streamlit apps inside its pip package. The bundled skill is a routing `SKILL.md` plus a `references/` folder of topic-specific reference docs (dashboards, themes, layouts, session state, custom components, etc.).

## Usage

Run the discovery script with the user's project directory:

```bash
uv run --frozen python .agents/skills/developing-with-streamlit/scripts/discover.py --project-dir .
```

The script prints either:

- **A path on stdout** (exit 0) — the bundled `SKILL.md`. Read it; it points into `references/`.
- **An `ERROR:` block on stderr** (non-zero exit). Follow the printed instructions and re-run.

`<SKILL_DIR>` is the directory containing this file; `<USER_PROJECT_DIR>` is the absolute path to the user's project. Passing `--project-dir` matters because the script resolves `.venv`, `../.venv`, `Pipfile`, `poetry.lock`, `pdm.lock`, and `uv.lock` relative to it.

For this repository, run discovery from the repository root. If the locked environment is missing, use `make setup`; do not follow generic pip-install or upgrade advice outside the canonical uv workflow.
