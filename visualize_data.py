import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.patches import Circle
import warnings
warnings.filterwarnings('ignore')

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Database connection
DB_PATH = "data/statsbomb.db"

def load_data():
    """Load player attributes and stats from database"""
    conn = sqlite3.connect(DB_PATH)
    
    # Load player attributes
    attributes_df = pd.read_sql("""
        SELECT * FROM player_attributes 
        ORDER BY CA DESC
    """, conn)
    
    # Load player stats
    stats_df = pd.read_sql("""
        SELECT ps.*, p.player_name 
        FROM player_stats ps 
        JOIN players p ON ps.player_id = p.player_id
        WHERE ps.minutes_played >= 500
        ORDER BY ps.minutes_played DESC
    """, conn)
    
    conn.close()
    
    return attributes_df, stats_df

def plot_attribute_distributions(attributes_df):
    """Plot distributions of all attributes"""
    print("📊 Creating attribute distribution plots...")
    
    # Technical attributes
    tech_attrs = ['passing', 'shooting', 'dribbling', 'first_touch', 'crossing', 'finishing', 'long_shots']
    # Physical attributes  
    phys_attrs = ['pace', 'acceleration', 'stamina', 'strength', 'jumping_reach']
    # Mental attributes
    mental_attrs = ['positioning', 'vision', 'composure', 'concentration', 'decisions', 'leadership']
    # Defensive attributes
    def_attrs = ['tackling', 'marking', 'heading']
    # Goalkeeping attributes
    gk_attrs = ['goalkeeping', 'reflexes', 'handling', 'kicking']
    
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle('Player Attribute Distributions', fontsize=20, fontweight='bold')
    
    # Technical attributes
    axes[0,0].hist([attributes_df[attr].dropna() for attr in tech_attrs], 
                   bins=20, alpha=0.7, label=tech_attrs)
    axes[0,0].set_title('Technical Attributes', fontsize=14, fontweight='bold')
    axes[0,0].set_xlabel('Attribute Rating (1-20)')
    axes[0,0].set_ylabel('Number of Players')
    axes[0,0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    axes[0,0].grid(True, alpha=0.3)
    
    # Physical attributes
    axes[0,1].hist([attributes_df[attr].dropna() for attr in phys_attrs], 
                  bins=20, alpha=0.7, label=phys_attrs)
    axes[0,1].set_title('Physical Attributes', fontsize=14, fontweight='bold')
    axes[0,1].set_xlabel('Attribute Rating (1-20)')
    axes[0,1].set_ylabel('Number of Players')
    axes[0,1].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    axes[0,1].grid(True, alpha=0.3)
    
    # Mental attributes
    axes[1,0].hist([attributes_df[attr].dropna() for attr in mental_attrs], 
                  bins=20, alpha=0.7, label=mental_attrs)
    axes[1,0].set_title('Mental Attributes', fontsize=14, fontweight='bold')
    axes[1,0].set_xlabel('Attribute Rating (1-20)')
    axes[1,0].set_ylabel('Number of Players')
    axes[1,0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    axes[1,0].grid(True, alpha=0.3)
    
    # Defensive + Goalkeeping attributes
    all_def_gk = def_attrs + gk_attrs
    axes[1,1].hist([attributes_df[attr].dropna() for attr in all_def_gk], 
                  bins=20, alpha=0.7, label=all_def_gk)
    axes[1,1].set_title('Defensive & Goalkeeping Attributes', fontsize=14, fontweight='bold')
    axes[1,1].set_xlabel('Attribute Rating (1-20)')
    axes[1,1].set_ylabel('Number of Players')
    axes[1,1].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    axes[1,1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('data/attribute_distributions.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_top_players(attributes_df, top_n=20):
    """Plot top players by different metrics"""
    print(f"🏆 Creating top {top_n} players visualization...")
    
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle(f'Top {top_n} Players Analysis', fontsize=20, fontweight='bold')
    
    # Top players by CA
    top_ca = attributes_df.nlargest(top_n, 'CA')
    axes[0,0].barh(range(len(top_ca)), top_ca['CA'], color='skyblue')
    axes[0,0].set_yticks(range(len(top_ca)))
    axes[0,0].set_yticklabels([f"{name[:15]}..." if len(name) > 15 else name 
                              for name in top_ca['player_name']], fontsize=8)
    axes[0,0].set_xlabel('Current Ability (CA)')
    axes[0,0].set_title(f'Top {top_n} Players by CA')
    axes[0,0].grid(True, alpha=0.3)
    
    # Top players by PA
    top_pa = attributes_df.nlargest(top_n, 'PA')
    axes[0,1].barh(range(len(top_pa)), top_pa['PA'], color='lightcoral')
    axes[0,1].set_yticks(range(len(top_pa)))
    axes[0,1].set_yticklabels([f"{name[:15]}..." if len(name) > 15 else name 
                              for name in top_pa['player_name']], fontsize=8)
    axes[0,1].set_xlabel('Potential Ability (PA)')
    axes[0,1].set_title(f'Top {top_n} Players by PA')
    axes[0,1].grid(True, alpha=0.3)
    
    # Position-specific CA comparison
    pos_ca_cols = ['CA_GK', 'CA_DEF', 'CA_MID', 'CA_FWD']
    pos_means = [attributes_df[col].mean() for col in pos_ca_cols]
    pos_labels = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
    
    axes[1,0].bar(pos_labels, pos_means, color=['gold', 'lightblue', 'lightgreen', 'orange'])
    axes[1,0].set_ylabel('Average CA')
    axes[1,0].set_title('Average CA by Position')
    axes[1,0].grid(True, alpha=0.3)
    
    # CA vs PA scatter
    axes[1,1].scatter(attributes_df['CA'], attributes_df['PA'], alpha=0.6, s=30)
    axes[1,1].set_xlabel('Current Ability (CA)')
    axes[1,1].set_ylabel('Potential Ability (PA)')
    axes[1,1].set_title('CA vs PA Relationship')
    axes[1,1].grid(True, alpha=0.3)
    
    # Add diagonal line for reference
    max_val = max(attributes_df['CA'].max(), attributes_df['PA'].max())
    axes[1,1].plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label='CA = PA')
    axes[1,1].legend()
    
    plt.tight_layout()
    plt.savefig('data/top_players_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_player_radar(player_name, attributes_df):
    """Create a radar chart for a specific player"""
    print(f"🎯 Creating radar chart for {player_name}...")
    
    player_data = attributes_df[attributes_df['player_name'] == player_name]
    if player_data.empty:
        print(f"Player '{player_name}' not found in database")
        return
    
    # Select key attributes for radar chart
    radar_attrs = ['passing', 'shooting', 'dribbling', 'pace', 'stamina', 'positioning', 
                   'tackling', 'goalkeeping']
    
    values = [player_data[attr].iloc[0] for attr in radar_attrs]
    
    # Create radar chart
    angles = np.linspace(0, 2 * np.pi, len(radar_attrs), endpoint=False).tolist()
    values += values[:1]  # Complete the circle
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    ax.plot(angles, values, 'o-', linewidth=2, label=player_name)
    ax.fill(angles, values, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(radar_attrs)
    ax.set_ylim(0, 20)
    ax.set_title(f'{player_name} - Attribute Radar Chart', size=16, fontweight='bold', pad=20)
    ax.grid(True)
    
    # Add value labels
    for angle, value in zip(angles[:-1], values[:-1]):
        ax.text(angle, value + 0.5, f'{value:.1f}', ha='center', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'data/{player_name.replace(" ", "_")}_radar.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_attribute_correlations(attributes_df):
    """Plot correlation matrix of attributes"""
    print("🔗 Creating attribute correlation matrix...")
    
    # Select numeric attributes for correlation
    numeric_attrs = attributes_df.select_dtypes(include=[np.number]).columns
    corr_matrix = attributes_df[numeric_attrs].corr()
    
    plt.figure(figsize=(16, 14))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='coolwarm', center=0,
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8}, fmt='.2f')
    plt.title('Attribute Correlation Matrix', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig('data/attribute_correlations.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_performance_stats(stats_df):
    """Plot performance statistics"""
    print("⚽ Creating performance statistics plots...")
    
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle('Player Performance Statistics', fontsize=20, fontweight='bold')
    
    # Goals per 90 vs xG per 90
    axes[0,0].scatter(stats_df['xG_per90'], stats_df['goals_per90'], alpha=0.6, s=30)
    axes[0,0].set_xlabel('Expected Goals per 90 (xG)')
    axes[0,0].set_ylabel('Goals per 90')
    axes[0,0].set_title('Goals vs xG per 90')
    axes[0,0].grid(True, alpha=0.3)
    
    # Add diagonal line
    max_val = max(stats_df['xG_per90'].max(), stats_df['goals_per90'].max())
    axes[0,0].plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label='xG = Goals')
    axes[0,0].legend()
    
    # Pass accuracy distribution
    axes[0,1].hist(stats_df['pass_accuracy'].dropna(), bins=30, alpha=0.7, color='lightblue')
    axes[0,1].set_xlabel('Pass Accuracy (%)')
    axes[0,1].set_ylabel('Number of Players')
    axes[0,1].set_title('Pass Accuracy Distribution')
    axes[0,1].grid(True, alpha=0.3)
    
    # Minutes played vs matches played
    axes[1,0].scatter(stats_df['matches_played'], stats_df['minutes_played'], alpha=0.6, s=30)
    axes[1,0].set_xlabel('Matches Played')
    axes[1,0].set_ylabel('Minutes Played')
    axes[1,0].set_title('Minutes vs Matches Played')
    axes[1,0].grid(True, alpha=0.3)
    
    # Top performers by different metrics
    top_goals = stats_df.nlargest(10, 'goals_per90')
    top_assists = stats_df.nlargest(10, 'assists_per90')
    
    x = np.arange(len(top_goals))
    width = 0.35
    
    axes[1,1].bar(x - width/2, top_goals['goals_per90'], width, label='Goals/90', alpha=0.8)
    axes[1,1].bar(x + width/2, top_assists['assists_per90'], width, label='Assists/90', alpha=0.8)
    axes[1,1].set_xlabel('Player Rank')
    axes[1,1].set_ylabel('Per 90 Stats')
    axes[1,1].set_title('Top 10 Goal Scorers vs Assist Leaders')
    axes[1,1].legend()
    axes[1,1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('data/performance_stats.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_summary_report(attributes_df, stats_df):
    """Create a summary report of the database"""
    print("📋 Creating summary report...")
    
    print("\n" + "="*60)
    print("📊 FOOTBALL SCOUT DATABASE SUMMARY REPORT")
    print("="*60)
    
    print(f"\n🏆 DATABASE OVERVIEW:")
    print(f"   • Total Players: {len(attributes_df):,}")
    print(f"   • Players with Stats: {len(stats_df):,}")
    print(f"   • Players with 500+ minutes: {len(stats_df):,}")
    
    print(f"\n⭐ TOP PLAYERS BY CA:")
    top_5_ca = attributes_df.nlargest(5, 'CA')[['player_name', 'CA', 'PA']]
    for _, player in top_5_ca.iterrows():
        print(f"   • {player['player_name']}: CA {player['CA']:.1f}, PA {player['PA']:.1f}")
    
    print(f"\n🚀 TOP PLAYERS BY PA:")
    top_5_pa = attributes_df.nlargest(5, 'PA')[['player_name', 'CA', 'PA']]
    for _, player in top_5_pa.iterrows():
        print(f"   • {player['player_name']}: CA {player['CA']:.1f}, PA {player['PA']:.1f}")
    
    print(f"\n⚽ PERFORMANCE STATS:")
    print(f"   • Average Goals/90: {stats_df['goals_per90'].mean():.2f}")
    print(f"   • Average Assists/90: {stats_df['assists_per90'].mean():.2f}")
    print(f"   • Average Pass Accuracy: {stats_df['pass_accuracy'].mean():.1f}%")
    print(f"   • Total Minutes: {stats_df['minutes_played'].sum():,}")
    
    print(f"\n📈 ATTRIBUTE RANGES:")
    key_attrs = ['passing', 'shooting', 'dribbling', 'pace', 'tackling', 'goalkeeping']
    for attr in key_attrs:
        if attr in attributes_df.columns:
            min_val = attributes_df[attr].min()
            max_val = attributes_df[attr].max()
            avg_val = attributes_df[attr].mean()
            print(f"   • {attr.capitalize()}: {min_val:.1f} - {max_val:.1f} (avg: {avg_val:.1f})")
    
    print("\n" + "="*60)

def main():
    """Main visualization function"""
    print("🎨 Starting Football Scout Data Visualization...")
    print("="*60)
    
    try:
        # Load data
        print("📂 Loading data from database...")
        attributes_df, stats_df = load_data()
        
        if attributes_df.empty:
            print("❌ No player attributes found in database!")
            return
        
        if stats_df.empty:
            print("⚠️  No player stats found in database!")
            return
        
        # Create visualizations
        plot_attribute_distributions(attributes_df)
        plot_top_players(attributes_df)
        plot_attribute_correlations(attributes_df)
        plot_performance_stats(stats_df)
        
        # Create summary report
        create_summary_report(attributes_df, stats_df)
        
        # Interactive player radar (example)
        if len(attributes_df) > 0:
            # Get a random player for radar chart example
            random_player = attributes_df.sample(1)['player_name'].iloc[0]
            plot_player_radar(random_player, attributes_df)
        
        print("\n✅ All visualizations completed!")
        print("📁 Images saved in the 'data/' directory")
        
    except Exception as e:
        print(f"❌ Error during visualization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
