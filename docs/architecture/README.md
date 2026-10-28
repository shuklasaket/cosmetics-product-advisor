# Architecture

The [editable draw.io diagram](cosmetic-advisor-architecture.drawio) shows the
implemented foundation and the smallest planned path through PRDs 02–09. It is one
local Streamlit application with shared Python services, one SQLite database, and a
separate local Ollama process when model analysis begins. The approved external API
is the only required remote runtime boundary. The [PRD index](../requirements/README.md#delivery-baseline-and-remaining-path)
records delivery status; the diagram does not imply that planned components exist.

![Incremental local architecture: existing catalog and source contracts, shared future services, one graph, and local model](system-architecture.drawio.svg)

## Read the diagram

- The top row is the existing PRD 01 catalog and source-contract foundation.
  Streamlit validates requests and calls the same catalog/search service that reads
  the SQLite evidence repository. The source registry is already stored there.
- PRD 02 adds one manual, allowlisted refresh path. PRDs 03–06 add ingredient
  screening, review analysis, deterministic ranking, and constrained explanations to
  the shared service layer. The model adapter begins with PRD 04; only local Ollama is
  required for the MVP.
- PRD 07 adds one fixed LangGraph conversation path. It calls the same services as
  the structured form. The model may extract request fields or select supported
  explanation claims; Python retains authority over eligibility, arithmetic,
  evidence, citations, and tool permissions.
- PRD 08 adds one reviewed, allowlisted preference record to the same database.
  PRD 09 displays redacted usage events captured from the first model call and runs
  frozen evaluation scenarios. Budgets, exclusions, raw chat, and active results stay
  in the current session. Public evidence and validated public extraction artifacts
  may persist; sensitive prompts and raw checkpoints do not.
- Failed refreshes retain dated last-valid evidence. Model failure leaves factual
  results available. A cancelled or superseded run cannot replace the current result.

[ADR-0001](../adr/0001-local-modular-architecture.md) explains the original local
boundary. [ADR-0003](../adr/0003-incremental-remaining-implementation.md) records the
proposed incremental implementation decision. Neither ADR changes existing behavior.

## Interaction sequences

The [PlantUML sequence guide](sequences.md) retains detailed planned paths for
catalog refresh, review analysis, recommendation, cancellation, and preference
memory. These are target flows, not implementation claims. Their nodes should call
shared services from the overview rather than create separate runtimes.

## Editing and verification

Edit `cosmetic-advisor-architecture.drawio` as the source. The
`system-architecture.drawio.svg` preview embeds its editable XML. Update both from
the same layout, inspect the preview for clipping and misleading arrows, then run
`make docs` and `make check`. The `.puml` files are editable sources for the sequence
diagrams. Keep diagram changes aligned with the PRDs and technical requirements.
