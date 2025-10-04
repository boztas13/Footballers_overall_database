# ⚽ Football Scout Dashboard

A beautiful, interactive web dashboard for analyzing football player data from StatsBomb. Built with Streamlit and Plotly for professional visualizations.

## 🚀 Quick Start

### Option 1: Simple Launch
```bash
python run_dashboard.py
```

### Option 2: Direct Streamlit
```bash
streamlit run football_dashboard.py
```

The dashboard will open at: **http://localhost:8501**

## 🎯 Features

### 📊 **Overview Page**
- **Database Statistics**: Total players, matches, competitions
- **Top Players Preview**: Best players by CA and PA
- **Attribute Distributions**: Interactive histograms for all attribute categories
- **Database Structure**: Complete overview of your data

### 🔍 **Player Search**
- **Real-time Search**: Find players by name with instant results
- **Player Profiles**: Detailed attribute breakdowns
- **Player Comparison**: Side-by-side radar chart comparisons
- **Performance Stats**: Goals, assists, minutes played

### 📈 **Analytics**
- **Correlation Matrix**: See which attributes are related
- **CA vs PA Analysis**: Current vs Potential Ability scatter plots
- **Position Analysis**: Average abilities by position
- **Interactive Heatmaps**: Beautiful correlation visualizations

### 🏆 **Top Players**
- **CA Rankings**: Top players by Current Ability
- **PA Rankings**: Top players by Potential Ability
- **Radar Charts**: Visual player attribute profiles
- **Interactive Selection**: Choose any player for detailed analysis

### ⚽ **Performance**
- **Performance Metrics**: Goals/90, Assists/90, Pass Accuracy
- **Top Performers**: Best goal scorers and assist leaders
- **Goals vs xG**: Expected vs actual performance analysis
- **Statistical Insights**: Key performance indicators

## 🎨 Dashboard Features

### **Interactive Visualizations**
- **Plotly Charts**: Professional, interactive charts
- **Radar Charts**: Player attribute profiles
- **Scatter Plots**: Relationship analysis
- **Bar Charts**: Ranking visualizations
- **Heatmaps**: Correlation matrices

### **User Interface**
- **Responsive Design**: Works on desktop and mobile
- **Sidebar Navigation**: Easy page switching
- **Search Functionality**: Real-time player search
- **Expandable Cards**: Detailed player information
- **Custom Styling**: Professional football theme

### **Data Features**
- **Caching**: Fast loading with intelligent caching
- **Real-time Updates**: Live data from your database
- **Filtering**: Search and filter capabilities
- **Export Ready**: Professional visualizations

## 📊 Data Requirements

The dashboard requires a populated database with the following tables:
- `player_attributes`: Player attribute ratings (1-20 scale)
- `player_stats`: Performance statistics
- `players`: Basic player information
- `matches`: Match data
- `competitions`: Competition information

## 🛠️ Technical Details

### **Built With**
- **Streamlit**: Web framework for data apps
- **Plotly**: Interactive visualizations
- **Pandas**: Data manipulation
- **SQLite**: Database backend

### **Performance**
- **Caching**: Data is cached for fast loading
- **Optimized Queries**: Efficient database queries
- **Responsive**: Smooth interactions

### **Browser Support**
- Chrome (recommended)
- Firefox
- Safari
- Edge

## 🎯 Usage Guide

### **Getting Started**
1. **Ensure Database Exists**: Run `python map_stats_bomb_db.py` first
2. **Launch Dashboard**: Run `python run_dashboard.py`
3. **Open Browser**: Navigate to http://localhost:8501
4. **Explore**: Use the sidebar to navigate between pages

### **Navigation**
- **📊 Overview**: Database summary and distributions
- **🔍 Player Search**: Find and compare players
- **📈 Analytics**: Advanced statistical analysis
- **🏆 Top Players**: Rankings and radar charts
- **⚽ Performance**: Performance statistics

### **Player Search Tips**
- **Partial Names**: Search for "Messi" to find "Lionel Messi"
- **Case Insensitive**: Works with any capitalization
- **Real-time**: Results update as you type

