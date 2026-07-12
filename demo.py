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


def assert_good(command, output):
    assert isinstance(output, str), f"{command!r} did not return a string"
    assert output.strip(), f"{command!r} returned empty output"
    assert "命令执行失败" not in output, f"{command!r} failed:\n{output}"


def main():
    commands = [
        "new_game 123",
        "help",
        "status",
        "schedule",
        "standings",
        "news",
        "bet wnl 1 home 1000",
        "bet score 1 2-1 500",
        "bet goals 1 over3 500",
        "next",
        "history",
        "summary",
        "titles",
    ]

    for command in commands:
        assert_good(command, gambler.cmd(command))

    for command in ["bet pk 1 yes 100", "bet score 1 abc 100", "unknown_command"]:
        assert_good(command, gambler.cmd(command))

    print("Smoke test passed.")


if __name__ == "__main__":
    main()
