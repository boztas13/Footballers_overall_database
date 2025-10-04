# 🎨 Football Scout Data Visualization

This directory contains several scripts to visualize and analyze the player data from your StatsBomb database.

## 📊 Available Scripts

### 1. `quick_analysis.py` - Quick Database Overview
**Purpose**: Get a fast overview of your database and top players.

**Features**:
- Database table overview with record counts
- Top 10 players by Current Ability (CA)
- Top 10 players by Potential Ability (PA)  
- Top 20 goal scorers per 90 minutes
- Top 10 assist leaders per 90 minutes
- Simple attribute distribution charts

**Usage**:
```bash
python quick_analysis.py
```

### 2. `visualize_data.py` - Comprehensive Analysis
**Purpose**: Detailed analysis with multiple visualization types.

**Features**:
- Attribute distribution histograms
- Top players analysis with bar charts
- Attribute correlation heatmap
- Performance statistics plots
- Player radar charts
- Summary report with key statistics

**Usage**:
```bash
python visualize_data.py
```

### 3. `player_explorer.py` - Interactive Player Explorer
**Purpose**: Interactive tool to explore individual players.

**Features**:
- Search players by name
- View detailed player profiles
- Create radar charts for specific players
- Compare two players side-by-side
- Interactive menu system

**Usage**:
```bash
python player_explorer.py
```

## 🎯 What Each Script Shows

### Quick Analysis Output:
- **Database Overview**: Shows all tables and record counts
- **Top Players**: Lists best players by CA and PA
- **Performance Stats**: Goal scorers and assist leaders
- **Charts**: Simple bar charts and scatter plots

### Comprehensive Analysis Output:
- **Distribution Plots**: How attributes are distributed across all players
- **Correlation Matrix**: Which attributes are related to each other
- **Performance Analysis**: Goals vs xG, pass accuracy, etc.
- **Summary Report**: Key statistics about your database

### Interactive Explorer Features:
- **Player Search**: Find players by partial name matching
- **Player Profiles**: Detailed attribute breakdowns
- **Radar Charts**: Visual representation of player strengths
- **Player Comparison**: Side-by-side comparison of two players

## 📁 Output Files

All scripts save their visualizations to the `data/` directory:

- `data/quick_analysis.png` - Quick analysis charts
- `data/attribute_distributions.png` - Attribute distribution plots
- `data/top_players_analysis.png` - Top players analysis
- `data/attribute_correlations.png` - Correlation heatmap
- `data/performance_stats.png` - Performance statistics
- `data/[player_name]_radar.png` - Individual player radar charts
- `data/[player1]_vs_[player2]_comparison.png` - Player comparison charts

## 🚀 Getting Started

1. **Make sure your database exists**: Run `python map_stats_bomb_db.py` first to create the database
2. **Start with quick analysis**: `python quick_analysis.py` to get an overview
3. **Explore specific players**: `python player_explorer.py` for interactive exploration
4. **Deep dive analysis**: `python visualize_data.py` for comprehensive visualizations

## 📊 Understanding the Visualizations

### Attribute Ratings (1-20 scale):
- **1-5**: Poor
- **6-10**: Below Average  
- **11-15**: Average
- **16-20**: Excellent

### Key Metrics:
- **CA (Current Ability)**: Overall current skill level
- **PA (Potential Ability)**: Maximum potential skill level
- **Per 90 Stats**: Statistics normalized to 90-minute games
- **Pass Accuracy**: Percentage of successful passes

### Position-Specific CAs:
- **CA_GK**: Goalkeeper ability
- **CA_DEF**: Defender ability  
- **CA_MID**: Midfielder ability
- **CA_FWD**: Forward ability

## 🔧 Customization

You can modify the scripts to:
- Change the number of top players shown
- Adjust chart colors and styles
- Add new attribute combinations
- Filter players by specific criteria
- Export data to different formats

## 📈 Example Usage

```bash
# Quick overview
python quick_analysis.py

# Interactive player search
python player_explorer.py
# Then choose option 1 and search for "Messi"

# Comprehensive analysis
python visualize_data.py
```

## 🎨 Chart Types Explained

- **Bar Charts**: Compare values across categories
- **Scatter Plots**: Show relationships between two variables
- **Histograms**: Show distribution of single variables
- **Radar Charts**: Show multiple attributes for one player
- **Heatmaps**: Show correlations between many variables

Enjoy exploring your football data! ⚽📊
