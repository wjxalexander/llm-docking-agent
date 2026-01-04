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

    @patch("app.tools.ligand_preparation.Scrub")
    @patch("app.tools.ligand_preparation.MoleculePreparation")
    @patch("app.tools.ligand_preparation.PDBQTWriterLegacy")
    @patch("app.tools.ligand_preparation.Chem.MolFromSmiles")
    def test_prepare_ligand_success(
        self, mock_mol_from_smiles, mock_writer, mock_prep, mock_scrub
    ):
        # Setup mocks
        mock_mol_from_smiles.return_value = MagicMock()
        
        mock_scrub_instance = mock_scrub.return_value
        mock_scrub_instance.return_value = [MagicMock()]
        
        mock_prep_instance = mock_prep.return_value
        mock_prep_instance.prepare.return_value = [MagicMock()]
        
        mock_writer.write_string.return_value = ("mock pdbqt content", True, "")

        result_path = prepare_ligand(self.smiles, self.output_filename)

        self.assertIn("successfully prepared", result_path)
        self.assertIn(os.path.abspath(self.output_filename), result_path)
        self.assertTrue(os.path.exists(self.output_filename))

    @patch("app.tools.ligand_preparation.Scrub")
    @patch("app.tools.ligand_preparation.MoleculePreparation")
    @patch("app.tools.ligand_preparation.PDBQTWriterLegacy")
    @patch("app.tools.ligand_preparation.Chem.MolFromSmiles")
    def test_prepare_ligand_success_with_artifact(
        self, mock_mol_from_smiles, mock_writer, mock_prep, mock_scrub
    ):
        # Setup mocks
        mock_mol_from_smiles.return_value = MagicMock()
        
        mock_scrub_instance = mock_scrub.return_value
        mock_scrub_instance.return_value = [MagicMock()]
        
        mock_prep_instance = mock_prep.return_value
        mock_prep_instance.prepare.return_value = [MagicMock()]
        
        mock_writer.write_string.return_value = ("mock pdbqt content", True, "")

        mock_tool_context = MagicMock()

        result_path = prepare_ligand(self.smiles, self.output_filename, tool_context=mock_tool_context)

        self.assertIn("saved as artifact", result_path)
        self.assertTrue(os.path.exists(self.output_filename))
        mock_tool_context.save_artifact.assert_called_once()

    @patch("app.tools.ligand_preparation.Scrub")
    @patch("app.tools.ligand_preparation.Chem.MolFromSmiles")
    def test_prepare_ligand_scrub_failure(self, mock_mol_from_smiles, mock_scrub):
        # Setup mocks
        mock_mol_from_smiles.return_value = MagicMock()
        mock_scrub_instance = mock_scrub.return_value
        mock_scrub_instance.side_effect = Exception("scrub error")

        with self.assertRaises(RuntimeError) as cm:
            prepare_ligand(self.smiles, self.output_filename)

        self.assertIn("Ligand preparation (molscrub) failed", str(cm.exception))

    @patch("app.tools.ligand_preparation.Scrub")
    @patch("app.tools.ligand_preparation.MoleculePreparation")
    @patch("app.tools.ligand_preparation.PDBQTWriterLegacy")
    @patch("app.tools.ligand_preparation.Chem.MolFromSmiles")
    def test_prepare_ligand_meeko_failure(
        self, mock_mol_from_smiles, mock_writer, mock_prep, mock_scrub
    ):
        # Setup mocks
        mock_mol_from_smiles.return_value = MagicMock()
        
        mock_scrub_instance = mock_scrub.return_value
        mock_scrub_instance.return_value = [MagicMock()]
        
        mock_prep_instance = mock_prep.return_value
        mock_prep_instance.prepare.return_value = [MagicMock()]
        
        mock_writer.write_string.return_value = ("", False, "meeko error")

        with self.assertRaises(RuntimeError) as cm:
            prepare_ligand(self.smiles, self.output_filename)

        self.assertIn("meeko PDBQT writing failed", str(cm.exception))


if __name__ == "__main__":
    unittest.main()

