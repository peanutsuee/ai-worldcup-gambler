import re
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


def cash_from_status(status_text):
    match = re.search(r"现金：([0-9,]+)", status_text)
    if not match:
        return 0
    return int(match.group(1).replace(",", ""))


def print_command(command):
    print(f">>> {command}")
    output = gambler.cmd(command)
    print(output)
    print()
    return output


def main():
    print("=" * 72)
    print("AI World Cup Gambler · loan demo")
    print("This deterministic demo intentionally goes broke to show loan mechanics.")
    print("=" * 72)

    print_command("new_game 999")
    print_command("schedule")

    status = gambler.cmd("status")
    cash = cash_from_status(status)
    print("All-in moment: cash is deliberately pushed to zero before settlement.")
    print_command(f"bet wnl 1 away {cash}")

    print_command("loan")
    print_command("status")

    print("One round passes, so the 10% compound interest should appear.")
    print_command("next")
    print_command("status")

    if cash_from_status(gambler.cmd("status")) >= 10_000:
        print_command("repay 10000")

    print_command("summary")
    print_command("quit")


if __name__ == "__main__":
    main()
