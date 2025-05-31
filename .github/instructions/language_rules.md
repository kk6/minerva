---
applyTo: '**'
---

# Language Usage Rules for Minerva Project

## Overview

This document defines the language usage rules for the Minerva project to ensure consistency across different types of content.

## Rules

### 1. Code and Technical Documentation

- **Source code comments and docstrings**: English only
  - All inline comments
  - Function and class docstrings
  - Module docstrings
  - Type hints and annotations

- **AI Instruction files**: English only
  - All files in `.github/instructions/` directory
  - AI assistant guidelines and patterns
  - Configuration files with natural language content

### 2. User-Facing Documentation

- **End-user documentation**: Japanese (with English terms where appropriate)
  - README.md
  - User guides
  - Feature documentation
  - API documentation in `docs/` directory

- **Development guides**: Japanese (with English terms where appropriate)
  - Technical specifications
  - Development workflow
  - Contribution guidelines
  - Release processes

### 3. Mixed-Content Guidelines

- **Variable and function names**: English only (camelCase or snake_case as per Python conventions)
- **Log messages**: English only
- **Error messages**:
  - System-level errors: English only
  - User-facing errors: Japanese

- **Comments in PR reviews**: Either Japanese or English depending on the context

### 4. File Format Requirements

- **Trailing whitespace**: No trailing whitespace allowed in any file
  - Python (.py)
  - Markdown (.md)
  - YAML (.yml, .yaml)
  - All other text files

- **Line endings**: Use Unix line endings (LF) for all files
  - No Windows line endings (CRLF)
  - No mixed line endings

- **Ensure files end with a newline**: All text files must end with a single newline character

- **Encoding**: Use UTF-8 encoding for all text files

## Enforcement

- Code review processes should enforce these language conventions
- AI assistants should be instructed to follow these rules when generating content
- Documentation templates should reflect the appropriate language for each document type

## Rationale

- **English for code**: Ensures accessibility for international developers and tools
- **Japanese for user docs**: Optimizes usability for the primary target audience
- **Consistency within document types**: Prevents confusing language mixing within the same context

## When in Doubt

When unsure which language to use for a specific context, follow this guidance:

1. If it's read primarily by machines or non-Japanese developers: use English
2. If it's read primarily by Japanese users: use Japanese
3. If it's technical terminology with established English terms: use English regardless of context
