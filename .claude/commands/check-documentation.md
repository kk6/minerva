# Check Documentation Updates

After completing an implementation or code changes, systematically review and update all relevant documentation following the hierarchical documentation strategy: `docs/` → `CLAUDE.md` → `README.md`.

## Instructions

1. **Implementation Analysis**
   - Review the recent code changes and their scope
   - Identify the nature of changes (new features, bug fixes, refactoring, etc.)
   - Determine which components, APIs, or workflows were modified
   - Assess the impact on existing functionality and user experience

2. **Hierarchical Documentation Strategy**
   **Primary Focus**: `docs/` directory (master source of truth)
   **Secondary**: `CLAUDE.md` (Claude Code essentials + references to docs/)
   **Tertiary**: `README.md` (user onboarding)
   **Supporting**: `.github/instructions/` (AI agent guidelines)

3. **Documentation Update Priority (Follow This Order)**

   ### 3.1 docs/ Directory Review (PRIMARY - Master Documentation)
   - **API documentation**: Are new endpoints/methods documented?
   - **User guides**: Do they work with current features?
   - **Architecture docs**: Do they reflect current design?
   - **Configuration guides**: Are new options documented?
   - **Troubleshooting**: Are new common issues included?
   - **Development workflow**: Complete development process documentation
   - **Testing guidelines**: Comprehensive testing strategies and patterns

   ### 3.2 CLAUDE.md Review (SECONDARY - Claude Code Essentials)
   - **Project context**: Does it reflect current architecture?
   - **Build/test commands**: Are they still valid and complete?
   - **Critical workflows**: Essential Claude Code-specific information only
   - **Known issues**: Resolved issues removed? New issues added?
   - **Reference links**: Do "See Also" links point to correct docs/ files?
   - **Size check**: Ensure file stays under 40,000 characters

   ### 3.3 README.md Review (TERTIARY - User Onboarding)
   - **Installation instructions**: Are they still accurate?
   - **Usage examples**: Do they reflect current API/interface?
   - **Feature list**: Are new features mentioned? Deprecated features removed?
   - **Getting started guide**: Does it work with current implementation?
   - **Dependencies**: Are version requirements up to date?

   ### 3.4 .github/instructions/ Review (SUPPORTING - AI Guidelines)
   - **Custom instructions**: Do they reflect current codebase structure?
   - **AI agent guidelines**: Are they consistent with current practices?
   - **Workflow instructions**: Do they match current development process?
   - **Code style guides**: Are they up to date with current standards?

4. **Content Verification**
   - **Accuracy**: All documented procedures actually work
   - **Completeness**: No missing steps or information
   - **Consistency**: Terminology and style are consistent across documents
   - **Currency**: Information reflects the current state of the project
   - **Examples**: Code examples compile and run successfully

5. **Update Prioritization**
   - **Critical**: Documentation that affects user onboarding or core functionality
   - **High**: API changes, new features, changed workflows
   - **Medium**: Clarifications, additional examples, improved explanations
   - **Low**: Cosmetic improvements, minor reorganization

6. **Documentation Updates**
   - **Update existing content**: Modify outdated information
   - **Add new sections**: Document new features or processes
   - **Remove obsolete content**: Delete information that no longer applies
   - **Improve clarity**: Enhance explanations based on recent learnings
   - **Add cross-references**: Link related documentation sections

7. **Consistency Checks**
   - **Terminology**: Use consistent terms across all documents
   - **Code style**: Follow established formatting conventions
   - **Structure**: Maintain consistent organization patterns
   - **Language**: Follow project language guidelines (English for technical, Japanese for user docs)
   - **Formatting**: Use consistent markdown style and conventions

8. **Validation**
   - **Test procedures**: Verify that documented steps actually work
   - **Link checking**: Ensure all internal and external links are valid
   - **Code examples**: Confirm all code snippets are functional
   - **Screenshots**: Update any outdated visual documentation
   - **Version compatibility**: Verify information applies to current versions

## Specific Areas to Check (Hierarchical Priority)

