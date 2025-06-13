# Check Documentation Updates

After completing an implementation or code changes, systematically review and update all relevant documentation to ensure consistency and completeness across the project.

## Instructions

1. **Implementation Analysis**
   - Review the recent code changes and their scope
   - Identify the nature of changes (new features, bug fixes, refactoring, etc.)
   - Determine which components, APIs, or workflows were modified
   - Assess the impact on existing functionality and user experience

2. **Documentation Impact Assessment**
   - **Core Documentation**: README.md, CLAUDE.md
   - **User Documentation**: docs/ directory (user guides, API docs, tutorials)
   - **AI Instructions**: .github/instructions/ directory (custom instructions for AI agents)
   - **Development Documentation**: Contributing guides, setup instructions, testing docs
   - **Configuration Files**: Comments in config files, environment examples

3. **Systematic Documentation Review**

   ### 3.1 README.md Review
   - **Installation instructions**: Are they still accurate?
   - **Usage examples**: Do they reflect current API/interface?
   - **Feature list**: Are new features mentioned? Deprecated features removed?
   - **Getting started guide**: Does it work with current implementation?
   - **Dependencies**: Are version requirements up to date?

   ### 3.2 CLAUDE.md Review
   - **Project context**: Does it reflect current architecture?
   - **Build/test commands**: Are they still valid?
   - **Development workflow**: Does it match current practices?
   - **Known issues**: Are resolved issues removed? New issues added?
   - **Service architecture**: Does it reflect recent refactoring?
   - **Testing strategy**: Are new testing approaches documented?

   ### 3.3 docs/ Directory Review
   - **API documentation**: Are new endpoints/methods documented?
   - **User guides**: Do they work with current features?
   - **Architecture docs**: Do they reflect current design?
   - **Configuration guides**: Are new options documented?
   - **Troubleshooting**: Are new common issues included?

   ### 3.4 .github/instructions/ Review
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

## Specific Areas to Check

### After Feature Implementation
- [ ] README.md feature list and usage examples
- [ ] API documentation for new endpoints/methods
- [ ] User guides for new functionality
- [ ] CLAUDE.md service architecture updates
- [ ] Configuration examples and environment variables

### After Bug Fixes
- [ ] Known issues section in CLAUDE.md
- [ ] Troubleshooting guides in docs/
- [ ] Common pitfalls documentation
- [ ] Testing strategy updates if testing approach changed

### After Refactoring
- [ ] Architecture documentation in docs/
- [ ] CLAUDE.md service layer descriptions
- [ ] Developer guides and setup instructions
- [ ] .github/instructions/ custom instructions
- [ ] Code examples throughout documentation

### After Configuration Changes
- [ ] Environment setup instructions
- [ ] Configuration file examples
- [ ] Deployment guides
- [ ] Development environment setup

### After Dependencies Updates
- [ ] Installation instructions
- [ ] Requirements documentation
- [ ] Compatibility information
- [ ] Known issues with specific versions

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
