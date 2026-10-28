# Project skills

The repository includes eight coding-agent skills under [`.agents/skills/`](../.agents/skills/). They support development; they are not runtime product agents, application dependencies, or an implemented PRD. Codex discovers repository skills from this location. See the [official OpenAI documentation](https://learn.chatgpt.com/docs/build-skills).

## Selected capabilities

| Skill | Use in this project | Origin |
| --- | --- | --- |
| [prd-to-stories](../.agents/skills/prd-to-stories/SKILL.md) | Draft PRD story plans or create/update GitHub stories when requested, with coverage, acceptance scenarios, verification, and dependencies | Project-authored entry point for the existing story workflow |
| [developing-with-streamlit](../.agents/skills/developing-with-streamlit/SKILL.md) | UI, forms, session state, native layout, performance, and AppTest throughout the releases | [Streamlit](https://github.com/streamlit/streamlit/tree/269e552f276f5757b2903174da18e083defb325b/lib/streamlit/.agents/meta-skill/developing-with-streamlit), matched to installed Streamlit 1.66.0 |
| [langgraph-fundamentals](../.agents/skills/langgraph-fundamentals/SKILL.md) | Typed Python graph state, reducers, routing, streaming, and failure handling from PRD 07 | [LangChain maintainers](https://github.com/langchain-ai/langchain-skills/tree/16a992f09ab3ccfb642dd4f08d350d833d1990bf/config/skills/langgraph-fundamentals) |
| [gh-fix-ci](../.agents/skills/gh-fix-ci/SKILL.md) | Diagnose failing GitHub Actions checks and implement authorized fixes on the task branch | [OpenAI](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/gh-fix-ci) |
| [gh-address-comments](../.agents/skills/gh-address-comments/SKILL.md) | Read and address requested PR review feedback | [OpenAI](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/gh-address-comments) |
| [security-threat-model](../.agents/skills/security-threat-model/SKILL.md) | Explicitly requested threat assessments of source/model boundaries, imports, stores, and sensitive session data | [OpenAI](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/security-threat-model) |
| [cosmetics-data-integrity](../.agents/skills/cosmetics-data-integrity/SKILL.md) | Sourced catalog imports, SQLite integrity, ingredient screening, and deterministic ranking in PRDs 01–03 and 05 | Project-authored for the existing PRDs and technical contracts |
| [cosmetics-model-evaluation](../.agents/skills/cosmetics-model-evaluation/SKILL.md) | Bounded Ollama calls, structured outputs, supported citations, usage accounting, and replay evaluation in PRDs 04, 06, and 09 | Project-authored for the existing PRDs and technical contracts |

Selection prioritized maintained first-party sources, fit with the documented stack, useful supporting references/scripts, portable discovery, and identifiable redistribution terms. These are project-fit choices rather than a claim that one public catalog establishes universally best skills.

Streamlit's old `streamlit/agent-skills` repository is deprecated. Its canonical entry point now ships with Streamlit, and the detailed references are bundled with the installed package. We vendor the small entry point from the source revision for the locked package version; it discovers the local references after `make setup`. No symlink to a developer's `.venv` is committed. See [Streamlit's current installation guidance](https://docs.streamlit.io/develop/api-reference/cli/skills).

## Application boundaries

Use a skill only when its description fits the requested work. Read the relevant entry point and only the supporting references needed. The [PRDs](requirements/README.md), [technical requirements](requirements/TECHNICAL_REQUIREMENTS.md), [data policy](../data/README.md), and [contributor workflow](../CONTRIBUTING.md) remain the project authority; generic examples are not additional product requirements or permission for external actions.

- Keep the local, single-user application and deterministic Python decision authority. LangGraph enters at PRD 07 as one trusted controller coordinating exactly five fixed roles; graph examples do not authorize autonomous agents, dynamic delegation, agent-to-agent messaging, or durable sensitive checkpoints.
- Apply the technical privacy contract before using generic cache, query-parameter, tracing, memory, logging, or persistence examples. Sensitive session inputs cannot enter shared/persistent caches, URLs, traces, raw checkpoints, databases, or exports. Show validated progress/events rather than raw hidden model reasoning.
- Continue the canonical uv workflow. Skill installation does not install Ollama/models, add LangGraph dependencies early, enable hosted inference, create accounts, connect MCP servers, publish a service, or authorize collecting source data.
- Reuse existing user authorization for scoped work. Ask only when material information or authorization is genuinely missing. A skill's generic confirmation sequence does not require asking again for already-authorized fixes or the established PR workflow.
- GitHub helpers read PR/check information through the existing `gh` authentication. Addressing code feedback does not itself authorize posting replies, resolving review threads, changing credentials, or bypassing branch protection.
- Security threat modeling applies when explicitly requested; it does not trigger a full security audit during ordinary implementation. Separate observed controls from proposed requirements.

The five imported entry points contain prominent adaptation notes. Their supporting scripts/references retain upstream content and licenses. Adaptations narrow triggers, use project-local commands, respect existing authorization, and reuse known project context. The three project-authored skills support story planning, data integrity, and model evaluation without replacing the source documents.

## Coverage and deliberate exclusions

Use the Streamlit skill's bundled `references/testing.md` for AppTest; ordinary Python/service/SQLite checks use the existing pytest workflow. The data-integrity skill covers project-specific import and deterministic policy decisions; validate current SQLite, Pydantic, and HTTPX APIs against primary documentation when implementing them. A separate generic skill is not needed for every library.

We considered OpenAI's security-best-practices package, but its framework references target Django, Flask, FastAPI, and non-Python web stacks rather than Streamlit. The selected threat-model skill and project-specific boundaries fit this repository more closely. LangChain's evaluation skill targets Harbor Tasks, so it does not replace the PRD 09 evaluation contract.

Cloud-deployment, React/Next.js, vector-store/RAG, Deep Agents, persistent graph memory, swarm, and model-training skills are excluded from the current scope. The bounded five-role graph is not an authorization to add an agent framework, role-specific runtime, or additional model provider. Browser automation is deferred until a UI acceptance check needs it beyond AppTest; installing a browser toolchain is not required for this setup. Existing diagram and engineering plugins remain available separately and are not copied from a developer's private plugin cache into the repository.

## Use and verification

Invoke a skill explicitly, for example `$cosmetics-data-integrity`, or let Codex select a matching description. New installations will be available on the next turn; if discovery does not refresh in the client, reopen the session.

From the repository root, locate the Streamlit references with:

```sh
uv run --frozen python .agents/skills/developing-with-streamlit/scripts/discover.py --project-dir .
```

Then read the returned `SKILL.md` and the relevant referenced topic. The other skills are self-contained except for their declared prerequisites: GitHub helpers need authenticated `gh`, and library implementation still needs the release's actual dependencies and data.

`make check` includes `make skills`, which verifies registered skill names, frontmatter presence, pinned source revisions, required license files, file inventories/SHA-256 integrity, and helper Python syntax without executing imported helpers or contacting the network. The installer skill's YAML validator is also used during initial review. These checks do not prove instruction quality, successful discovery in every client, or runtime behavior of future model integrations.

Vendored skill examples/helpers retain upstream formatting and are excluded from the application's Ruff checks, including explicit pre-commit file arguments. Three upstream files with existing whitespace irregularities have narrow Git whitespace exceptions so license/notice text and reference content remain unchanged; their hashes are still verified. Maintained application code and first-party verification scripts retain the existing formatting, lint, and type checks.

### Plan stories in chat

Open a Codex chat for this repository and name `$prd-to-stories` in your message. These are chat prompts, not terminal commands. Substitute another PRD number or its repository path as needed.

To review a plan in chat:

```text
Use $prd-to-stories to draft user stories for PRD 01. Check existing GitHub
issues, include acceptance criteria and verification, and show requirement
coverage and dependencies. Keep the result in chat.
```

To create the backlog in GitHub:

```text
Use $prd-to-stories to create the PRD 01 tracking issue and user stories in
GitHub. Reuse existing issues where appropriate, map requirement coverage,
and set sub-issue and blocking relationships.
```

To reconcile an existing backlog after requirements change:

```text
Use $prd-to-stories to review PRD 01 against its existing GitHub stories and
update the backlog for missing coverage or changed requirements. Preserve
existing decisions and acceptance-criterion IDs.
```

The skill follows the [story workflow](story-workflow.md); it does not start implementation. A request that only says to generate stories produces a chat draft. Explicit GitHub creation/update requests authorize that work without a second confirmation. GitHub reads and writes need the existing authenticated `gh` access; if unavailable, a draft can still be produced with backlog checks marked unverified. New issues begin in backlog until readiness is reviewed. Story IDs come from actual issue numbers after creation.

New skills should be available on the next turn. If discovery has not refreshed, reopen the repository chat or explicitly ask Codex to read [`.agents/skills/prd-to-stories/SKILL.md`](../.agents/skills/prd-to-stories/SKILL.md) and follow it.

## Sources and updates

[`.agents/skills-sources.json`](../.agents/skills-sources.json) records immutable Git revisions, upstream paths, license files, original hashes, and installed hashes. Streamlit and OpenAI imports preserve Apache-2.0 licensing; LangGraph preserves its MIT license. Streamlit's root notices are included with the skill. The three project-authored skills are tracked as project work rather than third-party imports.

Updates are deliberate PR changes. Compare the pinned source with the proposed revision, read changed instructions and helpers, retain required licenses/notices, record adaptations, and update source metadata and hashes. Upgrade Streamlit's entry point with its locked package version and verify discovery again. Do not blindly rerun an installer over an existing skill directory or follow an upstream instruction to change this project's architecture.

After reviewing intentional local skill edits, regenerate only the installed file hashes with `uv run --frozen python -m scripts.check_skills --refresh-hashes`, inspect the resulting manifest diff, and run `make check`. This does not update upstream provenance or approve changes; those require explicit review in the PR. CI only verifies the registry and never refreshes it.
