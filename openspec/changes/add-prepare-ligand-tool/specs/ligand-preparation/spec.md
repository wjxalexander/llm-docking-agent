## ADDED Requirements

### Requirement: Ligand Preparation from SMILES
The system SHALL provide a mechanism to convert a SMILES string into a PDBQT file suitable for AutoDock Vina.

#### Scenario: Successful Ligand Preparation
- **WHEN** a valid SMILES string, pH, and output filename are provided
- **THEN** the system generates an SDF file with a 3D conformer
- **AND** the system converts the SDF file into a PDBQT file
- **AND** the system returns the path to the generated PDBQT file

### Requirement: Custom Protonation States
The system MUST allow specifying pH and enumeration options (tautomers, acid-base) during ligand preparation.

#### Scenario: Preparation with Specific pH
- **WHEN** pH 7.4 is specified for a SMILES string
- **THEN** the generated conformer reflects the protonation state at that pH

