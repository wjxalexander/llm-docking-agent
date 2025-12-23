# project-conventions Specification

## Purpose
TBD - created by archiving change update-code-style. Update Purpose after archive.
## Requirements
### Requirement: Code Style Compliance
All code in the project SHALL follow the defined code style conventions based on "Code Complete 2" and PEP 8.

#### Scenario: Code follows naming conventions
- **WHEN** a developer creates a new variable or function
- **THEN** it must use snake_case and be descriptive as per project.md

#### Scenario: Code is logically organized
- **WHEN** a developer writes a new module
- **THEN** it must use whitespace and grouping to reflect logical structure as per project.md

### Requirement: Project Structure Stability
AI assistants SHALL NOT modify the project directory structure (e.g., creating, moving, or deleting top-level directories) without explicit justification and a formal change proposal.

#### Scenario: Unauthorized directory creation
- **WHEN** an assistant attempts to create a new top-level directory without a proposal
- **THEN** it must be blocked or flagged as a violation of project constraints

