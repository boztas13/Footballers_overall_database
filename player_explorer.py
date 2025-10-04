import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

def search_players(search_term="", limit=20):
    """Search for players by name"""
    conn = sqlite3.connect("data/statsbomb.db")
    
    query = """
    SELECT pa.player_name, pa.CA, pa.PA, pa.passing, pa.shooting, pa.dribbling, 
           pa.pace, pa.tackling, pa.goalkeeping, ps.minutes_played, ps.goals_per90, ps.assists_per90
    FROM player_attributes pa
    LEFT JOIN player_stats ps ON pa.player_name = ps.player_name
    WHERE pa.player_name LIKE ?
    ORDER BY pa.CA DESC
    LIMIT ?
    """
    
    results = pd.read_sql(query, conn, params=[f"%{search_term}%", limit])
    conn.close()
    
    return results

def create_player_radar(player_name):
    """Create a radar chart for a specific player"""
    conn = sqlite3.connect("data/statsbomb.db")
    
    # Get player attributes
    query = """
    SELECT * FROM player_attributes WHERE player_name = ?
    """
    player_data = pd.read_sql(query, conn, params=[player_name])
    conn.close()
    
    if player_data.empty:
        print(f"❌ Player '{player_name}' not found!")
        return None
    
    # Select key attributes for radar
    radar_attrs = ['passing', 'shooting', 'dribbling', 'pace', 'stamina', 
                   'positioning', 'tackling', 'goalkeeping', 'vision', 'composure']
    
    values = [player_data[attr].iloc[0] for attr in radar_attrs]
    
    # Create radar chart
    angles = np.linspace(0, 2 * np.pi, len(radar_attrs), endpoint=False).tolist()
    values += values[:1]  # Complete the circle
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    ax.plot(angles, values, 'o-', linewidth=3, label=player_name, color='blue')
    ax.fill(angles, values, alpha=0.25, color='blue')
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(radar_attrs)
    ax.set_ylim(0, 20)
    ax.set_title(f'{player_name} - Player Attributes', size=16, fontweight='bold', pad=20)
    ax.grid(True)
    
    # Add value labels
    for angle, value in zip(angles[:-1], values[:-1]):
        ax.text(angle, value + 0.5, f'{value:.1f}', ha='center', va='center', 
                fontweight='bold', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(f'data/{player_name.replace(" ", "_")}_radar.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return player_data.iloc[0]

def compare_players(player1_name, player2_name):
    """Compare two players side by side"""
    conn = sqlite3.connect("data/statsbomb.db")
    
    # Get both players' data
    query = """
    SELECT * FROM player_attributes WHERE player_name IN (?, ?)
    """
    players_data = pd.read_sql(query, conn, params=[player1_name, player2_name])
    conn.close()
    
    if len(players_data) != 2:
        print(f"❌ Could not find both players. Found {len(players_data)} players.")
        return
    
    # Create comparison chart
    radar_attrs = ['passing', 'shooting', 'dribbling', 'pace', 'stamina', 
                   'positioning', 'tackling', 'goalkeeping', 'vision', 'composure']
    
    fig, ax = plt.subplots(figsize=(12, 10), subplot_kw=dict(projection='polar'))
    
    colors = ['blue', 'red']
    for i, (_, player) in enumerate(players_data.iterrows()):
        values = [player[attr] for attr in radar_attrs]
        values += values[:1]  # Complete the circle
        angles = np.linspace(0, 2 * np.pi, len(radar_attrs), endpoint=False).tolist()
        angles += angles[:1]
        
        ax.plot(angles, values, 'o-', linewidth=3, label=player['player_name'], color=colors[i])
        ax.fill(angles, values, alpha=0.2, color=colors[i])
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(radar_attrs)
    ax.set_ylim(0, 20)
    ax.set_title(f'{player1_name} vs {player2_name} - Player Comparison', 
                size=16, fontweight='bold', pad=20)
    ax.grid(True)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
    
    plt.tight_layout()
    plt.savefig(f'data/{player1_name.replace(" ", "_")}_vs_{player2_name.replace(" ", "_")}_comparison.png', 
                dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print comparison table
    print(f"\n🔍 PLAYER COMPARISON: {player1_name} vs {player2_name}")
    print("="*80)
    print(f"{'Attribute':<15} {player1_name[:20]:<20} {player2_name[:20]:<20} {'Winner':<10}")
    print("-"*80)
    
    for attr in radar_attrs:
        val1 = players_data.iloc[0][attr]
        val2 = players_data.iloc[1][attr]
        winner = player1_name if val1 > val2 else player2_name if val2 > val1 else "Tie"
        print(f"{attr.capitalize():<15} {val1:<20.1f} {val2:<20.1f} {winner:<10}")

def show_player_details(player_name):
    """Show detailed information about a player"""
    conn = sqlite3.connect("data/statsbomb.db")
    
    # Get player attributes
    attr_query = """
    SELECT * FROM player_attributes WHERE player_name = ?
    """
    player_attrs = pd.read_sql(attr_query, conn, params=[player_name])
    
    # Get player stats
    stats_query = """
    SELECT ps.*, p.player_name 
    FROM player_stats ps 
    JOIN players p ON ps.player_id = p.player_id
    WHERE p.player_name = ?
    """
    player_stats = pd.read_sql(stats_query, conn, params=[player_name])
    
    conn.close()
    
    if player_attrs.empty:
        print(f"❌ Player '{player_name}' not found!")
        return
    
    print(f"\n👤 PLAYER PROFILE: {player_name}")
    print("="*60)
    
    # Basic info
    player = player_attrs.iloc[0]
    print(f"Current Ability (CA): {player['CA']:.1f}")
    print(f"Potential Ability (PA): {player['PA']:.1f}")
    print(f"Position-specific CAs:")
    print(f"  • Goalkeeper: {player['CA_GK']:.1f}")
    print(f"  • Defender: {player['CA_DEF']:.1f}")
    print(f"  • Midfielder: {player['CA_MID']:.1f}")
    print(f"  • Forward: {player['CA_FWD']:.1f}")
    
    # Technical attributes
    print(f"\n⚽ TECHNICAL ATTRIBUTES:")
    tech_attrs = ['passing', 'shooting', 'dribbling', 'first_touch', 'crossing', 'finishing', 'long_shots']
    for attr in tech_attrs:
        print(f"  • {attr.capitalize()}: {player[attr]:.1f}")
    
    # Physical attributes
    print(f"\n💪 PHYSICAL ATTRIBUTES:")
    phys_attrs = ['pace', 'acceleration', 'stamina', 'strength', 'jumping_reach']
    for attr in phys_attrs:
        print(f"  • {attr.capitalize()}: {player[attr]:.1f}")
    
    # Mental attributes
    print(f"\n🧠 MENTAL ATTRIBUTES:")
    mental_attrs = ['positioning', 'vision', 'composure', 'concentration', 'decisions', 'leadership']
    for attr in mental_attrs:
        print(f"  • {attr.capitalize()}: {player[attr]:.1f}")
    
    # Defensive attributes
    print(f"\n🛡️ DEFENSIVE ATTRIBUTES:")
    def_attrs = ['tackling', 'marking', 'heading']
    for attr in def_attrs:
        print(f"  • {attr.capitalize()}: {player[attr]:.1f}")
    
    # Goalkeeping attributes
    print(f"\n🥅 GOALKEEPING ATTRIBUTES:")
    gk_attrs = ['goalkeeping', 'reflexes', 'handling', 'kicking']
    for attr in gk_attrs:
        print(f"  • {attr.capitalize()}: {player[attr]:.1f}")
    
    # Performance stats if available
    if not player_stats.empty:
        stats = player_stats.iloc[0]
        print(f"\n📊 PERFORMANCE STATISTICS:")
        print(f"  • Minutes Played: {stats['minutes_played']:,}")
        print(f"  • Matches Played: {stats['matches_played']}")
        print(f"  • Goals per 90: {stats['goals_per90']:.2f}")
        print(f"  • Assists per 90: {stats['assists_per90']:.2f}")
        print(f"  • Pass Accuracy: {stats['pass_accuracy']:.1f}%")
        print(f"  • Shots per 90: {stats['shots_per90']:.2f}")
        print(f"  • Tackles per 90: {stats['tackles_per90']:.2f}")

def interactive_explorer():
    """Interactive player explorer"""
    print("🔍 FOOTBALL SCOUT - PLAYER EXPLORER")
    print("="*50)
    
    while True:
        print(f"\n📋 OPTIONS:")
        print("1. Search players")
        print("2. View player details")
        print("3. Create player radar chart")
        print("4. Compare two players")
        print("5. Exit")
        
        choice = input(f"\n🎯 Enter your choice (1-5): ").strip()
        
        if choice == "1":
            search_term = input("🔍 Enter player name to search: ").strip()
            results = search_players(search_term, 10)
            if not results.empty:
                print(f"\n📋 SEARCH RESULTS for '{search_term}':")
                print("-"*80)
                for i, (_, player) in enumerate(results.iterrows(), 1):
                    print(f"{i}. {player['player_name']} (CA: {player['CA']:.1f}, PA: {player['PA']:.1f})")
            else:
                print(f"❌ No players found matching '{search_term}'")
        
        elif choice == "2":
            player_name = input("👤 Enter player name: ").strip()
            show_player_details(player_name)
        
        elif choice == "3":
            player_name = input("📊 Enter player name for radar chart: ").strip()
            create_player_radar(player_name)
        
        elif choice == "4":
            player1 = input("👤 Enter first player name: ").strip()
            player2 = input("👤 Enter second player name: ").strip()
            compare_players(player1, player2)
        
        elif choice == "5":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    interactive_explorer()
