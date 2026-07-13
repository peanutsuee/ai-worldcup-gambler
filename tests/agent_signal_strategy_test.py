import math
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


MAX_SEEDS = 25000
MIN_TOTAL_BETS = 20000
OBSERVE_ROUNDS = 3
MIN_SOURCE_TRIALS = 2
RELIABLE_SOURCE_THRESHOLD = 0.8
SOURCE_SEPARATOR = chr(0xFF1A)

TEAM_BY_NAME = {team["name"]: team["id"] for team in gambler.TEAMS}
POSITIVE_MARKERS = ("伤愈复出", "保持不败", "必须拿下", "胜率高达")
NEGATIVE_MARKERS = ("训练受伤", "受时差影响", "不和传闻", "下调")


def visible_signal_from_news(text):
    if SOURCE_SEPARATOR not in text:
        return None
    source, body = text.split(SOURCE_SEPARATOR, 1)
    if any(marker in body for marker in NEGATIVE_MARKERS):
        direction = -1
    elif any(marker in body for marker in POSITIVE_MARKERS):
        direction = 1
    else:
        return None

    team_id = next((team_id for name, team_id in TEAM_BY_NAME.items() if name in body), None)
    if not team_id:
        return None
    return source, team_id, direction


def pick_from_visible_signal(match, team_id, direction):
    if team_id not in (match["home"], match["away"]):
        return None
    team_side = "home" if match["home"] == team_id else "away"
    if direction > 0:
        return team_side
    return "away" if team_side == "home" else "home"


def visible_round_recommendations(state):
    recommendations = []
    for item in state.get("round_news", []):
        parsed = visible_signal_from_news(item)
        if not parsed:
            continue
        source, team_id, direction = parsed
        for match in state.get("current_matches", []):
            pick = pick_from_visible_signal(match, team_id, direction)
            if pick:
                recommendations.append((source, match["global_id"], pick, match["odds"]["wnl"][pick]))
                break
    return recommendations


def strategy_result_for_seed(seed):
    state = gambler._new_state(seed)
    source_stats = {source: {"hits": 0, "trials": 0} for source in gambler.NEWS_SOURCES}
    total_staked = 0
    total_returned = 0.0

    while not state.get("ended"):
        recommendations = visible_round_recommendations(state)
        reliable_sources = {
            source
            for source, stats in source_stats.items()
            if stats["trials"] >= MIN_SOURCE_TRIALS
            and stats["hits"] / stats["trials"] >= RELIABLE_SOURCE_THRESHOLD
        }
        placed = [
            recommendation
            for recommendation in recommendations
            if state["round_index"] >= OBSERVE_ROUNDS and recommendation[0] in reliable_sources
        ]

        before_results = len(state.get("all_matches", []))
        gambler._cmd_next(state)
        results = {match["global_id"]: match for match in state.get("all_matches", [])[before_results:]}

        for source, match_id, pick, _odds in recommendations:
            match = results.get(match_id)
            if not match:
                continue
            source_stats[source]["trials"] += 1
            if match["result"]["wnl"] == pick:
                source_stats[source]["hits"] += 1

        for _source, match_id, pick, odds in placed:
            match = results.get(match_id)
            if not match:
                continue
            total_staked += 1
            if match["result"]["wnl"] == pick:
                total_returned += odds

    return {"seed": seed, "staked": total_staked, "returned": total_returned}


def weighted_cluster_mean_and_standard_error(clusters):
    total_staked = sum(cluster["staked"] for cluster in clusters)
    total_returned = sum(cluster["returned"] for cluster in clusters)
    cluster_count = len(clusters)
    mean = total_returned / total_staked
    residual_sum = sum(
        (cluster["returned"] - mean * cluster["staked"]) ** 2 for cluster in clusters
    )
    standard_error = math.sqrt(
        (cluster_count / (cluster_count - 1)) * residual_sum / (total_staked ** 2)
    )
    return mean, standard_error


def main():
    clusters = []
    total_staked = 0
    seeds_used = 0
    for seed in range(1, MAX_SEEDS + 1):
        result = strategy_result_for_seed(seed)
        if result["staked"] > 0:
            clusters.append(result)
            total_staked += result["staked"]
        seeds_used = seed
        if total_staked >= MIN_TOTAL_BETS:
            break

    assert total_staked >= MIN_TOTAL_BETS, f"only collected {total_staked} bets"
    assert len(clusters) > 1, "cluster standard error needs at least two betting seeds"
    return_multiple, standard_error = weighted_cluster_mean_and_standard_error(clusters)
    lower_bound = return_multiple - 2 * standard_error
    assert lower_bound > 1.0, (return_multiple, standard_error, lower_bound, len(clusters), total_staked)

    print(f"Seeds used: {seeds_used}")
    print(f"Betting seed clusters: {len(clusters)}")
    print(f"Total strategy bets: {total_staked}")
    print(f"Honest agent strategy weighted return multiple: {return_multiple:.4f}")
    print(f"Cluster standard error: {standard_error:.4f}")
    print(f"Mean minus 2 standard errors: {lower_bound:.4f}")
    print("Agent signal strategy test passed.")


if __name__ == "__main__":
    main()
