import sqlite3
import pandas as pd
from statsbombpy import sb
import os
from tqdm import tqdm

# ----------------------------
# CONFIG
# ----------------------------
DB_PATH = "data/statsbomb.db"
CHECKPOINT_INTERVAL = 50
checkpoint_file = "data/checkpoint_matches.txt"
processed_matches_file = "data/processed_players.csv"

# ----------------------------
# Load match list
# ----------------------------
print("Loading match list...")
with open("data/matches_to_process.txt", "r") as f:
    all_matches = [int(line.strip()) for line in f]

print(f"Found {len(all_matches)} matches to process")

# ----------------------------
# Connect to SQLite
# ----------------------------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ----------------------------
# CHECKPOINT SYSTEM
# ----------------------------
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

# ----------------------------
# PROCESS MATCH EVENTS
# ----------------------------
matches_to_process = [m for m in all_matches if str(m) not in processed_matches]
print(f"Processing {len(matches_to_process)} new matches...")

pbar = tqdm(total=len(matches_to_process), desc="Processing matches", unit="match")

for i, match_id in enumerate(matches_to_process):
    pbar.set_description(f"Match {match_id}")
    
    try:
        events = sb.events(match_id=match_id)
        
        if len(events) == 0:
            processed_matches.add(str(match_id))
            pbar.update(1)
            continue
            
        # Get match info for competition/season
        match_info = cur.execute(
            "SELECT competition_id, season_id FROM matches WHERE match_id = ?", 
            (match_id,)
        ).fetchone()
        
        if not match_info:
            processed_matches.add(str(match_id))
            pbar.update(1)
            continue
            
        comp_id, season_id = match_info

        # Compute per-player stats
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
                "assists": len(goals),
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
            # Save processed matches list
            with open(checkpoint_file, 'w') as f:
                for match in processed_matches:
                    f.write(f"{match}\n")
            
            # Save current player data
            if all_players:
                df_current = pd.concat(all_players, ignore_index=True)
                df_current.to_csv(processed_matches_file, index=False)
                pbar.set_postfix({"Saved": f"{len(df_current)} records"})
            
    except Exception as e:
        pbar.set_postfix({"Error": f"{str(e)[:30]}..."})
        processed_matches.add(str(match_id))
        continue
    
    pbar.update(1)

pbar.close()

# Final save of all data
if all_players:
    df_players = pd.concat(all_players, ignore_index=True)
    print(f"\nProcessed {len(df_players)} player-match records")
    
    # Save final checkpoint
    with open(checkpoint_file, 'w') as f:
        for match in processed_matches:
            f.write(f"{match}\n")
    
    df_players.to_csv(processed_matches_file, index=False)
    print(f"✅ Data saved to {processed_matches_file}")
else:
    print("No player data found")

conn.close()
