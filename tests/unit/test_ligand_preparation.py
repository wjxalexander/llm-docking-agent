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

"""Unit tests for the prepare_ligand tool."""

import os
import unittest
from unittest.mock import patch, MagicMock
from app.tools.ligand_preparation import prepare_ligand


class TestLigandPreparation(unittest.TestCase):
    def setUp(self):
        self.smiles = "CC1=C(NC2=NC=CC(C3=CN=CC=C3)=N2)C=C(NC(C4=CC=C(CN5CCN(C)CC5)C=C4)=O)C=C1"
        self.output_filename = "test_ligand.pdbqt"

    def tearDown(self):
        if os.path.exists(self.output_filename):
            os.remove(self.output_filename)
        sdf_file = "test_ligand_scrubbed.sdf"
        if os.path.exists(sdf_file):
            os.remove(sdf_file)

    @patch("subprocess.run")
    def test_prepare_ligand_success(self, mock_run):
        # Mock successful execution of scrub.py and mk_prepare_ligand.py
        mock_run.return_value = MagicMock(returncode=0, stdout="success", stderr="")
        
        # We need to simulate the creation of the output file because the tool checks for it/returns its path
        # and the real commands are mocked.
        with open(self.output_filename, "w") as f:
            f.write("mock pdbqt content")

        result_path = prepare_ligand(self.smiles, self.output_filename)
        
        self.assertTrue(result_path.endswith(self.output_filename))
        self.assertTrue(os.path.isabs(result_path))
        self.assertEqual(mock_run.call_count, 2)

    @patch("subprocess.run")
    def test_prepare_ligand_scrub_failure(self, mock_run):
        import subprocess
        # Mock failure in scrub.py
        mock_run.side_effect = subprocess.CalledProcessError(1, "scrub.py", stderr="scrub error")
        
        with self.assertRaises(RuntimeError) as cm:
            prepare_ligand(self.smiles, self.output_filename)
        
        self.assertIn("molscrub (scrub.py) failed", str(cm.exception))

    @patch("subprocess.run")
    def test_prepare_ligand_meeko_failure(self, mock_run):
        import subprocess
        # First call (scrub.py) succeeds, second call (mk_prepare_ligand.py) fails
        mock_run.side_effect = [
            MagicMock(returncode=0),
            subprocess.CalledProcessError(1, "mk_prepare_ligand.py", stderr="meeko error")
        ]
        
        with self.assertRaises(RuntimeError) as cm:
            prepare_ligand(self.smiles, self.output_filename)
        
        self.assertIn("mk_prepare_ligand.py failed", str(cm.exception))


if __name__ == "__main__":
    unittest.main()

