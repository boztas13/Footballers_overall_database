import sqlite3
import pandas as pd
import numpy as np
from tqdm import tqdm

# ----------------------------
# CONFIG
# ----------------------------
DB_PATH = "data/statsbomb.db"
ATTR_TABLE = "player_attributes"

# ----------------------------
# Connect to SQLite
# ----------------------------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ----------------------------
# Load player stats from database
# ----------------------------
print("Loading player stats from database...")
df_stats = pd.read_sql("""
SELECT ps.*, p.player_name 
FROM player_stats ps 
JOIN players p ON ps.player_id = p.player_id
""", conn)

if len(df_stats) == 0:
    print("No player stats found in database")
    conn.close()
    exit()

print(f"Loaded {len(df_stats)} player records")

# Add touches_per90 column (simplified calculation)
df_stats["touches_per90"] = (df_stats["passes_per90"] + df_stats["dribbles_per90"]).fillna(0)

# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def percentile_to_1_20(series, min_minutes=500):
    """Convert series to 1-20 scale using percentiles"""
    s = pd.Series(series).fillna(0)
    mask = df_stats["minutes_played"] >= min_minutes
    if mask.sum() > 0:
        baseline = s[mask]
        if len(baseline) > 0:
            ranks = s.rank(pct=True)
            return (1 + ranks * 19).round(2)
    # Fallback to simple scaling
    return ((s - s.min()) / (s.max() - s.min() + 1e-8) * 19 + 1).round(2)

def get_league_coefficient(comp_id):
    """Get league strength coefficient"""
    league_coeffs = {
        2: 1.0, 49: 0.95, 11: 0.9, 12: 0.85, 9: 0.8,
        37: 1.1, 38: 0.9, 55: 0.8,
        43: 1.05, 50: 1.0, 72: 0.85, 44: 0.8, 45: 0.75
    }
    return league_coeffs.get(comp_id, 0.8)

def calculate_age_factor(age):
    """Calculate age-based performance factor"""
    if age <= 21:
        return 1.1
    elif age <= 25:
        return 1.05
    elif age <= 30:
        return 1.0
    else:
        return 0.95

# Add age column (simplified - random for now)
df_stats["age"] = np.random.randint(18, 35, len(df_stats))

# ----------------------------
# CALCULATE ATTRIBUTES
# ----------------------------
print("\nCalculating Football Manager-style attributes...")
pbar = tqdm(total=7, desc="Processing", unit="category")

# Technical Attributes
print("Computing technical attributes...")
df_stats["passing"] = percentile_to_1_20(
    (df_stats["passes_per90"] * 0.3 + 
     df_stats["pass_accuracy"] * 0.25 + 
     df_stats["key_passes_per90"] * 0.25 +
     df_stats["assists_per90"] * 0.2) * 
    df_stats.apply(lambda x: get_league_coefficient(x.get('competition_id', 0)), axis=1) *
    df_stats.apply(lambda x: calculate_age_factor(x.get('age', 25)), axis=1)
)

df_stats["shooting"] = percentile_to_1_20(
    (df_stats["goals_per90"] * 0.3 + 
     df_stats["xG_per90"] * 0.25 + 
     df_stats["shots_on_target_per90"] * 0.25 +
     (df_stats["goals_per90"] / (df_stats["shots_per90"] + 0.1)) * 0.2) *
    df_stats.apply(lambda x: get_league_coefficient(x.get('competition_id', 0)), axis=1)
)

df_stats["dribbling"] = percentile_to_1_20(
    (df_stats["dribbles_per90"] * 0.4 +
     df_stats["dribbles_successful_per90"] * 0.4 +
     (df_stats["dribbles_successful_per90"] / (df_stats["dribbles_per90"] + 0.1)) * 0.2) *
    df_stats.apply(lambda x: get_league_coefficient(x.get('competition_id', 0)), axis=1)
)

