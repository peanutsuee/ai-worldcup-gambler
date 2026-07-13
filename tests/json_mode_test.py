import json
import os
import sys
import tempfile
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


def load_save(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    default_save = Path(gambler.__file__).with_name("gambler_save.json")
    default_stamp = default_save.stat().st_mtime_ns if default_save.exists() else None

    with tempfile.TemporaryDirectory() as tmp:
        save_path = Path(tmp) / "json_mode_save.json"
        os.environ["GAMBLER_SAVE"] = str(save_path)

        assert_good("new_game 4242", gambler.cmd("new_game 4242"))
        assert save_path.exists(), "GAMBLER_SAVE path was not written"
        if default_stamp is None:
            assert not default_save.exists(), "default save should not be created when GAMBLER_SAVE is set"
        else:
            assert default_save.stat().st_mtime_ns == default_stamp, "default save should not be touched"

        for command in ["status", "schedule", "standings", "news", "history", "summary", "titles"]:
            output = gambler.cmd(f"{command} --json")
            assert_good(f"{command} --json", output)
            data = json.loads(output)
            assert isinstance(data, dict), f"{command} --json did not return a JSON object"

        schedule = json.loads(gambler.cmd("schedule --json"))
        assert schedule["matches"], "schedule JSON should include matches"
        first_match = schedule["matches"][0]
        assert first_match["index"] == 1
        assert first_match["home"]["id"] and first_match["away"]["id"]
        for market in ["wnl", "goals", "score_examples"]:
            assert first_match["odds"][market], f"missing {market} odds"
            assert all(isinstance(value, float) for value in first_match["odds"][market].values())

        bad_extra = gambler.cmd("bet score 1 2-1 1000 2000")
        assert_good("bet score extra arg", bad_extra)
        assert "用法" in bad_extra, bad_extra

        assert_good("bet wnl 1 home 1000", gambler.cmd("bet wnl 1 home 1000"))
        state = load_save(save_path)
        bet = state["bets"][-1]
        expected_tax = round(max(0.0, bet["amount"] * (1 - bet["odds"] / bet["fair_odds"])), 2)
        assert abs(bet["house_edge"] - expected_tax) < 0.001, (bet["house_edge"], expected_tax)

        assert_good("bet goals 1 over9 100", gambler.cmd("bet goals 1 over9 100"))
        state = load_save(save_path)
        extreme = state["bets"][-1]
        assert extreme["odds"] <= 3.0, extreme
        assert extreme["fair_odds"] >= extreme["odds"], extreme

        history = json.loads(gambler.cmd("history --json"))
        assert {"fair_odds", "house_edge"}.issubset(history["bets"][-1])

        summary = json.loads(gambler.cmd("summary --json"))
        assert summary["house_edge_total"] >= bet["house_edge"]

    print("JSON mode test passed.")


if __name__ == "__main__":
    main()
