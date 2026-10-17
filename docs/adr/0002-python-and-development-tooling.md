# ADR-0002: Use Python 3.12 and a Locked uv Development Workflow

**Status:** Proposed

**Date:** 17 October 2026

**Deciders:** Project maintainer; review pending

**Implementation:** Development configuration added under the requested foundation setup; see the [completion report](../reports/development-foundation-report.md) for verification results.

## Context

The technical requirements permit Python 3.11 or 3.12 and require reproducible dependencies. The development Mac has Python 3.12.15 and uv 0.13.1 installed; its default `python3` is Python 3.9.13. Local and CI commands must select the supported interpreter consistently.

## Decision

Use Python 3.12, initially pinned to 3.12.15 in `.python-version`, and uv 0.13.1. Define dependencies/tool configuration in `pyproject.toml` and exact resolutions in `uv.lock`. Treat this as a local application rather than a distributable Python package for now.

Generate hashed `requirements.txt` and `requirements-dev.txt` from the lockfile for the pip compatibility path required by the technical documentation. CI verifies the exports match; they are not independent dependency sources. Use Ruff, mypy, pytest, local documentation checks, and the same Makefile commands locally and in CI.

## Options considered

| Option | Benefits | Costs |
| --- | --- | --- |
| uv with a canonical lockfile, selected | Reuses installed tools; frozen environments and repeatable exports | Requires the pinned uv tool and export consistency checks |
| pip/venv with manually maintained pins | Familiar commands and fewer project-management tools | Manual transitive pin/upgrade coordination and risk of differing environments |

## Consequences

The contributor workflow requires the pinned tools. The pip runtime path remains available. Python patch/tool upgrades require updating the pin/configuration, regenerating exports, and rerunning checks. No additional model, graph, or retrieval dependencies are installed before their releases need them.

The GitHub workflow uses pinned action revisions and read-only permissions. Its file does not establish that a remote CI run or branch protection is already active. Proposed architecture decisions in ADR-0001 retain their recorded status.

## Action items and revisit triggers

- Resolved environment, startup, offline tests, and exports verified locally; results recorded in the completion report.
- Revisit packaging when a CLI/distribution is needed, or runtime support when deployment requirements expand.
- Review dependency/tool updates deliberately; preserve one canonical dependency workflow.

## References

- [Technical requirements](../requirements/TECHNICAL_REQUIREMENTS.md)
- [Contributor workflow](../../CONTRIBUTING.md)
- [uv project workflow](https://docs.astral.sh/uv/guides/projects/)
- [uv exports and compatibility limitations](https://docs.astral.sh/uv/concepts/projects/export/)
- [uv GitHub Actions integration](https://docs.astral.sh/uv/guides/integration/github/)
