import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style
plt.style.use('default')
sns.set_palette("Set2")

def quick_database_overview():
    """Quick overview of the database contents"""
    conn = sqlite3.connect("data/statsbomb.db")
    
    print("🔍 QUICK DATABASE OVERVIEW")
    print("="*50)
    
    # Check what tables exist
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"📊 Tables in database: {[table[0] for table in tables]}")
    
    # Check player counts
    for table in tables:
        table_name = table[0]
        count = pd.read_sql(f"SELECT COUNT(*) as count FROM {table_name}", conn)['count'].iloc[0]
        print(f"   • {table_name}: {count:,} records")
    
    # Sample data from each table
    print(f"\n📋 SAMPLE DATA:")
    for table in tables:
        table_name = table[0]
        sample = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 3", conn)
        print(f"\n{table_name.upper()} (first 3 rows):")
        print(sample.to_string(index=False))
    
    conn.close()

def plot_simple_attributes():
    """Simple attribute visualization"""
    conn = sqlite3.connect("data/statsbomb.db")
    
    # Load attributes
    df = pd.read_sql("SELECT * FROM player_attributes ORDER BY CA DESC LIMIT 50", conn)
    conn.close()
    
    if df.empty:
        print("❌ No player attributes found!")
        return
    
    print(f"📊 Analyzing top {len(df)} players...")
    
    # Create subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Top 50 Players - Attribute Analysis', fontsize=16, fontweight='bold')
    
    # 1. CA vs PA scatter
    axes[0,0].scatter(df['CA'], df['PA'], alpha=0.7, s=50)
    axes[0,0].set_xlabel('Current Ability (CA)')
    axes[0,0].set_ylabel('Potential Ability (PA)')
    axes[0,0].set_title('CA vs PA (Top 50 Players)')
    axes[0,0].grid(True, alpha=0.3)
    
    # Add diagonal line
    max_val = max(df['CA'].max(), df['PA'].max())
    axes[0,0].plot([0, max_val], [0, max_val], 'r--', alpha=0.5)
    
    # 2. Position-specific CA comparison
    pos_cols = ['CA_GK', 'CA_DEF', 'CA_MID', 'CA_FWD']
    pos_means = [df[col].mean() for col in pos_cols]
    pos_labels = ['GK', 'DEF', 'MID', 'FWD']
    
    bars = axes[0,1].bar(pos_labels, pos_means, color=['gold', 'lightblue', 'lightgreen', 'orange'])
    axes[0,1].set_ylabel('Average CA')
    axes[0,1].set_title('Average CA by Position')
    axes[0,1].grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, mean in zip(bars, pos_means):
        axes[0,1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                      f'{mean:.1f}', ha='center', va='bottom', fontweight='bold')
    
    # 3. Top technical attributes
    tech_attrs = ['passing', 'shooting', 'dribbling', 'first_touch', 'crossing']
    tech_means = [df[attr].mean() for attr in tech_attrs]
    
    bars = axes[1,0].bar(tech_attrs, tech_means, color='skyblue')
    axes[1,0].set_ylabel('Average Rating')
    axes[1,0].set_title('Technical Attributes (Top 50)')
    axes[1,0].tick_params(axis='x', rotation=45)
    axes[1,0].grid(True, alpha=0.3)
    
    # Add value labels
    for bar, mean in zip(bars, tech_means):
        axes[1,0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                      f'{mean:.1f}', ha='center', va='bottom', fontweight='bold')
    
    # 4. Physical attributes
    phys_attrs = ['pace', 'acceleration', 'stamina', 'strength', 'jumping_reach']
    phys_means = [df[attr].mean() for attr in phys_attrs]
    
    bars = axes[1,1].bar(phys_attrs, phys_means, color='lightcoral')
    axes[1,1].set_ylabel('Average Rating')
    axes[1,1].set_title('Physical Attributes (Top 50)')
    axes[1,1].tick_params(axis='x', rotation=45)
    axes[1,1].grid(True, alpha=0.3)
    
    # Add value labels
    for bar, mean in zip(bars, phys_means):
        axes[1,1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                      f'{mean:.1f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('data/quick_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def show_top_players(n=10):
    """Show top N players by different metrics"""
    conn = sqlite3.connect("data/statsbomb.db")
    
    # Get top players by CA
    top_ca = pd.read_sql(f"""
        SELECT player_name, CA, PA, passing, shooting, dribbling, pace, tackling
        FROM player_attributes 
        ORDER BY CA DESC 
        LIMIT {n}
    """, conn)
    
    print(f"\n🏆 TOP {n} PLAYERS BY CURRENT ABILITY (CA):")
    print("="*80)
    print(f"{'Rank':<4} {'Player Name':<25} {'CA':<6} {'PA':<6} {'Pass':<6} {'Shoot':<6} {'Drib':<6} {'Pace':<6} {'Tack':<6}")
    print("-"*80)
    
    for i, (_, player) in enumerate(top_ca.iterrows(), 1):
        print(f"{i:<4} {player['player_name'][:24]:<25} {player['CA']:<6.1f} {player['PA']:<6.1f} "
              f"{player['passing']:<6.1f} {player['shooting']:<6.1f} {player['dribbling']:<6.1f} "
              f"{player['pace']:<6.1f} {player['tackling']:<6.1f}")
    
    # Get top players by PA
    top_pa = pd.read_sql(f"""
        SELECT player_name, CA, PA
        FROM player_attributes 
        ORDER BY PA DESC 
        LIMIT {n}
    """, conn)
    
    print(f"\n🚀 TOP {n} PLAYERS BY POTENTIAL ABILITY (PA):")
    print("="*60)
    print(f"{'Rank':<4} {'Player Name':<30} {'CA':<6} {'PA':<6}")
    print("-"*60)
    
    for i, (_, player) in enumerate(top_pa.iterrows(), 1):
        print(f"{i:<4} {player['player_name'][:29]:<30} {player['CA']:<6.1f} {player['PA']:<6.1f}")
    
    conn.close()

def analyze_performance_stats():
    """Analyze performance statistics"""
    conn = sqlite3.connect("data/statsbomb.db")
    
    # Get performance stats
    stats = pd.read_sql("""
        SELECT ps.*, p.player_name 
        FROM player_stats ps 
        JOIN players p ON ps.player_id = p.player_id
        WHERE ps.minutes_played >= 500
        ORDER BY ps.goals_per90 DESC
        LIMIT 20
    """, conn)
    
    if stats.empty:
        print("❌ No performance stats found!")
        conn.close()
        return
    
    print(f"\n⚽ TOP 20 GOAL SCORERS (per 90 minutes):")
    print("="*90)
    print(f"{'Rank':<4} {'Player Name':<25} {'Goals/90':<8} {'Assists/90':<10} {'Pass%':<6} {'Minutes':<8}")
    print("-"*90)
    
    for i, (_, player) in enumerate(stats.iterrows(), 1):
        print(f"{i:<4} {player['player_name'][:24]:<25} {player['goals_per90']:<8.2f} "
              f"{player['assists_per90']:<10.2f} {player['pass_accuracy']:<6.1f} {player['minutes_played']:<8}")
    
    # Top assist leaders
    assist_stats = pd.read_sql("""
        SELECT ps.*, p.player_name 
        FROM player_stats ps 
        JOIN players p ON ps.player_id = p.player_id
        WHERE ps.minutes_played >= 500
        ORDER BY ps.assists_per90 DESC
        LIMIT 10
    """, conn)
    
    print(f"\n🎯 TOP 10 ASSIST LEADERS (per 90 minutes):")
    print("="*70)
    print(f"{'Rank':<4} {'Player Name':<25} {'Assists/90':<10} {'Key Passes/90':<12} {'Minutes':<8}")
    print("-"*70)
    
    for i, (_, player) in enumerate(assist_stats.iterrows(), 1):
        print(f"{i:<4} {player['player_name'][:24]:<25} {player['assists_per90']:<10.2f} "
              f"{player['key_passes_per90']:<12.2f} {player['minutes_played']:<8}")
    
    conn.close()

def main():
    """Main function for quick analysis"""
    print("🚀 FOOTBALL SCOUT - QUICK ANALYSIS")
    print("="*50)
    
    try:
        # Quick database overview
        quick_database_overview()
        
        # Show top players
        show_top_players(10)
        
        # Analyze performance
        analyze_performance_stats()
        
        # Create simple plots
        plot_simple_attributes()
        
        print(f"\n✅ Quick analysis completed!")
        print(f"📁 Visualization saved as 'data/quick_analysis.png'")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
