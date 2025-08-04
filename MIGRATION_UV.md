# Migration to UV Package Manager

This document explains the migration from pip + requirements.txt to uv + pyproject.toml.

## What Changed

### ✅ New Files
- `pyproject.toml` - Modern Python project configuration with dependencies
- `.python-version` - Specifies Python 3.12 for uv
- `Makefile` - Development commands using uv
- `Dockerfile` - Optimized for uv builds
- `docker-compose.yml` - Container orchestration
- `scripts/setup_dev.py` - Automated development setup

### 📝 Updated Files
- `CLAUDE.md` - Updated with uv commands
- `README.md` - New installation instructions
- `.gitignore` - Added uv-specific entries
- `.dockerignore` - Docker build optimization

### ⚠️ Deprecated Files
- `requirements.txt` - Replaced by `pyproject.toml`
  - Can still be generated with `make requirements` for compatibility

## Migration Commands

### For New Contributors
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup project
make setup
```

### For Existing Contributors
```bash
# Remove old virtual environment
rm -rf venv/ .venv/

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup with uv
make setup
```

## Benefits of UV

1. **Faster**: 10-100x faster than pip
2. **Better Dependency Resolution**: More reliable than pip
3. **Python Version Management**: Built-in Python version management
4. **Modern Standard**: Uses pyproject.toml (PEP 518)
5. **Docker Optimized**: Better caching and smaller images

## Command Mapping

| Old (pip) | New (uv) |
|-----------|----------|
| `pip install -r requirements.txt` | `uv sync` |
| `pip install -e .` | `uv sync` |
| `python -m pytest` | `uv run pytest` |
| `black src/` | `uv run black src/` |
| Virtual env activation | Not needed (uv run handles it) |

## Troubleshooting

### uv not found
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart terminal or source your shell
```

### Python 3.12 not available
```bash
# uv will automatically install Python 3.12
uv python install 3.12
```

### Migration from existing environment
```bash
# Clean start
rm -rf .venv/
make setup
```