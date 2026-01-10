# Change: Add Receptor Preparation Tools

## Why
Researchers need to prepare receptor structures for docking simulations directly within the agent workflow. Currently, they have to do this manually or in a separate environment. Automating this process will streamline the docking workflow.

## What Changes
- Add `download_pdb` tool to fetch PDB files from RCSB.
- Add `prepare_receptor` tool to clean, protonate, and convert PDB files to PDBQT format with grid box definition.
- Add dependencies: `ProDy` for structure manipulation.

## Impact
- Affected specs: `receptor-preparation` (new capability)
- Affected code: `app/tools/receptor_preparation.py`, `app/agent.py`, `pyproject.toml`

