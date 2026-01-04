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
from pathlib import Path
from typing import Any

from google.genai import types
from meeko import MoleculePreparation, PDBQTWriterLegacy
from molscrub import Scrub
from rdkit import Chem


def prepare_ligand(
    smiles: str,
    output_filename: str = "ligand.pdbqt",
    ph: float = 6.0,
    skip_tautomer: bool = True,
    skip_acidbase: bool = False,
    tool_context: Any = None,
) -> str:
    """Prepares a ligand PDBQT file from a SMILES string for docking.

    This tool uses `molscrub` to generate a protonated 3D conformer
    and `meeko` to convert it to PDBQT format.

    Args:
        smiles: The SMILES string of the ligand molecule.
        output_filename: The desired name for the output PDBQT file.
        ph: The pH value for protonation. Defaults to 6.0.
        skip_tautomer: If True, skips tautomer enumeration. Defaults to True.
        skip_acidbase: If True, skips acid-base enumeration. Defaults to False.
        tool_context: The tool context provided by the ADK runtime.

    Returns:
        A message indicating success and the location of the file/artifact.

    Raises:
        RuntimeError: If ligand preparation fails.
    """
    # Step 1: Generate 3D conformer and protonate using molscrub
    try:
        input_mol = Chem.MolFromSmiles(smiles)
        if input_mol is None:
            raise ValueError(f"Invalid SMILES string: {smiles}")

        scrub = Scrub(
            ph_low=ph,
            ph_high=ph,
            skip_tautomers=skip_tautomer,
            skip_acidbase=skip_acidbase,
        )
        isomer_list = scrub(input_mol)

        if not isomer_list:
            raise RuntimeError("molscrub failed to generate any isomers.")

        # For simplicity, we take the first isomer/conformer generated
        ligand_mol = isomer_list[0]
    except Exception as e:
        raise RuntimeError(f"Ligand preparation (molscrub) failed: {e}") from e

    # Step 2: Convert to PDBQT using meeko
    try:
        preparator = MoleculePreparation()
        molsetups = preparator.prepare(ligand_mol)

        if not molsetups:
            raise RuntimeError("meeko failed to prepare molecule setup.")

        # Take the first setup
        molsetup = molsetups[0]
        pdbqt_string, success, error_msg = PDBQTWriterLegacy.write_string(molsetup)

        if not success:
            raise RuntimeError(f"meeko PDBQT writing failed: {error_msg}")

        # Always save to local file for persistence
        with open(output_filename, "w") as f:
            f.write(pdbqt_string)

        # If running in ADK context, save as an artifact for download
        if tool_context and hasattr(tool_context, "save_artifact"):
            part = types.Part(
                inline_data=types.Blob(
                    data=pdbqt_string.encode("utf-8"), mime_type="text/plain"
                )
            )
            tool_context.save_artifact(output_filename, part)
            return (
                f"Ligand successfully prepared and saved as artifact: '{output_filename}'. "
                "You can now download it directly from the dialog."
            )

    except Exception as e:
        raise RuntimeError(f"Ligand preparation (meeko) failed: {e}") from e

    if not os.path.exists(output_filename):
        raise RuntimeError(f"Failed to generate output file: {output_filename}")

    return f"Ligand successfully prepared and saved to: {os.path.abspath(output_filename)}"