df_stats["first_touch"] = percentile_to_1_20(
    (df_stats["dribbles_successful_per90"] * 0.4 +
     df_stats["pass_accuracy"] * 0.3 +
     df_stats["touches_per90"] * 0.3) *
    df_stats.apply(lambda x: calculate_age_factor(x.get('age', 25)), axis=1)
)

df_stats["crossing"] = percentile_to_1_20(
    (df_stats["key_passes_per90"] * 0.5 +
     df_stats["assists_per90"] * 0.3 +
     df_stats["pass_accuracy"] * 0.2) *
    df_stats.apply(lambda x: get_league_coefficient(x.get('competition_id', 0)), axis=1)
)

df_stats["finishing"] = percentile_to_1_20(
    (df_stats["goals_per90"] * 0.4 +
     df_stats["shots_on_target_per90"] * 0.3 +
     (df_stats["goals_per90"] / (df_stats["xG_per90"] + 0.1)) * 0.3)
)

df_stats["long_shots"] = percentile_to_1_20(
    (df_stats["shots_per90"] * 0.4 +
     df_stats["xG_per90"] * 0.3 +
     (df_stats["shots_on_target_per90"] / (df_stats["shots_per90"] + 0.1)) * 0.3) *
    df_stats.apply(lambda x: get_league_coefficient(x.get('competition_id', 0)), axis=1)
)
pbar.update(1)

# Physical Attributes
print("Computing physical attributes...")
df_stats["pace"] = percentile_to_1_20(
    (df_stats["dribbles_per90"] * 0.4 +
     df_stats["pressures_per90"] * 0.3 +
     df_stats["dribbles_successful_per90"] * 0.3) *
    df_stats.apply(lambda x: calculate_age_factor(x.get('age', 25)), axis=1)
)

df_stats["acceleration"] = percentile_to_1_20(
    (df_stats["dribbles_successful_per90"] * 0.5 +
     df_stats["dribbles_per90"] * 0.3 +
     df_stats["pressures_per90"] * 0.2) *
    df_stats.apply(lambda x: 1.1 if x.get('age', 25) <= 23 else 1.0, axis=1)
)

df_stats["stamina"] = percentile_to_1_20(
    (df_stats["minutes_played"] / 1000 * 0.4 +
     df_stats["pressures_per90"] * 0.3 +
     df_stats["tackles_per90"] * 0.3) *
    df_stats.apply(lambda x: 0.9 if x.get('age', 25) > 30 else 1.0, axis=1)
)

df_stats["strength"] = percentile_to_1_20(
    (df_stats["aerial_duels_per90"] * 0.4 +
     df_stats["tackles_per90"] * 0.3 +
     df_stats["aerial_duels_won_per90"] * 0.3) *
    df_stats.apply(lambda x: 1.05 if 25 <= x.get('age', 25) <= 30 else 1.0, axis=1)
)

df_stats["jumping_reach"] = percentile_to_1_20(
    (df_stats["aerial_duels_won_per90"] * 0.6 +
     df_stats["aerial_duels_per90"] * 0.4) *
    df_stats.apply(lambda x: 1.05 if 25 <= x.get('age', 25) <= 30 else 1.0, axis=1)
)
pbar.update(1)

# Mental Attributes
print("Computing mental attributes...")
df_stats["positioning"] = percentile_to_1_20(
    (df_stats["interceptions_per90"] * 0.3 +
     df_stats["key_passes_per90"] * 0.25 +
     df_stats["pressures_per90"] * 0.25 +
     df_stats["tackles_per90"] * 0.2) *
    df_stats.apply(lambda x: 1.1 if x.get('age', 25) >= 28 else 1.0, axis=1)
)

df_stats["vision"] = percentile_to_1_20(
    (df_stats["key_passes_per90"] * 0.4 +
     df_stats["assists_per90"] * 0.3 +
     df_stats["passes_per90"] * 0.3) *
    df_stats.apply(lambda x: get_league_coefficient(x.get('competition_id', 0)), axis=1)
)

