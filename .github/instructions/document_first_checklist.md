---
applyTo: '**/*.py'
---

# Document-First Checklist

## Pre-Development Checklist for New Features

Before starting implementation, the AI should encourage users to confirm the following items:

### 1. Requirements Document Check/Update (`docs/requirements.md`)

- [ ] Are feature requirements clearly described?
- [ ] Are input/output specifications defined?
- [ ] Are error conditions and edge cases identified?

### 2. Technical Specification Check/Update (`docs/technical_spec.md`)

- [ ] Are class/function signatures described?
- [ ] Is the processing flow clearly defined?
- [ ] Are data models (Pydantic models) defined?
- [ ] Is the error handling approach described?

### 3. Other Documentation Check/Update

- [ ] Is `README.md` updated as needed?
- [ ] Are related functional specifications (e.g., `docs/note_operations.md`) updated?
- [ ] Are test guidelines (`docs/test_guidelines.md`) updated if necessary?

### 4. Code Implementation Preparation

- [ ] Have documentation changes been reviewed and approved?
- [ ] Is the testing approach clear?

## Code Review Checklist

During code reviews, AI should encourage users to check the following items:

- [ ] Does the implementation match the specifications described in the documentation?
- [ ] Are there any inconsistencies between documentation and code?
- [ ] Do documentation change commits precede code implementation commits?

## Instructions for AI Assistants

* When a user requests code implementation:
  1. First, identify relevant documentation
  2. Verify that the documentation is up-to-date and reflects the planned functionality
  3. If documentation is insufficient, propose updating documentation before implementing code

* Document update and code implementation sequence:
  1. First present documentation update proposals
  2. After obtaining user approval, proceed with code implementation
  3. Once implementation is complete, verify consistency between documentation and code

* Template response example:

```
Before implementing the new feature "[feature name]", let's check the related documentation.

I recommend updating the following documents first:
1. docs/requirements.md: Add feature requirements
2. docs/technical_spec.md: Add implementation details

Once these documentation updates are complete, we can proceed with the actual code implementation.
Would you like me to create documentation update proposals, or have these documents already been updated?
```

## Explaining the Benefits

AI assistants should be able to explain to users that the document-first approach has the following benefits:

1. Promotes advance design thinking, improving implementation quality
2. Unifies feature understanding across the entire team
3. Makes code reviews more efficient
4. Maintains documentation freshness for future reference
5. Reduces training costs for new project members
6. Enables early detection of potential issues before implementation
