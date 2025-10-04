import sqlite3
import os

# ----------------------------
# CONFIG
# ----------------------------
DB_PATH = "data/statsbomb.db"

os.makedirs("data", exist_ok=True)

# ----------------------------
# Connect to SQLite
# ----------------------------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ----------------------------
# CREATE TABLES
# ----------------------------
print("Creating database schema...")

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
conn.close()

print(f"✅ Database schema created successfully at {DB_PATH}")