### **Comparison Features**
- **Select Players**: Choose from search results
- **Radar Charts**: Visual attribute comparison
- **Side-by-side**: Direct attribute comparisons

## 📈 Understanding the Data

### **Attribute Ratings (1-20 Scale)**
- **1-5**: Poor
- **6-10**: Below Average
- **11-15**: Average
- **16-20**: Excellent

### **Key Metrics**
- **CA (Current Ability)**: Overall current skill level
- **PA (Potential Ability)**: Maximum potential skill level
- **Per 90 Stats**: Statistics normalized to 90-minute games
- **Pass Accuracy**: Percentage of successful passes

### **Position-Specific Ratings**
- **CA_GK**: Goalkeeper ability
- **CA_DEF**: Defender ability
- **CA_MID**: Midfielder ability
- **CA_FWD**: Forward ability

## 🔧 Customization

### **Adding New Visualizations**
1. Create new functions in the dashboard
2. Add new pages to the sidebar
3. Use Plotly for interactive charts
4. Leverage Streamlit components

### **Modifying Data Sources**
1. Update the database connection
2. Modify the SQL queries
3. Adjust caching as needed
4. Test with your data

### **Styling Changes**
1. Modify the CSS in the dashboard
2. Update colors and themes
3. Add custom components
4. Enhance user experience

## 🚨 Troubleshooting

### **Common Issues**

**Dashboard won't start:**
- Check if Streamlit is installed: `pip install streamlit`
- Ensure database exists: `python map_stats_bomb_db.py`
- Check port 8501 is available

**No data showing:**
- Verify database has data
- Check table names match expected format
- Run data collection script first

**Slow loading:**
- Clear browser cache
- Check database size
- Restart the dashboard

### **Performance Tips**
- Use the caching features
- Limit data queries
- Optimize database indexes
- Use appropriate data types

## 📱 Mobile Support

The dashboard is responsive and works on mobile devices:
- **Touch-friendly**: All interactions work on touch
- **Responsive Layout**: Adapts to screen size
- **Mobile Navigation**: Easy sidebar access
- **Optimized Charts**: Charts scale to screen size

## 🎨 Visual Features

### **Color Scheme**
- **Primary**: Blue (#1f77b4)
- **Secondary**: Light blue, green, orange
- **Background**: Clean white and light gray
- **Text**: Dark gray for readability

### **Chart Types**
- **Bar Charts**: Rankings and comparisons
- **Scatter Plots**: Relationship analysis
- **Radar Charts**: Multi-attribute profiles
- **Heatmaps**: Correlation matrices
- **Histograms**: Distribution analysis

## 🏆 Best Practices

### **Data Analysis**
1. Start with Overview page for context
2. Use Player Search for specific players
3. Apply Analytics for insights
4. Check Top Players for rankings
5. Review Performance for stats

### **Player Comparison**
1. Search for players of interest
2. Use comparison feature
3. Analyze radar charts
4. Look at performance stats
5. Consider position-specific ratings

## 📊 Data Insights

The dashboard helps you discover:
- **Player Strengths**: High-rated attributes
- **Development Potential**: CA vs PA analysis
- **Position Suitability**: Position-specific ratings
- **Performance Trends**: Statistical analysis
- **Player Comparisons**: Direct attribute comparisons

## 🎯 Use Cases

### **Scouting**
- Find players with specific attributes
- Compare potential signings
- Analyze player development
- Identify undervalued players

### **Analysis**
- Understand attribute relationships
- Analyze performance statistics
- Study player distributions
- Research football metrics

### **Reporting**
- Generate professional reports
- Create player profiles
- Share visualizations
- Present findings

## 🚀 Advanced Features

### **Interactive Elements**
- **Hover Information**: Detailed tooltips
- **Zoom and Pan**: Chart interactions
- **Filtering**: Dynamic data filtering
- **Sorting**: Column sorting capabilities

### **Export Options**
- **Screenshot Charts**: Save visualizations
- **Data Export**: Download filtered data
- **Report Generation**: Professional reports
- **Sharing**: Easy sharing of insights

Enjoy exploring your football data with this comprehensive dashboard! ⚽📊🎯
