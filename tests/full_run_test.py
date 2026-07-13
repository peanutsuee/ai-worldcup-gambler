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


def assert_good(command, output):
    assert isinstance(output, str), f"{command!r} did not return a string"
    assert output.strip(), f"{command!r} returned empty output"
    assert "命令执行失败" not in output, f"{command!r} failed:\n{output}"


def match_count(schedule_text):
    return sum(1 for line in schedule_text.splitlines() if re.match(r"^\[\d+\]", line))


def cash_from_status(status_text):
    match = re.search(r"现金：([0-9,]+)", status_text)
    if not match:
        return 0
    return int(match.group(1).replace(",", ""))


def main():
    assert_good("new_game 777", gambler.cmd("new_game 777"))

    for _ in range(17):
        schedule = gambler.cmd("schedule")
        assert_good("schedule", schedule)

        for index in range(1, match_count(schedule) + 1):
            status = gambler.cmd("status")
            assert_good("status", status)
            cash = cash_from_status(status)
            if cash <= 0:
                assert_good("loan", gambler.cmd("loan"))
                cash = cash_from_status(gambler.cmd("status"))
            if cash >= 100:
                assert_good(f"bet wnl {index} home 100", gambler.cmd(f"bet wnl {index} home 100"))

        result = gambler.cmd("next")
        assert_good("next", result)
        if "游戏已结束" in result:
            break

    assert_good("status", gambler.cmd("status"))
    assert_good("standings", gambler.cmd("standings"))
    assert_good("summary", gambler.cmd("summary"))
    assert_good("quit", gambler.cmd("quit"))
    print("Full run test passed.")


if __name__ == "__main__":
    main()
