---
applyTo: '**'
---

# GitHub Labels Management for Minerva

## Predefined Labels Only Policy

This project maintains a strict "predefined labels only" policy to ensure consistency and avoid label proliferation.

## Complete List of Approved Labels

### Type Labels (Required)
- `type:feature` - New feature additions
- `type:bug` - Bug fixes
- `type:docs` - Documentation changes only
- `type:refactor` - Code refactoring without new features or bug fixes
- `type:test` - Test additions or corrections
- `type:chore` - Maintenance tasks (dependencies, build system, etc.)
- `type:ci` - CI/CD pipeline changes

### Feature Labels (Optional)
- `feature:obsidian` - Obsidian integration related
- `feature:claude` - Claude Desktop integration related
- `feature:markdown` - Markdown processing related
- `feature:create` - create_note function related
- `feature:edit` - edit_note function related
- `feature:read` - read_note function related
- `feature:search` - search_notes function related
- `feature:tags` - Tag management system related
- `feature:delete` - Note deletion functionality related
- `feature:config` - Configuration management related

### Area Labels (Optional)
- `area:backend` - Backend/server-side changes
- `area:ci` - CI/CD system and automation
- `area:docs` - Documentation area (different from type:docs)

### Priority Labels (Optional)
- `priority:high` - High priority issues/PRs
- `priority:medium` - Medium priority issues/PRs
- `priority:low` - Low priority issues/PRs

### Status Labels (Optional)
- `status:wip` - Work in progress
- `status:review` - Ready for review
- `status:blocked` - Blocked by dependencies or other issues
- `status:ready` - Ready for implementation

### Scope Labels (Optional)
- `scope:core` - Affects core functionality
- `scope:ui` - User interface changes
- `scope:performance` - Performance-related changes
- `scope:security` - Security-related changes

### Pull Request Specific Labels (Optional)
- `pr:ready` - Pull request ready for review
- `pr:wip` - Work in progress pull request
- `pr:needs-rebase` - Requires rebase against main branch
- `pr:needs-tests` - Requires additional tests

## Label Usage Guidelines

### Required Labels
- Every issue and PR MUST have exactly one `type:` label
- Choose the most appropriate type based on the primary purpose of the change

### Recommended Label Combinations

**New Feature Example:**
```
type:feature + feature:tags + priority:medium + scope:core
```

**Bug Fix Example:**
```
type:bug + feature:search + priority:high
```

**Documentation Update Example:**
```
type:docs + area:docs + priority:low
```

**CI/CD Improvement Example:**
```
type:ci + area:ci + priority:medium
```

## AI Assistant Rules

### Strict Prohibitions
1. **NEVER create new labels** without explicit human approval
2. **NEVER use labels not listed above**
3. **NEVER use variations or similar labels** (e.g., `bug` instead of `type:bug`)

### Required Actions
1. **Always use the predefined labels** from the list above
2. **Ask for permission** if you believe a new label is truly necessary
3. **Explain your reasoning** when requesting new labels:
   - Why existing labels are insufficient
   - What specific purpose the new label serves
   - How it fits into the existing categorization system

### Permission Request Format
If you need a new label, use this format:

```
I believe we need a new label for [specific use case].

Current situation:
- Existing labels [X, Y, Z] don't adequately cover this because [reason]
- This occurs frequently enough to warrant its own label because [evidence]

Proposed label:
- Name: `category:name`
- Purpose: [clear description]
- Usage criteria: [when to apply this label]

May I create this label, or would you prefer to use existing labels differently?
```

## Maintenance

This label system is maintained in:
1. This file (`.github/instructions/github_labels.md`)
2. `docs/github_workflow.md` (user-facing documentation)
3. `CLAUDE.md` (AI assistant quick reference)
4. `.github/instructions/ai_guidelines.md` (AI behavior guidelines)

When labels are added or changed, ALL these files must be updated consistently.
