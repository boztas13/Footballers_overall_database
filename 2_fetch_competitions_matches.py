import sqlite3
from statsbombpy import sb
from tqdm import tqdm

# ----------------------------
# CONFIG
# ----------------------------
DB_PATH = "data/statsbomb.db"

# Major competitions to fetch - Focus on latest seasons (2020-2024)
COMPETITIONS = [
    # Major European Leagues (Latest 3-4 seasons)
    {"id": 2, "name": "Premier League", "seasons": []},
    {"id": 49, "name": "La Liga", "seasons": []},
    {"id": 11, "name": "Serie A", "seasons": []},
    {"id": 9, "name": "Ligue 1", "seasons": []},
    {"id": 12, "name": "Bundesliga", "seasons": []},
    
    # UEFA Competitions (Latest 3-4 seasons)
    {"id": 37, "name": "UEFA Champions League", "seasons": []},
    {"id": 38, "name": "UEFA Europa League", "seasons": []},
    {"id": 55, "name": "UEFA Europa Conference League", "seasons": []},
    
    # International Competitions
    {"id": 43, "name": "FIFA World Cup", "seasons": []},
    {"id": 72, "name": "UEFA Nations League", "seasons": []},
    {"id": 50, "name": "UEFA Euro", "seasons": []},
    {"id": 44, "name": "Copa America", "seasons": []},
    {"id": 45, "name": "AFC Asian Cup", "seasons": []},
]

# ----------------------------
# Connect to SQLite
# ----------------------------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def get_latest_seasons(comp_id, max_seasons=4):
    """Get latest available seasons for a competition"""
    try:
        comps_df = sb.competitions()
        available_seasons = comps_df[comps_df.competition_id == comp_id]['season_id'].tolist()
        # Prioritize seasons from 2020 onwards (Season IDs 100+ are typically 2020+)
        recent_seasons = [s for s in available_seasons if s >= 100]
        if recent_seasons:
            return sorted(recent_seasons, reverse=True)[:max_seasons]
        else:
            return sorted(available_seasons, reverse=True)[:max_seasons]
    except Exception as e:
        print(f"  Error fetching seasons for comp {comp_id}: {e}")
        return []

# ----------------------------
# FETCH COMPETITIONS AND MATCHES
# ----------------------------
print("Detecting latest available seasons...")
for comp in COMPETITIONS:
    latest_seasons = get_latest_seasons(comp["id"])
    if latest_seasons:
        comp["seasons"] = latest_seasons
        print(f"  {comp['name']}: Found seasons {latest_seasons}")

all_matches = []

print("\nFetching competitions and matches...")
for comp in tqdm(COMPETITIONS, desc="Processing competitions"):
    comp_id = comp["id"]
    comp_name = comp["name"]
    
    for season_id in comp["seasons"]:
        try:
            # Get competition info
            comps_df = sb.competitions()
            comp_info = comps_df[(comps_df.competition_id == comp_id) & (comps_df.season_id == season_id)]
            
            if len(comp_info) > 0:
                season_name = comp_info["season_name"].iloc[0]
                
                # Insert competition
                cur.execute("""
                INSERT OR IGNORE INTO competitions (competition_id, competition_name, season_id, season_name)
                VALUES (?, ?, ?, ?)
                """, (comp_id, comp_name, season_id, season_name))
                
                # Get matches for this competition/season
                matches = sb.matches(competition_id=comp_id, season_id=season_id)
                
                if len(matches) > 0:
                    print(f"  Found {len(matches)} matches in {comp_name} {season_name}")
                    
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
                        
        except Exception as e:
            print(f"  Error processing {comp_name} season {season_id}: {e}")
            continue

conn.commit()

# Save match list for next script
with open("data/matches_to_process.txt", "w") as f:
    for match_id in all_matches:
        f.write(f"{match_id}\n")

conn.close()

print(f"\n✅ Fetched {len(all_matches)} matches from {len(COMPETITIONS)} competitions")
print(f"📝 Match list saved to data/matches_to_process.txt")

