# Football Match Predictor — Monte Carlo Simulation

Predicts Premier League match outcomes using a **Poisson-based Monte Carlo simulation** (10,000 iterations) with Dixon-Coles attack/defense ratio modeling.

## Model Overview

```
λ_home = baseline × attack_ratio × defense_ratio × home_advantage × form_multiplier
λ_away = baseline × attack_ratio × defense_ratio × form_multiplier

home_goals ~ Poisson(λ_home)  ×  10,000 simulations
away_goals ~ Poisson(λ_away)
```

Features used:
- Season goals scored/conceded per game
- Recent form (last 5 matches, weighted 70%)
- Injury adjustments (converted to goal deltas)
- Home advantage multiplier (12%)
- Form index (W=3, D=1, L=0 over last 5)

## Setup

```bash
pip install -r requirements.txt
```

## Usage

**Default match (Man City vs Arsenal):**
```bash
python predict.py
```

**Custom match:**
```bash
python predict.py --home "man city" --away "liverpool"
```

**List available teams:**
```bash
python predict.py --list
```

**Change number of simulations:**
```bash
python predict.py --home "arsenal" --away "chelsea" --sims 50000
```

## Example Output

```
════════════════════════════════════════════════════
       Manchester City      vs       Arsenal
════════════════════════════════════════════════════

  Expected Goals
  Manchester City        λ = 1.60
  Arsenal                λ = 0.87
  Total xG               2.47

  Simulation Results  (10,000 runs)
  Home Win            54.6%  ███████████████████████████
  Draw                25.0%  ████████████
  Away Win            20.4%  ██████████

  Most Likely Scorelines
  Scoreline    Outcome         Prob
  ------------------------------------
  1–0          City Win        13.5%
  1–1          Draw            11.8%
  2–0          City Win        10.8%
  2–1          City Win         9.4%
  0–0          Draw             8.5%
  0–1          Arsenal Win      7.6%

  Final Prediction
  ┌──────────────────────────────────────┐
  │  Home Win                            │
  │  Manchester City                     │
  │  Confidence: Medium (54.6%)          │
  └──────────────────────────────────────┘
```

## Adding Teams

Open `predict.py` and add an entry to the `TEAMS` dictionary:

```python
"your team": {
    "name": "Your Team FC",
    "season_gpg":    1.80,   # goals scored per game (season)
    "season_gcg":    0.95,   # goals conceded per game (season)
    "recent_gpg":    1.60,   # goals scored per game (last 5)
    "recent_gcg":    1.00,   # goals conceded per game (last 5)
    "form":          9,      # points from last 5 (max 15)
    "injury_attack_delta":   0.00,  # goals lost per game due to injuries
    "injury_defense_delta":  0.00,  # extra goals conceded due to injuries
    "ppg":           1.90,
},
```

## How It Works

1. **Attack strength** = weighted average of season + recent goals per game, minus injury penalty
2. **Defense strength** = season goals conceded + injury vulnerability
3. **λ (expected goals)** = league baseline × attack ratio × opponent defense ratio × home boost
4. **Simulation** = sample 10,000 independent Poisson draws for each team, count outcomes
5. **Output** = win/draw/loss probabilities + top scoreline distribution

## Prediction Context

All team data in this repo was last updated **April 13, 2026** for the 2025/26 Premier League season.
Update `TEAMS` values in `predict.py` as the season progresses for accurate predictions.

---

Built with Python + NumPy.
