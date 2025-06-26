# Create GitHub Pull Request

Creates a GitHub pull request with proper branch management and applies labels after creation.

## Usage

1. **Ensure Proper Branch**: Create and switch to a topic branch following naming conventions:
   ```bash
   # Check current branch
   git branch --show-current

   # Create topic branch (if not already on one)
   git checkout -b feature/issue-NUMBER-short-description
   git checkout -b fix/issue-NUMBER-short-description
   git checkout -b docs/issue-NUMBER-short-description
   ```

2. **Pre-PR Quality Checks**: Run mandatory quality checks before creating PR:
   ```bash
   # Run all quality checks (required)
   make check-all

   # Run pre-commit hooks (required)
   make pre-commit

   # Fix any issues found before proceeding
   ```

3. **Create Pull Request**: Use `gh pr create` with appropriate options:
   ```bash
   # Basic PR creation
   gh pr create --title "feat: add semantic search functionality" --body "Brief description"

   # With reviewers and assignees
   gh pr create --title "fix: resolve vector indexing issue" --body "Description" --reviewer @username --assignee @me

   # Draft PR for work in progress
   gh pr create --draft --title "WIP: implement auto-indexing" --body "Work in progress"
   ```

4. **Apply Labels**: After PR creation, apply appropriate labels:
   ```bash
   # Get PR number from creation output or list
   PR_URL=$(gh pr create --title "Title" --body "Description")
   PR_NUMBER=$(echo $PR_URL | grep -o '[0-9]*$')

   # Apply PR-specific and general labels
   gh pr edit $PR_NUMBER --add-label "pr:ready,type:feature,feature:search,priority:medium"
   gh pr edit $PR_NUMBER --add-label "pr:wip,type:bug,priority:high"
   ```

## PR-Specific Options

### Branch Management
```bash
# Push branch and set upstream
git push -u origin feature/issue-123-new-feature

# Create PR from specific branch
gh pr create --head feature/issue-123-new-feature --base main
```

### Review and Assignment
```bash
# Request specific reviewers
gh pr create --reviewer username1,username2

# Assign to yourself or others
gh pr create --assignee @me,@username

# Add to milestone
gh pr create --milestone "v0.21.0"
```

### Draft and Ready States
```bash
# Create as draft
gh pr create --draft

# Mark draft as ready for review
gh pr ready $PR_NUMBER

# Convert back to draft
gh pr edit $PR_NUMBER --add-label "pr:wip"
```

## PR-Specific Labels

**PR Status Labels**:
- `pr:ready` - Ready for review
- `pr:wip` - Work in progress
- `pr:needs-rebase` - Requires rebase
- `pr:needs-tests` - Requires additional tests

## Examples

### Feature PR
```bash
# Create feature branch and PR
git checkout -b feature/issue-45-vector-search
git push -u origin feature/issue-45-vector-search

# Run mandatory quality checks
make check-all
make pre-commit

gh pr create --title "feat: implement vector search functionality" \
  --body "Adds semantic search with embedding support" \
  --reviewer @maintainer --assignee @me

# Apply labels
gh pr edit $PR_NUMBER --add-label "pr:ready,type:feature,feature:search,priority:high"
```

### Bug Fix PR
```bash
# Create fix branch and PR
git checkout -b fix/issue-67-index-corruption

# Run mandatory quality checks
make check-all
make pre-commit

gh pr create --title "fix: resolve vector index corruption on batch updates" \
  --body "Fixes issue #67 by adding proper transaction handling"

# Apply labels
gh pr edit $PR_NUMBER --add-label "pr:ready,type:bug,priority:high,scope:core"
```

### Documentation PR
```bash
# Create docs branch and draft PR
git checkout -b docs/issue-89-api-documentation

# Run mandatory quality checks
make check-all
make pre-commit

gh pr create --draft --title "docs: add comprehensive API documentation" \
  --body "WIP: Adding detailed API docs for MCP tools"

# Apply WIP labels
gh pr edit $PR_NUMBER --add-label "pr:wip,type:docs,area:docs,priority:medium"
```

## Integration with Issues

### Link to Issues
```bash
# Reference issue in PR body
gh pr create --title "fix: resolve search timeout" \
  --body "Closes #123

This PR resolves the search timeout issue by implementing proper pagination."
```

### Convert Issue to PR
```bash
# Create PR from existing issue (if using GitHub CLI 2.0+)
gh pr create --title "$(gh issue view 123 --json title -q .title)" \
  --body "Closes #123"
```

## Reference

For detailed information on:
- **Label system and categories**: See `create-issue.md` � Available Labels section
- **Error handling patterns**: See `create-issue.md` � Troubleshooting section
- **Template verification**: See `create-issue.md` � Verify Templates Exist

## Notes

- **Write all PRs in English** - Titles, descriptions, and comments must be in English
- **Follow branch naming conventions** from `docs/github_workflow.md`
- Always use existing labels only - never create new labels without permission
- Apply labels after PR creation, not in the PR body
- **Ensure you're on a topic branch** before creating PR - never work directly on main
- Use draft PRs for work in progress to get early feedback
- Reference related issues using "Closes #123" syntax in PR body
