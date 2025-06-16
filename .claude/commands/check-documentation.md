# Check Documentation Updates

After completing an implementation or code changes, systematically review and update all relevant documentation following the hierarchical documentation strategy: `docs/` → `CLAUDE.md` → `README.md`.

## Instructions

1. **Automated Implementation vs Documentation Gap Analysis** ⚠️ **CRITICAL FIRST STEP**

   Before any manual documentation review, perform systematic implementation scanning to detect undocumented features:

   ### 1.1 MCP Tools Gap Detection
   ```
   Task: "Analyze MCP tools implementation vs documentation gaps"
   Instructions:
   - Extract all @mcp.tool() decorated functions from server.py
   - Check which tools are documented in note_operations.md, README.md
   - Identify completely undocumented tools
   - Identify tools with incomplete parameter documentation
   - Return specific list of gaps with tool names and missing documentation
   ```

   ### 1.2 Service Layer Gap Detection
   ```
   Task: "Analyze service layer implementation vs documentation gaps"
   Instructions:
   - Examine all service classes in services/ directory
   - Check public methods vs technical_spec.md documentation
   - Identify new service modules not reflected in architecture docs
   - Check configuration options in config.py vs environment documentation
   - Return specific service methods and config options that are undocumented
   ```

   ### 1.3 Advanced Features Gap Detection
   ```
   Task: "Analyze advanced features implementation vs documentation gaps"
   Instructions:
   - Check vector search module completeness (vector/ directory)
   - Examine error handling and safety mechanisms in code vs docs
   - Check performance optimization features vs documentation
   - Identify testing patterns and development tools not documented
   - Return specific features, classes, and capabilities that are undocumented
   ```

   ### 1.4 Configuration Gap Detection
   ```
   Task: "Analyze configuration implementation vs documentation gaps"
   Instructions:
   - Extract all environment variables from config.py and .env.example
   - Check which variables are documented in README.md and docs/
   - Check default values and behavior documentation
   - Identify optional feature configurations not explained
   - Return specific environment variables and config options that are undocumented
   ```

   **Expected Output**: Comprehensive gap report with:
   - Total number of implemented features vs documented features
   - Specific list of undocumented MCP tools (function names)
   - Specific list of undocumented service methods
   - Specific list of undocumented configuration options
   - Priority ranking for documentation updates
   - Recommended documentation files to update

2. **Implementation Analysis**
   - Review the recent code changes and their scope
   - Identify the nature of changes (new features, bug fixes, refactoring, etc.)
   - Determine which components, APIs, or workflows were modified
   - Assess the impact on existing functionality and user experience

3. **Hierarchical Documentation Strategy**
   **Primary Focus**: `docs/` directory (master source of truth)
   **Secondary**: `CLAUDE.md` (Claude Code essentials + references to docs/)
   **Tertiary**: `README.md` (user onboarding)
   **Supporting**: `.github/instructions/` (AI agent guidelines)

4. **Documentation Update Priority (Follow This Order)**

   **IMPORTANT**: Use the gap analysis results from step 1 to prioritize specific documentation updates rather than generic reviews.

   ### 4.1 docs/ Directory Review (PRIMARY - Master Documentation)
   - **API documentation**: Cross-reference gap analysis results for undocumented MCP tools and service methods
   - **User guides**: Update note_operations.md with any missing vector search or advanced features from gap analysis
   - **Architecture docs**: Reflect service layer changes identified in gap analysis
   - **Configuration guides**: Add all undocumented environment variables from gap analysis
   - **Troubleshooting**: Include error handling and safety mechanisms found in gap analysis
   - **Development workflow**: Document any testing patterns or development tools from gap analysis
   - **Testing guidelines**: Update with any new testing strategies or patterns

   ### 4.2 CLAUDE.md Review (SECONDARY - Claude Code Essentials)
   - **Project context**: Update with new features and architecture changes from gap analysis
   - **Build/test commands**: Add any new commands discovered in implementation
   - **Critical workflows**: Include essential information for newly discovered features
   - **Known issues**: Add any undocumented error handling or troubleshooting from gap analysis
   - **Reference links**: Ensure "See Also" links point to updated docs/ files
   - **Size check**: Ensure file stays under 40,000 characters

   ### 4.3 README.md Review (TERTIARY - User Onboarding)
   - **Installation instructions**: Update with any new dependency requirements from gap analysis
   - **Usage examples**: Add examples for undocumented MCP tools and features
   - **Feature list**: Add all undocumented features identified in gap analysis
   - **Getting started guide**: Include setup for advanced features like vector search
   - **Dependencies**: Update version requirements for any new dependencies

   ### 4.4 .github/instructions/ Review (SUPPORTING - AI Guidelines)
   - **Custom instructions**: Update with current codebase structure from gap analysis
   - **AI agent guidelines**: Include patterns for newly documented features
   - **Workflow instructions**: Update with any new development tools or processes
   - **Code style guides**: Reflect any new architectural patterns

