# Contributing to watershed-retrieve

## Development Setup

```bash
# Clone the repository
git clone https://github.com/CooperBigFoot/watershed-retrieve.git
cd watershed-retrieve

# Install dependencies (requires Python 3.13+ and uv)
uv sync
```

## Code Style

- **Formatter/Linter:** [ruff](https://docs.astral.sh/ruff/)
- **Type hints:** Required on all function signatures (use `list`, `dict`, `|` — not `typing.List`, `typing.Dict`, `typing.Optional`)

```bash
# Format
uv run ruff format src/ tests/

# Lint (with auto-fix)
uv run ruff check --fix src/ tests/
```

## Testing

```bash
# Unit tests (no data or network needed)
uv run pytest tests/ -v -m "not integration and not network"

# Integration tests (requires local parquet data)
WATERSHED_RETRIEVE_DATA_DIR=/path/to/data uv run pytest tests/ -v -m integration

# Network tests (requires internet access to R2)
uv run pytest tests/ -v -m network --run-network
```

## Pull Request Process

1. Create a feature branch from `main`
2. Write code following the project's style (type hints, ruff-clean)
3. Add or update tests as appropriate
4. Bump the patch version: `uv run bump-my-version bump patch`
5. Use [conventional commits](https://www.conventionalcommits.org/) for your commit message
6. Tag the commit: `git tag v$(uv run bump-my-version show current_version)`
7. Open a PR against `main`

## Questions?

Open an issue at [github.com/CooperBigFoot/watershed-retrieve/issues](https://github.com/CooperBigFoot/watershed-retrieve/issues).
