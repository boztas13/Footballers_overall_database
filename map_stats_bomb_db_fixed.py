import sqlite3
import pandas as pd
import numpy as np
from statsbombpy import sb
import os
from tqdm import tqdm

# ----------------------------
# CONFIG - Multiple competitions for comprehensive data
# ----------------------------
DB_PATH = "data/statsbomb.db"
# Major competitions to fetch - Focus on latest seasons (2020-2024)
COMPETITIONS = [
    # Major European Leagues (Latest 3-4 seasons)
    {"id": 2, "name": "Premier League", "seasons": []}, # Auto-detect latest
    {"id": 49, "name": "La Liga", "seasons": []}, # Auto-detect latest  
    {"id": 11, "name": "Serie A", "seasons": []}, # Auto-detect latest
    {"id": 9, "name": "Ligue 1", "seasons": []}, # Auto-detect latest
    {"id": 12, "name": "Bundesliga", "seasons": []}, # Auto-detect latest
    
    # UEFA Competitions (Latest 3-4 seasons)
    {"id": 37, "name": "UEFA Champions League", "seasons": []}, # Auto-detect latest
    {"id": 38, "name": "UEFA Europa League", "seasons": []}, # Auto-detect latest
    {"id": 55, "name": "UEFA Europa Conference League", "seasons": []}, # Auto-detect latest
    
    # International Competitions
    {"id": 43, "name": "FIFA World Cup", "seasons": []}, # Auto-detect latest
    {"id": 72, "name": "UEFA Nations League", "seasons": []}, # Auto-detect latest
    {"id": 50, "name": "UEFA Euro", "seasons": []}, # Auto-detect latest
    
    # Additional recent competitions
    {"id": 44, "name": "Copa America", "seasons": []}, # Auto-detect latest
    {"id": 45, "name": "AFC Asian Cup", "seasons": []}, # Auto-detect latest
]
ATTR_TABLE = "player_attributes"

os.makedirs("data", exist_ok=True)

# ----------------------------
# Connect to SQLite
# ----------------------------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ----------------------------
# CREATE TABLES
# ----------------------------
cur.executescript("""
CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY,
    player_name TEXT,
    nationality TEXT,
    position TEXT,
    birth_date TEXT,
    height_cm INTEGER,
    weight_kg INTEGER
);
CREATE TABLE IF NOT EXISTS competitions (
    competition_id INTEGER PRIMARY KEY,
    competition_name TEXT,
    season_id INTEGER,
    season_name TEXT
);
CREATE TABLE IF NOT EXISTS matches (
    match_id INTEGER PRIMARY KEY,
    competition_id INTEGER,
    season_id INTEGER,
    date TEXT,
    home_team TEXT,
    away_team TEXT,
    home_score INTEGER,
    away_score INTEGER
);
CREATE TABLE IF NOT EXISTS player_stats (
    player_id INTEGER,
    competition_id INTEGER,
    season_id INTEGER,
    minutes_played INTEGER,
    matches_played INTEGER,
    -- Passing
    passes_per90 REAL,
    completed_passes_per90 REAL,
    pass_accuracy REAL,
    progressive_passes_per90 REAL,
    key_passes_per90 REAL,
    assists_per90 REAL,
    -- Shooting
    shots_per90 REAL,
    shots_on_target_per90 REAL,
    goals_per90 REAL,
    xG_per90 REAL,
    xA_per90 REAL,
    -- Dribbling & Ball Control
    dribbles_per90 REAL,
    dribbles_successful_per90 REAL,
    progressive_carries_per90 REAL,
    touches_per90 REAL,
    -- Defending
    tackles_per90 REAL,
    tackles_won_per90 REAL,
    interceptions_per90 REAL,
    clearances_per90 REAL,
    blocks_per90 REAL,
    -- Aerial & Physical
    aerial_duels_per90 REAL,
    aerial_duels_won_per90 REAL,
    -- Goalkeeping
    saves_per90 REAL,
    clean_sheets INTEGER,
    goals_conceded_per90 REAL,
    -- Advanced Metrics
    pressures_per90 REAL,
    pressure_regains_per90 REAL,
    fouls_committed_per90 REAL,
    fouls_won_per90 REAL,
    cards_yellow INTEGER,
    cards_red INTEGER
);
CREATE TABLE IF NOT EXISTS player_attributes (
    player_id INTEGER PRIMARY KEY,
    -- Technical Attributes
    passing REAL,
    shooting REAL,
    dribbling REAL,
    first_touch REAL,
    crossing REAL,
    finishing REAL,
    long_shots REAL,
    -- Physical Attributes
    pace REAL,
    acceleration REAL,
    stamina REAL,
    strength REAL,
    jumping_reach REAL,
    -- Mental Attributes
    positioning REAL,
    vision REAL,
    composure REAL,
    concentration REAL,
    decisions REAL,
    leadership REAL,
    -- Defensive Attributes
    tackling REAL,
    marking REAL,
    heading REAL,
    -- Goalkeeping Attributes
    goalkeeping REAL,
    reflexes REAL,
    handling REAL,
    kicking REAL,
    -- Overall Ratings
    CA REAL,
    PA REAL,
    -- Position-specific ratings
    CA_GK REAL,
    CA_DEF REAL,
    CA_MID REAL,
    CA_FWD REAL
);
""")
conn.commit()

