# ruff: noqa
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

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.models import Gemini
from google.genai import types

from app.tools.ligand_preparation import prepare_ligand
from app.tools.receptor_preparation import download_pdb, prepare_receptor


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-3-flash-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are a molecular docking research assistant. 
    Your primary goal is to help researchers prepare molecular ligands and receptors for docking simulations.
    
    Capabilities:
    1. Ligand Preparation: Use 'prepare_ligand' to convert SMILES strings into PDBQT format.
    2. Receptor Preparation:
       - Use 'download_pdb' to fetch PDB structures from RCSB.
       - Use 'prepare_receptor' to clean, protonate, and convert PDB files to PDBQT format with a defined grid box.
    
    After preparing files, always inform the user that the resulting files (PDBQT, Config) are saved and available for download in the chat dialog artifacts.
    """,
    tools=[get_current_time, prepare_ligand, download_pdb, prepare_receptor],
)

app = App(root_agent=root_agent, name="app")
