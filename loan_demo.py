import sys
from pathlib import Path


def configure_utf8_output():
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


configure_utf8_output()

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gambler

commands = [
    "new_game 12345",
    "status",
    "schedule",
    "news",
    "bet wnl 1 home 5000",
    "bet score 1 2-1 1000",
    "next",
    "status",
    "history",
]

for command in commands:
    print(f">>> {command}")
    print(gambler.cmd(command))
    print()