# ----------------------------
# FETCH MULTIPLE COMPETITIONS AND MATCHES
# ----------------------------
print("Fetching competitions and matches...")

# Function to get latest available seasons for a competition
def get_latest_seasons(comp_id, max_seasons=4):
    try:
        comps_df = sb.competitions()
        available_seasons = comps_df[comps_df.competition_id == comp_id]['season_id'].tolist()
        # Return the latest seasons, sorted in descending order
        # Prioritize seasons from 2020 onwards
        recent_seasons = [s for s in available_seasons if s >= 100]  # Season IDs 100+ are typically 2020+
        if recent_seasons:
            return sorted(recent_seasons, reverse=True)[:max_seasons]
        else:
            return sorted(available_seasons, reverse=True)[:max_seasons]
    except:
        return []

# Update competitions with latest available seasons
print("Detecting latest available seasons...")
for comp in COMPETITIONS:
    latest_seasons = get_latest_seasons(comp["id"])
    if latest_seasons:
        comp["seasons"] = latest_seasons
        print(f"  {comp['name']}: Found seasons {latest_seasons}")

all_matches = []

for comp in COMPETITIONS:
    comp_id = comp["id"]
    comp_name = comp["name"]
    
    print(f"Processing {comp_name}...")
    
    for season_id in comp["seasons"]:
        try:
            # Get competition info
            comps_df = sb.competitions()
            comp_info = comps_df[(comps_df.competition_id == comp_id) & (comps_df.season_id == season_id)]
            
            if len(comp_info) > 0:
                # Insert competition
                cur.execute("""
                INSERT OR IGNORE INTO competitions (competition_id, competition_name, season_id, season_name)
                VALUES (?, ?, ?, ?)
                """, (comp_id, comp_name, season_id, comp_info["season_name"].iloc[0]))
                
                # Get matches for this competition/season
                matches = sb.matches(competition_id=comp_id, season_id=season_id)
                
                if len(matches) > 0:
                    print(f"  Found {len(matches)} matches in {comp_name} {comp_info['season_name'].iloc[0]}")
                    
                    # Insert matches
                    for _, m in matches.iterrows():
                        cur.execute("""
                        INSERT OR IGNORE INTO matches (match_id, competition_id, season_id, date, home_team, away_team, home_score, away_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            m["match_id"],
                            comp_id,
                            season_id,
                            m.get("match_date", ""),
                            m.get("home_team", ""),
                            m.get("away_team", ""),
                            m.get("home_score", 0),
                            m.get("away_score", 0)
                        ))
                        all_matches.append(m["match_id"])
                else:
                    print(f"  No matches found for {comp_name} season {season_id}")
            else:
                print(f"  Competition {comp_name} season {season_id} not found")
                
        except Exception as e:
            print(f"  Error processing {comp_name} season {season_id}: {e}")
            continue

conn.commit()
print(f"Total matches to process: {len(all_matches)}")

# ----------------------------
# FETCH EVENTS & AGGREGATE PLAYER STATS WITH CHECKPOINTING
# ----------------------------
print("Processing match events and calculating player stats...")

# Checkpoint system - save progress every 50 matches
CHECKPOINT_INTERVAL = 50
checkpoint_file = "data/checkpoint_matches.txt"
processed_matches_file = "data/processed_players.csv"

# Load previously processed matches if checkpoint exists
processed_matches = set()
if os.path.exists(checkpoint_file):
    with open(checkpoint_file, 'r') as f:
        processed_matches = set(line.strip() for line in f)
    print(f"Resuming from checkpoint: {len(processed_matches)} matches already processed")

# Load existing player data if available
all_players = []
if os.path.exists(processed_matches_file):
    try:
        df_existing = pd.read_csv(processed_matches_file)
        all_players.append(df_existing)
        print(f"Loaded existing player data: {len(df_existing)} records")
    except:
        print("Could not load existing player data, starting fresh")

# Process matches with error handling and checkpointing
matches_to_process = [m for m in all_matches if str(m) not in processed_matches]
print(f"Processing {len(matches_to_process)} new matches...")

# Create progress bar for match processing
pbar = tqdm(total=len(matches_to_process), desc="Processing matches", unit="match")

for i, match_id in enumerate(matches_to_process):
    pbar.set_description(f"Processing match {i+1}/{len(matches_to_process)}: {match_id}")
    
    try:
        events = sb.events(match_id=match_id)
        
        if len(events) == 0:
            processed_matches.add(str(match_id))
            continue
            
        # Get match info for competition/season
        match_info = cur.execute("SELECT competition_id, season_id FROM matches WHERE match_id = ?", (match_id,)).fetchone()
        if not match_info:
            processed_matches.add(str(match_id))
            continue
        comp_id, season_id = match_info

        # Compute comprehensive per-player stats
        player_stats = []
        
        for player in events["player"].dropna().unique():
            player_events = events[events["player"] == player]
            
            # Basic stats
            minutes = player_events["minute"].max() if len(player_events) > 0 else 0
            if minutes == 0:
                continue
                
            # Passing stats
            passes = player_events[player_events["type"] == "Pass"]
            completed_passes = passes[passes.get("pass_outcome", "") == "Complete"] if "pass_outcome" in passes.columns else passes
            key_passes = passes[passes.get("pass_goal_assist", False) == True] if "pass_goal_assist" in passes.columns else pd.DataFrame()
            
            # Shooting stats
            shots = player_events[player_events["type"] == "Shot"]
            shots_on_target = shots[shots.get("shot_outcome", "").isin(["Goal", "Saved"])] if "shot_outcome" in shots.columns else shots
            goals = shots[shots.get("shot_outcome", "") == "Goal"] if "shot_outcome" in shots.columns else pd.DataFrame()
            
            # Dribbling stats
            dribbles = player_events[player_events["type"] == "Dribble"]
            successful_dribbles = dribbles[dribbles.get("dribble_outcome", "") == "Complete"] if "dribble_outcome" in dribbles.columns else dribbles
            
            # Defensive stats
            tackles = player_events[player_events["type"] == "Tackle"]
            won_tackles = tackles[tackles.get("tackle_outcome", "") == "Won"] if "tackle_outcome" in tackles.columns else tackles
            interceptions = player_events[player_events["type"] == "Interception"]
            clearances = player_events[player_events["type"] == "Clearance"]
            blocks = player_events[player_events["type"] == "Block"]
            
            # Aerial stats
            aerial_duels = player_events[player_events["type"] == "Duel"]
            aerial_duels = aerial_duels[aerial_duels.get("duel_type", "") == "Aerial"] if "duel_type" in aerial_duels.columns else pd.DataFrame()
            won_aerial_duels = aerial_duels[aerial_duels.get("duel_outcome", "") == "Won"] if "duel_outcome" in aerial_duels.columns else pd.DataFrame()
            
            # Advanced stats
            pressures = player_events[player_events["type"] == "Pressure"]
            fouls_committed = player_events[player_events["type"] == "Foul Committed"]
            fouls_won = player_events[player_events["type"] == "Foul Won"]
            
            # xG and xA
            xG = shots["shot_statsbomb_xg"].sum() if "shot_statsbomb_xg" in shots.columns else 0
            xA = passes["pass_statsbomb_xa"].sum() if "pass_statsbomb_xa" in passes.columns else 0
            
            # Cards
            cards = player_events[player_events["type"] == "Card"]
            yellow_cards = len(cards[cards.get("card_type", "") == "Yellow Card"]) if "card_type" in cards.columns else 0
            red_cards = len(cards[cards.get("card_type", "") == "Red Card"]) if "card_type" in cards.columns else 0
            
            player_stat = {
                "player": player,
                "match_id": match_id,
                "competition_id": comp_id,
                "season_id": season_id,
                "minutes_played": minutes,
                "matches_played": 1,
                # Passing
                "passes": len(passes),
                "completed_passes": len(completed_passes),
                "key_passes": len(key_passes),
                "assists": len(goals),  # Simplified
                # Shooting
                "shots": len(shots),
                "shots_on_target": len(shots_on_target),
                "goals": len(goals),
                "xG": xG,
                "xA": xA,
                # Dribbling
                "dribbles": len(dribbles),
                "dribbles_successful": len(successful_dribbles),
                # Defending
                "tackles": len(tackles),
                "tackles_won": len(won_tackles),
                "interceptions": len(interceptions),
                "clearances": len(clearances),
                "blocks": len(blocks),
                # Aerial
                "aerial_duels": len(aerial_duels),
                "aerial_duels_won": len(won_aerial_duels),
                # Advanced
                "pressures": len(pressures),
                "fouls_committed": len(fouls_committed),
                "fouls_won": len(fouls_won),
                "cards_yellow": yellow_cards,
                "cards_red": red_cards,
                # Goalkeeping (simplified)
                "saves": 0,
                "clean_sheets": 0,
                "goals_conceded": 0
            }
            
            player_stats.append(player_stat)
        
        if player_stats:
            df_match = pd.DataFrame(player_stats)
            all_players.append(df_match)
            
        # Mark match as processed
        processed_matches.add(str(match_id))
        
        # Save checkpoint every CHECKPOINT_INTERVAL matches
        if (i + 1) % CHECKPOINT_INTERVAL == 0:
            pbar.set_postfix({"Checkpoint": f"Saving progress at match {i+1}"})
            # Save processed matches list
            with open(checkpoint_file, 'w') as f:
                for match in processed_matches:
                    f.write(f"{match}\n")
            
            # Save current player data
            if all_players:
                df_current = pd.concat(all_players, ignore_index=True)
                df_current.to_csv(processed_matches_file, index=False)
                pbar.set_postfix({"Saved": f"{len(df_current)} player records"})
            
    except Exception as e:
        pbar.set_postfix({"Error": f"Match {match_id}: {str(e)[:30]}..."})
        # Still mark as processed to avoid infinite retry
        processed_matches.add(str(match_id))
        continue
    
    # Update progress bar
    pbar.update(1)

# Close progress bar
pbar.close()

# Final save of all data
if all_players:
    df_players = pd.concat(all_players, ignore_index=True)
    print(f"Processed {len(df_players)} player-match records")
    # Save final checkpoint
    with open(checkpoint_file, 'w') as f:
        for match in processed_matches:
            f.write(f"{match}\n")
    df_players.to_csv(processed_matches_file, index=False)
    print("Final checkpoint saved")
else:
    print("No player data found")
    df_players = pd.DataFrame()

# Aggregate player stats across all competitions
if len(df_players) > 0:
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

    # Compute per-90 stats
    minutes_90 = agg["minutes_played"] / 90
    agg["passes_per90"] = agg["passes"] / minutes_90
    agg["completed_passes_per90"] = agg["completed_passes"] / minutes_90
    agg["pass_accuracy"] = (agg["completed_passes"] / agg["passes"] * 100).fillna(0)
    agg["key_passes_per90"] = agg["key_passes"] / minutes_90
    agg["assists_per90"] = agg["assists"] / minutes_90
    
    agg["shots_per90"] = agg["shots"] / minutes_90
    agg["shots_on_target_per90"] = agg["shots_on_target"] / minutes_90
    agg["goals_per90"] = agg["goals"] / minutes_90
    agg["xG_per90"] = agg["xG"] / minutes_90
    agg["xA_per90"] = agg["xA"] / minutes_90
    
    agg["dribbles_per90"] = agg["dribbles"] / minutes_90
    agg["dribbles_successful_per90"] = agg["dribbles_successful"] / minutes_90
    
    agg["tackles_per90"] = agg["tackles"] / minutes_90
    agg["tackles_won_per90"] = agg["tackles_won"] / minutes_90
    agg["interceptions_per90"] = agg["interceptions"] / minutes_90
    agg["clearances_per90"] = agg["clearances"] / minutes_90
    agg["blocks_per90"] = agg["blocks"] / minutes_90
    
    agg["aerial_duels_per90"] = agg["aerial_duels"] / minutes_90
    agg["aerial_duels_won_per90"] = agg["aerial_duels_won"] / minutes_90
    
    agg["pressures_per90"] = agg["pressures"] / minutes_90
    agg["fouls_committed_per90"] = agg["fouls_committed"] / minutes_90
    agg["fouls_won_per90"] = agg["fouls_won"] / minutes_90
    
    print(f"Aggregated stats for {len(agg)} players")
else:
    print("No player data to aggregate")
    agg = pd.DataFrame()

# ----------------------------
# Insert players and stats into DB with error handling
# ----------------------------
if len(agg) > 0:
    print("Inserting player data into database...")
    
    try:
        # Insert players with error handling
        players_inserted = 0
        print("Inserting players into database...")
        for _, row in tqdm(agg.iterrows(), total=len(agg), desc="Inserting players", unit="player"):
            try:
                cur.execute("INSERT OR IGNORE INTO players (player_name) VALUES (?)", (row["player"],))
                players_inserted += 1
            except Exception as e:
                print(f"  Error inserting player {row['player']}: {e}")
                continue
        
        conn.commit()
        print(f"Inserted {players_inserted} players into database")
        
        # Map player_name → player_id
        players_dict = {name: i for i, name in enumerate(agg["player"], start=1)}
        
        # Insert comprehensive player_stats with batch processing
        stats_inserted = 0
        batch_size = 100
        num_batches = (len(agg) - 1) // batch_size + 1
        print(f"Processing {num_batches} batches of player stats...")
        
        for i in tqdm(range(0, len(agg), batch_size), desc="Processing batches", unit="batch"):
            batch = agg.iloc[i:i+batch_size]
            
            for _, row in batch.iterrows():
                try:
                    player_id = players_dict[row["player"]]
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
                        player_id, 0, 0,  # competition_id=0 for aggregated stats, season_id=0 for all seasons
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
                    print(f"  Error inserting stats for player {row['player']}: {e}")
                    continue
            
            # Commit batch
            try:
                conn.commit()
                print(f"  Committed batch {i//batch_size + 1}")
            except Exception as e:
                print(f"  Error committing batch: {e}")
                conn.rollback()
        
        print(f"Successfully inserted stats for {stats_inserted} players")
        
    except Exception as e:
        print(f"Critical error in database insertion: {e}")
        conn.rollback()
        print("Database transaction rolled back")

# ----------------------------
# Advanced attribute calculation with error handling
# ----------------------------
if len(agg) > 0:
    print("Calculating Football Manager-style attributes...")
    
    try:
        # Read stats from database
        df_stats = pd.read_sql("""
        SELECT ps.*, p.player_name 
        FROM player_stats ps 
        JOIN players p ON ps.player_id = p.player_id
        """, conn)
        
        if len(df_stats) == 0:
            print("No player stats found in database")
            conn.close()
            exit()
        
        print(f"Loaded {len(df_stats)} player records for attribute calculation")
        
        # Percentile helper with better handling
        def percentile_to_1_20(series, min_minutes=500):
            s = pd.Series(series).fillna(0)
            # Only use players with sufficient minutes for percentile baseline
            mask = df_stats["minutes_played"] >= min_minutes
            if mask.sum() > 0:
                baseline = s[mask]
                if len(baseline) > 0:
                    ranks = s.rank(pct=True)
                    return (1 + ranks * 19).round(2)
            # Fallback to simple scaling
            return ((s - s.min()) / (s.max() - s.min() + 1e-8) * 19 + 1).round(2)
        
        # Enhanced attribute calculation with league coefficients and contextual factors
        print("Computing enhanced technical attributes...")
        
        # Create progress bar for attribute calculation
        attr_pbar = tqdm(total=7, desc="Calculating attributes", unit="category")
        
        # Calculate league strength coefficients based on competition
        def get_league_coefficient(comp_id):
            """Get league strength coefficient based on competition prestige"""
            league_coeffs = {
                2: 1.0,    # Premier League
                49: 0.95,   # La Liga  
                11: 0.9,    # Serie A
                12: 0.85,   # Bundesliga
                9: 0.8,     # Ligue 1
                37: 1.1,    # Champions League
                38: 0.9,    # Europa League
                55: 0.8,    # Europa Conference League
                43: 1.05,   # World Cup
                50: 1.0,    # Euro
                72: 0.85,   # Nations League
                44: 0.8,    # Copa America
                45: 0.75    # AFC Asian Cup
            }
            return league_coeffs.get(comp_id, 0.8)
        
        # Calculate opponent strength factor (simplified - based on competition level)
        def get_opponent_strength_factor(comp_id, season_id):
            """Calculate opponent strength factor"""
            base_coeff = get_league_coefficient(comp_id)
            # Champions League and international competitions have higher opponent strength
            if comp_id in [37, 43, 50]:  # Champions League, World Cup, Euro
                return base_coeff * 1.2
            elif comp_id in [38, 55]:  # Europa competitions
                return base_coeff * 1.1
            else:
                return base_coeff
        
        # Calculate performance consistency (lower variance = more consistent)
        def calculate_consistency_factor(series):
            """Calculate consistency factor based on performance variance"""
            if len(series) < 3:
                return 1.0
            mean_val = series.mean()
            if mean_val == 0:
                return 1.0
            cv = series.std() / mean_val  # Coefficient of variation
            # Lower CV = more consistent = higher factor
            return max(0.7, 1.0 - (cv * 0.3))
        
        # Calculate pressure performance (performance in high-pressure situations)
        def calculate_pressure_performance(row):
            """Calculate how well player performs under pressure"""
            # Based on performance in Champions League, World Cup, Euro
            high_pressure_comps = [37, 43, 50]  # Champions League, World Cup, Euro
            # This is simplified - in reality you'd track performance by competition
            return 1.0 + (0.1 if row.get('competition_id', 0) in high_pressure_comps else 0.0)
        
        # Calculate age factor (younger players get potential boost, older players get experience boost)
        def calculate_age_factor(age):
            """Calculate age-based performance factor"""
            if age <= 21:
                return 1.1  # Young players get potential boost
            elif age <= 25:
                return 1.05  # Peak age
            elif age <= 30:
                return 1.0   # Prime age
            else:
                return 0.95  # Slight decline for older players
        
        # Enhanced passing calculation with multiple factors
        df_stats["passing"] = percentile_to_1_20(
            (df_stats["passes_per90"] * 0.3 + 
             df_stats["pass_accuracy"] * 0.25 + 
             df_stats["key_passes_per90"] * 0.25 +
             df_stats["assists_per90"] * 0.2) * 
            df_stats.apply(lambda x: get_league_coefficient(x.get('competition_id', 0)), axis=1) *
            df_stats.apply(lambda x: calculate_age_factor(x.get('age', 25)), axis=1)
        )
        attr_pbar.update(1)
        
        # Enhanced shooting with efficiency and pressure factors
        df_stats["shooting"] = percentile_to_1_20(
            (df_stats["goals_per90"] * 0.3 + 
             df_stats["xG_per90"] * 0.25 + 
             df_stats["shots_on_target_per90"] * 0.25 +
             (df_stats["goals_per90"] / (df_stats["shots_per90"] + 0.1)) * 0.2) *  # Efficiency factor
            df_stats.apply(lambda x: get_league_coefficient(x.get('competition_id', 0)), axis=1) *
            df_stats.apply(lambda x: calculate_pressure_performance(x), axis=1)
        )
        
        # Enhanced dribbling with success rate and opponent strength
        df_stats["dribbling"] = percentile_to_1_20(
            (df_stats["dribbles_per90"] * 0.4 + 
             df_stats["dribbles_successful_per90"] * 0.4 +
             (df_stats["dribbles_successful_per90"] / (df_stats["dribbles_per90"] + 0.1)) * 0.2) *  # Success rate
            df_stats.apply(lambda x: get_league_coefficient(x.get('competition_id', 0)), axis=1)
        )
        
        # Enhanced first touch with ball control metrics
        df_stats["first_touch"] = percentile_to_1_20(
            (df_stats["dribbles_successful_per90"] * 0.4 + 
             df_stats["pass_accuracy"] * 0.3 +
             df_stats["touches_per90"] * 0.3) *  # Ball control factor
            df_stats.apply(lambda x: calculate_age_factor(x.get('age', 25)), axis=1)
        )
        
        # Enhanced crossing with wide play and delivery accuracy
        df_stats["crossing"] = percentile_to_1_20(
            (df_stats["key_passes_per90"] * 0.5 + 
             df_stats["assists_per90"] * 0.3 +
             df_stats["pass_accuracy"] * 0.2) *  # Delivery accuracy
            df_stats.apply(lambda x: get_league_coefficient(x.get('competition_id', 0)), axis=1)
        )
        
        # Enhanced finishing with clinical efficiency
        df_stats["finishing"] = percentile_to_1_20(
            (df_stats["goals_per90"] * 0.4 + 
             df_stats["shots_on_target_per90"] * 0.3 +
             (df_stats["goals_per90"] / (df_stats["xG_per90"] + 0.1)) * 0.3) *  # Clinical efficiency
            df_stats.apply(lambda x: calculate_pressure_performance(x), axis=1)
        )
        
        # Enhanced long shots with range and accuracy
        df_stats["long_shots"] = percentile_to_1_20(
            (df_stats["shots_per90"] * 0.4 + 
             df_stats["xG_per90"] * 0.3 +
             (df_stats["shots_on_target_per90"] / (df_stats["shots_per90"] + 0.1)) * 0.3) *  # Accuracy from distance
            df_stats.apply(lambda x: get_league_coefficient(x.get('competition_id', 0)), axis=1)
        )
        attr_pbar.update(1)
        
        print("Computing enhanced physical attributes...")
        
        # Enhanced pace with speed and intensity factors
        df_stats["pace"] = percentile_to_1_20(
            (df_stats["dribbles_per90"] * 0.4 + 
             df_stats["pressures_per90"] * 0.3 +
             df_stats["dribbles_successful_per90"] * 0.3) *  # Speed with ball
            df_stats.apply(lambda x: calculate_age_factor(x.get('age', 25)), axis=1)  # Age affects pace
        )
        
        # Enhanced acceleration with burst and change of pace
        df_stats["acceleration"] = percentile_to_1_20(
            (df_stats["dribbles_successful_per90"] * 0.5 + 
             df_stats["dribbles_per90"] * 0.3 +
             df_stats["pressures_per90"] * 0.2) *  # Quick bursts
            df_stats.apply(lambda x: 1.1 if x.get('age', 25) <= 23 else 1.0, axis=1)  # Young players excel
        )
        
        # Enhanced stamina with work rate and consistency
        df_stats["stamina"] = percentile_to_1_20(
            (df_stats["minutes_played"] / 1000 * 0.4 +  # Playing time
             df_stats["pressures_per90"] * 0.3 +  # Work rate
             df_stats["tackles_per90"] * 0.3) *  # Defensive work
            df_stats.apply(lambda x: 0.9 if x.get('age', 25) > 30 else 1.0, axis=1)  # Age affects stamina
        )
        
        # Enhanced strength with physical duels and aerial ability
        df_stats["strength"] = percentile_to_1_20(
            (df_stats["aerial_duels_per90"] * 0.4 + 
             df_stats["tackles_per90"] * 0.3 +
             df_stats["aerial_duels_won_per90"] * 0.3) *  # Physical dominance
            df_stats.apply(lambda x: 1.05 if 25 <= x.get('age', 25) <= 30 else 1.0, axis=1)  # Peak physical age
        )
        
        # Enhanced jumping reach with aerial dominance
        df_stats["jumping_reach"] = percentile_to_1_20(
            (df_stats["aerial_duels_won_per90"] * 0.6 + 
             df_stats["aerial_duels_per90"] * 0.4) *  # Aerial success rate
            df_stats.apply(lambda x: 1.05 if 25 <= x.get('age', 25) <= 30 else 1.0, axis=1)  # Peak physical age
        )
        attr_pbar.update(1)
        
        print("Computing enhanced mental attributes...")
        
        # Enhanced positioning with spatial awareness and tactical intelligence
        df_stats["positioning"] = percentile_to_1_20(
            (df_stats["interceptions_per90"] * 0.3 + 
             df_stats["key_passes_per90"] * 0.25 + 
             df_stats["pressures_per90"] * 0.25 +
             df_stats["tackles_per90"] * 0.2) *  # Defensive positioning
            df_stats.apply(lambda x: 1.1 if x.get('age', 25) >= 28 else 1.0, axis=1)  # Experience helps
        )
        
        # Enhanced vision with creativity and passing intelligence
        df_stats["vision"] = percentile_to_1_20(
            (df_stats["key_passes_per90"] * 0.4 + 
             df_stats["assists_per90"] * 0.3 +
             df_stats["passes_per90"] * 0.3) *  # Passing volume indicates vision
            df_stats.apply(lambda x: get_league_coefficient(x.get('competition_id', 0)), axis=1)  # Higher leagues = better vision
        )
        
        # Enhanced composure with pressure handling and consistency
        df_stats["composure"] = percentile_to_1_20(
            (df_stats["pass_accuracy"] * 0.4 + 
             df_stats["dribbles_successful_per90"] * 0.3 +
             df_stats["goals_per90"] * 0.3) *  # Goals under pressure
            df_stats.apply(lambda x: calculate_pressure_performance(x), axis=1)  # Pressure situations
        )
        
        # Enhanced concentration with defensive focus and consistency
        df_stats["concentration"] = percentile_to_1_20(
            (df_stats["interceptions_per90"] * 0.4 + 
             df_stats["tackles_won_per90"] * 0.3 +
             df_stats["clearances_per90"] * 0.3) *  # Defensive focus
            df_stats.apply(lambda x: 1.1 if x.get('age', 25) >= 26 else 1.0, axis=1)  # Experience helps concentration
        )
        
        # Enhanced decisions with tactical intelligence and efficiency
        df_stats["decisions"] = percentile_to_1_20(
            (df_stats["key_passes_per90"] * 0.3 + 
             df_stats["tackles_won_per90"] * 0.25 + 
             df_stats["dribbles_successful_per90"] * 0.25 +
             (df_stats["assists_per90"] + df_stats["goals_per90"]) * 0.2) *  # End product decisions
            df_stats.apply(lambda x: 1.1 if x.get('age', 25) >= 24 else 1.0, axis=1)  # Maturity helps decisions
        )
        
        # Enhanced leadership with experience and influence
        df_stats["leadership"] = percentile_to_1_20(
            (df_stats["minutes_played"] / 1000 * 0.4 +  # Playing time
             df_stats["assists_per90"] * 0.3 +  # Creating for others
             df_stats["goals_per90"] * 0.3) *  # Leading by example
            df_stats.apply(lambda x: 1.2 if x.get('age', 25) >= 28 else 1.0, axis=1)  # Age brings leadership
        )
        attr_pbar.update(1)
        
        print("Computing enhanced defensive attributes...")
        
        # Enhanced tackling with success rate and physicality
        df_stats["tackling"] = percentile_to_1_20(
            (df_stats["tackles_won_per90"] * 0.5 + 
             df_stats["tackles_per90"] * 0.3 +
             (df_stats["tackles_won_per90"] / (df_stats["tackles_per90"] + 0.1)) * 0.2) *  # Success rate
            df_stats.apply(lambda x: 1.05 if 25 <= x.get('age', 25) <= 30 else 1.0, axis=1)  # Peak physical age
        )
        
        # Enhanced marking with anticipation and defensive intelligence
        df_stats["marking"] = percentile_to_1_20(
            (df_stats["interceptions_per90"] * 0.4 + 
             df_stats["pressures_per90"] * 0.3 +
             df_stats["tackles_per90"] * 0.3) *  # Defensive activity
            df_stats.apply(lambda x: 1.1 if x.get('age', 25) >= 26 else 1.0, axis=1)  # Experience helps marking
        )
        
        # Enhanced heading with aerial dominance and timing
        df_stats["heading"] = percentile_to_1_20(
            (df_stats["aerial_duels_won_per90"] * 0.6 + 
             df_stats["aerial_duels_per90"] * 0.4) *  # Aerial success
            df_stats.apply(lambda x: 1.05 if 25 <= x.get('age', 25) <= 30 else 1.0, axis=1)  # Peak physical age
        )
        attr_pbar.update(1)
        
        print("Computing enhanced goalkeeping attributes...")
        
        # Enhanced goalkeeping with shot-stopping and command
        df_stats["goalkeeping"] = percentile_to_1_20(
            (df_stats["saves_per90"] * 0.4 + 
             df_stats["clean_sheets"] * 0.3 + 
             (100 - df_stats["goals_conceded_per90"] * 10) * 0.3) *  # Goals prevented
            df_stats.apply(lambda x: 1.1 if x.get('age', 25) >= 26 else 1.0, axis=1)  # Experience helps goalkeeping
        )
        
        # Enhanced reflexes with shot-stopping ability
        df_stats["reflexes"] = percentile_to_1_20(
            df_stats["saves_per90"] * 
            df_stats.apply(lambda x: 1.05 if x.get('age', 25) <= 28 else 1.0, axis=1)  # Reflexes decline with age
        )
        
        # Enhanced handling with ball control and distribution
        df_stats["handling"] = percentile_to_1_20(
            (df_stats["clean_sheets"] * 0.6 + 
             df_stats["pass_accuracy"] * 0.4) *  # Ball control
            df_stats.apply(lambda x: 1.1 if x.get('age', 25) >= 26 else 1.0, axis=1)  # Experience helps handling
        )
        
        # Enhanced kicking with distribution and accuracy
        df_stats["kicking"] = percentile_to_1_20(
            (df_stats["passes_per90"] * 0.5 + 
             df_stats["pass_accuracy"] * 0.5) *  # Distribution accuracy
            df_stats.apply(lambda x: get_league_coefficient(x.get('competition_id', 0)), axis=1)  # League quality affects kicking
        )
        attr_pbar.update(1)
        
        # Enhanced position-specific CA calculations with league and age factors
        def compute_position_CA(row, position_type):
            # Base weights for each position
            if position_type == "GK":
                weights = {"goalkeeping": 0.4, "reflexes": 0.2, "handling": 0.2, "kicking": 0.2}
            elif position_type == "DEF":
                weights = {"tackling": 0.25, "marking": 0.25, "heading": 0.2, "positioning": 0.15, "pace": 0.15}
            elif position_type == "MID":
                weights = {"passing": 0.25, "vision": 0.2, "positioning": 0.15, "dribbling": 0.15, "tackling": 0.15, "stamina": 0.1}
            else:  # FWD
                weights = {"shooting": 0.3, "pace": 0.2, "dribbling": 0.2, "finishing": 0.15, "positioning": 0.15}
            
            # Calculate base CA
            base_ca = sum(row[k] * w for k, w in weights.items())
            
            # Apply league coefficient
            league_coeff = get_league_coefficient(row.get('competition_id', 0))
            
            # Apply age factor based on position
            age = row.get('age', 25)
            if position_type == "GK":
                # Goalkeepers peak later and decline slower
                age_factor = 1.1 if 28 <= age <= 32 else 1.0
            elif position_type == "DEF":
                # Defenders peak in late 20s
                age_factor = 1.05 if 26 <= age <= 30 else 1.0
            elif position_type == "MID":
                # Midfielders peak in mid-20s
                age_factor = 1.05 if 24 <= age <= 28 else 1.0
            else:  # FWD
                # Forwards peak earlier
                age_factor = 1.05 if 22 <= age <= 26 else 1.0
            
            # Apply pressure performance factor
            pressure_factor = calculate_pressure_performance(row)
            
            return round(base_ca * league_coeff * age_factor * pressure_factor, 2)
        
        # Calculate position-specific CAs
        df_stats["CA_GK"] = df_stats.apply(lambda x: compute_position_CA(x, "GK"), axis=1)
        df_stats["CA_DEF"] = df_stats.apply(lambda x: compute_position_CA(x, "DEF"), axis=1)
        df_stats["CA_MID"] = df_stats.apply(lambda x: compute_position_CA(x, "MID"), axis=1)
        df_stats["CA_FWD"] = df_stats.apply(lambda x: compute_position_CA(x, "FWD"), axis=1)
        
        # Enhanced overall CA with versatility and consistency factors
        def calculate_versatility_factor(row):
            """Calculate versatility based on how well player performs in multiple positions"""
            position_cas = [row["CA_GK"], row["CA_DEF"], row["CA_MID"], row["CA_FWD"]]
            max_ca = max(position_cas)
            min_ca = min(position_cas)
            
            # Versatility bonus if player can play multiple positions well
            if max_ca > 0:
                versatility = 1.0 + (0.1 * (max_ca - min_ca) / max_ca)  # More versatile = higher factor
                return min(1.2, versatility)  # Cap at 1.2
            return 1.0
        
        def calculate_consistency_factor(row):
            """Calculate consistency based on performance stability"""
            # This is simplified - in reality you'd track performance variance over time
            age = row.get('age', 25)
            if age >= 26:  # More experienced players are more consistent
                return 1.05
            return 1.0
        
        # Calculate versatility and consistency factors
        df_stats["versatility_factor"] = df_stats.apply(calculate_versatility_factor, axis=1)
        df_stats["consistency_factor"] = df_stats.apply(calculate_consistency_factor, axis=1)
        
        # Enhanced overall CA with multiple factors
        df_stats["CA"] = (
            (df_stats["CA_GK"] * 0.1 + 
             df_stats["CA_DEF"] * 0.3 + 
             df_stats["CA_MID"] * 0.3 + 
             df_stats["CA_FWD"] * 0.3) *
            df_stats["versatility_factor"] *
            df_stats["consistency_factor"]
        ).round(2)
        
        # Enhanced PA calculation with multiple factors
        def compute_PA(ca, age, league_coeff, versatility_factor):
            """Calculate Potential Ability with enhanced factors"""
            # Base age-based potential
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
            
            # Apply league coefficient (better leagues = higher potential)
            league_bonus = (league_coeff - 0.8) * 2  # Scale league difference
            
            # Apply versatility bonus (versatile players have higher potential)
            versatility_bonus = (versatility_factor - 1.0) * 3
            
            # Calculate final uplift
            total_uplift = base_uplift + league_bonus + versatility_bonus + np.random.normal(0, variance)
            
            # Ensure PA is at least CA and capped at 20
            return min(20, max(ca, ca + total_uplift))
        
        # Calculate PA with enhanced factors
        df_stats["PA"] = df_stats.apply(
            lambda x: compute_PA(
                x["CA"], 
                x["age"], 
                get_league_coefficient(x.get('competition_id', 0)),
                x["versatility_factor"]
            ), 
            axis=1
        )
        
        # Add age column (simplified - you'd get this from player data)
        df_stats["age"] = np.random.randint(18, 35, len(df_stats))
        attr_pbar.update(1)
        
        # Save comprehensive attributes to DB
        print("Saving attributes to database...")
        cur.execute(f"DROP TABLE IF EXISTS {ATTR_TABLE}")
        attr_pbar.update(1)
        
        # Close attribute progress bar
        attr_pbar.close()
        
        # Select all attribute columns
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

        conn.commit()
        conn.close()
        print(f"✅ Comprehensive database created at {DB_PATH}")
        print(f"📊 {len(df_stats)} players with detailed attributes")
        print(f"🏆 Multiple competitions and seasons included")
        
    except Exception as e:
        print(f"❌ Error in attribute calculation: {e}")
        conn.rollback()
        conn.close()
        print("Database transaction rolled back")
        
else:
    print("❌ No data to process")
    conn.close()
