---
applyTo: '**'
---

# AI Assistant Guidelines for Minerva

## Issue Creation Guidelines

When creating GitHub issues, AI assistants must:

1. **Always identify yourself**: Include your model name in the issue description
2. **Use appropriate templates**: Select the most relevant issue template
3. **Provide complete information**: Fill out all required fields in the template

### Required Information for AI-Created Issues and Pull Requests

- **Creator identification**: Clearly state your AI model name (e.g., "Claude 3.5 Sonnet", "GPT-4", etc.)
- **Context**: Explain the context that led to the issue creation or the pull request
- **Specificity**: Provide specific, actionable descriptions

### Example Format

```markdown
## AI生成情報
<!-- AIアシスタントが作成した場合は記入してください -->
- [ ] この Issue は AI アシスタントによって作成されました
- AIモデル: <!-- 自身のモデル名を記載。例: Claude Sonnet 4, GPT-4.1 など -->
- 作成日時: <!-- YYYY-MM-DD HH:MM 形式 -->
- 生成根拠: <!-- ユーザーの要求やプロンプトの概要 -->
```

## Document-First Approach

Before creating issues for new features or improvements, ensure relevant documentation is updated first according to the project's document-first philosophy.

## Virtual Environment Protection

**CRITICAL**: Never delete, modify, or run commands that affect files in the `.venv` directory. This can break the Python virtual environment and cause development issues. If you need to recommend package installations or environment changes, always use `uv` commands as specified in the build instructions.
