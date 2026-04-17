"""
Football Match Predictor — Monte Carlo Simulation
Uses Poisson distribution + Dixon-Coles attack/defense ratio model.
"""

import argparse
import numpy as np
from collections import Counter


# ── League baseline (PL 2025/26 avg goals per team per game) ──────────────────
LEAGUE_AVG_GPG = 1.38
HOME_ADVANTAGE  = 1.12   # 12% boost for home team
SIMULATIONS     = 10_000

# ── Team database ─────────────────────────────────────────────────────────────
# Add or edit teams here. All values are per-game averages for current season.
# injury_attack_delta  = goals lost per game due to injuries (negative impact)
# injury_defense_delta = extra goals conceded per game due to injuries

TEAMS = {
    "man city": {
        "name": "Manchester City",
        "season_gpg":    2.03,   # goals scored per game (PL season)
        "season_gcg":    0.87,   # goals conceded per game (PL season)
        "recent_gpg":    2.40,   # goals scored per game (last 5 all comps)
        "recent_gcg":    0.60,   # goals conceded per game (last 5)
        "form":          13,     # points from last 5 matches (W=3 D=1 L=0, max 15)
        "injury_attack_delta":   0.00,
        "injury_defense_delta":  0.28,  # Dias + Stones + Gvardiol out
        "ppg":           2.23,
    },
    "arsenal": {
        "name": "Arsenal",
        "season_gpg":    1.91,
        "season_gcg":    0.69,
        "recent_gpg":    0.80,   # reduced — Saka/Odegaard missing
        "recent_gcg":    1.00,
        "form":          7,
        "injury_attack_delta":   0.19,  # Saka out + Odegaard doubt (50%)
        "injury_defense_delta":  0.13,  # Timber + Calafiori out
        "ppg":           2.19,
    },
    "liverpool": {
        "name": "Liverpool",
        "season_gpg":    2.10,
        "season_gcg":    0.80,
        "recent_gpg":    2.20,
        "recent_gcg":    0.80,
        "form":          12,
        "injury_attack_delta":   0.00,
        "injury_defense_delta":  0.00,
        "ppg":           2.30,
    },
    "chelsea": {
        "name": "Chelsea",
        "season_gpg":    1.60,
        "season_gcg":    1.10,
        "recent_gpg":    1.40,
        "recent_gcg":    1.20,
        "form":          8,
        "injury_attack_delta":   0.00,
        "injury_defense_delta":  0.00,
        "ppg":           1.80,
    },
}


# ── Feature engineering ───────────────────────────────────────────────────────

def effective_attack(team: dict) -> float:
    """Weighted attack (30% season, 70% recent) minus injury penalty."""
    weighted = 0.3 * team["season_gpg"] + 0.7 * team["recent_gpg"]
    return max(weighted - team["injury_attack_delta"], 0.3)


def effective_defense(team: dict) -> float:
    """Season goals conceded plus injury-related defensive vulnerability."""
    return team["season_gcg"] + team["injury_defense_delta"]


def form_multiplier(form_pts: int, max_pts: int = 15) -> float:
    """
    Convert form points to a small lambda multiplier.
    Average form = 9/15. Above average = boost, below = drag.
    Range: 0.94 – 1.06
    """
    avg = max_pts * 0.60          # 9 pts = average
    delta = (form_pts - avg) / max_pts
    return 1.0 + (delta * 0.20)  # max ±6%


# ── Lambda (expected goals) calculation ───────────────────────────────────────

def compute_lambda(attacker: dict, defender: dict, home: bool) -> float:
    """
    Dixon-Coles ratio model:
      λ = baseline × attack_ratio × defense_ratio × [home_mult]
    """
    att = effective_attack(attacker)
    def_ = effective_defense(defender)

    attack_ratio  = att  / LEAGUE_AVG_GPG
    defense_ratio = def_ / LEAGUE_AVG_GPG   # higher = more porous

    lam = LEAGUE_AVG_GPG * attack_ratio * defense_ratio

    if home:
        lam *= HOME_ADVANTAGE

    lam *= form_multiplier(attacker["form"])

    return round(max(lam, 0.10), 4)


# ── Monte Carlo simulation ────────────────────────────────────────────────────

