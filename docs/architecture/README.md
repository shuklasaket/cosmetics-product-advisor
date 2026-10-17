# Architecture

The [editable draw.io architecture diagram](cosmetic-advisor-architecture.drawio) describes the planned MVP from the [technical requirements](../requirements/TECHNICAL_REQUIREMENTS.md) and [nine PRDs](../requirements/README.md). It represents the target design, not an already deployed application.

[ADR-0001](../adr/0001-local-modular-architecture.md) records the proposed architecture decision, alternatives, trade-offs, and revisit triggers. The [ADR index](../adr/README.md) tracks its status and future decisions.

## Diagram pages

1. **System architecture** shows the local MacBook boundary, Streamlit interface, validated controller, single LangGraph orchestrator, application services, source/model adapters, SQLite repositories, session memory, and opted-in preference tools. Approved external sources and manual evidence imports sit outside the local boundary.
2. **Recommendation flow** shows request validation and clarification, product research, review analysis, ingredient screening, hard eligibility checks, deterministic ranking, evidence validation, explanation generation, claim checking, factual fallback, and redacted reporting.

## How to read it

- Blue components implement application behavior and deterministic rules; purple components use language models; green components handle source evidence; amber components hold personal session data or unresolved outcomes.
- Arrows represent invocation or data exchange. Two-headed arrows show request/result or read/write exchange. The bottom control panel applies across components; it is not a separate background service.
- The form calls application services directly. The conversational path reaches the same services through LangGraph from PRD 07 onward.
- SQLite stores versioned product evidence, validated public-evidence artifacts, redacted events, and the three opted-in preferences. Avoid lists, raw conversation, current budgets, and personal matching details remain in session memory.
- Eligibility is evaluated before scores. The model explains validated evidence and cannot alter product selection, ranking, or ingredient-rule outcomes.
- Hosted inference is an optional, disabled extension through the model adapter. Public hosting, a vector database, independent agents, and MCP serving are outside this diagram's MVP.

## Editing

Open `cosmetic-advisor-architecture.drawio` with a draw.io-compatible editor, or open it through **File → Open from → Device** at [draw.io](https://app.diagrams.net/). Both pages contain native editable shapes, labels, containers, and connectors. No draw.io Desktop installation is needed to edit the XML-backed file in the web editor.

Keep diagram changes aligned with the technical requirements and affected PRDs. The existing Mermaid overview in the technical requirements remains a compact text representation; this file provides the fuller component and execution views.
