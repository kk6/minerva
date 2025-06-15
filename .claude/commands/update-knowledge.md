# Update Knowledge Base

Analyze the current conversation for valuable insights and knowledge gained during coding tasks, then update the appropriate documentation following the hierarchical strategy: `docs/` (primary) → `CLAUDE.md` (essentials only).

## Instructions

1. **Review Current Conversation**
   - Analyze the entire conversation history for valuable insights
   - Identify coding patterns, solutions, best practices, and lessons learned
   - Look for troubleshooting approaches, error resolutions, and workarounds
   - Note any technology-specific discoveries or configuration insights
   - Examine feedback provided during code reviews and subsequent improvements

2. **Knowledge Classification and Target Selection**
   - **Comprehensive Knowledge** → `docs/` directory (master documentation)
   - **Claude Code Essentials** → `CLAUDE.md` (essential commands/workflows only)
   - **Quick Reference** → Update existing docs/ files with new patterns
   - **Troubleshooting** → Specific docs/ troubleshooting files

3. **Primary Target: docs/ Directory Updates**
   **Priority 1**: Update appropriate `docs/` files based on knowledge type:
   - **Development patterns** → `docs/development_workflow.md`
   - **Testing insights** → `docs/test_guidelines.md`
   - **Technical solutions** → `docs/technical_spec.md`
   - **Troubleshooting** → `docs/vector_search_troubleshooting.md` or relevant files
   - **Configuration** → `docs/optional_dependencies.md`
   - **Performance tips** → `docs/property_based_testing.md` or relevant files

4. **Secondary Target: CLAUDE.md Updates (Minimal)**
   **Only update CLAUDE.md for**:
   - **Critical commands** that Claude Code frequently uses
   - **Essential workflows** specific to Claude Code usage
   - **Critical pitfalls** that must be immediately visible
   - **Environment setup** changes that affect Claude Code execution
   - **Size constraint**: Ensure CLAUDE.md stays under 40,000 characters

5. **Content Analysis and Preparation**
   Extract actionable insights categorized by documentation target:

   **For docs/ files**:
   - Comprehensive troubleshooting procedures
   - Detailed best practices and patterns
   - Complete workflow documentation
   - In-depth technical explanations
   - Extensive code examples and configurations

   **For CLAUDE.md (essentials only)**:
   - Critical command shortcuts
   - Essential workflow reminders
   - Key pitfalls that affect Claude Code specifically
   - References to detailed docs/ files

6. **Implementation Strategy**

   ### 6.1 docs/ Directory Updates (Primary Focus)
   - **Update appropriate docs/ files** with comprehensive knowledge
   - **Use clear, descriptive headings** and subheadings
   - **Include detailed examples** with full context and explanations
   - **Add comprehensive code snippets** with configuration examples
   - **Cross-reference related sections** within docs/ files
   - **Maintain existing structure** of each docs/ file

   ### 6.2 CLAUDE.md Updates (Secondary, Minimal)
   - **Add only essential references** with links to detailed docs/ files
   - **Keep additions concise** (prefer 1-3 lines + "See docs/file.md")
   - **Update existing sections** rather than creating new ones
   - **Maintain size constraint** (under 40,000 characters)
   - **Focus on Claude Code-specific needs** only

7. **Quality Assurance**
   - **Accuracy**: Verify all content is accurate and actionable
   - **Consistency**: Ensure formatting matches existing file styles
   - **Non-duplication**: Check that new content doesn't duplicate existing information
   - **Hierarchical compliance**: Detailed info in docs/, essentials in CLAUDE.md
   - **Transferability**: Confirm knowledge applies to similar future situations
   - **Privacy protection**: Exclude sensitive information
   - **Size monitoring**: Keep CLAUDE.md under character limit

8. **Documentation Standards**

   ### 8.1 For docs/ Files (Comprehensive)
   - **Detailed explanations** with full context
   - **Complete code examples** with setup and configuration
   - **Multiple approaches** when applicable
   - **Troubleshooting sections** for common issues
   - **Cross-references** to related docs/ files

   ### 8.2 For CLAUDE.md (Essential Only)
   - **Concise language** with immediate actionability
   - **Quick reference format** with command examples
   - **"See Also" references** to detailed docs/ files
   - **Critical warnings** only for immediate pitfalls

## Expected Outcomes

- **Primary**: Comprehensive knowledge preserved in appropriate docs/ files
- **Secondary**: CLAUDE.md updated with essential Claude Code-specific information
- **Hierarchical structure**: Detailed documentation in docs/, quick reference in CLAUDE.md
- **Maintainability**: Reduced duplication through clear documentation hierarchy
- **Performance**: CLAUDE.md remains under size limit for optimal Claude Code performance

## Content Management Guidelines

### Information Scope (Hierarchical Distribution)

**For docs/ Files**:
- **Include**: Comprehensive technical solutions, detailed best practices, complete troubleshooting procedures, full configuration guides
- **Exclude**: Sensitive data, temporary debugging info, personal opinions without technical basis
- **Prioritize**: Complete workflows, detailed patterns, comprehensive error handling, extensive examples

**For CLAUDE.md**:
- **Include**: Essential commands, critical pitfalls, quick references to docs/ files
- **Exclude**: Detailed explanations, comprehensive examples, extensive troubleshooting
- **Prioritize**: Claude Code-specific workflows, immediate action items, critical warnings

### Structure Maintenance

**docs/ Files**:
- **Respect existing hierarchy**: Follow established docs/ file organization
- **Use comprehensive formatting**: Detailed sections with full context
- **Add detailed sections**: Create comprehensive documentation
- **Internal cross-references**: Link between related docs/ files

**CLAUDE.md**:
- **Maintain lean structure**: Keep existing organization, minimal additions
- **Use concise formatting**: Brief sections with "See Also" references
- **Avoid new sections**: Update existing sections or reference docs/ files
- **External references**: Link to detailed docs/ files

### Long-term Sustainability

**docs/ Files**:
- **Comprehensive review**: Periodic in-depth content review
- **Natural expansion**: Allow detailed content growth as needed
- **Update workflows**: Regular maintenance of complete procedures
- **Version tracking**: Detailed version compatibility information

**CLAUDE.md**:
- **Size monitoring**: Regular character count monitoring (under 40,000)
- **Lean maintenance**: Remove outdated content, add only essentials
- **Reference validation**: Ensure "See Also" links remain accurate
- **Performance focus**: Prioritize Claude Code execution speed
