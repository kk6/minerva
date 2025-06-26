# Create GitHub Issue

Creates a GitHub issue using the appropriate template from `.github/ISSUE_TEMPLATE` and applies labels after creation.

## Usage

1. **Select Issue Template**: Choose the appropriate template based on the issue type:
   - `bug_report.yml` - For bug reports
   - `feature_request.yml` - For feature requests
   - `documentation.yml` - For documentation improvements

2. **Create Issue**: Use `gh issue create` with the selected template:
   ```bash
   gh issue create --template bug_report.yml
   gh issue create --template feature_request.yml
   gh issue create --template documentation.yml
   ```

3. **Apply Labels**: After issue creation, apply appropriate labels using `gh issue edit`:
   ```bash
   # Method 1: Capture issue URL and extract number
   ISSUE_URL=$(gh issue create --template bug_report.yml)
   ISSUE_NUMBER=$(echo $ISSUE_URL | grep -o '[0-9]*$')

   # Method 2: Get latest issue number (if creation succeeded)
   ISSUE_NUMBER=$(gh issue list --limit 1 --json number --jq '.[0].number')

   # Apply labels based on issue type and content
   gh issue edit $ISSUE_NUMBER --add-label "type:bug,priority:medium"
   gh issue edit $ISSUE_NUMBER --add-label "type:feature,feature:obsidian,priority:high"
   gh issue edit $ISSUE_NUMBER --add-label "type:docs,area:docs,priority:low"
   ```

4. **Optional: Assign and Add to Project**:
   ```bash
   # Assign to yourself
   gh issue edit $ISSUE_NUMBER --assignee @me

   # Add to project (if project exists)
   gh issue edit $ISSUE_NUMBER --add-project "Project Name"
   ```

## Available Labels

**Required Labels**:
- `type:` - bug, feature, docs, refactor, test, chore, ci

**Recommended Labels**:
- `feature:` - obsidian, claude, markdown, create, edit, read, search, tags, delete, config
- `priority:` - high, medium, low

**Optional Labels**:
- `area:` - backend, ci, docs
- `status:` - wip, review, blocked, ready
- `scope:` - core, ui, performance, security

## Examples

### Bug Report
```bash
gh issue create --template bug_report.yml
# After creation, apply labels:
gh issue edit $ISSUE_NUMBER --add-label "type:bug,feature:search,priority:high"
```

### Feature Request
```bash
gh issue create --template feature_request.yml
# After creation, apply labels:
gh issue edit $ISSUE_NUMBER --add-label "type:feature,feature:obsidian,priority:medium,scope:core"
```

### Documentation Issue
```bash
gh issue create --template documentation.yml
# After creation, apply labels:
gh issue edit $ISSUE_NUMBER --add-label "type:docs,area:docs,priority:low"
```

## Troubleshooting

### Verify Templates Exist
```bash
# List available templates
ls .github/ISSUE_TEMPLATE/

# Check if specific template exists
test -f .github/ISSUE_TEMPLATE/bug_report.yml && echo "Template exists" || echo "Template missing"
```

### Error Handling
```bash
# Check if gh command succeeded
if ISSUE_URL=$(gh issue create --template bug_report.yml); then
    ISSUE_NUMBER=$(echo $ISSUE_URL | grep -o '[0-9]*$')
    echo "Created issue #$ISSUE_NUMBER"
    gh issue edit $ISSUE_NUMBER --add-label "type:bug,priority:medium"
else
    echo "Failed to create issue"
    exit 1
fi
```

## Notes

- **Write all issues in English** - Issue titles, descriptions, and comments must be in English
- Always use existing labels only - never create new labels without permission
- Apply labels after issue creation, not in the issue body
- Reference the complete label system in `docs/github_workflow.md`
- Use `gh issue list` to verify the issue was created successfully
- **Verify templates exist** before attempting to create issues
- **Handle errors gracefully** - check command success before proceeding
