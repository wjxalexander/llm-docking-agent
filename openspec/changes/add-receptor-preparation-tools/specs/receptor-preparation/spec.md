## ADDED Requirements
### Requirement: Download PDB Structure
The agent SHALL provide a tool to download molecular structures from the RCSB PDB server.

#### Scenario: Download success
- **WHEN** user asks to "download PDB 1iep"
- **THEN** the file `1iep.pdb` is saved to the workspace and the path is returned.

#### Scenario: Invalid PDB ID
- **WHEN** user asks to "download PDB xxxxx"
- **THEN** the tool returns an error message indicating the ID is invalid or not found.

### Requirement: Prepare Receptor for Docking
The agent SHALL provide a tool to prepare a receptor PDB file for docking, including cleaning, protonation (optional/best-effort), and PDBQT conversion with grid box definition.

#### Scenario: Full preparation
- **WHEN** user invokes `prepare_receptor` with a PDB file and box parameters
- **THEN** the tool cleans the structure (removes water/heteroatoms), adds hydrogens, generates a PDBQT file, and creates a box configuration file.

#### Scenario: Custom selection
- **WHEN** user provides a custom ProDy selection string
- **THEN** only the selected atoms are included in the receptor.

#### Scenario: Box definition by ligand
- **WHEN** user specifies a ligand residue for the box center
- **THEN** the grid box is centered on the geometric center of that ligand.