5. **Content Verification**
   - **Accuracy**: All documented procedures actually work, especially newly documented features from gap analysis
   - **Completeness**: Verify all gaps from analysis have been addressed
   - **Consistency**: Terminology and style are consistent across documents
   - **Currency**: Information reflects the current state of the project
   - **Examples**: Code examples compile and run successfully, especially for new MCP tools

6. **Update Prioritization Based on Gap Analysis**
   - **Critical**: Undocumented MCP tools and core functionality identified in gap analysis
   - **High**: New service methods, configuration options, and architecture changes
   - **Medium**: Enhanced examples for existing but incompletely documented features
   - **Low**: Cosmetic improvements after all gaps are addressed

7. **Documentation Updates**
   - **Add new sections**: Document all features identified in gap analysis
   - **Update existing content**: Enhance incomplete documentation identified in analysis
   - **Remove obsolete content**: Delete information that no longer applies
   - **Improve clarity**: Enhance explanations based on gap analysis findings
   - **Add cross-references**: Link related documentation sections for new features

8. **Consistency Checks**
   - **Terminology**: Use consistent terms across all documents
   - **Code style**: Follow established formatting conventions
   - **Structure**: Maintain consistent organization patterns
   - **Language**: Follow project language guidelines (English for technical, Japanese for user docs)
   - **Formatting**: Use consistent markdown style and conventions

9. **Validation**
   - **Test procedures**: Verify that documented steps actually work, especially for newly documented features
   - **Link checking**: Ensure all internal and external links are valid
   - **Code examples**: Confirm all code snippets are functional, test new MCP tool examples
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

- **Zero implementation-documentation gaps**: All implemented features are properly documented
- **Quantifiable coverage**: Report showing X/Y MCP tools documented, Z/W service methods documented
- All documentation accurately reflects current implementation
- No outdated or misleading information remains
- New features and changes are properly documented with examples
- Documentation consistency is maintained across all files
- Users can successfully follow all documented procedures
- AI agents have current and accurate project context

## Post-Update Verification

1. **Re-run gap analysis** to verify all gaps have been addressed
2. **Test all new code examples** to ensure they work, especially for newly documented MCP tools
3. **Run through key user workflows** using only the documentation
4. **Verify all links** are functional and point to correct resources
5. **Check cross-references** between different documentation files
6. **Confirm language consistency** across all updated documents
7. **Validate that changes align** with project documentation standards

## Automated Gap Detection - Key Learnings

Based on the comprehensive audit that identified 9 undocumented vector search tools:

### Common Gap Patterns to Watch For:
1. **MCP Tools**: `@mcp.tool()` decorated functions not in user documentation
2. **Service Methods**: Public methods in services/ not in technical documentation
3. **Configuration Options**: Environment variables in config.py not documented
4. **Advanced Features**: Optional dependencies and their capabilities
5. **Error Handling**: Safety mechanisms and recovery procedures
6. **Performance Features**: Optimization tools and monitoring capabilities

### Prevention Strategies:
- **Always run automated gap analysis first** before manual documentation review
- **Use Task tool with specific implementation scanning instructions**
- **Focus on concrete, discoverable gaps** rather than general documentation quality
- **Generate actionable gap reports** with specific function names and missing documentation
- **Prioritize user-facing features** (MCP tools) over internal implementation details

## Maintenance Recommendations

- **CRITICAL**: Always start with automated gap analysis using the Task tool
- **Link this command** to your pull request template
- **Run after every significant implementation**
- **Schedule periodic comprehensive reviews** (monthly automated gap scans)
- **Update documentation templates** when patterns emerge
- **Create issue templates** for documentation gaps (see Issue #98 as example)
- **Track documentation coverage metrics** (X/Y tools documented)
