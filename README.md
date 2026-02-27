# lykke.day

![Tests](https://github.com/smartfastlabs/lykke.day/actions/workflows/ci.yml/badge.svg?branch=main)
[![codecov](https://codecov.io/github/smartfastlabs/lykke.day/graph/badge.svg?token=LKE5MI43G4)](https://codecov.io/github/smartfastlabs/lykke.day)

> **Work in progress / experiment**  
> This repository is actively changing and may break at any time.

## What This Is

`lykke.day` is an ongoing experiment in AI-native software development:

- LLMs write essentially all production code in this repo.
- Humans set direction, constraints, and review.
- The goal is to learn what workflows, architecture, and guardrails make this approach reliable.

This means commits may be frequent, structure may shift, and rough edges are expected.

## Current Status

- Not stable
- Not production-ready
- No compatibility guarantees between commits

If you are reading this, treat the project as a live lab notebook rather than a finished product.

## Local Development

### Prerequisites

- Docker
- Python 3.12+ with Poetry
- Node.js 18+ with npm

### Setup

```bash
git clone https://github.com/smartfastlabs/lykke.day.git
cd lykke.day

# Backend
cd backend
poetry install
make docker-up
make init-db
make migrate-dev
make serve

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Common Commands

```bash
# backend/
make test
make typecheck
make check

# frontend/
npm run test
npm run type-check
npm run lint
```

## Contributing

Contributions are welcome, especially if you are interested in AI-assisted development practices.

Before opening a PR:

1. Run checks (`make check` in `backend/`, tests/lint in `frontend/`)
2. Keep changes small and explicit
3. Add or update tests when behavior changes
4. Document any prompt, workflow, or guardrail improvements

## License

GNU Affero General Public License v3.0 (AGPLv3) - see `LICENSE`.
