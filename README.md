# lykke.day

![Tests](https://github.com/smartfastlabs/lykke.day/actions/workflows/ci.yml/badge.svg?branch=main)
[![codecov](https://codecov.io/github/smartfastlabs/lykke.day/graph/badge.svg?token=LKE5MI43G4)](https://codecov.io/github/smartfastlabs/lykke.day)

> **⚠️ PRE-ALPHA SOFTWARE** — This project is in very early development. Expect breaking changes, bugs, and incomplete features. Not recommended for production use.

> **Lykke** _(n.)_ — the Danish art of finding happiness in everyday moments. _(pronounced: loo-kah)_

## What is lykke.day?

A daily companion that helps you get the small stuff done so you're more effective at the big stuff. Not a todo app. Not a productivity tool. Just a gentle way to build rhythms that fit your life.

### One day at a time

No backlogs. No guilt. No endless task lists. Just small, meaningful goals for today. Because lasting change comes from consistent, manageable habits — your way, at your pace.

## Why lykke.day?

**Three things you'll find:**

- **The comfort of routines** — There's a quiet confidence that comes from knowing what to do next. Your routines become second nature, freeing your mind for what really matters.

- **The calmness of successful days** — End your day knowing you showed up. Not perfectly, but meaningfully. That sense of accomplishment creates a peace that compounds over time.

- **The freedom to focus on what's big** — When the small stuff is handled, your energy flows toward your dreams, your relationships, your growth. The things you can't outsource to an app.

## Features

- **🌅 One Day at a Time** — Focus on today. No overwhelming backlogs or distant deadlines.
- **🔄 Gentle Routines** — Build rhythms that fit your life, not someone else's idea of productivity.
- **📅 Calendar Aware** — Integrates with your calendar so wellness fits into your real life, not around it.
- **🔔 Soft Reminders** — Nudges, not nagging. We'll help you remember what matters to you.

## Is Lykke For You?

Whether you're navigating specific challenges or just know something needs to change, it all starts with a solid foundation. Lykke can help with:

- **🌱 Anxiety & Depression** — Daily structure and gentle routines create stability when everything feels overwhelming.
- **🎯 ADD & ADHD** — One day at a time, with reminders that help without adding to the noise.
- **💪 Substance Abuse Recovery** — Daily structure and accountability help build the foundation for lasting sobriety.

## Getting Started

### Prerequisites

- **Docker** (for PostgreSQL and Redis)
- **Python 3.12+** with Poetry (for backend)
- **Node.js 18+** with npm (for frontend)

### Quick Start

1. **Clone the repository**

```bash
git clone https://github.com/smartfastlabs/lykke.day.git
cd lykke.day
```

2. **Set up the backend**

```bash
cd backend
poetry install
make docker-up    # Starts PostgreSQL and Redis
make init-db      # Initializes databases
make migrate-dev  # Runs database migrations
make serve        # Starts API server, worker, and scheduler
```

The API will be available at `http://localhost:8080`

3. **Set up the frontend**

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`

### Configuration

The backend requires environment variables. Create a `.env` file in the `backend` directory:

```bash
DATABASE_URL=postgresql+psycopg://lykke:password@localhost:5432/lykke_dev
REDIS_URL=redis://localhost:6379
SECRET=your-secret-key-here
```

See `backend/.env.example` for more configuration options.

## Tech Stack

**Frontend:**

- SolidJS (reactive UI framework)
- TypeScript
- Vite (build tool)
- TailwindCSS (styling)

**Backend:**

- Python 3.12+
- FastAPI (web framework)
- SQLAlchemy (database ORM)
- PostgreSQL (database)
- Redis (caching & pub/sub)
- Poetry (dependency management)

**Architecture:**

- Domain-Driven Design
- Clean Architecture (Domain, Application, Infrastructure, Presentation layers)
- Event-driven patterns

## Project Structure

```
lykke.day/
├── frontend/          # SolidJS web application
│   ├── src/
│   │   ├── pages/     # Application pages
│   │   └── components/# Reusable UI components
│   └── package.json
│
├── backend/           # Python FastAPI application
│   ├── lykke/
│   │   ├── domain/    # Core business logic
│   │   ├── application/# Use cases & commands
│   │   ├── infrastructure/# External services
│   │   └── presentation/# API routes
│   └── pyproject.toml
│
└── docker-compose.yml # Development infrastructure
```

## Development

### Running Tests

**Backend:**

```bash
cd backend
make test              # Run all tests
make test-target TARGET=test_name  # Run specific test
```

**Frontend:**

```bash
cd frontend
npm run test
```

### Code Quality

**Backend:**

```bash
cd backend
make typecheck       # Run mypy type checking
make check-mappers   # Check for missing mappers/schemas
make check           # Run typecheck + tests
```

**Frontend:**

```bash
cd frontend
npm run type-check   # TypeScript checking
npm run lint         # ESLint
```

## Contributing

We welcome contributions! Whether it's:

- 🐛 Bug reports
- 💡 Feature suggestions
- 📝 Documentation improvements
- 🔧 Code contributions

Please feel free to open an issue or submit a pull request.

## The Experiment: Building with AI

This project is also an experiment in building software with LLMs (Large Language Models). The codebase is **heavily reliant on AI assistance** — from architecture decisions to implementation details.

**Why this matters:**

- 🤖 **AI-First Development** — We're exploring what's possible when humans and AI collaborate deeply on software development
- 📚 **Learning in Public** — This is a real-world test of AI-assisted development practices, patterns, and pitfalls
- 🔄 **Rapid Iteration** — LLMs enable us to experiment faster and refactor more boldly
- 🎯 **Human-Centered AI** — The goal remains human wellness; AI is the tool, not the purpose

This means the codebase might look different from traditional hand-crafted code. That's intentional. We're discovering new ways to build software.

## Philosophy

**What lykke is NOT:**

- ❌ **A Todo List App** — No endless backlogs or overflowing task lists. Just what matters today.
- ❌ **A Productivity Tool** — We're not about doing more. We're about living better — with intention and ease.
- ❌ **A Magic Bullet** — We're not about quick fixes. We're about building lasting routines and patterns.

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPLv3)**.

This means:

- ✅ You can use, modify, and distribute this software
- ✅ You must share your modifications under the same license
- ✅ If you run a modified version on a server, you must make your source code available to users

See the [LICENSE](LICENSE) file for full details.

## Additional Documentation

- [HTTPS Setup Guide](docs/https-certs.md)
- [PostgreSQL Configuration](docs/postgresql.md)
- [VAPID Keys for Push Notifications](docs/vapid-keys.md)

## Support

If you find lykke.day helpful, please consider:

- ⭐ Starring the repository
- 🐦 Sharing it with others who might benefit
- 🤝 Contributing to the project

---

> **Note:** This README was auto-generated by Claude (Anthropic) as part of our AI-assisted development process.
