import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Football Scout Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .player-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .stSelectbox > div > div {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_data
def load_database_info():
    """Load basic database information"""
    conn = sqlite3.connect("data/statsbomb.db")
    
    # Get table counts
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    table_counts = {}
    for table in tables:
        table_name = table[0]
        count = pd.read_sql(f"SELECT COUNT(*) as count FROM {table_name}", conn)['count'].iloc[0]
        table_counts[table_name] = count
    
    conn.close()
    return table_counts

@st.cache_data
def load_player_attributes(limit=None):
    """Load player attributes"""
    conn = sqlite3.connect("data/statsbomb.db")
    
    query = "SELECT * FROM player_attributes ORDER BY CA DESC"
    if limit:
        query += f" LIMIT {limit}"
    
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data
def load_player_stats(limit=None):
    """Load player stats"""
    conn = sqlite3.connect("data/statsbomb.db")
    
    query = """
    SELECT ps.*, p.player_name 
    FROM player_stats ps 
    JOIN players p ON ps.player_id = p.player_id
    WHERE ps.minutes_played >= 500
    ORDER BY ps.minutes_played DESC
    """
    if limit:
        query += f" LIMIT {limit}"
    
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data
def search_players(search_term, limit=50):
    """Search for players"""
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
    
    df = pd.read_sql(query, conn, params=[f"%{search_term}%", limit])
    conn.close()
    return df

def create_radar_chart(player_data, player_name):
    """Create radar chart for a player"""
    radar_attrs = ['passing', 'shooting', 'dribbling', 'pace', 'stamina', 
                   'positioning', 'tackling', 'goalkeeping', 'vision', 'composure']
    
    values = [player_data[attr] for attr in radar_attrs]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=radar_attrs,
        fill='toself',
        name=player_name,
        line_color='blue'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 20]
            )),
        showlegend=True,
        title=f"{player_name} - Player Attributes",
        height=500
    )
    
    return fig

