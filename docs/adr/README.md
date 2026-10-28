# Architecture Decision Records

ADRs explain why the project chooses an architectural approach, which alternatives were considered, and what would justify changing it. Product behavior remains defined in the [PRDs](../requirements/README.md); implementation contracts remain in the [technical requirements](../requirements/TECHNICAL_REQUIREMENTS.md).

| Record | Status | Decision |
| --- | --- | --- |
| [ADR-0001](0001-local-modular-architecture.md) | Proposed | Local modular application, deterministic policy authority, SQLite evidence storage, and local inference; orchestration detail superseded by ADR-0004 |
| [ADR-0002](0002-python-and-development-tooling.md) | Proposed | Python 3.12 and a canonical uv lockfile, generated pip exports, and shared local/CI checks |
| [ADR-0003](0003-incremental-remaining-implementation.md) | Proposed | Extend the implemented catalog incrementally; role-orchestration detail superseded by ADR-0004 |
| [ADR-0004](0004-bounded-five-role-orchestration.md) | Proposed | One trusted controller with exactly five fixed, least-privilege specialist roles |

“Proposed” records a concrete design for review; it does not imply stakeholder approval or completed implementation. Acceptance should record the actual deciders and date. Later changes use a new numbered ADR with links to any superseded record so the decision history remains available.

See the [architecture guide and diagram](../architecture/README.md) for the
implemented foundation and planned path.