### After Feature Implementation
**Priority 1 - docs/ (Master Documentation)**:
- [ ] docs/technical_spec.md for new API endpoints/methods
- [ ] docs/note_operations.md or relevant feature docs for user guides
- [ ] docs/development_workflow.md for development process changes

**Priority 2 - CLAUDE.md (Claude Code Essentials)**:
- [ ] Key Features section for new functionality summary
- [ ] Build/Test/Lint Commands if new commands added
- [ ] Service architecture overview (brief, with reference to docs/)

**Priority 3 - README.md (User Onboarding)**:
- [ ] Feature list and usage examples
- [ ] Installation/getting started if setup changed

### After Bug Fixes
**Priority 1 - docs/ (Master Documentation)**:
- [ ] docs/vector_search_troubleshooting.md or relevant troubleshooting docs
- [ ] docs/test_guidelines.md if testing approach changed
- [ ] docs/error_handling.md for common pitfalls

**Priority 2 - CLAUDE.md (Claude Code Essentials)**:
- [ ] Known Issues section (brief summary with reference to docs/)
- [ ] Common Pitfalls to Avoid section

### After Refactoring
**Priority 1 - docs/ (Master Documentation)**:
- [ ] docs/technical_spec.md for architecture changes
- [ ] docs/development_workflow.md for process updates
- [ ] docs/test_guidelines.md for testing approach changes

**Priority 2 - CLAUDE.md (Claude Code Essentials)**:
- [ ] Service-Based Architecture section (overview only)
- [ ] Code examples update if patterns changed

**Priority 3 - .github/instructions/**:
- [ ] Custom instructions for AI agents
- [ ] Code style guides and patterns

### After Configuration Changes
**Priority 1 - docs/ (Master Documentation)**:
- [ ] docs/development_setup.md for environment setup
- [ ] docs/optional_dependencies.md for feature configuration

**Priority 2 - CLAUDE.md (Claude Code Essentials)**:
- [ ] Environment Setup section
- [ ] Optional Feature Configuration patterns

### After Dependencies Updates
**Priority 1 - docs/ (Master Documentation)**:
- [ ] docs/requirements.md for detailed dependency information
- [ ] docs/optional_dependencies.md for optional feature dependencies

**Priority 2 - README.md (User Onboarding)**:
- [ ] Installation instructions
- [ ] Compatibility information

**Priority 3 - CLAUDE.md (Claude Code Essentials)**:
- [ ] Known Issues section for version-specific issues

## Documentation Quality Standards

### Content Requirements
- **Actionable**: Every instruction should be executable
- **Complete**: No missing prerequisites or steps
- **Accurate**: Information must reflect current implementation
- **Clear**: Written for the intended audience level
- **Maintainable**: Easy to update when changes occur

### Format Requirements
- **Consistent markdown style**: Follow project conventions
- **Proper heading hierarchy**: Use logical H1-H6 structure
- **Code formatting**: Use appropriate syntax highlighting
- **Link formatting**: Use descriptive link text
- **Table formatting**: Properly aligned and readable

### Language Requirements
- **Technical content**: English for code, APIs, and development docs
- **User content**: Japanese for user-facing documentation (where applicable)
- **Consistent terminology**: Use established project vocabulary
- **Professional tone**: Clear, helpful, and professional language

## Expected Outcomes

- All documentation accurately reflects current implementation
- No outdated or misleading information remains
- New features and changes are properly documented
- Documentation consistency is maintained across all files
- Users can successfully follow all documented procedures
- AI agents have current and accurate project context

## Post-Update Verification

1. **Run through key user workflows** using only the documentation
2. **Test all code examples** to ensure they work
3. **Verify all links** are functional and point to correct resources
4. **Check cross-references** between different documentation files
5. **Confirm language consistency** across all updated documents
6. **Validate that changes align** with project documentation standards

## Maintenance Recommendations

- **Link this command** to your pull request template
- **Run after every significant implementation**
- **Schedule periodic comprehensive reviews**
- **Update documentation templates** when patterns emerge
- **Create documentation update checklists** for common change types
