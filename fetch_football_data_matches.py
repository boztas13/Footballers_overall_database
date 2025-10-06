import os
import sqlite3
import requests
from datetime import datetime
import logging
from tqdm import tqdm
import time
import json
from typing import Dict, Any, List, Set

# Progress tracking
PROGRESS_FILE = "data/fetch_progress.json"

def load_progress() -> tuple[Set[int], List[Dict[str, str]]]:
    """Load progress from file"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get('completed_matches', [])), data.get('skipped_seasons', [])
    return set(), []

def save_progress(completed_matches: Set[int]):
    """Save progress to file"""
    with open(PROGRESS_FILE, 'r') as f:
        data = json.load(f)
    data['completed_matches'] = list(completed_matches)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def should_skip_season(season_year: str, competition_code: str, skipped_seasons: List[Dict[str, str]]) -> bool:
    """Check if this season should be skipped"""
    return any(
        skip['competition_code'] == competition_code and skip['year'] == season_year
        for skip in skipped_seasons
    )

def make_request(url: str, headers: Dict[str, str], delay: int = 6) -> Dict[str, Any]:
    """Make a request to the API with rate limiting handling"""
    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', delay))
            logging.warning(f"Rate limit hit. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            continue
        elif response.status_code == 200:
            time.sleep(delay)  # Wait 6 seconds between successful requests (10 requests per minute limit)
            return response.json()
        else:
            logging.error(f"Request failed: {response.status_code}")
            return {}


# Setup logging
logging.basicConfig(
    filename='data/fetch_football_data.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

DB_PATH = "data/football_data.db"
FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY', 'edab257cb26c4a0c87f18d5f629a17e6')

try:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
except Exception as e:
    logging.error(f"Error connecting to database: {e}")
    raise

# Fetch competitions
# Specify major competitions we want to fetch
TIER_ONE_COMPETITIONS = [
    'PL',    # Premier League
    'BL1',   # Bundesliga
    'SA',    # Serie A
    'PD',    # La Liga
    'FL1',   # Ligue 1
    'DED',   # Eredivisie
    'PPL',   # Primeira Liga
    'BSA',   # Brasileiro Serie A
    'CL',    # UEFA Champions League
    'EC'     # European Championship
]

url = 'https://api.football-data.org/v4/competitions'
headers = {'X-Auth-Token': FOOTBALL_DATA_API_KEY}
try:
    response_data = make_request(url, headers)
    all_competitions = response_data.get('competitions', [])
    # Print all available competitions and their codes
    print("\nAvailable competitions:")
    for comp in all_competitions:
        print(f"Name: {comp.get('name')}, Code: {comp.get('code')}, Area: {comp.get('area', {}).get('name')}")

    # Filter for tier one competitions only
    competitions = [comp for comp in all_competitions if comp.get('code') in TIER_ONE_COMPETITIONS]
    print(f"\nFiltered competitions to fetch:")
    for comp in competitions:
        print(f"Name: {comp.get('name')}, Code: {comp.get('code')}, Area: {comp.get('area', {}).get('name')}")
    
    logging.info(f"Filtered {len(competitions)} tier one competitions from {len(all_competitions)} total competitions")
except Exception as e:
    logging.error(f"Error fetching competitions: {e}")
    competitions = []

# Insert competitions
for comp in competitions:
    try:
        comp_id = comp.get('id')
        name = comp.get('name')
        area_name = comp.get('area', {}).get('name', '')
        code = comp.get('code', '')
        type_ = comp.get('type', '')
        plan = comp.get('plan', '')
        cur.execute("""
            INSERT OR IGNORE INTO competitions (competition_id, name, area_name, code, type, plan)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (comp_id, name, area_name, code, type_, plan))
        logging.info(f"Inserted competition: {name} ({comp_id})")
    except Exception as e:
        logging.error(f"Error inserting competition {comp.get('name')}: {e}")

conn.commit()

# Load progress and skipped seasons
completed_matches, skipped_seasons = load_progress()
print(f"\nLoaded {len(completed_matches)} completed matches and {len(skipped_seasons)} skipped seasons")

