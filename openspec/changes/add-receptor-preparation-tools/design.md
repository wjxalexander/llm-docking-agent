## Context
The goal is to integrate receptor preparation for docking into the agent, mirroring the workflow in `basic_docking.ipynb`. This involves downloading PDBs, cleaning them, protonating them, and converting to PDBQT with a defined grid box.

## Goals / Non-Goals
- **Goals**: 
    - Provide a simple tool `prepare_receptor` that handles the full pipeline.
    - Provide `download_pdb` for fetching structures.
    - Use `ProDy` for structure manipulation (selection, cleaning).
    - Use `meeko` for PDBQT conversion and box generation.
- **Non-Goals**:
    - Full replacement of complex manual prep if `reduce2` cannot be easily bundled. We will prioritize functionality available via PyPI packages.

## Decisions
- **Decision**: Use `ProDy` for PDB parsing and atom selection.
    - **Rationale**: Efficient, Python-native, and specified in the notebook logic.
- **Decision**: Use `meeko` library API for PDBQT conversion.
    - **Rationale**: Avoids subprocess calls to `mk_prepare_receptor.py` and allows better error handling.
- **Decision**: Handling Protonation.
    - **Rationale**: The notebook uses `reduce2`. If `reduce2` is not available in the python environment as a package, we may need to use RDKit or similar for adding hydrogens, or document `reduce` as an external dependency. For the initial implementation, we will structure the code to allow a protonation step, potentially defaulting to a simpler RDKit-based method if `reduce` is missing, or requiring the user to provide a protonated PDB. *Update*: We will attempt to implement a robust fall-back or check for `reduce` presence.

## Risks / Trade-offs
- **Risk**: `reduce2` dependency complexity.
    - **Mitigation**: Document clear error messages if external tools are missing. Provide a "skip_protonation" option if the user supplies an already prepped PDB.

## Open Questions
- Is `reduce2` available in the deployment environment?
- Can we ship a lightweight protonator?

