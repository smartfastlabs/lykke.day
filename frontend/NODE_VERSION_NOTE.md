# Node Version Requirement

## Issue
The local development environment is running **Node.js v16.19.1**, which is incompatible with the testing stack.

## Error
```
TypeError: crypto.getRandomValues is not a function
```

This error occurs because:
- Vitest 4.x requires Node 20+
- Vite 7.x requires Node 20+  
- ESLint 9.x requires Node 18.18+

## Solution

### For Local Development
Upgrade to Node.js 20+ using one of these methods:

**Using nvm (recommended):**
```bash
nvm install 20
nvm use 20
```

**Using Homebrew (macOS):**
```bash
brew install node@20
brew link node@20
```

**Verify installation:**
```bash
node --version  # Should show v20.x.x
npm run test    # Tests should now run
```

### For CI/CD
✅ **Already configured** - GitHub Actions uses Node 20 (see `.github/workflows/ci.yml`)

## What Works Now
Even without upgrading locally:
- ✅ GitHub Actions will run tests successfully
- ✅ Type checking works (`npm run type-check`)  
- ✅ Building works (`npm run build`)
- ✅ Development server works (`npm run dev`)

## What Requires Node 20+
- ❌ Running tests (`npm test`)
- ❌ Running linter (`npm run lint`)
- ❌ Full check command (`npm run check`)

## Recommendation
Upgrade your local Node.js to version 20 or later to match the CI environment and enable the full development workflow.