# Fetch and insert last 3 years of seasons and matches
print("\nProcessing competitions...")
for comp in tqdm(competitions, desc="Fetching competitions"):
    comp_id = comp.get('id')
    # Fetch competition details to get seasons
    comp_url = f'https://api.football-data.org/v4/competitions/{comp_id}'
    try:
        comp_details = make_request(comp_url, headers)
        seasons = comp_details.get('seasons', [])
    except Exception as e:
        logging.error(f"Error fetching competition details for {comp_id}: {e}")
        seasons = []
    seasons_pbar = tqdm(seasons, desc=f"Processing seasons for {comp.get('name')}", leave=False)
    for season in seasons_pbar:
        try:
            season_id = season.get('id', 0)
            start_date = season.get('startDate', '')
            end_date = season.get('endDate', '')
            year = start_date[:4]
            
            # Check if we should skip this season
            if should_skip_season(year, comp.get('code'), skipped_seasons):
                logging.info(f"Skipping season {year} for competition {comp.get('name')} ({comp.get('code')})")
                continue
                
            current_matchday = season.get('currentMatchday', None)
            winner = season.get('winner', {}).get('name', '') if season.get('winner') else None
            cur.execute("""
                INSERT OR IGNORE INTO seasons (season_id, competition_id, start_date, end_date, current_matchday, winner)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (season_id, comp_id, start_date, end_date, current_matchday, winner))
            logging.info(f"Inserted season {season_id} for competition {comp_id}")
        except Exception as e:
            logging.error(f"Error inserting season {season_id} for competition {comp_id}: {e}")
        # Fetch matches for this season
        year = start_date[:4]
        matches_url = f'https://api.football-data.org/v4/competitions/{comp_id}/matches?season={year}'
        try:
            matches_data = make_request(matches_url, headers)
            matches = matches_data.get('matches', [])
        except Exception as e:
            logging.error(f"Error fetching matches for competition {comp_id} season {season_id}: {e}")
            matches = []
        matches_pbar = tqdm(matches, desc=f"Processing matches for {comp.get('name')} {year}", leave=False)
        for m in matches_pbar:
            try:
                match_id = m.get('id')

                # Skip if we've already processed this match
                if match_id in completed_matches:
                    logging.info(f"Skipping already processed match {match_id}")
                    continue

                utc_date = m.get('utcDate', '')
                status = m.get('status', '')
                matchday = m.get('matchday', None)
                stage = m.get('stage', '')
                group_name = m.get('group', '')
                home_team = m.get('homeTeam', {}).get('name', '')
                away_team = m.get('awayTeam', {}).get('name', '')
                home_score = m.get('score', {}).get('fullTime', {}).get('home', 0)
                away_score = m.get('score', {}).get('fullTime', {}).get('away', 0)
                cur.execute("""
                    INSERT OR IGNORE INTO matches (
                        match_id, competition_id, season_id, utc_date, status, matchday, stage, group_name, home_team, away_team, home_score, away_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    match_id, comp_id, season_id, utc_date, status, matchday, stage, group_name, home_team, away_team, home_score, away_score
                ))
                logging.info(f"Inserted match {match_id} for competition {comp_id} season {season_id}")

                # Fetch detailed match information including scorers and stats
                try:
                    match_detail_url = f'https://api.football-data.org/v4/matches/{match_id}'
                    match_details = make_request(match_detail_url, headers)

                    if match_details:
                        logging.info(f"Match details response: {str(match_details)[:200]}...")  # Log first 200 chars

                        # Insert scorers
                        scorers = match_details.get('scorers', [])
                        logging.info(f"Found {len(scorers)} scorers")
                        for scorer in scorers:
                            try:
                                player = scorer.get('player', {})
                                team = scorer.get('team', {})
                                cur.execute("""
                                    INSERT OR IGNORE INTO scorers (
                                        match_id, team_id, player_name, minute, additional_minute, type
                                    ) VALUES (?, ?, ?, ?, ?, ?)
                                """, (
                                    match_id,
                                    team.get('id'),
                                    player.get('name'),
                                    scorer.get('minute'),
                                    scorer.get('extraTime'),
                                    scorer.get('type', 'REGULAR')
                                ))
                                logging.info(f"Inserted scorer: {player.get('name')} for match {match_id}")
                            except Exception as e:
                                logging.error(f"Error inserting scorer: {e}")

                        # Insert match statistics
                        for team in ['homeTeam', 'awayTeam']:
                            try:
                                stats = match_details.get('statistics', [])
                                team_stats = next((s for s in stats if s.get('team', {}).get('name') == match_details.get(team, {}).get('name')), {})

                                if team_stats:
                                    team_id = match_details.get(team, {}).get('id')
                                    stats_data = team_stats.get('statistics', {})
                                    logging.info(f"Found stats for team {team_id}: {str(stats_data)[:200]}...")

                                    cur.execute("""
                                        INSERT OR IGNORE INTO match_stats (
                                            match_id, team_id, shots, shots_on_goal, possession,
                                            passes, pass_accuracy, fouls, yellow_cards, red_cards,
                                            offsides, corners
                                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        match_id,
                                        team_id,
                                        next((item['value'] for item in stats_data if item['type'] == 'SHOT_ON_GOAL'), 0),
                                        next((item['value'] for item in stats_data if item['type'] == 'SHOT_ON_TARGET'), 0),
                                        next((item['value'] for item in stats_data if item['type'] == 'BALL_POSSESSION'), 0),
                                        next((item['value'] for item in stats_data if item['type'] == 'PASS'), 0),
                                        next((item['value'] for item in stats_data if item['type'] == 'PASS_ACCURACY'), 0),
                                        next((item['value'] for item in stats_data if item['type'] == 'FOUL'), 0),
                                        next((item['value'] for item in stats_data if item['type'] == 'YELLOW_CARD'), 0),
                                        next((item['value'] for item in stats_data if item['type'] == 'RED_CARD'), 0),
                                        next((item['value'] for item in stats_data if item['type'] == 'OFFSIDE'), 0),
                                        next((item['value'] for item in stats_data if item['type'] == 'CORNER_KICK'), 0)
                                    ))
                                    logging.info(f"Inserted match stats for team {team_id} in match {match_id}")
                                else:
                                    logging.warning(f"No stats found for {team} in match {match_id}")
                            except Exception as e:
                                logging.error(f"Error processing stats for {team} in match {match_id}: {e}")
                        # Mark match as completed and save progress
                        completed_matches.add(match_id)
                        save_progress(completed_matches)
                    else:
                        logging.error(f"Failed to get match details")
                        logging.warning("No data received from the API for this match")

                    # Add a small delay to avoid rate limiting
                    time.sleep(1)

                except Exception as e:
                    logging.error(f"Error inserting match {m.get('id')} for competition {comp_id} season {season_id}: {e}")
            except Exception as e:
                logging.error(f"Error processing match {m.get('id')}: {e}")

            # End of competition loop
            conn.commit()

# Close connection at the very end
conn.close()
logging.info("✅ Fetched and inserted last 3 years of Football-Data.org matches.")
print("✅ Fetched and inserted last 3 years of Football-Data.org matches.")
