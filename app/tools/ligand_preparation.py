# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tool for preparing molecular ligands for docking."""

import os
import subprocess
from pathlib import Path


def prepare_ligand(
    smiles: str,
    output_filename: str = "ligand.pdbqt",
    ph: float = 6.0,
    skip_tautomer: bool = True,
    skip_acidbase: bool = False,
) -> str:
    """Prepares a ligand PDBQT file from a SMILES string for docking.

    This tool uses `scrub.py` (from molscrub) to generate a protonated 3D conformer
    and `mk_prepare_ligand.py` (from meeko) to convert it to PDBQT format.

    Args:
        smiles: The SMILES string of the ligand molecule.
        output_filename: The desired name for the output PDBQT file.
        ph: The pH value for protonation. Defaults to 6.0.
        skip_tautomer: If True, skips tautomer enumeration. Defaults to True.
        skip_acidbase: If True, skips acid-base enumeration. Defaults to False.

    Returns:
        The absolute path to the generated PDBQT file.

    Raises:
        RuntimeError: If ligand preparation scripts fail.
    """
    base_name = Path(output_filename).stem
    sdf_file = f"{base_name}_scrubbed.sdf"

    # Step 1: Run molscrub (scrub.py) to generate 3D conformer and protonate
    scrub_args = []
    if skip_tautomer:
        scrub_args.append("--skip_tautomer")
    if skip_acidbase:
        scrub_args.append("--skip_acidbase")

    scrub_cmd = ["scrub.py", smiles, "-o", sdf_file, "--ph", str(ph)] + scrub_args

    try:
        # Added timeout to prevent hanging on complex molecules
        subprocess.run(
            scrub_cmd, check=True, capture_output=True, text=True, timeout=60
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("molscrub (scrub.py) timed out after 60 seconds.") from None
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"molscrub (scrub.py) failed: {e.stderr}") from e
    except FileNotFoundError:
        raise RuntimeError(
            "scrub.py not found in PATH. Ensure molscrub is installed."
        ) from None

    # Step 2: Run meeko (mk_prepare_ligand.py) to convert SDF to PDBQT
    prepare_cmd = ["mk_prepare_ligand.py", "-i", sdf_file, "-o", output_filename]

    try:
        # Added timeout to prevent hanging
        subprocess.run(
            prepare_cmd, check=True, capture_output=True, text=True, timeout=60
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            "mk_prepare_ligand.py timed out after 60 seconds."
        ) from None
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"mk_prepare_ligand.py failed: {e.stderr}") from e
    except FileNotFoundError:
        raise RuntimeError(
            "mk_prepare_ligand.py not found in PATH. Ensure meeko is installed."
        ) from None
    finally:
        # Cleanup temporary SDF file
        if os.path.exists(sdf_file):
            os.remove(sdf_file)

    if not os.path.exists(output_filename):
        raise RuntimeError(f"Failed to generate output file: {output_filename}")

    return os.path.abspath(output_filename)


