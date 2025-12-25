# Project Context

## Purpose
You are a research assistant focusing on molecular docking using AutoDock Vina. The project provides a ReAct agent built with Google's Agent Development Kit (ADK) to help researchers perform basic, flexible, and advanced docking workflows.

## Tech Stack
- **Language**: Python 3.10+
- **Agent Framework**: Google Agent Development Kit (ADK) / Agent Starter Pack
- **LLM**: Google Gemini 3 (Flash Preview)
- **Package Manager**: `uv`
- **Infrastructure**: Google Cloud Platform (Agent Engine, Vertex AI)
- **IaC**: Terraform
- **Scientific Libraries**: RDKit, Meeko, Gemmi, Numpy, Scipy
- **Docking Engine**: AutoDock Vina (CLI)
- **CI/CD**: Google Cloud Build / GitHub Actions

## Project Conventions

### Code Style
- **Formatting**: Strictly follow `ruff` formatting and linting rules (configured in `pyproject.toml`).
- **Typing**: Use static type hints for all function signatures. `mypy` is used for verification.
- **Descriptive Naming**: Use clear, specific names for variables, functions, and classes. Favor readability over brevity.
  - Variables/Functions: `snake_case` (e.g., `docking_score_threshold`).
  - Classes: `PascalCase` (e.g., `DockingAnalyzer`).
  - Constants: `SCREAMING_SNAKE_CASE` (e.g., `MAX_RETRY_COUNT`).
- **Logical Layout**: Use whitespace to group related operations and separate logical sections. Follow PEP 8 for indentation (4 spaces).
- **Strong Verb-Noun Pairs**: Functions should be named using a strong verb and a clear noun (e.g., `parse_ligand_file`).
- **Simplicity & Readability**: Prefer straightforward code over "clever" solutions. Code should be self-documenting.
- **Defensive Programming**: Validate inputs and handle edge cases or errors early (fail-fast).
- **Documentation**: Use Google-style docstrings for all public modules, classes, and functions. Use comments to explain *why* something is done if it's not obvious.
- **Single Responsibility**: Each function or class should focus on a single, well-defined task.

### Architecture Patterns
- **ReAct Agent**: Follows the Reason+Act pattern using `google.adk`.
- **Tool-Based Design**: Functionality is exposed to the agent via discrete tools (typically in `app/tools/` or as functions in `app/agent.py`).
- **Artifact Management**: Uses `GcsArtifactService` for cloud deployments and `InMemoryArtifactService` for local development.
- **Telemetry**: OpenTelemetry is used for tracing and monitoring (integrated with Google Cloud Trace).

### Testing Strategy
- **Unit Testing**: Focused on individual tools and utility functions in `tests/unit/`.
- **Integration Testing**: End-to-end tests for agent flows in `tests/integration/`, often involving streaming responses.
- **Load Testing**: Performance testing using Locust (scripts in `tests/load_test/`).
- **Command**: Use `make test` to run the suite.

### Git Workflow
- **Spec-Driven Development**: All significant changes must follow the OpenSpec process (create proposal in `openspec/changes/`, update specs, then implement).
- **Branching**: Use descriptive feature branches (e.g., `feat/add-autodock-tool`).
- **PRs**: All PRs should pass linting (`make lint`) and tests (`make test`) before merging.

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
- **Directory Structure Stability**: Do not modify the project directory structure (e.g., creating, moving, or deleting top-level directories) without a formal change proposal.
- **Dependency Management**: Use `uv` exclusively for Python dependency management. Do not use `pip` directly unless inside a Dockerfile where `uv` is not yet available.
- **Specific Versions**: Certain scientific packages (e.g., `meeko==0.6.1`) have strict version requirements due to API compatibility with docking workflows.
- **Vina Execution**: Vina MUST be called via subprocess using the path provided in the `VINA_PATH` environment variable.
## External Dependencies

### Core Libraries (via uv)
- `google-adk`: Agent Development Kit for building ReAct agents.
- `google-cloud-aiplatform`: Vertex AI SDK for Gemini and Agent Engine.
- `rdkit`, `meeko`, `gemmi`: specialized libraries for molecular preparation and analysis.
- `opentelemetry`: for observability.

### System Dependencies
- **AutoDock Vina**: Required for docking simulations.
  - **Local (macOS)**: Installed via Conda (Miniforge) to avoid compilation issues with Apple Silicon. Binary path typically `/opt/homebrew/Caskroom/miniforge/base/envs/vina-cli/bin/vina`.
  - **Deployment**: Installed via Conda in the custom Docker container.

#### Deployment (Google Cloud Agent Engine)

For deployment, the project uses a custom Docker image to ensure Vina and its system dependencies (like Conda/Miniconda) are available.

```dockerfile 
FROM python:3.11-slim

# Install miniconda for vina
RUN apt-get update && apt-get install -y wget && \
    wget -qO /tmp/miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash /tmp/miniconda.sh -b -p /opt/conda && \
    rm /tmp/miniconda.sh && \
    /opt/conda/bin/conda install -c conda-forge vina -y && \
    /opt/conda/bin/conda clean -afy

ENV VINA_PATH=/opt/conda/bin/vina

# Install uv and project dependencies
RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
COPY app/ app/

CMD ["uv", "run", "python", "-m", "app.agent_engine_app"]
```

#### Summary Table

| Component | Manager | Location / Path |
|-----------|---------|-----------------|
| Python deps | `uv` | `pyproject.toml` |
| Vina CLI | Conda | `/opt/conda/bin/vina` (Docker) or local conda env |
| Infrastructure | Terraform | `deployment/terraform/` |
| Orchestration | Make | `Makefile` |

#### Related Packages (installable via uv)

```bash
uv add numpy scipy rdkit gemmi meeko==0.6.1 py3Dmol molscrub
```

**Note**: `autogrid` and `cctbx-base` are only available via conda-forge. If needed for AD4 scoring function workflows, install them in the `vina-cli` conda environment and call via subprocess.
