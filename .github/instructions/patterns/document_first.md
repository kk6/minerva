---
applyTo: '**/*.py,**/*.md'
---

# Minerva Document-First Development Pattern

## Overview

The Minerva project adopts a "Document-First" approach. This pattern requires updating or creating documentation before implementing code. This approach improves implementation consistency and quality while promoting shared understanding across the team.

## Fundamental Principles

1. **Pre-Implementation Documentation**: Always update relevant documentation first when adding new features, modifying existing features, or fixing bugs.

2. **Phased Approach**:
   - First update the requirements document (`docs/requirements.md`)
   - Then update the technical specifications (`docs/technical_spec.md`)
   - Update other documentation as needed
   - Finally implement the code

3. **Documentation-Code Consistency**: After implementation, verify that the documentation content matches the actual code.

## Implementation Procedure

### 1. Update Requirements Document

Update the relevant section in `docs/requirements.md`:

```markdown
#### 2.1.X New Feature Name (Function Name)
- Overview of the feature
- Description of input parameters and return values
- Processing flow
- Error conditions
```

### 2. Update Technical Specifications

Update the relevant section in `docs/technical_spec.md`:

```markdown
#### 3.1.X New Feature Name

Describe the technical details of the feature:
- Class or function signatures
- Algorithm explanation
- Data structures
- Error handling
```

### 3. Update Other Related Documents

Update additional documents as needed:
- `README.md`: List of major features and usage examples
- `docs/note_operations.md`: Detailed specifications for note operations
- `docs/test_guidelines.md`: Testing approach for the new feature

### 4. Code Implementation

After documentation updates are complete and necessary reviews conducted, proceed with code implementation.

## Instructions for AI Assistants

AI assistants should follow these guidelines:

1. When a user requests code implementation, first suggest verifying and updating related documentation.

2. Recommend that users follow these steps before implementation:
   - Review existing documentation
   - Create documentation update proposals
   - Reflect code design in documentation
   - Only then implement the code

3. Maintain consistency with documentation when generating code.

4. If documentation is insufficient, prioritize suggesting documentation creation.

## Best Practice Examples

```python
# Good pattern - Document-first example
"""
1. Add note deletion feature specification to docs/requirements.md:
   - Describe two-phase process (confirmation → execution) details
   - Address safety and error handling

2. Add processing flow to docs/technical_spec.md:
   - Method for separating confirmation and execution steps
   - Confirmation information generation and validation logic

3. Code implementation:
   - Implement get_note_delete_confirmation function
   - Implement perform_note_delete function
"""
```

```python
# Bad pattern - Documentation as an afterthought
"""
1. Implement deletion feature code
2. Add tests
3. (If time permits) Update documentation
"""
```

## Important Considerations

- Include documentation updates as part of the commit
- Avoid the "update documentation later" approach
- Inconsistencies between documentation and code are considered technical debt
