# Development Guide

## Prerequisites

- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- Python 3.9.2 or higher
- Git

## Setup

1. **Install uv**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/getyourguide/auto-pr.git
   cd auto-pr
   ```

3. **Install dependencies**:
   ```bash
   uv sync --extra dev
   ```

   This will:
   - Create a virtual environment in `.venv/`
   - Install all dependencies including dev dependencies
   - Install the project in editable mode

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov-report xml --cov=autopr test/ -v

# Run linting and pre-commit hooks
uv run pre-commit run --all-files
```

## Running Locally

```bash
# Run auto-pr command directly from source
uv run auto-pr --help

# Or activate the virtual environment and use commands directly
source .venv/bin/activate
auto-pr --help
```

## Building the Package

```bash
# Build wheel and source distribution
uv build

# The built packages will be in the dist/ directory
ls dist/
# auto_pr-1.2.0-py3-none-any.whl
# auto_pr-1.2.0.tar.gz
```

## Dependency Management

```bash
# Add a new dependency
uv add <package-name>

# Add a dev dependency
uv add --dev <package-name>

# Update lock file
uv lock

# Update a specific package
uv lock --upgrade-package <package-name>
```

## Common Development Tasks

### Update pre-commit hooks
```bash
uv run pre-commit autoupdate
```

### Run specific test file
```bash
uv run pytest test/test_config.py -v
```

### Check code formatting
```bash
uv run black --check autopr/ test/
```

### Generate coverage HTML report
```bash
uv run pytest --cov-report html --cov=autopr test/
open htmlcov/index.html
```

## Troubleshooting

### Clear uv cache
```bash
uv cache clean
```

### Recreate virtual environment
```bash
rm -rf .venv
uv sync --extra dev
```

### Check installed packages
```bash
uv pip list
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on submitting changes.