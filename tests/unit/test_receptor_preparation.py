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

"""Unit tests for the receptor_preparation tools."""

import sys
from unittest.mock import MagicMock

# Mock external dependencies to allow importing app modules without installation
sys.modules["google"] = MagicMock()
sys.modules["google.adk"] = MagicMock()
sys.modules["google.adk.agents"] = MagicMock()
sys.modules["google.adk.apps.app"] = MagicMock()
sys.modules["google.adk.models"] = MagicMock()
sys.modules["google.genai"] = MagicMock()
sys.modules["google.genai.types"] = MagicMock()
sys.modules["prody"] = MagicMock()
sys.modules["meeko"] = MagicMock()
sys.modules["rdkit"] = MagicMock()
sys.modules["rdkit.Chem"] = MagicMock()
sys.modules["molscrub"] = MagicMock()

import os
import unittest
from unittest.mock import patch

# Import requests (it should be available if we want to catch its exception, 
# or we mock it if it is not)
try:
    import requests
except ImportError:
    # If requests is missing, we must mock it in sys.modules too?
    # But we assumed it is installed.
    # If not, we define a dummy exception for the test.
    sys.modules["requests"] = MagicMock()
    import requests
    requests.RequestException = Exception

# Now we can import the module under test
from app.tools.receptor_preparation import download_pdb, prepare_receptor


class TestReceptorPreparation(unittest.TestCase):
    def setUp(self):
        self.pdb_id = "1iep"
        self.output_name = "test_receptor"
        
        # Configure Meeko mock since it's imported inside the function
        # We need to access the mock we injected
        self.mock_meeko = sys.modules["meeko"]
        self.mock_prep_cls = self.mock_meeko.MoleculePreparation
        self.mock_prep_instance = self.mock_prep_cls.return_value
        self.mock_prep_instance.write_pdbqt_string.return_value = "ATOM PDBQT"

    def tearDown(self):
        files_to_remove = [
            f"{self.output_name}_clean.pdb",
            f"{self.output_name}.pdbqt",
            f"{self.output_name}_config.txt",
            f"{self.output_name}.box.pdb",
            "dummy.pdb",
            os.path.join("pdb", f"{self.pdb_id}.pdb"),
        ]
        for f in files_to_remove:
            if os.path.exists(f):
                os.remove(f)
        # Remove pdb directory if empty
        if os.path.exists("pdb") and not os.listdir("pdb"):
            os.rmdir("pdb")

    @patch("app.tools.receptor_preparation.requests.get")
    def test_download_pdb_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "PDB CONTENT"
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = download_pdb(self.pdb_id)
        
        # Result is now a dict with file_path (no pdb_content to avoid LLM overload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["pdb_id"], self.pdb_id)
        self.assertIn("file_path", result)
        self.assertEqual(result["file_size"], len("PDB CONTENT"))
        self.assertIn("Successfully downloaded", result["message"])
        
        # Check file was saved to ./pdb directory
        expected_path = os.path.join("pdb", f"{self.pdb_id}.pdb")
        self.assertTrue(os.path.exists(expected_path))
        with open(expected_path, 'r') as f:
            self.assertEqual(f.read(), "PDB CONTENT")

    def test_download_pdb_cache_hit(self):
        # Create pdb directory and pre-existing file
        os.makedirs("pdb", exist_ok=True)
        cached_file = os.path.join("pdb", f"{self.pdb_id}.pdb")
        cached_content = "CACHED PDB CONTENT"
        with open(cached_file, 'w') as f:
            f.write(cached_content)
        
        # Should use cached file without making network request
        result = download_pdb(self.pdb_id)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["pdb_id"], self.pdb_id)
        self.assertIn("file_path", result)
        self.assertEqual(result["file_size"], len(cached_content))
        self.assertIn("already exists", result["message"])
        self.assertIn("skipped download", result["message"])

    @patch("app.tools.receptor_preparation.requests.get")
    def test_download_pdb_failure(self, mock_get):
        # Mock requests.get raising an exception
        # We use a generic Exception or requests.RequestException if available
        mock_get.side_effect = requests.RequestException("Network Error")
        
        with self.assertRaises(RuntimeError):
            download_pdb(self.pdb_id)

    @patch("app.tools.receptor_preparation.prody")
    def test_prepare_receptor_with_file(self, mock_prody):
        # Mock ProDy atoms
        mock_atoms = MagicMock()
        mock_selection = MagicMock()
        mock_atoms.select.return_value = mock_selection
        mock_prody.parsePDB.return_value = mock_atoms
        mock_prody.calcCenter.return_value = MagicMock(tolist=lambda: [1.0, 2.0, 3.0])
        
        # Mock writePDB to actually create file
        def side_effect_write(filename, atoms):
            with open(filename, 'w') as f:
                f.write("ATOM")
        mock_prody.writePDB.side_effect = side_effect_write

        # Configure Meeko mock from setUp
        self.mock_prep_instance.write_pdbqt_string.return_value = "ATOM PDBQT"
            
        # Create a dummy input file for read
        with open("dummy.pdb", "w") as f:
            f.write("ATOM")
            
        # New signature: output_name first, then input_pdb as kwarg
        result = prepare_receptor(self.output_name, input_pdb="dummy.pdb")
        self.assertIn("Receptor prepared", result)
        self.assertIn("Box Center: [1.0, 2.0, 3.0]", result)
        self.assertTrue(os.path.exists(f"{self.output_name}_config.txt"))


    @patch("app.tools.receptor_preparation.prody")
    def test_prepare_receptor_with_artifact(self, mock_prody):
        mock_atoms = MagicMock()
        mock_prody.parsePDB.return_value = mock_atoms
        mock_atoms.select.return_value = MagicMock()
        mock_prody.calcCenter.return_value = MagicMock(tolist=lambda: [0.0, 0.0, 0.0])

        # Mock writePDB
        def side_effect_write(filename, atoms):
            with open(filename, 'w') as f:
                f.write("ATOM")
        mock_prody.writePDB.side_effect = side_effect_write

        mock_tool_context = MagicMock()
        
        # Configure Meeko mock to force fallback path (return None for molecule)
        self.mock_chem = sys.modules["rdkit.Chem"]
        self.mock_chem.MolFromPDBFile.return_value = None

        # Explicitly ensure clean_pdb exists before call
        with open(f"{self.output_name}_clean.pdb", 'w') as f:
            f.write("ATOM")
        
        # Create dummy input file
        with open("dummy.pdb", "w") as f:
            f.write("ATOM")
            
        # Test with file path and tool_context
        prepare_receptor(self.output_name, input_pdb="dummy.pdb", tool_context=mock_tool_context)
        # Check artifacts saved
        self.assertTrue(mock_tool_context.save_artifact.called)
        # Should be 3: PDBQT, Config, Box PDB
        self.assertEqual(mock_tool_context.save_artifact.call_count, 3)

if __name__ == "__main__":
    unittest.main()
