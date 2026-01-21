# Frontend

SolidJS + Vite + TypeScript application.

## Requirements

- **Node.js 20+** (required for running tests, linting, and development tooling)
- npm 8+

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Testing

```bash
# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

## Code Quality

```bash
# Type check
npm run type-check

# Lint
npm run lint

# Fix linting issues
npm run lint:fix

# Run all checks (type check + lint + tests)
npm run check
```

## Architecture

The frontend follows a component-based architecture using SolidJS:

- `/src/components` - Reusable UI components
- `/src/pages` - Page components and routes
- `/src/providers` - Context providers for global state
- `/src/utils` - Utility functions and API clients
- `/src/types` - TypeScript type definitions

### Real-time Data

The application uses WebSocket connections for real-time data synchronization via the `StreamingDataProvider`. See `src/providers/streaming-data.tsx` for implementation details.
