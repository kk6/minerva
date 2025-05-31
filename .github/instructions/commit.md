---
applyTo: '**'
---

# Commit Message Guidelines for Minerva

The Minerva project follows the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification for commit messages. Detailed rules are described in `docs/github_workflow.md`.

## Commit Message Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Main Types
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `build`: Changes that affect the build system or external dependencies
- `ci`: Changes to CI configuration files and scripts
- `chore`: Other changes that don't modify source or test files

## Scope
You can specify a scope in parentheses to indicate the section of the codebase affected:
- `(obsidian)`
- `(claude)`
- `(file-handler)`
- `(tools)`
- `(config)`
etc.

## Examples
- `feat(obsidian): Add support for note synchronization`
- `fix(tools): Fix incorrect path handling in search_notes function`
- `docs: Update installation instructions`
- `test(file-handler): Add unit tests for create_note function`
- `refactor: Move common functions to utils module`

Include related issue numbers in the footer:
```
Issue #42
```

Or to close multiple issues:
```
Closes #42, #43
```

## Language
Commit messages must be written in English.
```
feat(tools): Add file search functionality

Implement fast search using search indices
Closes #24
```
