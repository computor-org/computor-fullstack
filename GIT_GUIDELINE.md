# Git Commit Guidelines for Claude

Follow **Conventional Commits** format: `<type>: <description>`

## Types to Use
- `feat`: new feature/functionality
- `fix`: bug fix
- `docs`: documentation changes
- `style`: formatting/whitespace (no logic change)
- `refactor`: code restructuring (no behavior change)
- `test`: adding/updating tests
- `chore`: maintenance, dependencies, tooling

## Rules
- **Imperative mood**: "add" not "added"
- **No period** at end
- **Be specific**: what changed and why
- **One logical change** per commit

## Examples
```
feat: implement database version constraint resolution
fix: handle missing studentTemplates in workflow
docs: update example dependency documentation
refactor: extract template processing to separate function
test: add coverage for version resolver service
chore: update alembic to latest version
```

## When Making Commits
1. Stage related changes together
2. Write clear, specific message
3. Reference issues if applicable: `fixes #123`
4. Keep first line under 72 chars

Remember: Each commit should leave the codebase working.