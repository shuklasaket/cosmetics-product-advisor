# Architecture Decision Records

ADRs explain why the project chooses an architectural approach, which alternatives were considered, and what would justify changing it. Product behavior remains defined in the [PRDs](../requirements/README.md); implementation contracts remain in the [technical requirements](../requirements/TECHNICAL_REQUIREMENTS.md).

| Record | Status | Decision |
| --- | --- | --- |
| [ADR-0001](0001-local-modular-architecture.md) | Proposed | Local modular application, one controlled orchestrator, deterministic policy authority, SQLite evidence storage, and local inference |

“Proposed” records a concrete design for review; it does not imply stakeholder approval or completed implementation. Acceptance should record the actual deciders and date. Later changes use a new numbered ADR with links to any superseded record so the decision history remains available.

See the [architecture guide and diagram](../architecture/README.md) for the current system structure and recommendation flow.
