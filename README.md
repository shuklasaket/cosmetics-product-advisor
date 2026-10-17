# AI Cosmetic Product Advisor

A local application for comparing sunscreen and moisturiser available in India using sourced product facts, review evidence, ingredient screening, and transparent ranking.

**Current stage:** development foundation. The runnable preview validates configuration and shows project status. Catalog search and genuine seed data are delivered by PRD 01; later PRDs add analysis, recommendations, conversation, and memory.

## Quick start

Prerequisites: Python **3.12.15**, uv **0.13.1**, and Git. The default `python3` on this development Mac is older; use the pinned interpreter through uv. Install instructions are available in the [uv guide](https://docs.astral.sh/uv/getting-started/installation/).

From the repository root:

```sh
uv sync --locked
uv run --frozen streamlit run app.py
```

Open `http://127.0.0.1:8501`. Press Ctrl+C in the terminal to stop the application. No source API, Ollama installation, credentials, or catalog is needed for the development preview.

If the pinned interpreter is unavailable, `uv python install` installs the version in [.python-version](.python-version). Existing compatible installations can be reused.

## Configuration

Defaults work without a `.env` file. To override local data paths, copy [.env.example](.env.example) to `.env` and edit the documented keys. Environment variables override `.env` values. Invalid or unknown `.env` fields fail validation with values omitted from the UI error.

The preview does not create a database, load product data, save preferences, or start model/source connections. Hosted inference cannot be enabled in this foundation. Streamlit is configured to listen on loopback only.

## Development commands

| Command | Purpose |
| --- | --- |
| `make setup` | Install the locked development environment |
| `make run` | Start the local preview |
| `make check` | Formatting, linting, typing, offline tests, documentation, and dependency-export checks |
| `make format` | Apply formatting and safe automatic lint fixes |
| `make test` | Run isolated tests with outbound network sockets disabled; allow local Unix sockets for Streamlit's event loop |
| `make docs` | Check repository links and editable diagram structure |
| `make exports` | Regenerate pip compatibility files from `uv.lock` |

`pyproject.toml` defines dependencies and tools; `uv.lock` records exact resolutions. The two `requirements*.txt` files are generated compatibility exports, not separately maintained dependency lists. See [CONTRIBUTING.md](CONTRIBUTING.md) for upgrades and optional local Git hooks.

Every change uses a dedicated branch and a pull request to `main`. Required GitHub CI must pass before a squash merge. See the [Git workflow and enforcement policy](CONTRIBUTING.md#local-workflow).

For a pip-only runtime installation, create a Python 3.12 virtual environment, activate it, and run `python -m pip install --require-hashes -r requirements.txt`, then `streamlit run app.py`. `requirements-dev.txt` includes runtime plus development dependencies. The standard contributor/CI workflow uses uv.

## Documentation

- [Product requirements and release order](docs/requirements/README.md)
- [Technical requirements](docs/requirements/TECHNICAL_REQUIREMENTS.md)
- [Architecture diagram and guide](docs/architecture/README.md)
- [Architecture decision records](docs/adr/README.md)
- [Development readiness and completion criteria](docs/development.md)
- [Development foundation completion report](docs/reports/development-foundation-report.md)
- [Data intake, provenance, and fixture policy](data/README.md)

The supported MVP is single-user and local. Each PRD must add a usable increment with its own acceptance evidence. The preview is not a completed PRD 01 release.