df_stats["composure"] = percentile_to_1_20(
    (df_stats["pass_accuracy"] * 0.4 +
     df_stats["dribbles_successful_per90"] * 0.3 +
     df_stats["goals_per90"] * 0.3)
)

df_stats["concentration"] = percentile_to_1_20(
    (df_stats["interceptions_per90"] * 0.4 +
     df_stats["tackles_won_per90"] * 0.3 +
     df_stats["clearances_per90"] * 0.3) *
    df_stats.apply(lambda x: 1.1 if x.get('age', 25) >= 26 else 1.0, axis=1)
)

df_stats["decisions"] = percentile_to_1_20(
    (df_stats["key_passes_per90"] * 0.3 +
     df_stats["tackles_won_per90"] * 0.25 +
     df_stats["dribbles_successful_per90"] * 0.25 +
     (df_stats["assists_per90"] + df_stats["goals_per90"]) * 0.2) *
    df_stats.apply(lambda x: 1.1 if x.get('age', 25) >= 24 else 1.0, axis=1)
)

df_stats["leadership"] = percentile_to_1_20(
    (df_stats["minutes_played"] / 1000 * 0.4 +
     df_stats["assists_per90"] * 0.3 +
     df_stats["goals_per90"] * 0.3) *
    df_stats.apply(lambda x: 1.2 if x.get('age', 25) >= 28 else 1.0, axis=1)
)
pbar.update(1)

# Defensive Attributes
print("Computing defensive attributes...")
df_stats["tackling"] = percentile_to_1_20(
    (df_stats["tackles_won_per90"] * 0.5 +
     df_stats["tackles_per90"] * 0.3 +
     (df_stats["tackles_won_per90"] / (df_stats["tackles_per90"] + 0.1)) * 0.2) *
    df_stats.apply(lambda x: 1.05 if 25 <= x.get('age', 25) <= 30 else 1.0, axis=1)
)

df_stats["marking"] = percentile_to_1_20(
    (df_stats["interceptions_per90"] * 0.4 +
     df_stats["pressures_per90"] * 0.3 +
     df_stats["tackles_per90"] * 0.3) *
    df_stats.apply(lambda x: 1.1 if x.get('age', 25) >= 26 else 1.0, axis=1)
)

df_stats["heading"] = percentile_to_1_20(
    (df_stats["aerial_duels_won_per90"] * 0.6 +
     df_stats["aerial_duels_per90"] * 0.4) *
    df_stats.apply(lambda x: 1.05 if 25 <= x.get('age', 25) <= 30 else 1.0, axis=1)
)
pbar.update(1)

# Goalkeeping Attributes
print("Computing goalkeeping attributes...")
df_stats["goalkeeping"] = percentile_to_1_20(
    (df_stats["saves_per90"] * 0.4 +
     df_stats["clean_sheets"] * 0.3 +
     (100 - df_stats["goals_conceded_per90"] * 10) * 0.3) *
    df_stats.apply(lambda x: 1.1 if x.get('age', 25) >= 26 else 1.0, axis=1)
)

df_stats["reflexes"] = percentile_to_1_20(
    df_stats["saves_per90"] *
    df_stats.apply(lambda x: 1.05 if x.get('age', 25) <= 28 else 1.0, axis=1)
)

df_stats["handling"] = percentile_to_1_20(
    (df_stats["clean_sheets"] * 0.6 +
     df_stats["pass_accuracy"] * 0.4) *
    df_stats.apply(lambda x: 1.1 if x.get('age', 25) >= 26 else 1.0, axis=1)
)

df_stats["kicking"] = percentile_to_1_20(
    (df_stats["passes_per90"] * 0.5 +
     df_stats["pass_accuracy"] * 0.5) *
    df_stats.apply(lambda x: get_league_coefficient(x.get('competition_id', 0)), axis=1)
)
pbar.update(1)

