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


def cash_from_status(status_text):
    match = re.search(r"现金：([0-9,]+)", status_text)
    if not match:
        return 0
    return int(match.group(1).replace(",", ""))


def main():
    assert_good("new_game 999", gambler.cmd("new_game 999"))
    status = gambler.cmd("status")
    assert_good("status", status)
    cash = cash_from_status(status)
    assert cash > 0, "new game should start with cash"

    edge_bet = cash - 50
    assert edge_bet >= 100, "edge bet should leave cash below minimum bet"
    assert_good(f"bet wnl 1 away {edge_bet}", gambler.cmd(f"bet wnl 1 away {edge_bet}"))
    loan_output = gambler.cmd("loan")
    assert_good("loan", loan_output)
    assert "高利贷到账" in loan_output, loan_output

    next_output = gambler.cmd("next")
    assert_good("next", next_output)
    assert "高利贷利息" in next_output, next_output

    assert_good("summary", gambler.cmd("summary"))
    assert_good("quit", gambler.cmd("quit"))
    print("Loan test passed.")


if __name__ == "__main__":
    main()
