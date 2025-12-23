## ADDED Requirements
### Requirement: Project Structure Stability
AI assistants SHALL NOT modify the project directory structure (e.g., creating, moving, or deleting top-level directories) without explicit justification and a formal change proposal.

#### Scenario: Unauthorized directory creation
- **WHEN** an assistant attempts to create a new top-level directory without a proposal
- **THEN** it must be blocked or flagged as a violation of project constraints