def main():
    # Header
    st.markdown('<h1 class="main-header">⚽ Football Scout Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("🎯 Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["📊 Overview", "🔍 Player Search", "📈 Analytics", "🏆 Top Players", "⚽ Performance"]
    )
    
    # Load data
    with st.spinner("Loading database..."):
        db_info = load_database_info()
        attributes_df = load_player_attributes()
        stats_df = load_player_stats()
    
    # Overview Page
    if page == "📊 Overview":
        st.header("📊 Database Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Players",
                value=f"{db_info.get('player_attributes', 0):,}",
                delta=None
            )
        
        with col2:
            st.metric(
                label="Players with Stats",
                value=f"{db_info.get('player_stats', 0):,}",
                delta=None
            )
        
        with col3:
            st.metric(
                label="Total Matches",
                value=f"{db_info.get('matches', 0):,}",
                delta=None
            )
        
        with col4:
            st.metric(
                label="Competitions",
                value=f"{db_info.get('competitions', 0)}",
                delta=None
            )
        
        # Database structure
        st.subheader("🗄️ Database Structure")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Tables in Database:**")
            for table, count in db_info.items():
                st.write(f"• **{table}**: {count:,} records")
        
        with col2:
            # Top players preview
            st.write("**Top 5 Players by CA:**")
            top_5 = attributes_df.head(5)[['player_name', 'CA', 'PA']]
            for _, player in top_5.iterrows():
                st.write(f"• **{player['player_name']}**: CA {player['CA']:.1f}, PA {player['PA']:.1f}")
        
        # Attribute distributions
        st.subheader("📈 Attribute Distributions")
        
        # Select attributes to visualize
        attr_categories = {
            "Technical": ['passing', 'shooting', 'dribbling', 'first_touch', 'crossing', 'finishing'],
            "Physical": ['pace', 'acceleration', 'stamina', 'strength', 'jumping_reach'],
            "Mental": ['positioning', 'vision', 'composure', 'concentration', 'decisions', 'leadership'],
            "Defensive": ['tackling', 'marking', 'heading'],
            "Goalkeeping": ['goalkeeping', 'reflexes', 'handling', 'kicking']
        }
        
        selected_category = st.selectbox("Select attribute category:", list(attr_categories.keys()))
        selected_attrs = attr_categories[selected_category]
        
        # Create distribution plot
        fig = make_subplots(rows=2, cols=3, subplot_titles=selected_attrs[:6])
        
        for i, attr in enumerate(selected_attrs[:6]):
            row = (i // 3) + 1
            col = (i % 3) + 1
            
            fig.add_trace(
                go.Histogram(x=attributes_df[attr], name=attr, showlegend=False),
                row=row, col=col
            )
        
        fig.update_layout(
            title=f"{selected_category} Attributes Distribution",
            height=600,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Player Search Page
    elif page == "🔍 Player Search":
        st.header("🔍 Player Search & Analysis")
        
        # Search functionality
        search_term = st.text_input("🔍 Search for a player:", placeholder="Enter player name...")
        
        if search_term:
            search_results = search_players(search_term, 20)
            
            if not search_results.empty:
                st.success(f"Found {len(search_results)} players matching '{search_term}'")
                
                # Display search results
                for _, player in search_results.iterrows():
                    with st.expander(f"👤 {player['player_name']} (CA: {player['CA']:.1f}, PA: {player['PA']:.1f})"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write("**Basic Info:**")
                            st.write(f"• Current Ability: {player['CA']:.1f}")
                            st.write(f"• Potential Ability: {player['PA']:.1f}")
                        
                        with col2:
                            st.write("**Key Attributes:**")
                            st.write(f"• Passing: {player['passing']:.1f}")
                            st.write(f"• Shooting: {player['shooting']:.1f}")
                            st.write(f"• Dribbling: {player['dribbling']:.1f}")
                        
                        with col3:
                            st.write("**Performance:**")
                            if pd.notna(player['goals_per90']):
                                st.write(f"• Goals/90: {player['goals_per90']:.2f}")
                            if pd.notna(player['assists_per90']):
                                st.write(f"• Assists/90: {player['assists_per90']:.2f}")
                            if pd.notna(player['minutes_played']):
                                st.write(f"• Minutes: {player['minutes_played']:,}")
                
                # Player comparison
                st.subheader("🆚 Player Comparison")
                
                if len(search_results) >= 2:
                    player1_name = st.selectbox("Select first player:", search_results['player_name'].tolist())
                    player2_name = st.selectbox("Select second player:", 
                                              [p for p in search_results['player_name'].tolist() if p != player1_name])
                    
                    if st.button("Compare Players"):
                        player1_data = search_results[search_results['player_name'] == player1_name].iloc[0]
                        player2_data = search_results[search_results['player_name'] == player2_name].iloc[0]
                        
                        # Create comparison chart
                        radar_attrs = ['passing', 'shooting', 'dribbling', 'pace', 'tackling', 'goalkeeping']
                        
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatterpolar(
                            r=[player1_data[attr] for attr in radar_attrs],
                            theta=radar_attrs,
                            fill='toself',
                            name=player1_name,
                            line_color='blue'
                        ))
                        
                        fig.add_trace(go.Scatterpolar(
                            r=[player2_data[attr] for attr in radar_attrs],
                            theta=radar_attrs,
                            fill='toself',
                            name=player2_name,
                            line_color='red'
                        ))
                        
                        fig.update_layout(
                            polar=dict(radialaxis=dict(visible=True, range=[0, 20])),
                            title=f"{player1_name} vs {player2_name}",
                            height=500
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"No players found matching '{search_term}'")
    
    # Analytics Page
    elif page == "📈 Analytics":
        st.header("📈 Advanced Analytics")
        
        # Attribute correlations
        st.subheader("🔗 Attribute Correlations")
        
        # Select attributes for correlation
        all_attrs = ['passing', 'shooting', 'dribbling', 'pace', 'stamina', 'tackling', 'goalkeeping', 'CA', 'PA']
        selected_attrs = st.multiselect("Select attributes for correlation:", all_attrs, default=all_attrs[:6])
        
        if selected_attrs:
            corr_data = attributes_df[selected_attrs].corr()
            
            fig = px.imshow(
                corr_data,
                text_auto=True,
                aspect="auto",
                title="Attribute Correlation Matrix",
                color_continuous_scale="RdBu_r"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # CA vs PA analysis
        st.subheader("📊 CA vs PA Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Scatter plot
            fig = px.scatter(
                attributes_df, 
                x='CA', 
                y='PA',
                title="Current Ability vs Potential Ability",
                labels={'CA': 'Current Ability', 'PA': 'Potential Ability'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Position-specific CA comparison
            pos_cols = ['CA_GK', 'CA_DEF', 'CA_MID', 'CA_FWD']
            pos_means = [attributes_df[col].mean() for col in pos_cols]
            pos_labels = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
            
            fig = px.bar(
                x=pos_labels,
                y=pos_means,
                title="Average CA by Position",
                labels={'x': 'Position', 'y': 'Average CA'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Top Players Page
    elif page == "🏆 Top Players":
        st.header("🏆 Top Players Analysis")
        
        # Top players by different metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🥇 Top 10 by Current Ability")
            top_ca = attributes_df.head(10)[['player_name', 'CA', 'PA']]
            
            fig = px.bar(
                top_ca,
                x='CA',
                y='player_name',
                orientation='h',
                title="Top 10 Players by CA",
                labels={'CA': 'Current Ability', 'player_name': 'Player'}
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🚀 Top 10 by Potential Ability")
            top_pa = attributes_df.nlargest(10, 'PA')[['player_name', 'CA', 'PA']]
            
            fig = px.bar(
                top_pa,
                x='PA',
                y='player_name',
                orientation='h',
                title="Top 10 Players by PA",
                labels={'PA': 'Potential Ability', 'player_name': 'Player'}
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Player radar charts
        st.subheader("🎯 Player Radar Charts")
        
        selected_player = st.selectbox("Select a player for radar chart:", attributes_df['player_name'].head(20))
        
        if selected_player:
            player_data = attributes_df[attributes_df['player_name'] == selected_player].iloc[0]
            radar_fig = create_radar_chart(player_data, selected_player)
            st.plotly_chart(radar_fig, use_container_width=True)
    
    # Performance Page
    elif page == "⚽ Performance":
        st.header("⚽ Performance Statistics")
        
        if not stats_df.empty:
            # Performance metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_goals = stats_df['goals_per90'].mean()
                st.metric("Avg Goals/90", f"{avg_goals:.2f}")
            
            with col2:
                avg_assists = stats_df['assists_per90'].mean()
                st.metric("Avg Assists/90", f"{avg_assists:.2f}")
            
            with col3:
                avg_pass_acc = stats_df['pass_accuracy'].mean()
                st.metric("Avg Pass Accuracy", f"{avg_pass_acc:.1f}%")
            
            with col4:
                total_minutes = stats_df['minutes_played'].sum()
                st.metric("Total Minutes", f"{total_minutes:,}")
            
            # Top performers
            st.subheader("🏆 Top Performers")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Top 10 Goal Scorers (per 90):**")
                top_goals = stats_df.nlargest(10, 'goals_per90')[['player_name', 'goals_per90', 'minutes_played']]
                
                fig = px.bar(
                    top_goals,
                    x='goals_per90',
                    y='player_name',
                    orientation='h',
                    title="Top 10 Goal Scorers",
                    labels={'goals_per90': 'Goals per 90', 'player_name': 'Player'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.write("**Top 10 Assist Leaders (per 90):**")
                top_assists = stats_df.nlargest(10, 'assists_per90')[['player_name', 'assists_per90', 'minutes_played']]
                
                fig = px.bar(
                    top_assists,
                    x='assists_per90',
                    y='player_name',
                    orientation='h',
                    title="Top 10 Assist Leaders",
                    labels={'assists_per90': 'Assists per 90', 'player_name': 'Player'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Goals vs xG analysis
            st.subheader("📊 Goals vs Expected Goals")
            
            if 'xG_per90' in stats_df.columns:
                fig = px.scatter(
                    stats_df,
                    x='xG_per90',
                    y='goals_per90',
                    title="Goals per 90 vs Expected Goals per 90",
                    labels={'xG_per90': 'Expected Goals per 90', 'goals_per90': 'Goals per 90'},
                    hover_data=['player_name']
                )
                
                # Add diagonal line
                max_val = max(stats_df['xG_per90'].max(), stats_df['goals_per90'].max())
                fig.add_shape(
                    type="line",
                    x0=0, y0=0, x1=max_val, y1=max_val,
                    line=dict(dash="dash", color="red")
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No performance statistics available. Please run the data collection script first.")
    
    # Footer
    st.markdown("---")
    st.markdown("⚽ **Football Scout Dashboard** - Powered by StatsBomb Data")

if __name__ == "__main__":
    main()
