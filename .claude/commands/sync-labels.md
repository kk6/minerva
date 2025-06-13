# /sync-labels - GitHub Labels Synchronization Command

Synchronize GitHub labels based on implementation-first analysis: Implementation → Documentation → GitHub Labels.

## Actions Performed

### Phase 1: Implementation Analysis
1. Analyze codebase implementation to identify all features and functionality:
   - MCP server tools in `server.py`
   - Service layer operations in `services/`
   - Core infrastructure components
   - User-facing functionality areas

### Phase 2: Documentation Synchronization
2. Compare implementation with labels defined in `docs/github_workflow.md`
3. Identify missing labels that should be documented based on actual implementation
4. Update documentation to reflect all implemented features
5. Ensure documentation accuracy matches codebase reality

### Phase 3: GitHub Labels Creation
6. Retrieve current GitHub labels list
7. Compare with updated documentation definitions
8. Create missing labels with appropriate colors and descriptions
9. Identify extra labels (manual confirmation required for deletion)
10. Check for inconsistencies in label colors and descriptions

## Target Files

- **Primary Analysis**: Source code in `src/` directory (implementation)
- **Documentation**: `docs/github_workflow.md` (label definitions)
- **Target**: GitHub repository label settings

## Implementation-First Approach

This command follows the principle that **implementation is the source of truth**:

1. **What exists in code** → Should be documented
2. **What's documented** → Should have corresponding GitHub labels
3. **What's labeled** → Should accurately reflect actual functionality

This ensures labels remain relevant and useful for actual development work.

## Prerequisites

- Execute within a GitHub repository
- `gh` CLI installed and authenticated
- Administrator permissions for the repository
- Access to source code for analysis

## Usage

This command will:
- Perform comprehensive codebase analysis to identify all implemented features
- Update documentation to match implementation reality
- Synchronize GitHub labels with documented (and implemented) functionality
- Report any inconsistencies for manual review
- Ensure the repository follows implementation-driven label management
