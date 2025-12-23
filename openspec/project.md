# Project Context

## Purpose
You are a research assitant who focus on using AutoDock-Vina to help us docking.

## Tech Stack
- Google Genimi 3
- Python
- Google Agent Starter Pack

## Project Conventions

### Code Style
- **Descriptive Naming**: Use clear, specific names for variables, functions, and classes. Favor readability over brevity.
  - Variables/Functions: `snake_case` (e.g., `docking_score_threshold`).
  - Classes: `PascalCase` (e.g., `DockingAnalyzer`).
  - Constants: `SCREAMING_SNAKE_CASE` (e.g., `MAX_RETRY_COUNT`).
- **Logical Layout**: Use whitespace to group related operations and separate logical sections. Follow PEP 8 for indentation (4 spaces).
- **Strong Verb-Noun Pairs**: Functions should be named using a strong verb and a clear noun (e.g., `parse_ligand_file`).
- **Simplicity & Readability**: Prefer straightforward code over "clever" solutions. Code should be self-documenting.
- **Defensive Programming**: Validate inputs and handle edge cases or errors early (fail-fast).
- **Documentation**: Use docstrings for all public modules, classes, and functions to explain *what* they do. Use comments to explain *why* something is done if it's not obvious.
- **Single Responsibility**: Each function or class should focus on a single, well-defined task.

### Architecture Patterns
[Document your architectural decisions and patterns]

### Testing Strategy

### Git Workflow

## Domain Context
there are some ipynb prjects you can refer:
under the directory *notebooks/auto-dock-vina* there are 3 examples:
1. notebooks/auto-dock-vina/basic_docking.ipynb
The basic docking example is a rewrite based on the original basic docking example. In this example, a small molecule ligand (Imatinib, PDB token STI) is docked back to a hollow protein structure of mouse c-Abl (PDB token 1IEP) to reproduce the complex structure. A docked pose that closely resembles the original position of the ligand is expected among the top-ranked poses.
2. notebooks/auto-dock-vina/flexible_docking.ipynb
The flexible docking example is a rewrite based on the original flexible docking example. In this example, a variant of Imatinib (PDB token PRC) is docked back to a hollow protein structure of mouse c-Abl (PDB token 1FPU) to reproduce the complex structure. Additionally, Thr315 is set to be a flexible residue. A docked pose that closely resembles the original position of the ligand and a flipped Thr315 are expected among the top-ranked poses.
3.notebooks/auto-dock-vina/docking_with_AD4SF.ipynb
The using AutoDock4 (AD4) scoring function (SF) example is a rewrite based on the corresponding part of the original basic docking example. This example conducts the same redocking experiment as in Basic docking with the AutoDock4 scoring function instead of Vina. To do this, Autogrid4 is used to compute the grid maps, as an additional step after receptor preparation.


## Important Constraints
- **Directory Structure Stability**: Do not modify the project directory structure (e.g., creating, moving, or deleting top-level directories) easily. Any such changes must be justified and proposed through a formal change process.
## External Dependencies
