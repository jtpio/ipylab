from __future__ import annotations

import json
import pathlib

module_name = "ipylab"

# Read in the javascript version so the exact value can be specified
path = pathlib.Path(__file__).parent.joinpath("labextension", "package.json")
with path.open("rb") as f:
    data = json.load(f)
module_version = data["version"]
