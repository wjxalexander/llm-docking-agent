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

"""Tools for preparing receptor molecules for docking."""

import os
import requests
import logging
import shutil
import subprocess
import tempfile
from typing import Any, Optional, List

import prody
from google.genai import types

# Configure ProDy to be less verbose
prody.confProDy(verbosity='none')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _run_reduce2(input_pdb: str, output_pdb: str, original_pdb: Optional[str] = None) -> bool:
    """Run reduce2 to add hydrogens to the receptor.
    
    Args:
        input_pdb: Path to the cleaned PDB file (without hydrogens).
        output_pdb: Path for the output protonated PDB file.
        original_pdb: Path to original PDB (to extract CRYST1 card if needed).
    
    Returns:
        True if reduce2 succeeded, False otherwise.
    """
    # Check if reduce2 is available (part of cctbx/mmtbx)
    reduce2_path = shutil.which("mmtbx.reduce2")
    if not reduce2_path:
        # Try alternative names
        reduce2_path = shutil.which("reduce2")
    if not reduce2_path:
        # Try running as python module
        try:
            result = subprocess.run(
                ["python", "-c", "from mmtbx.command_line import reduce2"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                reduce2_path = "python -m mmtbx.command_line.reduce2"
        except Exception:
            pass
    
    if not reduce2_path:
        logger.warning("[reduce2] reduce2 not found. Skipping hydrogen addition.")
        return False
    
    try:
        # Prepare input file with CRYST1 card if needed
        # reduce2 requires CRYST1 record
        temp_input = input_pdb
        cryst1_line = None
        
        # Try to get CRYST1 from original PDB
        if original_pdb and os.path.exists(original_pdb):
            with open(original_pdb, 'r') as f:
                for line in f:
                    if line.startswith("CRYST1"):
                        cryst1_line = line
                        break
        
        # Check if input already has CRYST1
        has_cryst1 = False
        with open(input_pdb, 'r') as f:
            for line in f:
                if line.startswith("CRYST1"):
                    has_cryst1 = True
                    break
        
        # If no CRYST1, add a dummy one or from original
        if not has_cryst1:
            temp_input = input_pdb + ".reduce_input.pdb"
            with open(temp_input, 'w') as out_f:
                if cryst1_line:
                    out_f.write(cryst1_line)
                else:
                    # Add dummy CRYST1 card
                    out_f.write("CRYST1    1.000    1.000    1.000  90.00  90.00  90.00 P 1           1\n")
                with open(input_pdb, 'r') as in_f:
                    out_f.write(in_f.read())
        
        # Run reduce2
        # reduce2 options: approach=add add_flip_movers=True
        # This is equivalent to -build or -flip in standalone reduce
        logger.info(f"[reduce2] Running reduce2 on {temp_input}")
        
        cmd = f"{reduce2_path} {temp_input} approach=add add_flip_movers=True"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode != 0:
            logger.warning(f"[reduce2] reduce2 failed: {result.stderr}")
            return False
        
        # reduce2 outputs to {basename}FH.pdb by default
        basename = os.path.splitext(os.path.basename(temp_input))[0]
        reduce_output = f"{basename}FH.pdb"
        
        # Check in current directory and input directory
        possible_outputs = [
            reduce_output,
            os.path.join(os.path.dirname(temp_input), reduce_output),
            os.path.join(os.path.dirname(input_pdb), reduce_output),
        ]
        
        for possible_output in possible_outputs:
            if os.path.exists(possible_output):
                shutil.move(possible_output, output_pdb)
                logger.info(f"[reduce2] Successfully added hydrogens: {output_pdb}")
                
                # Cleanup temp input if created
                if temp_input != input_pdb and os.path.exists(temp_input):
                    os.unlink(temp_input)
                return True
        
        logger.warning(f"[reduce2] Output file not found. Expected: {reduce_output}")
        return False
        
    except subprocess.TimeoutExpired:
        logger.warning("[reduce2] reduce2 timed out")
        return False
    except Exception as e:
        logger.warning(f"[reduce2] Error running reduce2: {e}")
        return False


def download_pdb(pdb_id: str, tool_context: Any = None) -> dict:
    """Downloads a PDB structure from the RCSB PDB server.

    Saves the file to ./pdb directory. Returns the file path (not the content)
    to avoid overwhelming the LLM with large PDB files.

    Args:
        pdb_id: The 4-character PDB identifier (e.g., '1iep').
        tool_context: The tool context provided by the ADK runtime.

    Returns:
        A dictionary containing:
            - pdb_id: The PDB identifier
            - file_path: Path to the saved PDB file
            - file_size: Size of the file in bytes
            - message: A success message

    Raises:
        ValueError: If the PDB ID is invalid.
        RuntimeError: If the download fails.
    """
    pdb_id = pdb_id.lower().strip()
    if len(pdb_id) != 4:
        raise ValueError(f"Invalid PDB ID format: {pdb_id}. Must be 4 characters.")

    # Create ./pdb directory if it doesn't exist
    pdb_dir = "./pdb"
    os.makedirs(pdb_dir, exist_ok=True)
    
    file_path = os.path.join(pdb_dir, f"{pdb_id}.pdb")
    abs_path = os.path.abspath(file_path)
    
    # Check if file already exists (cache hit)
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        logger.info(f"[download_pdb] Cache hit: {pdb_id} at {file_path} ({file_size} bytes)")

        return {
            "pdb_id": pdb_id,
            "file_path": abs_path,
            "file_size": file_size,
            "message": f"PDB {pdb_id} already exists at {file_path} (skipped download). Use file_path='{abs_path}' in prepare_receptor.",
        }

    # Download from RCSB
    url = f"https://files.rcsb.org/view/{pdb_id}.pdb"
    logger.debug(f"[download_pdb] Downloading {pdb_id} from {url}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        pdb_content = response.text
        
        # Save the PDB file
        with open(file_path, 'w') as f:
            f.write(pdb_content)
        
        file_size = len(pdb_content)
        logger.info(f"[download_pdb] Downloaded {pdb_id} to {file_path} ({file_size} bytes)")

        return {
            "pdb_id": pdb_id,
            "file_path": abs_path,
            "file_size": file_size,
            "message": f"Successfully downloaded PDB {pdb_id} to {file_path}. Use file_path='{abs_path}' in prepare_receptor.",
        }

    except requests.RequestException as e:
        raise RuntimeError(f"Failed to download PDB {pdb_id}: {e}")


def prepare_receptor(
    output_name: str,
    input_pdb: Optional[str] = None,
    pdb_content: Optional[str] = None,
    selection: str = "chain A and not water and not hetero",
    box_reference: Optional[str] = None,
    box_center: Optional[List[float]] = None,
    box_size: List[float] = [20.0, 20.0, 20.0],
    tool_context: Any = None,
) -> str:
    """Prepares a receptor PDBQT file for docking.

    Performs cleaning (using ProDy) and converts to PDBQT.
    Calculates and saves the grid box configuration.

    Args:
        output_name: Base name for the output files (e.g., '1iep_receptor').
        input_pdb: Path to the input PDB file. Use this OR pdb_content.
        pdb_content: Raw PDB content as a string (from download_pdb). Use this OR input_pdb.
        selection: ProDy selection string for the receptor atoms.
        box_reference: ProDy selection string to calculate box center (e.g., 'resname STI').
        box_center: Explicit [x, y, z] coordinates for box center. Overrides box_reference.
        box_size: Box dimensions in Angstroms [x, y, z].
        tool_context: The tool context provided by the ADK runtime.

    Returns:
        A message with paths to the generated PDBQT and box files.
    """
    temp_pdb_file = None

    try:
        # Validate input - need either file path or content
        if not input_pdb and not pdb_content:
            raise ValueError("Must provide either 'input_pdb' (file path) or 'pdb_content' (string).")

        # If content is provided, write to a temporary file for ProDy
        if pdb_content:
            temp_pdb_file = tempfile.NamedTemporaryFile(
                mode='w', suffix='.pdb', delete=False
            )
            temp_pdb_file.write(pdb_content)
            temp_pdb_file.close()
            pdb_to_parse = temp_pdb_file.name
        else:
            pdb_to_parse = input_pdb

        # 1. Parse and Clean Receptor
        atoms = prody.parsePDB(pdb_to_parse)
        if atoms is None:
            raise ValueError(f"Could not parse PDB file: {input_pdb}")
            
        receptor = atoms.select(selection)
        if receptor is None:
            raise ValueError(f"Selection '{selection}' matched no atoms.")
            
        # 2. Determine Box Center
        center = [0.0, 0.0, 0.0]
        if box_center:
            if len(box_center) != 3:
                raise ValueError("box_center must have 3 elements [x, y, z]")
            center = box_center
        elif box_reference:
            ref_atoms = atoms.select(box_reference)
            if ref_atoms is None:
                raise ValueError(f"Box reference selection '{box_reference}' matched no atoms.")
            center = prody.calcCenter(ref_atoms).tolist()
        else:
            # Default to center of receptor if nothing specified
            center = prody.calcCenter(receptor).tolist()

        # 3. Write Cleaned PDB (intermediate)
        clean_pdb = f"{output_name}_clean.pdb"
        prody.writePDB(clean_pdb, receptor)

        # 4. Add Hydrogens with reduce2 (if available)
        # reduce2 is part of cctbx/mmtbx and adds hydrogens with proper optimization
        protonated_pdb = f"{output_name}_protonated.pdb"
        reduce2_success = _run_reduce2(
            input_pdb=clean_pdb,
            output_pdb=protonated_pdb,
            original_pdb=pdb_to_parse  # For CRYST1 card
        )
        
        # Use protonated PDB if reduce2 succeeded, otherwise use clean PDB
        pdb_for_pdbqt = protonated_pdb if reduce2_success else clean_pdb
        
        # 5. Convert to PDBQT
        output_pdbqt = f"{output_name}.pdbqt"
        
        # Try to use mk_prepare_receptor if available
        mk_prepare_exec = shutil.which("mk_prepare_receptor")
        pdbqt_success = False
        
        if mk_prepare_exec:
            try:
                logger.info(f"[prepare_receptor] Running mk_prepare_receptor on {pdb_for_pdbqt}")
                cmd = [
                    mk_prepare_exec,
                    "-i", pdb_for_pdbqt,
                    "-o", output_name,
                    "-p",  # Preserve hydrogens
                    "-v",  # Verbose
                    "--box_center", str(center[0]), str(center[1]), str(center[2]),
                    "--box_size", str(box_size[0]), str(box_size[1]), str(box_size[2])
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0 and os.path.exists(output_pdbqt):
                    pdbqt_success = True
                    logger.info(f"[prepare_receptor] mk_prepare_receptor succeeded")
                else:
                    logger.warning(f"[prepare_receptor] mk_prepare_receptor failed: {result.stderr}")
            except Exception as e:
                logger.warning(f"[prepare_receptor] mk_prepare_receptor error: {e}")
        
        # Fallback: copy the PDB as PDBQT (basic fallback without proper partial charges)
        if not pdbqt_success:
            shutil.copy(pdb_for_pdbqt, output_pdbqt)
            if reduce2_success:
                logger.info(
                    "Created PDBQT from protonated structure. "
                    "Note: Partial charges not assigned (mk_prepare_receptor not available)."
                )
            else:
                logger.warning(
                    "Created basic PDBQT without hydrogens or partial charges. "
                    "For production use, install cctbx (for reduce2) and meeko (for mk_prepare_receptor)."
                )
        
        # Write Box Config
        config_file = f"{output_name}_config.txt"
        with open(config_file, 'w') as f:
            f.write(f"center_x = {center[0]:.3f}\n")
            f.write(f"center_y = {center[1]:.3f}\n")
            f.write(f"center_z = {center[2]:.3f}\n")
            f.write(f"size_x = {box_size[0]:.3f}\n")
            f.write(f"size_y = {box_size[1]:.3f}\n")
            f.write(f"size_z = {box_size[2]:.3f}\n")
        
        # Write Box PDB for visualization
        # We create a simple PDB with 8 atoms representing the box corners
        box_file = f"{output_name}.box.pdb"
        half_size = [s / 2.0 for s in box_size]
        corners = []
        for x in [-1, 1]:
            for y in [-1, 1]:
                for z in [-1, 1]:
                    corners.append([
                        center[0] + x * half_size[0],
                        center[1] + y * half_size[1],
                        center[2] + z * half_size[2]
                    ])
        
        with open(box_file, 'w') as f:
            for i, (x, y, z) in enumerate(corners):
                # Simple HETATM record for a dummy atom
                f.write(f"HETATM{i+1:5d}  C   BOX A   1    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           C\n")
            # Connect atoms to draw the box (optional but good for viz)
            # Just simple corners is often enough for py3dmol if strictly viewing points, 
            # but drawing lines requires CONECT records.
            # For simplicity, we just output corners.

        # Build output message
        msg_lines = [
            "Receptor prepared.",
            f"Clean PDB: {os.path.abspath(clean_pdb)}",
        ]
        if reduce2_success:
            msg_lines.append(f"Protonated PDB: {os.path.abspath(protonated_pdb)} (hydrogens added with reduce2)")
        else:
            msg_lines.append("Protonation: Skipped (reduce2 not available)")
        msg_lines.extend([
            f"PDBQT: {os.path.abspath(output_pdbqt)}",
            f"Box Config: {os.path.abspath(config_file)}",
            f"Box Visualization: {os.path.abspath(box_file)}",
            f"Box Center: {center}",
            f"Box Size: {box_size}",
        ])
        msg = "\n".join(msg_lines)
        
        # Save artifacts if context available
        if tool_context and hasattr(tool_context, "save_artifact"):
            # Save PDBQT
            with open(output_pdbqt, 'rb') as f:
                 tool_context.save_artifact(output_pdbqt, types.Part.from_bytes(data=f.read(), mime_type="text/plain"))
            # Save Config
            with open(config_file, 'rb') as f:
                 tool_context.save_artifact(config_file, types.Part.from_bytes(data=f.read(), mime_type="text/plain"))
            # Save Box PDB
            with open(box_file, 'rb') as f:
                 tool_context.save_artifact(box_file, types.Part.from_bytes(data=f.read(), mime_type="chemical/x-pdb"))

        return msg

    except Exception as e:
        raise RuntimeError(f"Receptor preparation failed: {e}")

    finally:
        # Clean up temporary file if created
        if temp_pdb_file and os.path.exists(temp_pdb_file.name):
            os.unlink(temp_pdb_file.name)

