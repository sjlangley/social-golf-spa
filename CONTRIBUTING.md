# Contributing to Caringbah Social Golf Club

Thank you for contributing to this project! Please follow these guidelines to ensure code quality and consistency.

## Prerequisites

- **Node.js 20+** (for frontend development)
- **Python 3.12+** (for backend development)
- **Google Cloud Project** with Firestore, Cloud Run, and Pub/Sub enabled
- Familiarity with [Google Style Guides](https://google.github.io/styleguide/)

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `test/` - Test additions or fixes
- `refactor/` - Code refactoring

### 2. Make Your Changes

Follow the coding conventions in [.github/copilot-instructions.md](.github/copilot-instructions.md):
- **Python**: [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- **TypeScript**: [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)

### 3. Write Tests

**Minimum 80% test coverage is required** for all code changes.

- **Backend**: Write pytest tests in `tests/` directory
- **Frontend**: Write Vitest tests in `tests/` directory
- Test both happy paths and error cases
- Include integration tests for API endpoints

### 4. Run Pre-Commit Checks (MANDATORY)

**⚠️ CRITICAL: All checks must pass before committing. CI will reject PRs that fail these checks.**

#### Backend (Python)

From `apps/golf-api/` or `apps/handicap-calculator/`:

```bash
# 1. Format code
ruff format .

# 2. Lint code
ruff check .

# 3. Type check
pyright .

# 4. Run tests with minimum 80% coverage
pytest --cov=src/golf_api --cov-fail-under=80 --cov-report=term-missing
# OR for handicap-calculator:
# pytest --cov=src/handicap_calculator --cov-fail-under=80 --cov-report=term-missing
```

#### Frontend (TypeScript)

From `apps/golf-ui/`:

```bash
# 1. Lint code
npm run lint

# 2. Check formatting
npm run format:check

# 3. Run tests
npm test
```

To auto-fix issues:
```bash
npm run lint:fix   # Fix ESLint issues
npm run format     # Fix Prettier formatting
```

### 5. Commit Your Changes

Use [Conventional Commits](https://www.conventionalcommits.org/) syntax:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `test` - Test additions or modifications
- `refactor` - Code refactoring (no functional changes)
- `perf` - Performance improvements
- `chore` - Maintenance tasks (deps, configs)
- `ci` - CI/CD changes

**Examples:**
```bash
git commit -m "feat(members): add member search by email"
git commit -m "fix(api): handle missing handicap in score calculation"
git commit -m "docs(readme): add pre-commit checklist instructions"
git commit -m "test(matches): add edge case tests for 26-player matches"
git commit -m "refactor(auth): extract token verification to separate function"
```

**Scope** should be the app or module affected:
- `golf-ui` - Frontend application
- `golf-api` - Backend API
- `handicap-calculator` - Handicap calculator service
- `members`, `matches`, `scores`, `auth`, etc. - Specific modules

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-description
```

Go to GitHub and create a Pull Request with:
- **Clear title** using conventional commit syntax
- **Description** explaining what changed and why
- **Reference issues** if applicable (e.g., "Fixes #123")
- **Screenshots** if UI changes are involved
- **Breaking changes** clearly documented in PR description

### 7. Address Review Feedback

- Respond to all review comments
- Make requested changes in new commits (don't force-push)
- Re-run all pre-commit checks after changes
- Request re-review when ready

## Code Quality Standards

### Test Coverage

- **Minimum 80% coverage** across all services
- Tests must pass in CI
- Coverage reports generated automatically

### Type Safety

- **Python**: Full type hints on all functions (enforced by pyright)
- **TypeScript**: Strict mode enabled, no `any` types without justification

### Code Style

- **Python**: Enforced by ruff (Google Python Style Guide)
- **TypeScript**: Enforced by ESLint + Prettier (Google TypeScript Style Guide)
- Auto-formatting is enabled - use it!

### Security

- Never commit secrets or API keys
- Use environment variables for configuration
- Follow security guidelines in [docs/security.md](docs/security.md)
- All auth endpoints must verify tokens and check roles

## Common Mistakes to Avoid

❌ **Don't:**
- Commit without running pre-commit checks
- Skip writing tests for new features
- Use `any` type in TypeScript without justification
- Commit commented-out code or TODOs in production code
- Force-push to branches under review
- Commit `.env` files with secrets

✅ **Do:**
- Run all linting, formatting, and tests before committing
- Write meaningful commit messages using conventional syntax
- Add tests for all new features and bug fixes
- Update documentation when changing behavior
- Keep PRs focused and reasonably sized
- Respond to review feedback promptly

## Getting Help

- **Architecture questions**: See [docs/architecture.md](docs/architecture.md)
- **Security questions**: See [docs/security.md](docs/security.md)
- **Coding conventions**: See [.github/copilot-instructions.md](.github/copilot-instructions.md)
- **Issues**: Open a GitHub issue
- **Questions**: Start a GitHub Discussion

## Release Process

Releases are managed automatically via **release-please**:
- Conventional commits determine version bumps
- Release notes generated from commit history
- No manual version updates needed

Just write good commit messages and the release automation handles the rest!

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE)).