# Position-specific CA calculations
print("Computing position-specific ratings...")
def compute_position_CA(row, position_type):
    if position_type == "GK":
        weights = {"goalkeeping": 0.4, "reflexes": 0.2, "handling": 0.2, "kicking": 0.2}
    elif position_type == "DEF":
        weights = {"tackling": 0.25, "marking": 0.25, "heading": 0.2, "positioning": 0.15, "pace": 0.15}
    elif position_type == "MID":
        weights = {"passing": 0.25, "vision": 0.2, "positioning": 0.15, "dribbling": 0.15, "tackling": 0.15, "stamina": 0.1}
    else:  # FWD
        weights = {"shooting": 0.3, "pace": 0.2, "dribbling": 0.2, "finishing": 0.15, "positioning": 0.15}
    
    base_ca = sum(row[k] * w for k, w in weights.items())
    league_coeff = get_league_coefficient(row.get('competition_id', 0))
    
    age = row.get('age', 25)
    if position_type == "GK":
        age_factor = 1.1 if 28 <= age <= 32 else 1.0
    elif position_type == "DEF":
        age_factor = 1.05 if 26 <= age <= 30 else 1.0
    elif position_type == "MID":
        age_factor = 1.05 if 24 <= age <= 28 else 1.0
    else:  # FWD
        age_factor = 1.05 if 22 <= age <= 26 else 1.0
    
    return round(base_ca * league_coeff * age_factor, 2)

df_stats["CA_GK"] = df_stats.apply(lambda x: compute_position_CA(x, "GK"), axis=1)
df_stats["CA_DEF"] = df_stats.apply(lambda x: compute_position_CA(x, "DEF"), axis=1)
df_stats["CA_MID"] = df_stats.apply(lambda x: compute_position_CA(x, "MID"), axis=1)
df_stats["CA_FWD"] = df_stats.apply(lambda x: compute_position_CA(x, "FWD"), axis=1)

# Overall CA
df_stats["CA"] = (
    df_stats["CA_GK"] * 0.1 +
    df_stats["CA_DEF"] * 0.3 +
    df_stats["CA_MID"] * 0.3 +
    df_stats["CA_FWD"] * 0.3
).round(2)

# Potential Ability (PA)
def compute_PA(ca, age):
    if age <= 20:
        base_uplift = 6
        variance = 2
    elif age <= 24:
        base_uplift = 4
        variance = 1.5
    elif age <= 28:
        base_uplift = 2
        variance = 1
    else:
        base_uplift = 0
        variance = 0.5
    
    total_uplift = base_uplift + np.random.normal(0, variance)
    return min(20, max(ca, ca + total_uplift))

df_stats["PA"] = df_stats.apply(lambda x: compute_PA(x["CA"], x["age"]), axis=1)
pbar.update(1)

# ----------------------------
# Save to database
# ----------------------------
print("Saving attributes to database...")
cur.execute(f"DROP TABLE IF EXISTS {ATTR_TABLE}")

attr_cols = [
    "player_name", "passing", "shooting", "dribbling", "first_touch", "crossing", "finishing", "long_shots",
    "pace", "acceleration", "stamina", "strength", "jumping_reach",
    "positioning", "vision", "composure", "concentration", "decisions", "leadership",
    "tackling", "marking", "heading",
    "goalkeeping", "reflexes", "handling", "kicking",
    "CA", "PA", "CA_GK", "CA_DEF", "CA_MID", "CA_FWD"
]

df_save = df_stats[attr_cols].copy()
df_save.to_sql(ATTR_TABLE, conn, index=False)

pbar.update(1)
pbar.close()

conn.commit()
conn.close()

print(f"\n✅ Attributes calculated and saved to {ATTR_TABLE}")
print(f"📊 {len(df_stats)} players with detailed attributes")