def run_simulation(lambda_home: float, lambda_away: float, n: int = SIMULATIONS):
    rng = np.random.default_rng(seed=42)
    home_goals = rng.poisson(lambda_home, n)
    away_goals = rng.poisson(lambda_away, n)

    home_wins = int((home_goals > away_goals).sum())
    draws      = int((home_goals == away_goals).sum())
    away_wins  = int((home_goals < away_goals).sum())

    scorelines = Counter(zip(home_goals.tolist(), away_goals.tolist()))
    top_scores = scorelines.most_common(6)

    return {
        "home_wins":  home_wins,
        "draws":      draws,
        "away_wins":  away_wins,
        "top_scores": top_scores,
        "n":          n,
    }


# ── Output ────────────────────────────────────────────────────────────────────

def print_results(home: dict, away: dict, lam_h: float, lam_a: float, results: dict):
    n = results["n"]
    hw = results["home_wins"] / n * 100
    d  = results["draws"]     / n * 100
    aw = results["away_wins"] / n * 100

    print("\n" + "═" * 52)
    print(f"  {home['name']:^22} vs  {away['name']:^22}")
    print("═" * 52)

    print(f"\n  Expected Goals")
    print(f"  {home['name']:<22}  λ = {lam_h:.2f}")
    print(f"  {away['name']:<22}  λ = {lam_a:.2f}")
    print(f"  Total xG               {lam_h + lam_a:.2f}")

    print(f"\n  Simulation Results  ({n:,} runs)")
    print(f"  {'Home Win':<18}  {hw:5.1f}%  {'█' * int(hw // 2)}")
    print(f"  {'Draw':<18}  {d:5.1f}%  {'█' * int(d  // 2)}")
    print(f"  {'Away Win':<18}  {aw:5.1f}%  {'█' * int(aw // 2)}")

    print(f"\n  Most Likely Scorelines")
    print(f"  {'Scoreline':<12}  {'Outcome':<14}  {'Prob':>6}")
    print(f"  {'-'*36}")
    for (h, a), count in results["top_scores"]:
        prob = count / n * 100
        if h > a:
            outcome = f"{home['name'].split()[0]} Win"
        elif h == a:
            outcome = "Draw"
        else:
            outcome = f"{away['name'].split()[0]} Win"
        print(f"  {h}–{a:<10}  {outcome:<14}  {prob:5.1f}%")

    if hw >= d and hw >= aw:
        winner, pct = home["name"], hw
        label = "Home Win"
    elif aw >= d and aw >= hw:
        winner, pct = away["name"], aw
        label = "Away Win"
    else:
        winner, pct = "Draw", d
        label = "Draw"

    confidence = "High" if pct >= 60 else "Medium" if pct >= 45 else "Low"

    print(f"\n  Final Prediction")
    print(f"  ┌{'─'*38}┐")
    print(f"  │  {label:<36}│")
    print(f"  │  {winner:<36}│")
    print(f"  │  Confidence: {confidence} ({pct:.1f}%){' ' * (22 - len(confidence) - len(f'{pct:.1f}'))}│")
    print(f"  └{'─'*38}┘")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def list_teams():
    print("\nAvailable teams:")
    for key, val in TEAMS.items():
        print(f"  {key:<15}  →  {val['name']}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Football Monte Carlo match predictor"
    )
    parser.add_argument("--home",  type=str, help="Home team key (e.g. 'man city')")
    parser.add_argument("--away",  type=str, help="Away team key (e.g. 'arsenal')")
    parser.add_argument("--sims",  type=int, default=SIMULATIONS, help="Number of simulations")
    parser.add_argument("--list",  action="store_true", help="List available teams")
    args = parser.parse_args()

    if args.list:
        list_teams()
        return

    home_key = (args.home or "man city").lower()
    away_key = (args.away or "arsenal").lower()

    if home_key not in TEAMS:
        print(f"  Team '{home_key}' not found.")
        list_teams()
        return
    if away_key not in TEAMS:
        print(f"  Team '{away_key}' not found.")
        list_teams()
        return

    home_team = TEAMS[home_key]
    away_team = TEAMS[away_key]

    lam_h = compute_lambda(home_team, away_team, home=True)
    lam_a = compute_lambda(away_team, home_team, home=False)

    results = run_simulation(lam_h, lam_a, n=args.sims)
    print_results(home_team, away_team, lam_h, lam_a, results)


if __name__ == "__main__":
    main()
