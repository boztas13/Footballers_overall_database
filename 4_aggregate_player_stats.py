import sqlite3
import pandas as pd
from tqdm import tqdm

# ----------------------------
# CONFIG
# ----------------------------
DB_PATH = "data/statsbomb.db"
processed_matches_file = "data/processed_players.csv"

# ----------------------------
# Load processed player data
# ----------------------------
print("Loading processed player data...")
df_players = pd.read_csv(processed_matches_file)
print(f"Loaded {len(df_players)} player-match records")

# ----------------------------
# Connect to SQLite
# ----------------------------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ----------------------------
# Aggregate player stats
# ----------------------------
print("Aggregating player statistics...")
agg = df_players.groupby("player").agg(
    minutes_played=("minutes_played", "sum"),
    matches_played=("matches_played", "sum"),
    # Passing
    passes=("passes", "sum"),
    completed_passes=("completed_passes", "sum"),
    key_passes=("key_passes", "sum"),
    assists=("assists", "sum"),
    # Shooting
    shots=("shots", "sum"),
    shots_on_target=("shots_on_target", "sum"),
    goals=("goals", "sum"),
    xG=("xG", "sum"),
    xA=("xA", "sum"),
    # Dribbling
    dribbles=("dribbles", "sum"),
    dribbles_successful=("dribbles_successful", "sum"),
    # Defending
    tackles=("tackles", "sum"),
    tackles_won=("tackles_won", "sum"),
    interceptions=("interceptions", "sum"),
    clearances=("clearances", "sum"),
    blocks=("blocks", "sum"),
    # Aerial
    aerial_duels=("aerial_duels", "sum"),
    aerial_duels_won=("aerial_duels_won", "sum"),
    # Advanced
    pressures=("pressures", "sum"),
    fouls_committed=("fouls_committed", "sum"),
    fouls_won=("fouls_won", "sum"),
    cards_yellow=("cards_yellow", "sum"),
    cards_red=("cards_red", "sum")
).reset_index()

# ----------------------------
# Compute per-90 stats
# ----------------------------
print("Computing per-90 statistics...")
minutes_90 = agg["minutes_played"] / 90

# Passing
agg["passes_per90"] = agg["passes"] / minutes_90
agg["completed_passes_per90"] = agg["completed_passes"] / minutes_90
agg["pass_accuracy"] = (agg["completed_passes"] / agg["passes"] * 100).fillna(0)
agg["key_passes_per90"] = agg["key_passes"] / minutes_90
agg["assists_per90"] = agg["assists"] / minutes_90

# Shooting
agg["shots_per90"] = agg["shots"] / minutes_90
agg["shots_on_target_per90"] = agg["shots_on_target"] / minutes_90
agg["goals_per90"] = agg["goals"] / minutes_90
agg["xG_per90"] = agg["xG"] / minutes_90
agg["xA_per90"] = agg["xA"] / minutes_90

# Dribbling
agg["dribbles_per90"] = agg["dribbles"] / minutes_90
agg["dribbles_successful_per90"] = agg["dribbles_successful"] / minutes_90

# Defending
agg["tackles_per90"] = agg["tackles"] / minutes_90
agg["tackles_won_per90"] = agg["tackles_won"] / minutes_90
agg["interceptions_per90"] = agg["interceptions"] / minutes_90
agg["clearances_per90"] = agg["clearances"] / minutes_90
agg["blocks_per90"] = agg["blocks"] / minutes_90

# Aerial
agg["aerial_duels_per90"] = agg["aerial_duels"] / minutes_90
agg["aerial_duels_won_per90"] = agg["aerial_duels_won"] / minutes_90

# Advanced
agg["pressures_per90"] = agg["pressures"] / minutes_90
agg["fouls_committed_per90"] = agg["fouls_committed"] / minutes_90
agg["fouls_won_per90"] = agg["fouls_won"] / minutes_90

print(f"Aggregated stats for {len(agg)} players")

# ----------------------------
# Insert into database
# ----------------------------
print("Inserting player data into database...")

# Insert players
players_inserted = 0
print("Inserting players...")
for _, row in tqdm(agg.iterrows(), total=len(agg), desc="Players", unit="player"):
    try:
        cur.execute("INSERT OR IGNORE INTO players (player_name) VALUES (?)", (row["player"],))
        players_inserted += 1
    except Exception as e:
        print(f"  Error inserting player {row['player']}: {e}")
        continue

conn.commit()
print(f"Inserted {players_inserted} players")

# FIXED: Fetch actual player_id mapping from database instead of using enumerate
print("Fetching player IDs from database...")
player_id_map = {}
for _, row in agg.iterrows():
    result = cur.execute("SELECT player_id FROM players WHERE player_name = ?", (row["player"],)).fetchone()
    if result:
        player_id_map[row["player"]] = result[0]

print(f"Mapped {len(player_id_map)} players to database IDs")

# Delete existing stats before inserting (to avoid duplicates on re-run)
print("Clearing existing aggregated stats...")
cur.execute("DELETE FROM player_stats WHERE competition_id = 0 AND season_id = 0")
conn.commit()

# Insert player_stats with batch processing
stats_inserted = 0
batch_size = 100
print(f"Inserting player stats in batches of {batch_size}...")

for i in tqdm(range(0, len(agg), batch_size), desc="Batches", unit="batch"):
    batch = agg.iloc[i:i+batch_size]
    
    for _, row in batch.iterrows():
        try:
            player_id = player_id_map.get(row["player"])
            if player_id is None:
                print(f"  Warning: No player_id found for {row['player']}")
                continue
                
            cur.execute("""
            INSERT INTO player_stats (
                player_id, competition_id, season_id, minutes_played, matches_played,
                passes_per90, completed_passes_per90, pass_accuracy, key_passes_per90, assists_per90,
                shots_per90, shots_on_target_per90, goals_per90, xG_per90, xA_per90,
                dribbles_per90, dribbles_successful_per90,
                tackles_per90, tackles_won_per90, interceptions_per90, clearances_per90, blocks_per90,
                aerial_duels_per90, aerial_duels_won_per90,
                pressures_per90, fouls_committed_per90, fouls_won_per90, cards_yellow, cards_red
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player_id, 0, 0,  # competition_id=0, season_id=0 for aggregated stats
                row["minutes_played"], row["matches_played"],
                row["passes_per90"], row["completed_passes_per90"], row["pass_accuracy"],
                row["key_passes_per90"], row["assists_per90"],
                row["shots_per90"], row["shots_on_target_per90"], row["goals_per90"],
                row["xG_per90"], row["xA_per90"],
                row["dribbles_per90"], row["dribbles_successful_per90"],
                row["tackles_per90"], row["tackles_won_per90"], row["interceptions_per90"],
                row["clearances_per90"], row["blocks_per90"],
                row["aerial_duels_per90"], row["aerial_duels_won_per90"],
                row["pressures_per90"], row["fouls_committed_per90"], row["fouls_won_per90"],
                row["cards_yellow"], row["cards_red"]
            ))
            stats_inserted += 1
        except Exception as e:
            print(f"  Error inserting stats for {row['player']}: {e}")
            continue
    
    conn.commit()

print(f"Successfully inserted stats for {stats_inserted} players")

conn.close()
