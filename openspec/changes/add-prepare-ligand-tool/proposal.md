# Change: Add Prepare Ligand Tool

## Why
Currently, the agent lacks a dedicated tool for preparing molecular ligands for docking. This process, as demonstrated in the notebooks, is a critical first step in any docking workflow. Adding this tool will allow the agent to automate the conversion of SMILES strings into the PDBQT format required by AutoDock Vina.

## What Changes
- Add a new tool `prepare_ligand` to the agent.
- The tool will wrap `molscrub` for 3D conformer generation and `meeko` for PDBQT preparation.
- The tool will handle SMILES input, pH specification, and optional enumeration settings.

## Impact
- Affected specs: `ligand-preparation` (new capability)
- Affected code: `app/agent.py` (tool registration), `app/tools/ligand_preparation.py` (new tool implementation)

